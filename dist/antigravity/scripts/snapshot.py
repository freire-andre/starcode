"""Snapshot do modo 1 (fase 12): grava o estado do worktree em um ref, sem tocar índice, árvore, HEAD ou branches.

Usage:
  python snapshot.py take SLUG TICKET [--root DIR]
  python snapshot.py list SLUG [--root DIR] [--json]
  python snapshot.py drop SLUG [--root DIR]

O snapshot usa um índice temporário (GIT_INDEX_FILE só nos subprocessos) e fica em
refs/starcode/snapshots/<slug>/<ticket>, fora de refs/heads.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REF_PREFIX = "refs/starcode/snapshots"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TICKET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class GitError(Exception):
    def __init__(self, step: str, reason: str) -> None:
        super().__init__(f"{step}: {reason}")
        self.step = step
        self.reason = reason


def ref_name(slug: str, ticket: str) -> str:
    return f"{REF_PREFIX}/{slug}/{ticket}"


def run_git(root, *args: str, env: dict | None = None) -> str:
    full_env = {**os.environ, **env} if env else None
    step = " ".join(args[:2])
    try:
        res = subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True,
                             encoding="utf-8", errors="replace", env=full_env)
    except OSError as exc:
        raise GitError(step, str(exc)) from exc
    if res.returncode != 0:
        lines = (res.stderr or res.stdout).strip().splitlines()
        raise GitError(step, lines[-1] if lines else f"código {res.returncode}")
    return res.stdout


def valid_names(slug: str, ticket: str) -> bool:
    if not SLUG_RE.match(slug) or not TICKET_RE.match(ticket):
        return False
    try:
        res = subprocess.run(["git", "check-ref-format", ref_name(slug, ticket)], capture_output=True)
    except OSError:
        return False
    return res.returncode == 0


def _existing(root, ref: str) -> str | None:
    try:
        return run_git(root, "rev-parse", "--verify", "-q", ref).strip() or None
    except GitError:
        return None


def snapshot_commit(root, slug: str, ticket: str) -> tuple[str, str | None]:
    """Grava o snapshot e devolve (commit, commit antigo do ref ou None). Levanta GitError."""
    run_git(root, "rev-parse", "--verify", "HEAD^{commit}")
    ref = ref_name(slug, ticket)
    old = _existing(root, ref)
    tmpdir = tempfile.mkdtemp(prefix="starcode-snapshot-")
    try:
        env = {"GIT_INDEX_FILE": os.path.join(tmpdir, "index")}
        run_git(root, "read-tree", "HEAD", env=env)
        run_git(root, "add", "-A", env=env)
        tree = run_git(root, "write-tree", env=env).strip()
        commit = run_git(root, "commit-tree", tree, "-p", "HEAD", "-m",
                         f"starcode snapshot {slug}/{ticket}", env=env).strip()
        run_git(root, "update-ref", ref, commit)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return commit, old


def _count(root, commit: str) -> int:
    return len([ln for ln in run_git(root, "ls-tree", "-r", "--name-only", commit).splitlines() if ln])


def _short(root, commit: str) -> str:
    return run_git(root, "rev-parse", "--short", commit).strip()


def cmd_take(args) -> int:
    if not valid_names(args.slug, args.ticket):
        bad = args.slug if not SLUG_RE.match(args.slug) else args.ticket
        print(f"nome inválido para o snapshot: {bad}")
        return 2
    try:
        commit, old = snapshot_commit(args.root, args.slug, args.ticket)
        line = f"snapshot {args.slug}/{args.ticket} {_short(args.root, commit)} ({_count(args.root, commit)} arquivos)"
        if old:
            line += f" (substituído {_short(args.root, old)})"
    except GitError as exc:
        print(f"snapshot falhou: {exc}")
        return 1
    print(line)
    return 0


def _refs(root, slug: str) -> list[tuple[str, str]]:
    out = run_git(root, "for-each-ref", "--format=%(refname) %(objectname)", f"{REF_PREFIX}/{slug}/")
    rows = []
    for ln in out.splitlines():
        name, _, sha = ln.partition(" ")
        if name:
            rows.append((name, sha))
    return rows


def cmd_list(args) -> int:
    try:
        rows = []
        for name, sha in _refs(args.root, args.slug):
            date = run_git(args.root, "show", "-s", "--format=%cI", sha).strip()
            rows.append({"ticket": name[len(f"{REF_PREFIX}/{args.slug}/"):], "commit": _short(args.root, sha),
                         "date": date, "files": _count(args.root, sha)})
    except GitError as exc:
        print(f"listagem falhou: {exc}")
        return 1
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif not rows:
        print(f"nenhum snapshot de {args.slug}")
    else:
        for r in rows:
            print(f"{r['ticket']}  {r['commit']}  {r['date']}  {r['files']} arquivos")
    return 0


def cmd_drop(args) -> int:
    try:
        refs = _refs(args.root, args.slug)
        for name, _ in refs:
            run_git(args.root, "update-ref", "-d", name)
    except GitError as exc:
        print(f"remoção falhou: {exc}")
        return 1
    print(f"removidos {len(refs)} snapshots de {args.slug}")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="Snapshot do modo 1 (StarCode).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_take = sub.add_parser("take")
    p_take.add_argument("slug")
    p_take.add_argument("ticket")
    p_list = sub.add_parser("list")
    p_list.add_argument("slug")
    p_list.add_argument("--json", action="store_true")
    p_drop = sub.add_parser("drop")
    p_drop.add_argument("slug")
    for p in (p_take, p_list, p_drop):
        p.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    return {"take": cmd_take, "list": cmd_list, "drop": cmd_drop}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
