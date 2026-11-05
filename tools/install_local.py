#!/usr/bin/env python3
"""Instala o StarCode localmente em um dos CLIs (codex, antigravity, opencode).

Saída: 0 sucesso, 1 comando do CLI falhou (saída repassada), 2 pré-condição (R13).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BINARIES = {"codex": "codex", "antigravity": "agy", "opencode": "opencode"}
PLUGIN = "starcode"


def _run(cmd, runner, **kw):
    print("$ " + " ".join(str(c) for c in cmd))
    res = runner(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, **kw)
    if res.stdout:
        sys.stdout.write(res.stdout)
    if res.stderr:
        sys.stderr.write(res.stderr)
    return res.returncode


def _codex(binary, root, dry, runner):
    cmds = [[binary, "plugin", "marketplace", "add", str(root)],
            [binary, "plugin", "add", f"{PLUGIN}@{PLUGIN}"]]
    for cmd in cmds:
        if dry:
            print("[dry-run] " + " ".join(cmd))
        elif _run(cmd, runner) != 0:
            return 1
    return 0


def _antigravity(binary, root, dry, runner):
    target = (root / "dist" / "antigravity").resolve()
    validate = [binary, "plugin", "validate", "dist/antigravity", "--strict"]
    install = [binary, "plugin", "install", str(target)]
    if dry:
        print("[dry-run] " + " ".join(validate))
        print("[dry-run] " + " ".join(install))
        return 0
    if _run(validate, runner, cwd=str(root)) != 0:
        return 1
    return 1 if _run(install, runner) != 0 else 0


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
    for s in skills:
        if s not in have:
            have.append(s)
    if dry:
        print(f"[dry-run] gravar {len(skills)} caminhos de skill em {conf}")
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
    if cli == "antigravity":
        return _antigravity(binary, root, args.dry_run, runner)
    return _opencode(root, home, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
