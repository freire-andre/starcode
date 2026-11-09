#!/usr/bin/env python3
"""Scaffold de projetos a partir dos perfis de stack (R9-R19, R40, R41, R45). Só stdlib.

  scaffold.py list [--json]
  scaffold.py versions <app>[+<db>] [--json]
  scaffold.py new <pasta> --profile <app> [--db <db>] [--name N] [--description "<frase>"]
                  [--pin-tested | --allow-new-series]
  scaffold.py detect <repo> [--json]
  scaffold.py record <repo> --profiles a[,b] [--yes]
  scaffold.py checks <pasta> [--json]
  scaffold.py gates <pasta> [--json] [--timeout-min 30]

Perfis em <script>/../profiles (STARCODE_PROFILES_DIR substitui). STARCODE_REGISTRY_FIXTURE troca o registro.
Exit: 0 ok | 1 falha (geração, gate FAIL, stack.json ausente) | 2 uso/entrada inválida ou registro
indisponível | 3 gate SKIP sem FAIL | 5 versão fora da série testada.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import registry  # noqa: E402

NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
GATE_ORDER = ("lint", "typecheck", "unit", "build", "integration")
BUILD_KEYS = ("lint", "typecheck", "build")
_MARK = re.compile(r"\{\{\s*(name|module|description|version:[^}\s]+)\s*\}\}")


class ScaffoldError(Exception):
    def __init__(self, message: str, code: int = 2) -> None:
        super().__init__(message)
        self.code = code


# --- leitor YAML (subconjunto do tools/miniyaml.py, com coleções de fluxo aninhadas) -------------------

def _strip_comment(line: str) -> str:
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


def _scalar(text: str):
    t = text.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        return t[1:-1]
    if t in ("true", "false"):
        return t == "true"
    if t in ("null", "~", ""):
        return None
    if re.fullmatch(r"[-+]?\d+", t):
        return int(t)
    if re.fullmatch(r"[-+]?\d+\.\d+", t):
        return float(t)
    return t


def _split_top(text: str, sep: str) -> list[str]:
    parts, depth, quote, cur = [], 0, None, []
    for ch in text:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch in "[{":
            depth += 1
            cur.append(ch)
        elif ch in "]}":
            depth -= 1
            cur.append(ch)
        elif ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def _flow(text: str):
    t = text.strip()
    if t.startswith("[") and t.endswith("]"):
        inner = t[1:-1].strip()
        return [_flow(p) for p in _split_top(inner, ",")] if inner else []
    if t.startswith("{") and t.endswith("}"):
        inner = t[1:-1].strip()
        out = {}
        for item in _split_top(inner, ",") if inner else []:
            kv = _split_top(item, ":")
            if len(kv) < 2:
                raise ValueError(f"item de mapa inválido: {item!r}")
            out[_scalar(kv[0])] = _flow(":".join(kv[1:]))
        return out
    return _scalar(t)


_KEY = re.compile(r"""^("[^"]*"|'[^']*'|[^\s"'\[\]{},#:][^:]*?):(?:\s+(.*))?$""")


def loads(text: str):
    lines = []
    for raw in text.splitlines():
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ValueError("tabulação na indentação")
        s = _strip_comment(raw).rstrip()
        if s.strip():
            lines.append((len(s) - len(s.lstrip(" ")), s.strip()))

    def block(i: int, indent: int):
        if lines[i][1].startswith("- ") or lines[i][1] == "-":
            return seq(i, indent)
        return mapping(i, indent)

    def seq(i: int, indent: int):
        out = []
        while i < len(lines) and lines[i][0] == indent and (lines[i][1].startswith("- ") or lines[i][1] == "-"):
            content = lines[i][1][1:].strip()
            if not content:
                i += 1
                if i < len(lines) and lines[i][0] > indent:
                    val, i = block(i, lines[i][0])
                else:
                    val = None
                out.append(val)
            elif content[0] not in "[{\"'" and _KEY.match(content):
                lines[i] = (indent + 2, content)
                val, i = mapping(i, indent + 2)
                out.append(val)
            else:
                out.append(_flow(content))
                i += 1
        return out, i

    def mapping(i: int, indent: int):
        out = {}
        while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("- "):
            m = _KEY.match(lines[i][1])
            if not m:
                raise ValueError(f"linha inválida: {lines[i][1]!r}")
            key, rest = _scalar(m.group(1)), (m.group(2) or "").strip()
            i += 1
            if rest:
                out[key] = _flow(rest)
            elif i < len(lines) and (lines[i][0] > indent or (lines[i][0] == indent and lines[i][1].startswith("- "))):
                out[key], i = block(i, lines[i][0])
            else:
                out[key] = None
        return out, i

    if not lines:
        return {}
    val, i = block(0, lines[0][0])
    if i != len(lines):
        raise ValueError(f"indentação inesperada: {lines[i][1]!r}")
    return val


# --- perfis ------------------------------------------------------------------------------------------

def profiles_dir() -> Path:
    env = os.environ.get("STARCODE_PROFILES_DIR")
    return Path(env) if env else HERE.parent / "profiles"


def load_profiles() -> dict[str, dict]:
    out: dict[str, dict] = {}
    base = profiles_dir()
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir()):
        f = d / "profile.yaml"
        if not f.is_file():
            continue
        try:
            doc = loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise ScaffoldError(f"perfil {d.name} ilegível: {exc}") from exc
        if not isinstance(doc, dict):
            raise ScaffoldError(f"perfil {d.name} ilegível: esperava um mapa")
        doc.setdefault("name", d.name)
        doc["_dir"] = d
        out[doc["name"]] = doc
    return out


def valid_summary(profiles: dict[str, dict]) -> str:
    apps = [p for p in profiles.values() if p.get("kind") == "app"]
    dbs = [p["name"] for p in profiles.values() if p.get("kind") == "db"]
    combos = [f"{a['name']}+{d}" for a in apps for d in (a.get("combinesWith") or []) if d in dbs]
    return (f"perfis de app: {', '.join(a['name'] for a in apps) or '-'}; "
            f"perfis de banco: {', '.join(dbs) or '-'}; combinações válidas: {', '.join(combos) or '-'}")


def pick(profiles: dict[str, dict], app: str, db: str | None) -> list[dict]:
    a = profiles.get(app)
    if not a or a.get("kind") != "app":
        raise ScaffoldError(f"perfil inexistente: {app}. Válidos — {valid_summary(profiles)}")
    chosen = [a]
    if db:
        d = profiles.get(db)
        if not d or d.get("kind") != "db" or db not in (a.get("combinesWith") or []):
            raise ScaffoldError(f"combinação inexistente: {app}+{db}. Válidos — {valid_summary(profiles)}")
        chosen.append(d)
    return chosen


# --- versões -----------------------------------------------------------------------------------------

def _tested(dep: dict) -> str | None:
    t = dep.get("tested")
    return None if t is None else str(t)


def resolve_versions(chosen: list[dict]) -> dict:
    """{'versions': {pkg: entry}, 'image': {profile: 'img:major'}, 'outside': [...]}; levanta ScaffoldError."""
    at = datetime.now(timezone.utc).date().isoformat()
    source = registry.source()
    deps: dict[str, dict] = {}
    for prof in chosen:
        for dep in prof.get("deps") or []:
            deps.setdefault(dep["name"], dep)
    forced: dict[str, str] = {}
    try:
        for group in chosen[0].get("alignMajor") or []:
            src = deps.get(group["from"])
            if src is None:
                raise ScaffoldError(f"alignMajor: {group['from']} não está em deps")
            major = registry.latest_stable(src["registry"], src["name"]).split(".")[0]
            forced[src["name"]] = registry.latest_stable(src["registry"], src["name"], series=major)
            for name in group.get("deps") or []:
                dep = deps.get(name)
                if dep is None:
                    raise ScaffoldError(f"alignMajor: {name} não está em deps")
                try:
                    forced[name] = registry.latest_stable(dep["registry"], name, series=major)
                except registry.RegistryError as exc:
                    if "sem série" in str(exc):
                        kind = "crate" if dep["registry"] == "crates" else "pacote"
                        raise ScaffoldError(f"{name}: {kind} sem versão estável no major {major}") from exc
                    raise
        versions: dict[str, dict] = {}
        outside = []
        for name, dep in deps.items():
            version = forced.get(name) or registry.latest_stable(dep["registry"], name)
            entry = {"version": version, "registry": dep["registry"], "source": source, "at": at}
            series = _tested(dep)
            if series and not registry.in_series(version, series):
                try:
                    newest = registry.latest_stable(dep["registry"], name, series=series)
                except registry.RegistryError as exc:
                    if "sem série" not in str(exc):
                        raise
                    newest = None
                outside.append({"name": name, "version": version, "series": series, "newest": newest})
            versions[name] = entry
        image = {}
        for prof in chosen:
            img = prof.get("image")
            if img:
                major = registry.latest_stable(img["registry"], img["name"])
                image[prof["name"]] = f"{img['name']}:{major}"
                versions.setdefault(img["name"], {"version": major, "registry": img["registry"],
                                                  "source": source, "at": at, "image": True})
    except registry.RegistryError as exc:
        raise ScaffoldError(str(exc)) from exc
    return {"versions": versions, "image": image, "outside": outside}


def apply_series_policy(res: dict, pin: bool, allow_new: bool) -> None:
    if not res["outside"]:
        return
    if not (pin or allow_new):
        msgs = [f"{o['name']} {o['version']} fora da série testada {o['series']}: "
                "use --pin-tested ou --allow-new-series" for o in res["outside"]]
        raise ScaffoldError("\n".join(msgs), 5)
    for o in res["outside"]:
        entry = res["versions"][o["name"]]
        if pin:
            if not o["newest"]:
                raise ScaffoldError(f"{o['name']}: sem versão estável na série testada {o['series']}")
            entry["version"] = o["newest"]
        else:
            entry["outsideTested"] = True


def parse_combo(spec: str) -> tuple[str, str | None]:
    app, _, db = spec.partition("+")
    return app, db or None


def cmd_list(args) -> int:
    profiles = load_profiles()
    if args.json:
        print(json.dumps({"profiles": {n: p.get("kind") for n, p in profiles.items()},
                          "summary": valid_summary(profiles)}, ensure_ascii=False))
    else:
        for n, p in profiles.items():
            extra = " (experimental)" if p.get("experimental") else ""
            print(f"{n} [{p.get('kind')}]{extra}")
        print(valid_summary(profiles))
    return 0


def cmd_versions(args) -> int:
    app, db = parse_combo(args.combo)
    chosen = pick(load_profiles(), app, db)
    res = resolve_versions(chosen)
    outside = {o["name"]: o for o in res["outside"]}
    if args.json:
        data = {"profiles": [p["name"] for p in chosen], "image": res["image"], "versions": {}}
        for n, e in res["versions"].items():
            item = dict(e)
            if n in outside:
                item.update(outsideTested=True, testedSeries=outside[n]["series"], newestInTested=outside[n]["newest"])
            data["versions"][n] = item
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    for n, e in res["versions"].items():
        line = f"{n} {e['version']} ({e['registry']})"
        if n in outside:
            o = outside[n]
            line += f" — fora da série testada ({o['series']}); mais nova da série: {o['newest'] or 'nenhuma'}"
        print(line)
    return 0


# --- new ---------------------------------------------------------------------------------------------

def render(text: str, ctx: dict) -> str:
    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key.startswith("version:"):
            pkg = key.split(":", 1)[1]
            if pkg not in ctx["versions"]:
                raise ScaffoldError(f"marcador sem versão resolvida: {{{{{key}}}}}", 1)
            return ctx["versions"][pkg]["version"]
        return ctx[key]
    return _MARK.sub(sub, text)


def copy_template(src: Path, dest: Path, ctx: dict, written: set[Path]) -> None:
    for path in sorted(src.rglob("*")):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        rel = Path(*[render(p, ctx) for p in path.relative_to(src).parts])
        target = dest / rel
        if target in written:
            raise ScaffoldError(f"arquivo duplicado entre templates: {rel.as_posix()}", 1)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = path.read_bytes()
        try:
            target.write_text(render(data.decode("utf-8"), ctx), encoding="utf-8", newline="")
        except UnicodeDecodeError:
            target.write_bytes(data)
        written.add(target)


def apply_inject(db: dict, dest: Path, ctx: dict) -> None:
    for item in db.get("inject") or []:
        target = dest / item["file"]
        if not target.is_file():
            raise ScaffoldError(f"inject: arquivo {item['file']} ausente no template do app", 1)
        out, hit = [], False
        for line in target.read_text(encoding="utf-8").splitlines(keepends=True):
            if not hit and item["marker"] in line:
                hit = True
                indent = line[: len(line) - len(line.lstrip())]
                eol = "\r\n" if line.endswith("\r\n") else "\n"
                out.extend(indent + render(str(x), ctx) + eol for x in item.get("lines") or [])
            else:
                out.append(line)
        if not hit:
            raise ScaffoldError(f"inject: marcador {item['marker']!r} ausente em {item['file']}", 1)
        target.write_text("".join(out), encoding="utf-8", newline="")


def validate_inputs(args, folder: Path) -> tuple[str, str]:
    name = args.name or folder.name
    if not NAME_RE.fullmatch(name):
        raise ScaffoldError("nome inválido: use minúsculas, dígitos e hífen, começando por letra")
    desc = args.description if args.description is not None else f"Projeto {name}."
    if "\n" in desc or "\r" in desc or len(desc) > 200 or not desc.strip():
        raise ScaffoldError("descrição inválida: uma linha, até 200 caracteres")
    # só `.specs/` é aceito: é o cache que a skill nova-missao grava antes do `new` (R31)
    if folder.exists() and (not folder.is_dir() or any(c.name != ".specs" for c in folder.iterdir())):
        raise ScaffoldError(f"pasta não vazia: {folder}")
    return name, desc


def cmd_new(args) -> int:
    folder = Path(args.folder).resolve()
    name, desc = validate_inputs(args, folder)
    chosen = pick(load_profiles(), args.profile, args.db)
    res = resolve_versions(chosen)  # antes de escrever qualquer arquivo
    apply_series_policy(res, args.pin_tested, args.allow_new_series)
    ctx = {"name": name, "module": name.replace("-", "_"), "description": desc, "versions": res["versions"]}

    pre_existing = folder.exists()
    keep_specs = pre_existing and (folder / ".specs").exists()
    top = folder
    while not pre_existing and not top.parent.exists():
        top = top.parent
    try:
        folder.mkdir(parents=True, exist_ok=True)
        written: set[Path] = set()
        for prof in chosen:
            tpl = prof["_dir"] / "template"
            if tpl.is_dir():
                copy_template(tpl, folder, ctx, written)
        for prof in chosen[1:]:
            apply_inject(prof, folder, ctx)
            script = HERE / "ephemeral_db.py"
            if prof.get("kind") == "db":
                (folder / "scripts").mkdir(exist_ok=True)
                shutil.copyfile(script, folder / "scripts" / "ephemeral_db.py")
        stack = {"schemaVersion": 1, "profiles": [p["name"] for p in chosen],
                 "versions": {n: {k: v for k, v in e.items() if k != "image"}
                              for n, e in res["versions"].items() if not e.get("image")}}
        if res["image"]:
            stack["image"] = res["image"]
        (folder / ".starcode").mkdir(exist_ok=True)
        (folder / ".starcode" / "stack.json").write_text(
            json.dumps(stack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - qualquer falha desfaz o que esta execução criou
        _cleanup(folder, top, pre_existing, keep_specs)
        code = exc.code if isinstance(exc, ScaffoldError) else 1
        print(f"falha na geração: {exc}", file=sys.stderr)
        return code if code == 1 else 1

    for n, e in res["versions"].items():
        print(f"{n} {e['version']} ({e['registry']}, {e['at']})")
    print(f"template: {'+'.join(p['name'] for p in chosen)}")
    print(f"pasta: {folder}")
    return 0


def _cleanup(folder: Path, top: Path, pre_existing: bool, keep_specs: bool = False) -> None:
    def onerr(func, path, _exc):  # arquivos somente leitura no Windows
        os.chmod(path, 0o700)
        func(path)
    if pre_existing:
        for child in folder.iterdir():
            if keep_specs and child.name == ".specs":
                continue  # já existia antes desta execução
            shutil.rmtree(child, onerror=onerr) if child.is_dir() else child.unlink()
    elif top.exists():
        shutil.rmtree(top, onerror=onerr)


# --- detect / record (repo existente, R31) ---------------------------------------------------------------

_VER = re.compile(r"\d+(?:\.\d+)*")
_DB_DEPS = {"psycopg": "postgresql", "psycopg2": "postgresql", "pymysql": "mysql"}


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _same(name: str) -> str:
    return name


def _read_toml(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return {}


def _read_json(path: Path) -> dict:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return doc if isinstance(doc, dict) else {}


def _spec_version(spec) -> str | None:
    m = _VER.search(spec) if isinstance(spec, str) else None
    return m.group(0) if m else None


def _py_manifest(repo: Path) -> dict[str, str | None]:
    """{nome normalizado: versão do manifesto | None}."""
    doc = _read_toml(repo / "pyproject.toml")
    project = doc.get("project") or {}
    specs: list[str] = list(project.get("dependencies") or [])
    for group in (project.get("optional-dependencies") or {}).values():
        specs += [x for x in group if isinstance(x, str)]
    for group in (doc.get("dependency-groups") or {}).values():
        specs += [x for x in group if isinstance(x, str)]
    specs += [x for x in ((doc.get("tool") or {}).get("uv") or {}).get("dev-dependencies") or []
              if isinstance(x, str)]
    out: dict[str, str | None] = {}
    for spec in specs:
        m = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(.*)", spec)
        if m:
            out.setdefault(_norm(m.group(1)), _spec_version(m.group(2)))
    return out


def _lock_versions(path: Path, norm=_norm) -> dict[str, str]:
    return {norm(p["name"]): str(p["version"]) for p in _read_toml(path).get("package") or []
            if isinstance(p, dict) and "name" in p and "version" in p}


def _npm_manifest(repo: Path) -> dict[str, str | None]:
    doc = _read_json(repo / "package.json")
    out: dict[str, str | None] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        for name, spec in (doc.get(key) or {}).items():
            out.setdefault(name, _spec_version(spec))
    return out


def _npm_lock(repo: Path) -> dict[str, str]:
    pk = _read_json(repo / "package-lock.json").get("packages") or {}
    prefix = "node_modules/"
    return {k[len(prefix):]: str(v["version"]) for k, v in pk.items()
            if k.startswith(prefix) and prefix not in k[len(prefix):] and isinstance(v, dict) and "version" in v}


def _cargo_dirs(repo: Path) -> list[Path]:
    return [d for d in (repo, repo / "src-tauri") if (d / "Cargo.toml").is_file()]


def _cargo_manifest(repo: Path) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for d in _cargo_dirs(repo):
        doc = _read_toml(d / "Cargo.toml")
        for key in ("dependencies", "dev-dependencies", "build-dependencies"):
            for name, spec in (doc.get(key) or {}).items():
                out.setdefault(name, _spec_version(spec.get("version") if isinstance(spec, dict) else spec))
    return out


def _cargo_lock(repo: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for d in _cargo_dirs(repo):
        for name, ver in _lock_versions(d / "Cargo.lock", norm=_same).items():
            out.setdefault(name, ver)
    return out


def detect_profiles(repo: Path) -> dict:
    py, npm, cargo = _py_manifest(repo), _npm_manifest(repo), _cargo_manifest(repo)
    apps: list[str] = []
    evidence: dict[str, str] = {}
    tauri = (repo / "src-tauri" / "tauri.conf.json").is_file()
    if "flask" in py:
        apps.append("python-flask")
        evidence["python-flask"] = "pyproject.toml com flask"
    if tauri:
        apps.append("tauri")
        evidence["tauri"] = "src-tauri/tauri.conf.json"
    elif (repo / "Cargo.toml").is_file():
        name = "gpui" if "gpui" in cargo else "rust"
        apps.append(name)
        evidence[name] = "Cargo.toml com gpui" if name == "gpui" else "Cargo.toml"
    if "typescript" in npm and not tauri:  # o perfil tauri já inclui o pacote TS
        apps.append("typescript")
        evidence["typescript"] = "package.json com typescript"
    dbs: list[str] = []
    for dep, prof in _DB_DEPS.items():
        if dep in py and prof not in dbs:
            dbs.append(prof)
            evidence[prof] = f"dependência {dep}"
    return {"profiles": apps + dbs, "apps": apps, "db": dbs, "evidence": evidence,
            "ambiguous": len(apps) > 1 or len(dbs) > 1}


def read_versions(repo: Path, chosen: list[dict]) -> dict[str, dict]:
    lock_py = _lock_versions(repo / "uv.lock") or _lock_versions(repo / "poetry.lock")
    src = {"pypi": (_py_manifest(repo), lock_py, _norm),
           "npm": (_npm_manifest(repo), _npm_lock(repo), _same),
           "crates": (_cargo_manifest(repo), _cargo_lock(repo), _same)}
    at = datetime.now(timezone.utc).date().isoformat()
    out: dict[str, dict] = {}
    for prof in chosen:
        for dep in prof.get("deps") or []:
            manifest, lock, norm = src.get(dep["registry"], ({}, {}, _same))
            key = norm(dep["name"])
            version = lock.get(key) or manifest.get(key)
            if version:
                out.setdefault(dep["name"], {"version": version, "registry": dep["registry"],
                                             "source": "manifest", "at": at})
    return out


def cmd_detect(args) -> int:
    repo = Path(args.repo)
    if not repo.is_dir():
        raise ScaffoldError(f"repositório inexistente: {repo}")
    found = detect_profiles(repo)
    if args.json:
        print(json.dumps(found, ensure_ascii=False, indent=2))
        return 0
    if not found["profiles"]:
        print("nenhum perfil detectado")
    for name in found["profiles"]:
        print(f"{name}: {found['evidence'][name]}")
    if found["ambiguous"]:
        print("perfis misturados: escolha quais registrar (record --profiles a[,b])")
    return 0


def cmd_record(args) -> int:
    repo = Path(args.repo)
    if not repo.is_dir():
        raise ScaffoldError(f"repositório inexistente: {repo}")
    names = [n.strip() for n in args.profiles.split(",") if n.strip()]
    profiles = load_profiles()
    unknown = [n for n in names if n not in profiles]
    if unknown:
        raise ScaffoldError(f"perfil inexistente: {', '.join(unknown)}. Válidos — {valid_summary(profiles)}")
    apps = [n for n in names if profiles[n].get("kind") == "app"]
    dbs = [n for n in names if profiles[n].get("kind") == "db"]
    if len(apps) != 1 or len(dbs) > 1:
        raise ScaffoldError("informe um perfil de app e, no máximo, um de banco. "
                            f"Válidos — {valid_summary(profiles)}")
    chosen = pick(profiles, apps[0], dbs[0] if dbs else None)
    versions = read_versions(repo, chosen)
    stack = {"schemaVersion": 1, "profiles": [p["name"] for p in chosen], "versions": versions}
    print(f"perfis: {'+'.join(stack['profiles'])}")
    for n, e in versions.items():
        print(f"{n} {e['version']} ({e['registry']}, manifest)")
    if not args.yes:
        print("nada gravado: confirme com o usuário e rode de novo com --yes")
        return 0
    (repo / ".starcode").mkdir(exist_ok=True)
    (repo / ".starcode" / "stack.json").write_text(
        json.dumps(stack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"gravado: {repo / '.starcode' / 'stack.json'}")
    return 0


# --- checks / gates ----------------------------------------------------------------------------------

def load_stack(folder: Path) -> tuple[dict, list[dict]]:
    f = folder / ".starcode" / "stack.json"
    if not f.is_file():
        raise ScaffoldError("perfil não registrado: rode o Scotty", 1)
    try:
        stack = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScaffoldError(f"stack.json ilegível: {exc}", 1) from exc
    profiles = load_profiles()
    chosen = []
    for n in stack.get("profiles", []):
        if n not in profiles:
            raise ScaffoldError(f"perfil {n} do stack.json não existe em {profiles_dir()}", 1)
        chosen.append(profiles[n])
    return stack, chosen


def gate_items(prof: dict, key: str) -> list[tuple[str, str | None]]:
    out = []
    for g in (prof.get("gates") or {}).get(key) or []:
        if isinstance(g, dict):
            out.append((str(g.get("run") or g.get("cmd")), g.get("cwd")))
        else:
            out.append((str(g), None))
    return out


def _display(cmd: str, cwd: str | None) -> str:
    return f"{cmd} [{cwd}]" if cwd else cmd


def _joined(items: list[tuple[str, str | None]]) -> str:
    return " && ".join(f"cd {c} && {cmd}" if c else cmd for cmd, c in items)


def cmd_checks(args) -> int:
    _, chosen = load_stack(Path(args.folder))
    lines: dict[str, str] = {}
    build = [i for p in chosen for k in BUILD_KEYS for i in gate_items(p, k)]
    if build:
        lines["Build"] = _joined(build)
    unit = [i for p in chosen for i in gate_items(p, "unit")]
    if unit:
        lines["Run unit"] = _joined(unit)
    integ = [i for p in chosen if p.get("kind") == "db" for i in gate_items(p, "integration")]
    if integ:
        lines["Run integration"] = _joined(integ)
    if args.json:
        print(json.dumps(lines, ensure_ascii=False, indent=2))
    else:
        for k, v in lines.items():
            print(f"**{k}**: `{v}`")
    return 0


def _kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        try:
            os.killpg(proc.pid, 9)
        except OSError:
            proc.kill()


def run_cmd(cmd: str, cwd: Path, timeout_s: float) -> tuple[int | None, str]:
    """(exit code | None no estouro, saída combinada)."""
    argv = shlex.split(cmd)
    if not argv:
        return 127, "comando vazio"
    if argv[0] in ("python", "python3"):
        argv[0] = sys.executable
    else:
        argv[0] = shutil.which(argv[0]) or argv[0]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, env=env, text=True, encoding="utf-8",
                                errors="replace", start_new_session=os.name != "nt")
    except OSError as exc:
        return 127, str(exc)
    try:
        out, _ = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        out, _ = proc.communicate()
        return None, out or ""
    return proc.returncode, out or ""


def cmd_gates(args) -> int:
    folder = Path(args.folder).resolve()
    _, chosen = load_stack(folder)
    all_tools = [t for p in chosen for t in (p.get("tools") or [])]
    plan: list[tuple[str, str | None, list[str]]] = []
    for p in chosen:
        tools = list(p.get("tools") or [])
        for cmd in p.get("install") or []:
            plan.append((str(cmd), None, tools))
    for p in chosen:
        tools = all_tools if p.get("kind") == "db" else list(p.get("tools") or [])
        for key in GATE_ORDER:
            for cmd, cwd in gate_items(p, key):
                plan.append((cmd, cwd, tools))
    results, fail, skip = [], False, False
    timeout_s = args.timeout_min * 60
    for cmd, cwd, tools in plan:
        shown = _display(cmd, cwd)
        missing = next((t for t in tools if not shutil.which(t)), None)
        if missing:
            res = {"status": "SKIP", "cmd": shown, "detail": f"{missing} ausente"}
        else:
            rc, out = run_cmd(cmd, folder / cwd if cwd else folder, timeout_s)
            tail = "\n".join(out.strip().splitlines()[-20:])
            if rc is None:
                res = {"status": "FAIL", "cmd": shown, "detail": f"timeout {args.timeout_min:g} min", "output": tail}
            elif rc == 3 and "ephemeral_db.py" in cmd:
                res = {"status": "SKIP", "cmd": shown, "detail": "Docker indisponível"}
            elif rc != 0:
                res = {"status": "FAIL", "cmd": shown, "detail": "", "output": tail}
            else:
                res = {"status": "PASS", "cmd": shown, "detail": ""}
        fail |= res["status"] == "FAIL"
        skip |= res["status"] == "SKIP"
        results.append(res)
        if not args.json:
            print(f"{res['status']} {res['cmd']}" + (f": {res['detail']}" if res["detail"] else ""), flush=True)
            if res["status"] == "FAIL" and res.get("output"):
                print("\n".join("    " + line for line in res["output"].splitlines()), flush=True)
    code = 1 if fail else 3 if skip else 0
    if args.json:
        print(json.dumps({"results": results, "exit": code}, ensure_ascii=False, indent=2))
    return code


# --- main --------------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="scaffold.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("versions")
    p.add_argument("combo")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("new")
    p.add_argument("folder")
    p.add_argument("--profile", required=True)
    p.add_argument("--db")
    p.add_argument("--name")
    p.add_argument("--description")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--pin-tested", action="store_true")
    g.add_argument("--allow-new-series", action="store_true")
    p = sub.add_parser("detect")
    p.add_argument("repo")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("record")
    p.add_argument("repo")
    p.add_argument("--profiles", required=True)
    p.add_argument("--yes", action="store_true")
    p = sub.add_parser("checks")
    p.add_argument("folder")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("gates")
    p.add_argument("folder")
    p.add_argument("--json", action="store_true")
    p.add_argument("--timeout-min", type=float, default=30)
    return ap


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    handler = {"list": cmd_list, "versions": cmd_versions, "new": cmd_new,
               "detect": cmd_detect, "record": cmd_record,
               "checks": cmd_checks, "gates": cmd_gates}[args.cmd]
    try:
        return handler(args)
    except ScaffoldError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
