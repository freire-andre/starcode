"""Snapshot do modo 1 (fase 12): grava o estado do worktree em um ref, sem tocar índice, árvore, HEAD ou branches.

Usage:
  python snapshot.py take SLUG TICKET [--root DIR]
  python snapshot.py list SLUG [--root DIR] [--json]
  python snapshot.py restore SLUG TICKET [--root DIR] [--yes]
  python snapshot.py drop SLUG [--root DIR]

O snapshot usa um índice temporário (GIT_INDEX_FILE só nos subprocessos) e fica em
refs/starcode/snapshots/<slug>/<ticket>, fora de refs/heads.
"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "gates"))

import check_scope  # noqa: E402
import gates_common as gc  # noqa: E402

REF_PREFIX = "refs/starcode/snapshots"
PRE_PREFIX = "refs/starcode/pre-restore"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TICKET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class GitError(Exception):
    def __init__(self, step: str, reason: str) -> None:
        super().__init__(f"{step}: {reason}")
        self.step = step
        self.reason = reason


def ref_name(slug: str, ticket: str) -> str:
    return f"{REF_PREFIX}/{slug}/{ticket}"


def pre_ref_name(slug: str, ticket: str) -> str:
    return f"{PRE_PREFIX}/{slug}/{ticket}"


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
        kept = _existing(args.root, ref_name(args.slug, args.ticket))
        if kept:
            print(f"snapshot {args.slug}/{args.ticket} mantido {_short(args.root, kept)} ({_count(args.root, kept)} arquivos)")
            return 0
        commit, _old = snapshot_commit(args.root, args.slug, args.ticket)
        line = f"snapshot {args.slug}/{args.ticket} {_short(args.root, commit)} ({_count(args.root, commit)} arquivos)"
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


OUTSIDE_LIMIT = 50


def _ticket_may_change(root, slug: str, ticket: str) -> tuple[list[str] | None, str]:
    """May change do ticket (tasks.md) ou, sem tasks.md, o da spec. Devolve (lista, motivo do erro)."""
    fdir = Path(root) / ".specs" / "features" / slug
    if (fdir / "tasks.md").is_file():
        task = check_scope.find_task(fdir, ticket)
        if task is None:
            return None, f"ticket {ticket} não está no tasks.md de {slug}"
        paths = task.may_change
    elif (fdir / "spec.md").is_file():
        paths = check_scope.spec_may_change(fdir)
    else:
        return None, f"nem tasks.md nem spec.md em .specs/features/{slug}"
    if not paths:
        return None, f"ticket {ticket} sem May change"
    return paths, ""


def _clean_patterns(paths: list[str]) -> list[str]:
    out = []
    for raw in paths:
        pat = gc.norm_path(raw)
        norm = posixpath.normpath(pat)
        if norm == ".." or norm.startswith("../") or posixpath.isabs(norm) or re.match(r"^[A-Za-z]:", norm):
            print(f"aviso: May change ignorado (sai da raiz): {raw}")
            continue
        out.append(norm + "/" if pat.endswith("/") and norm != "." else norm)
    return out


def _current_tree(root) -> str:
    tmpdir = tempfile.mkdtemp(prefix="starcode-restore-")
    try:
        env = {"GIT_INDEX_FILE": os.path.join(tmpdir, "index")}
        run_git(root, "read-tree", "HEAD", env=env)
        run_git(root, "add", "-A", env=env)
        return run_git(root, "write-tree", env=env).strip()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _diff(root, snapshot: str) -> list[tuple[str, str, str]]:
    """(ação, caminho, status) das diferenças snapshot -> árvore atual: voltar (existe no snapshot) ou remover.

    O status é o do diff-tree: D = existe no snapshot e sumiu da árvore atual."""
    out = run_git(root, "-c", "core.quotepath=off", "diff-tree", "-r", "-z", "--name-status", "--no-renames",
                  f"{snapshot}^{{tree}}", _current_tree(root))
    parts = out.split("\0")
    rows = []
    for i in range(0, len(parts) - 1, 2):
        status, path = parts[i].strip(), parts[i + 1]
        rows.append(("remover" if status.startswith("A") else "voltar", path, status[:1]))
    return sorted(rows, key=lambda r: r[1])


def _write_blob(root, snapshot: str, path: str) -> None:
    mode = run_git(root, "ls-tree", snapshot, "--", path).split()[0]
    res = subprocess.run(["git", "cat-file", "blob", f"{snapshot}:{path}"], cwd=str(root), capture_output=True)
    if res.returncode != 0:
        lines = res.stderr.decode("utf-8", "replace").strip().splitlines()
        raise OSError(lines[-1] if lines else "cat-file falhou")
    target = Path(root) / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.is_file():
        target.unlink()
    target.write_bytes(res.stdout)
    if mode == "100755":
        target.chmod(target.stat().st_mode | 0o111)
    else:
        target.chmod(target.stat().st_mode & ~0o111)


def _remove(root, path: str) -> None:
    target = Path(root) / path
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        raise OSError("é uma pasta")
    parent = target.parent
    while parent != Path(root) and parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
        parent = parent.parent


def _plan_path(root, slug: str, ticket: str) -> Path:
    gitdir = Path(run_git(root, "rev-parse", "--absolute-git-dir").strip())
    return gitdir / "starcode" / f"restore-{slug}-{ticket}.json"


def _load_plan(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("snapshot"), str) or not isinstance(data.get("lines"), list):
        return None
    return data


def _save_plan(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def _write_pre_restore(root, slug: str, ticket: str) -> str:
    """Grava a árvore atual (índice temporário, pai HEAD) em refs/starcode/pre-restore/<slug>/<ticket>."""
    tree = _current_tree(root)
    ref = pre_ref_name(slug, ticket)
    parents = ["-p", "HEAD"]
    previous = _existing(root, ref)
    if previous:  # mantém o pre-restore anterior alcançável pelo mesmo ref (segundo pai)
        parents += ["-p", previous]
    commit = run_git(root, "commit-tree", tree, *parents, "-m", f"starcode pre-restore {slug}/{ticket}").strip()
    run_git(root, "update-ref", ref, commit)
    return commit


def cmd_restore(args) -> int:
    root = args.root
    if not valid_names(args.slug, args.ticket):
        bad = args.slug if not SLUG_RE.match(args.slug) else args.ticket
        print(f"nome inválido para o snapshot: {bad}")
        return 2
    name = f"{args.slug}/{args.ticket}"
    try:
        snap = _existing(root, ref_name(args.slug, args.ticket))
        if not snap:
            print(f"sem snapshot de {name}: restauração recusada")
            return 1
        paths, why = _ticket_may_change(root, args.slug, args.ticket)
        if paths is None:
            print(f"{why}: restauração recusada")
            return 1
        patterns = _clean_patterns(paths)
        if not patterns:
            print(f"ticket {args.ticket} sem May change válido: restauração recusada")
            return 1
        parent = run_git(root, "rev-parse", f"{snap}^").strip()
        head = run_git(root, "rev-parse", "HEAD").strip()
        if parent != head:
            print(f"HEAD mudou desde o snapshot ({parent[:7]} → {head[:7]}): restauração recusada")
            return 1
        rows = _diff(root, snap)
        plan_file = _plan_path(root, args.slug, args.ticket)
    except GitError as exc:
        print(f"restauração falhou: {exc}")
        return 1
    plan = [(a, p) for a, p, _ in rows if check_scope.allowed(p, patterns)]
    outside = [p for _, p, _ in rows if not check_scope.allowed(p, patterns)]
    missing = [p for _, p, st in rows if st == "D" and not check_scope.allowed(p, patterns)]
    if missing:
        print("restauração recusada: arquivos do snapshot ausentes fora do ticket:")
        for p in missing:
            print(f"  {p}")
        return 1

    def outside_lines() -> list[str]:
        if not outside:
            return []
        lines = ["fora do ticket (não tocados):"] + [f"  {p}" for p in outside[:OUTSIDE_LIMIT]]
        if len(outside) > OUTSIDE_LIMIT:
            lines.append(f"e mais {len(outside) - OUTSIDE_LIMIT}")
        return lines

    if not args.yes:
        old = _load_plan(plan_file)
        old_lines = {tuple(r) for r in old["lines"] if isinstance(r, list) and len(r) == 2} if old else set()
        # só herda "iniciado" se o plano novo cabe no antigo; trabalho novo pede outro pre-restore
        started = bool(old and old.get("snapshot") == snap and old.get("started") and set(plan) <= old_lines)
        try:
            _save_plan(plan_file, {"slug": args.slug, "ticket": args.ticket, "snapshot": snap,
                                   "lines": [list(r) for r in plan], "started": started})
        except OSError as exc:
            print(f"restauração falhou: não gravou o plano: {exc}")
            return 1
        print(f"plano {name} (May change: {', '.join(patterns)})")
        for action, path in plan:
            print(f"  {action:<8} {path}")
        for ln in outside_lines():
            print(ln)
        print("nada foi alterado: rode de novo com --yes depois da confirmação do usuário")
        return 0

    saved = _load_plan(plan_file)
    if saved is None:
        print(f"sem plano gravado de {name}: rode restore sem --yes primeiro")
        return 1
    saved_lines = {tuple(r) for r in saved["lines"] if isinstance(r, list) and len(r) == 2}
    if saved["snapshot"] != snap or not set(plan) <= saved_lines:
        print("plano mudou desde o dry-run: rode restore sem --yes de novo")
        return 1
    if not saved.get("started"):
        try:
            pre = _write_pre_restore(root, args.slug, args.ticket)
            saved["started"] = True
            _save_plan(plan_file, saved)
        except (GitError, OSError) as exc:
            print(f"restauração recusada: pre-restore falhou: {getattr(exc, 'reason', None) or exc}")
            return 1
        print(f"pre-restore {_short(root, pre)}")

    done: list[tuple[str, str]] = []
    # remover antes de voltar: arquivo do snapshot trocado por pasta de mesmo nome (a pasta sai, o arquivo volta)
    plan = sorted(plan, key=lambda r: r[0] != "remover")
    for i, (action, path) in enumerate(plan):
        try:
            if action == "voltar":
                _write_blob(root, snap, path)
            else:
                _remove(root, path)
        except (OSError, GitError, IndexError) as exc:
            print(f"restauração parcial {name}: parou em {path}")
            print(f"restaurados ({len(done)}):")
            for a, p in done:
                print(f"  {a:<8} {p}")
            print(f"falhou: {action} {path}: {getattr(exc, 'reason', None) or exc}")
            rest = plan[i + 1:]
            print(f"faltaram ({len(rest)}):")
            for a, p in rest:
                print(f"  {a:<8} {p}")
            print("rode de novo com --yes para terminar")
            return 1
        done.append((action, path))
    try:
        plan_file.unlink()
    except OSError as exc:
        print(f"restaurado {name}, mas o plano não foi apagado: {exc}; rode restore --yes de novo para limpar")
        return 1
    v = sum(1 for a, _ in done if a == "voltar")
    print(f"restaurado {name}: {v} voltaram, {len(done) - v} removidos")
    for ln in outside_lines():
        print(ln)
    return 0


def _longer_slugs(root, slug: str) -> set[str]:
    """Slugs `<slug>-...` com ref de snapshot ou de pre-restore (donos possíveis de um plano ilegível)."""
    found = set()
    for prefix in (REF_PREFIX, PRE_PREFIX):
        for name in run_git(root, "for-each-ref", "--format=%(refname)", f"{prefix}/{slug}-*/*").split():
            found.add(name[len(prefix) + 1:].split("/", 1)[0])
    return found


def cmd_drop(args) -> int:
    try:
        refs = _refs(args.root, args.slug)
        for name, _ in refs:
            run_git(args.root, "update-ref", "-d", name)
        pre = run_git(args.root, "for-each-ref", "--format=%(refname)", f"{PRE_PREFIX}/{args.slug}/").split()
        for name in pre:
            run_git(args.root, "update-ref", "-d", name)
        plans_dir = _plan_path(args.root, args.slug, "x").parent
        if plans_dir.is_dir():
            longer = _longer_slugs(args.root, args.slug)
            for f in plans_dir.glob(f"restore-{args.slug}-*.json"):
                data = _load_plan(f)  # o glob também casa slug que começa igual: confere o slug gravado
                if data is not None:
                    mine = data.get("slug") == args.slug
                else:  # ilegível: não há slug gravado; é de outra feature só se um slug mais longo também casa o nome
                    mine = not any(f.name.startswith(f"restore-{o}-") for o in longer)
                if mine:
                    f.unlink()
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
    p_restore = sub.add_parser("restore")
    p_restore.add_argument("slug")
    p_restore.add_argument("ticket")
    p_restore.add_argument("--yes", action="store_true")
    p_drop = sub.add_parser("drop")
    p_drop.add_argument("slug")
    for p in (p_take, p_list, p_restore, p_drop):
        p.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    return {"take": cmd_take, "list": cmd_list, "restore": cmd_restore, "drop": cmd_drop}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
