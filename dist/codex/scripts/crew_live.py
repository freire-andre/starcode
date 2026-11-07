"""crew_live.py: who is working now and how far the feature is, in two small JSON files for a live panel.

Files (in the MAIN worktree, so every Orca worktree of the repo writes to the same place):
    <main worktree>/.starcode/live/crew.json      {"picard": 1, "spock": 0, ...}   1 = working, 0 = idle
    <main worktree>/.starcode/live/progress.json  {"<slug>": {"done": 2, "total": 5, "percent": 40,
                                                              "phase": "execute", "updatedAt": "<iso>"}}
The folder ignores itself in Git (`.gitignore` with `*`). Writes are atomic (temp file + os.replace), so a
reader never sees half a file. Each command prints at most a few lines, to keep the agent's turn cheap.

    python crew_live.py start <member> [--mission "<text>"]   # status 1 + prints the crew header (markdown)
    python crew_live.py stop <member>                         # status 0, one line
    python crew_live.py set <member> 0|1                      # quiet change (Picard marks its workers)
    python crew_live.py progress <slug> [--done N --total N] [--phase P]
                                                              # without --done/--total: counted from tasks.md
                                                              # and the commits of feature/<slug> (as dispatch.py)
    python crew_live.py show                                  # paths and contents (debug)
    python crew_live.py reset                                 # everyone 0 (stale states after a crash)

Options: --cwd DIR (default: current directory). Exit: 0 ok, 1 not a git repo / unknown member / no tasks,
2 usage error. Python stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "gates"))

import starcode_common as sc  # noqa: E402

LIVE_DIR = Path(".starcode") / "live"
RULE = "━" * 36


# --- location ---------------------------------------------------------------------------------

def main_worktree(cwd: str | Path | None) -> Path | None:
    """Root of the main worktree: parent of the common git dir (shared by every linked worktree)."""
    common = sc.git(["rev-parse", "--path-format=absolute", "--git-common-dir"], cwd)
    if not common:
        return None
    common_path = Path(common)
    if common_path.name == ".git":
        return common_path.parent
    return sc.repo_root(cwd)  # bare or unusual layout: fall back to this worktree


def live_dir(cwd: str | Path | None) -> Path | None:
    root = main_worktree(cwd)
    if root is None:
        return None
    d = root / LIVE_DIR
    d.mkdir(parents=True, exist_ok=True)
    ignore = d / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n", encoding="utf-8")
    return d


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict) -> None:
    fd, tmp = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    for _ in range(5):  # Windows: a reader holding the file can make replace fail for a moment
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            import time  # noqa: PLC0415
            time.sleep(0.05)
    os.replace(tmp, path)


# --- crew status ------------------------------------------------------------------------------

def crew_members() -> tuple[dict[str, dict], list[str]]:
    doc = sc.load_crew()
    user_cfg, user_err = sc.load_user_config()
    crew = sc.effective_crew(doc, None if user_err else user_cfg)
    available = doc.get("available") or list(crew)
    return crew, [k for k in crew if k in available]


def set_status(d: Path, member: str, value: int, available: list[str]) -> dict:
    path = d / "crew.json"
    current = read_json(path)
    def norm(k, v):  # only laforge may count 0..10 (active workers); everyone else is 0/1
        if k == "laforge":
            return v if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 10 else 0
        return 1 if v == 1 else 0

    data = {k: norm(k, current.get(k)) for k in available}  # fixed order
    for k, v in current.items():  # keep members of other versions that a panel may still show
        data.setdefault(k, norm(k, v))
    data[member] = value
    write_json(path, data)
    return data


def header(member: dict, mission: str | None) -> str:
    model = "padrão do CLI" if member.get("model") in (None, "cli-default") else member["model"]
    open_line = (member.get("voice") or {}).get("open", "")
    lines = [
        f"> **{RULE}**",
        f"> ### {member.get('emoji', '')} {member['name'].upper()} ASSUME A PONTE",
        f"> **{member.get('role', '')}** · `{member.get('cli')} · {model}`",
    ]
    if mission:
        lines.append(f"> Missão: {mission}")
    if open_line:
        lines.append(f"> *“{open_line}”*")
    lines.append(f"> **{RULE}**")
    return "\n".join(lines)


# --- progress ---------------------------------------------------------------------------------

def count_tasks(slug: str, root: Path) -> tuple[int, int]:
    """(done, total) from tasks.md and the commits of feature/<slug>, with dispatch.py's rule."""
    import dispatch  # noqa: PLC0415

    fdir, tasks = dispatch.load_tasks(slug, root)
    proj = dispatch.gc.project_root(fdir)
    cfg, _ = sc.load_repo_config(proj)
    base = (cfg or {}).get("baseBranch", "main")
    done = dispatch.integrated(tasks, proj, base, f"feature/{fdir.name}")
    return len(done), len(tasks)


def handoff_phase(slug: str, root: Path) -> str | None:
    import handoff  # noqa: PLC0415

    fdir = handoff.feature_dir(slug, root)
    for art in handoff.ARTIFACTS:
        f = fdir / art
        if f.is_file():
            lines = f.read_text(encoding="utf-8").splitlines()
            b = handoff.section_bounds(lines)
            if b:
                return handoff.read_fields(lines, b).get("phase")
    return None


def set_progress(d: Path, slug: str, done: int, total: int, phase: str | None) -> dict:
    done = max(0, min(done, total)) if total > 0 else 0
    percent = round(100 * done / total) if total > 0 else 0
    if phase == "done":
        percent, done = 100, total
    path = d / "progress.json"
    data = read_json(path)
    entry = {"done": done, "total": total, "percent": percent}
    if phase:
        entry["phase"] = phase
    entry["updatedAt"] = sc.now_iso()  # the status line shows the most recently updated feature (F6-9)
    data[slug] = entry
    write_json(path, data)
    return entry


# --- cli --------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    sc.utf8_stdio()
    p = argparse.ArgumentParser(prog="crew_live.py")
    p.add_argument("--cwd", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("start")
    ps.add_argument("member")
    ps.add_argument("--mission")
    pt = sub.add_parser("stop")
    pt.add_argument("member")
    pq = sub.add_parser("set")
    pq.add_argument("member")
    pq.add_argument("value", type=int)
    pp = sub.add_parser("progress")
    pp.add_argument("slug")
    pp.add_argument("--done", type=int)
    pp.add_argument("--total", type=int)
    pp.add_argument("--phase")
    pp.add_argument("--root", default=".")
    sub.add_parser("show")
    sub.add_parser("reset")
    try:
        args = p.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0

    cwd = args.cwd or os.getcwd()
    d = live_dir(cwd)
    if d is None:
        print("ERRO: fora de um repositório Git; status ao vivo não gravado", file=sys.stderr)
        return 1

    if args.cmd in ("start", "stop", "set", "reset"):
        crew, available = crew_members()
        if args.cmd == "reset":
            write_json(d / "crew.json", {k: 0 for k in available})
            print("Status da tripulação zerado")
            return 0
        member = args.member.lower()
        if member not in crew:
            print(f"ERRO: tripulante desconhecido {args.member!r}; use um de: {', '.join(available)}",
                  file=sys.stderr)
            return 1
        if args.cmd == "set":
            limit = 10 if member == "laforge" else 1
            if not 0 <= args.value <= limit:
                print(f"ERRO: valor {args.value} fora de 0..{limit} para {member}", file=sys.stderr)
                return 2
            value = args.value
        else:
            value = 1 if args.cmd == "start" else 0
        set_status(d, member, value, available)
        if args.cmd == "start":
            print(header(crew[member], args.mission))
        elif args.cmd == "stop":
            print(f"{crew[member]['name']}: parado")
        return 0

    if args.cmd == "progress":
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", Path(args.slug).name):
            print(f"ERRO: slug inválido {args.slug!r}", file=sys.stderr)
            return 2
        root = Path(args.root)
        phase = args.phase or handoff_phase(args.slug, root)
        if args.done is None or args.total is None:
            try:
                done, total = count_tasks(args.slug, root)
            except Exception as exc:  # noqa: BLE001 - missing tasks.md, bad layout
                if args.total is None:
                    print(f"ERRO: não foi possível contar os tickets de {args.slug} ({exc}); "
                          "passe --done e --total", file=sys.stderr)
                    return 1
                done, total = 0, args.total
            done = args.done if args.done is not None else done
            total = args.total if args.total is not None else total
        else:
            done, total = args.done, args.total
        e = set_progress(d, Path(args.slug).name, done, total, phase)
        print(f"Progresso {Path(args.slug).name}: {e['done']}/{e['total']} ({e['percent']}%)")
        return 0

    # show
    for name in ("crew.json", "progress.json"):
        f = d / name
        print(f"{f}:")
        print(f.read_text(encoding="utf-8").strip() if f.exists() else "(vazio)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
