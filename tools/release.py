#!/usr/bin/env python3
"""Release do StarCode: confere a tag, extrai as notas e cria tag + release.

Saída: 0 sucesso, 1 falha (tag divergente, tag no remoto, seção ausente, comando falhou).
"""
from __future__ import annotations

import argparse
import json
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


FIRST_ACEITE_PHASE = 6


def _out(runner, cmd: list[str]):
    res = runner(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return res.returncode, (res.stdout or "").strip(), res.stderr or ""


def _aceites(root: Path) -> list[tuple[int, Path]]:
    found = []
    for p in (root / "docs" / "aceite").glob("fase-*.md"):
        m = re.fullmatch(r"fase-(\d+)\.md", p.name)
        if m and int(m.group(1)) >= FIRST_ACEITE_PHASE:
            found.append((int(m.group(1)), p))
    return sorted(found)


def _aceite_pending(path: Path) -> str | None:
    """Seção do primeiro resultado não aprovado do arquivo, ou None se aprovado."""
    section, seen = "", False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        elif line.startswith("**Resultado**:"):
            seen = True
            if line.split(":", 1)[1].strip() != "aprovado":
                return section
    return None if seen else "sem resultado"


def _undated(root: Path, version: str) -> bool:
    text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(rf"^## \[{re.escape(version)}\](.*)$", text, re.M)
    return bool(m) and not re.search(r"\d{4}-\d{2}-\d{2}", m.group(1))


def _preconditions(root: Path, runner) -> int:
    aceites = _aceites(root)
    if not aceites:
        print("aceite não aprovado em docs/aceite/fase-6.md: arquivo ausente", file=sys.stderr)
        return 1
    for n, path in aceites:
        pending = _aceite_pending(path)
        if pending is not None:
            print(f"aceite não aprovado em docs/aceite/fase-{n}.md: {pending}", file=sys.stderr)
            return 1
    rc, branch, err = _out(runner, ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc != 0:
        sys.stderr.write(err)
        print("git rev-parse falhou", file=sys.stderr)
        return 1
    if branch != "main":
        print(f"release só a partir de main (ramo atual: {branch})", file=sys.stderr)
        return 1
    rc, _, err = _out(runner, ["git", "fetch", "origin", "main"])
    if rc != 0:
        sys.stderr.write(err)
        print("git fetch falhou", file=sys.stderr)
        return 1
    rc, head, _ = _out(runner, ["git", "rev-parse", "HEAD"])
    rc2, origin, _ = _out(runner, ["git", "rev-parse", "origin/main"])
    if rc != 0 or rc2 != 0 or head != origin:
        print("HEAD diverge de origin/main: faça pull ou push antes do release", file=sys.stderr)
        return 1
    rc, raw, err = _out(runner, ["gh", "run", "list", "--workflow", "CI", "--branch", "main",
                                 "--commit", head, "--json", "conclusion,status", "--limit", "1"])
    runs = []
    if rc == 0:
        try:
            runs = json.loads(raw or "[]")
        except ValueError:
            runs = []
    if not runs:
        estado = "sem run"
    elif runs[0].get("status") != "completed":
        estado = runs[0].get("status") or "sem status"
    else:
        estado = runs[0].get("conclusion") or "sem conclusão"
        if estado == "success":
            return 0
    print(f"CI de main não está verde em {head[:7]} ({estado})", file=sys.stderr)
    return 1


def _create(root: Path, version: str, yes: bool, runner) -> int:
    tag = f"v{version}"
    if _check(tag, version):
        return 1
    notes = _notes(root, version)
    if notes is None:
        print(f"CHANGELOG.md sem a seção [{version}]", file=sys.stderr)
        return 1
    if _undated(root, version):
        print(f"CHANGELOG.md: a seção [{version}] não tem data (não lançada); "
              "date a seção antes do release", file=sys.stderr)
        return 1
    if _preconditions(root, runner):
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
