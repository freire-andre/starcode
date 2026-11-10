#!/usr/bin/env python3
"""Instala o StarCode localmente em um dos CLIs (codex, antigravity, opencode, orca).

Saída: 0 sucesso, 1 comando do CLI falhou (saída repassada), 2 pré-condição (R13),
3 a Orca pede aprovação do plugin (R34): o pedido é impresso e a aprovação é sempre humana.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BINARIES = {"codex": "codex", "antigravity": "agy", "opencode": "opencode", "orca": "orca"}
PLUGIN = "starcode"
PLACEHOLDER = "{{STARCODE_ROOT}}"
STALE_SOURCE_RE = re.compile(r"already added from a different source", re.I)


def _run(cmd, runner, **kw):
    """Run and echo; returns (returncode, stdout + stderr)."""
    print("$ " + " ".join(str(c) for c in cmd))
    res = runner(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, **kw)
    if res.stdout:
        sys.stdout.write(res.stdout)
    if res.stderr:
        sys.stderr.write(res.stderr)
    return res.returncode, (res.stdout or "") + "\n" + (res.stderr or "")


def _codex(binary, root, dry, runner):
    add = [binary, "plugin", "marketplace", "add", str(root)]
    remove = [binary, "plugin", "marketplace", "remove", PLUGIN]
    install = [binary, "plugin", "add", f"{PLUGIN}@{PLUGIN}"]
    if dry:
        print("[dry-run] " + " ".join(add))
        print("[dry-run] se o marketplace já existir de outra fonte: " + " ".join(remove) + " e repetir o add")
        print("[dry-run] " + " ".join(install))
        return 0
    rc, out = _run(add, runner)
    if rc != 0:
        if not STALE_SOURCE_RE.search(out):
            return 1
        print(f"marketplace '{PLUGIN}' já existe de outra fonte: removendo e adicionando de {root}")
        if _run(remove, runner)[0] != 0 or _run(add, runner)[0] != 0:
            return 1
    return 1 if _run(install, runner)[0] != 0 else 0


def _antigravity(binary, root, home, dry, runner):
    target = (root / "dist" / "antigravity").resolve()
    validate = [binary, "plugin", "validate", "dist/antigravity", "--strict"]
    install = [binary, "plugin", "install", str(target)]
    installed = home / ".gemini" / "config" / "plugins" / PLUGIN
    hooks = installed / "hooks.json"
    if " " in installed.as_posix():
        print(f"Caminho de instalação com espaço: o Antigravity não aceita aspas no comando do hook ({installed.as_posix()})",
              file=sys.stderr)
        return 2
    if dry:
        print("[dry-run] " + " ".join(validate))
        print("[dry-run] " + " ".join(install))
        print(f"[dry-run] trocar {PLACEHOLDER} por {installed.as_posix()} em {hooks}")
        return 0
    if _run(validate, runner, cwd=str(root))[0] != 0:
        return 1
    if _run(install, runner)[0] != 0:
        return 1
    if not hooks.is_file():
        print(f"antigravity: {hooks} não encontrado; caminhos dos hooks não gravados", file=sys.stderr)
        return 1
    hooks.write_text(hooks.read_text(encoding="utf-8").replace(PLACEHOLDER, installed.as_posix()), encoding="utf-8")
    print(f"gravado {hooks}")
    return 0


def _find_fingerprint(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if "fingerprint" in key.lower() and isinstance(value, str) and value:
                return value
        for value in data.values():
            found = _find_fingerprint(value)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = _find_fingerprint(value)
            if found:
                return found
    return None


def _find_command(data):
    if isinstance(data, str):
        return data if data.lstrip().startswith("orca ") and "--approve" in data else None
    values = data.values() if isinstance(data, dict) else data if isinstance(data, list) else ()
    for value in values:
        found = _find_command(value)
        if found:
            return found
    return None


def _show_approval_request(out, target):
    """R34: mostra o que a Orca pediu (error.data) e o comando com --approve que ela devolveu. Nunca executa."""
    try:
        error = json.JSONDecoder().raw_decode(out[out.index("{"):])[0]["error"]
    except (ValueError, KeyError, TypeError):
        error = {}
    data = error.get("data") if isinstance(error, dict) else None
    print("orca: a instalação precisa de aprovação humana (exit 3); nada foi instalado.", file=sys.stderr)
    if isinstance(error, dict) and error.get("message"):
        print(f"  {error['message']}", file=sys.stderr)
    if data is not None:
        print("  acessos pedidos (error.data):", file=sys.stderr)
        for line in json.dumps(data, indent=2, ensure_ascii=False).splitlines():
            print("    " + line, file=sys.stderr)
    fingerprint = _find_fingerprint(data)
    command = _find_command(data) or (
        f"orca plugin install {target} --approve {fingerprint}" if fingerprint else None)
    if command:
        print("  depois de revisar, rode você mesmo (este script nunca passa --approve):", file=sys.stderr)
        print(f"    {command}", file=sys.stderr)
    else:
        print("  a Orca não devolveu um fingerprint; rode o install manualmente e leia o pedido.", file=sys.stderr)


def _orca(binary, root, dry, runner):
    target = (root / "dist" / "orca").resolve()
    validate = [binary, "plugin", "validate", "dist/orca", "--json"]
    install = [binary, "plugin", "install", str(target), "--json"]
    if dry:
        print("[dry-run] " + " ".join(validate))
        print("[dry-run] " + " ".join(install))
        print("[dry-run] exit 3 (approval_required): mostra os acessos e o comando com --approve; nunca aprova sozinho")
        return 0
    if _run(validate, runner, cwd=str(root))[0] != 0:
        return 1
    rc, out = _run(install, runner)
    if rc == 3:
        _show_approval_request(out, target)
        return 3
    return 0 if rc == 0 else 1


def _opencode(root, home, dry):
    dist = root / "dist" / "opencode"
    skills = sorted(str(p.resolve()) for p in (dist / "skills").iterdir() if p.is_dir())
    commands = sorted((dist / "commands").glob("*.md"))
    conf_dir = home / ".config" / "opencode"
    conf = conf_dir / "opencode.json"
    data = {}
    if conf.exists():
        try:
            data = json.loads(conf.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("raiz não é objeto")
        except ValueError as exc:
            print(f"opencode: {conf} inválido ({exc})", file=sys.stderr)
            return 2
    cur = data.get("skills")
    if isinstance(cur, list):
        have = cur
    else:
        if not isinstance(cur, dict):
            cur = data["skills"] = {}
        have = cur.setdefault("paths", [])
    suffixes = {("dist", "opencode", "skills", Path(s).name.casefold()) for s in skills}

    def is_starcode(entry):
        if not isinstance(entry, str):
            return False
        parts = [x.casefold() for x in re.split(r"[\\/]+", entry) if x]
        return tuple(parts[-4:]) in suffixes

    kept = [e for e in have if not is_starcode(e)]
    removed = len(have) - len(kept)
    have[:] = kept + skills
    plugin_src = dist / "plugins" / "starcode.js"
    plugin_dst = conf_dir / "plugins" / "starcode.js"
    if dry:
        print(f"[dry-run] gravar plugin {plugin_dst} (com {PLACEHOLDER} = {dist.resolve().as_posix()})")
        print(f"[dry-run] remover {removed} e gravar {len(skills)} caminhos de skill do StarCode em {conf}")
        for c in commands:
            print(f"[dry-run] copiar {c.name} para {conf_dir / 'commands'}")
        return 0
    conf_dir.mkdir(parents=True, exist_ok=True)
    conf.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"gravado {conf}")
    (conf_dir / "commands").mkdir(exist_ok=True)
    for c in commands:
        shutil.copyfile(c, conf_dir / "commands" / c.name)
        print(f"copiado {c.name}")
    if not plugin_src.is_file():
        print(f"opencode: {plugin_src} não encontrado", file=sys.stderr)
        return 2
    plugin_dst.parent.mkdir(parents=True, exist_ok=True)
    text = plugin_src.read_text(encoding="utf-8").replace(PLACEHOLDER, dist.resolve().as_posix())
    plugin_dst.write_text(text, encoding="utf-8")
    print(f"gravado {plugin_dst}")
    return 0


def main(argv=None, runner=subprocess.run, which=shutil.which, root: Path = ROOT) -> int:
    ap = argparse.ArgumentParser(prog="install_local.py")
    ap.add_argument("--cli", required=True, choices=sorted(BINARIES))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--home", default=None)
    args = ap.parse_args(argv)
    cli = args.cli
    binary = which(BINARIES[cli])
    if not binary:
        print(f"{cli}: {BINARIES[cli]} não encontrado", file=sys.stderr)
        return 2
    if not (root / "dist" / cli).is_dir():
        print(f"{cli}: dist/{cli} não encontrado", file=sys.stderr)
        return 2
    home = Path(args.home) if args.home else Path.home()
    if cli == "codex":
        return _codex(binary, root, args.dry_run, runner)
    if cli == "orca":
        return _orca(binary, root, args.dry_run, runner)
    if cli == "antigravity":
        return _antigravity(binary, root, home, args.dry_run, runner)
    return _opencode(root, home, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
