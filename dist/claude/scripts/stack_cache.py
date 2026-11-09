#!/usr/bin/env python3
"""Cache do Context7 em .specs/stack/ (R26, R27). Só stdlib.

  stack_cache.py write <repo> <lib> --id ID --project-version V --doc-version V|desconhecida
                 --summary-file ARQ [--verified context7|"não verificada (<url>)"] [--date AAAA-MM-DD]
  stack_cache.py check <repo> [--json] [--today AAAA-MM-DD]

Exit: 0 ok | 1 alguma entrada fora de `ok` (check) | 2 uso/entrada inválida.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

MAX_SUMMARY_LINES = 30
MAX_AGE_DAYS = 30
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION_RE = re.compile(r"\d+(?:\.\d+)*")


class UsageError(Exception):
    pass


def file_name(lib: str) -> str:
    name = re.sub(r"[^a-z0-9._-]+", "-", lib.strip().lower()).strip("-.")
    if not name:
        raise UsageError(f"nome de lib inválido: {lib!r}")
    return name + ".md"


def norm_lib(lib: str) -> str:
    return file_name(lib)[:-3]


def parse_date(text: str, what: str) -> date:
    if not DATE_RE.match(text):
        raise UsageError(f"{what} deve ser AAAA-MM-DD: {text!r}")
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise UsageError(f"{what} inválida: {text!r}") from exc


def stack_dir(repo: str) -> Path:
    p = Path(repo)
    if not p.is_dir():
        raise UsageError(f"repositório não encontrado: {repo}")
    return p / ".specs" / "stack"


def cmd_write(a) -> int:
    d = stack_dir(a.repo)
    fetched = parse_date(a.date, "--date") if a.date else date.today()
    for label, val in (("--id", a.id), ("--project-version", a.project_version),
                       ("--doc-version", a.doc_version), ("--verified", a.verified)):
        if not val.strip() or "\n" in val:
            raise UsageError(f"{label} inválido")
    try:
        raw = Path(a.summary_file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise UsageError(f"não consegui ler --summary-file: {exc}") from exc
    lines = raw.rstrip().splitlines()
    if len(lines) > MAX_SUMMARY_LINES:
        print(f"aviso: resumo com {len(lines)} linhas cortado para {MAX_SUMMARY_LINES}", file=sys.stderr)
        lines = lines[:MAX_SUMMARY_LINES]
    text = (f"# {a.lib}\n**Context7 ID**: {a.id}\n**Project version**: {a.project_version}\n"
            f"**Doc version**: {a.doc_version}\n**Fetched**: {fetched.isoformat()}\n"
            f"**Verified**: {a.verified}\n## Summary\n" + "\n".join(lines) + "\n")
    d.mkdir(parents=True, exist_ok=True)
    target = d / file_name(a.lib)
    target.write_text(text, encoding="utf-8")
    print(f"gravado: {target.as_posix()}")
    return 0


def parse_entry(path: Path) -> dict:
    out = {"lib": path.stem}
    titled = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# ") and not titled:
            out["lib"] = line[2:].strip()
            titled = True
            continue
        if line.startswith("## Summary"):
            break
        m = re.match(r"\*\*([^*]+)\*\*:\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def first_version(spec: str) -> str | None:
    m = VERSION_RE.search(spec or "")
    return m.group(0) if m else None


def _read_toml(path: Path) -> dict:
    try:
        import tomllib
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - manifesto ilegível = sem versão
        return {}


def manifest_versions(repo: Path) -> dict[str, str]:
    """lib normalizada -> versão do manifesto (a primeira que aparecer)."""
    found: dict[str, str] = {}

    def add(name: str, spec: str) -> None:
        v = first_version(spec)
        if v:
            found.setdefault(norm_lib(name), v)

    py = repo / "pyproject.toml"
    if py.is_file():
        data = _read_toml(py)
        proj = data.get("project", {})
        deps = list(proj.get("dependencies", []))
        for group in proj.get("optional-dependencies", {}).values():
            deps += group
        for group in data.get("dependency-groups", {}).values():
            deps += [g for g in group if isinstance(g, str)]
        for dep in deps:
            m = re.match(r"\s*([A-Za-z0-9_.-]+)(?:\[[^\]]*\])?\s*(.*)", dep)
            if m:
                add(m.group(1).replace("_", "-"), m.group(2))
    pk = repo / "package.json"
    if pk.is_file():
        try:
            data = json.loads(pk.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            for name, spec in (data.get(key) or {}).items():
                if isinstance(spec, str):
                    add(name, spec)
    cg = repo / "Cargo.toml"
    if cg.is_file():
        data = _read_toml(cg)
        for key in ("dependencies", "dev-dependencies", "build-dependencies"):
            for name, spec in (data.get(key) or {}).items():
                add(name, spec if isinstance(spec, str) else str(spec.get("version", "")))
    return found


def project_versions(repo: Path) -> dict[str, str]:
    """Versões do .starcode/stack.json têm prioridade sobre o manifesto."""
    versions = manifest_versions(repo)
    sj = repo / ".starcode" / "stack.json"
    if sj.is_file():
        try:
            data = json.loads(sj.read_text(encoding="utf-8"))
            for name, e in (data.get("versions") or {}).items():
                v = first_version(e.get("version", "") if isinstance(e, dict) else "")
                if v:
                    versions[norm_lib(name)] = v
        except (OSError, ValueError, AttributeError):
            pass
    return versions


def parts(v: str) -> list[int]:
    return [int(x) for x in re.findall(r"\d+", v)]


def same_prefix(a: str, b: str, limit: int | None = None) -> bool:
    pa, pb = parts(a), parts(b)
    n = min(len(pa), len(pb))
    if limit:
        n = min(n, limit)
    return n > 0 and pa[:n] == pb[:n]


def classify(e: dict, current: str | None, today: date) -> str:
    proj, doc = e.get("Project version", ""), e.get("Doc version", "")
    if not parts(proj) or not e.get("Fetched"):
        return "inválida"
    if current and not same_prefix(current, proj):
        return "versão mudou"
    unknown_doc = not parts(doc)
    if not unknown_doc and not same_prefix(doc, proj, 2):
        return "outra versão"
    try:
        age = (today - datetime.strptime(e["Fetched"], "%Y-%m-%d").date()).days
    except ValueError:
        return "inválida"
    if age > MAX_AGE_DAYS:
        return "velha"
    return "ok (doc sem versão)" if unknown_doc else "ok"


def cmd_check(a) -> int:
    d = stack_dir(a.repo)
    today = parse_date(a.today, "--today") if a.today else date.today()
    versions = project_versions(Path(a.repo))
    rows = []
    for f in sorted(d.glob("*.md")) if d.is_dir() else []:
        e = parse_entry(f)
        rows.append({"lib": e["lib"], "file": f.name,
                     "state": classify(e, versions.get(norm_lib(e["lib"])), today)})
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif not rows:
        print("cache vazio (.specs/stack/ sem entradas)")
    else:
        for r in rows:
            print(f"{r['lib']}: {r['state']}")
    return 0 if all(r["state"].startswith("ok") for r in rows) else 1


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def build_parser() -> argparse.ArgumentParser:
    p = _Parser(prog="stack_cache.py")
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=_Parser)
    w = sub.add_parser("write")
    w.add_argument("repo")
    w.add_argument("lib")
    w.add_argument("--id", required=True)
    w.add_argument("--project-version", required=True)
    w.add_argument("--doc-version", required=True)
    w.add_argument("--summary-file", required=True)
    w.add_argument("--verified", default="context7")
    w.add_argument("--date")
    c = sub.add_parser("check")
    c.add_argument("repo")
    c.add_argument("--json", action="store_true")
    c.add_argument("--today")
    return p


def main(argv=None) -> int:
    try:
        a = build_parser().parse_args(argv)
        return cmd_write(a) if a.cmd == "write" else cmd_check(a)
    except UsageError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
