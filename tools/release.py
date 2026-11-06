#!/usr/bin/env python3
"""Release do StarCode: confere a tag, extrai as notas e cria tag + release.

Saída: 0 sucesso, 1 falha (tag divergente, tag no remoto, seção ausente, comando falhou).
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _version(root: Path) -> str:
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def _check(tag: str, version: str) -> int:
    if tag != f"v{version}":
        print(f"tag {tag} diverge de VERSION {version}", file=sys.stderr)
        return 1
    return 0


def _notes(root: Path, version: str) -> str | None:
    text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip("\n") + "\n" if m else None


def _create(root: Path, version: str, yes: bool, runner) -> int:
    tag = f"v{version}"
    if _check(tag, version):
        return 1
    notes = _notes(root, version)
    if notes is None:
        print(f"CHANGELOG.md sem a seção [{version}]", file=sys.stderr)
        return 1
    res = runner(["git", "ls-remote", "--tags", "origin", tag], capture_output=True, text=True,
                 stdin=subprocess.DEVNULL)
    if res.returncode != 0:
        sys.stderr.write(res.stderr or "")
        print("git ls-remote falhou", file=sys.stderr)
        return 1
    if (res.stdout or "").strip():
        print(f"tag {tag} já existe no remoto", file=sys.stderr)
        return 1
    fd, notes_file = tempfile.mkstemp(prefix="starcode-notes-", suffix=".md")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(notes)
    cmds = [
        ["git", "tag", "-a", tag, "-m", f"StarCode {tag}"],
        ["git", "push", "origin", tag],
        ["gh", "release", "create", tag, "--notes-file", notes_file],
    ]
    if not yes:
        for c in cmds:
            print("$ " + " ".join(f'"{a}"' if " " in a else a for a in c))
        return 0
    try:
        for c in cmds:
            print("$ " + " ".join(c))
            if runner(c, stdin=subprocess.DEVNULL).returncode != 0:
                return 1
    finally:
        Path(notes_file).unlink(missing_ok=True)
    return 0


def main(argv=None, runner=subprocess.run, root: Path = ROOT) -> int:
    ap = argparse.ArgumentParser(prog="release.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").add_argument("--tag", required=True)
    sub.add_parser("notes")
    sub.add_parser("create").add_argument("--yes", action="store_true")
    args = ap.parse_args(argv)
    version = _version(root)
    if args.cmd == "check":
        return _check(args.tag, version)
    if args.cmd == "notes":
        notes = _notes(root, version)
        if notes is None:
            print(f"CHANGELOG.md sem a seção [{version}]", file=sys.stderr)
            return 1
        sys.stdout.write(notes)
        return 0
    return _create(root, version, args.yes, runner)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
