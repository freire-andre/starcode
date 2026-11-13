"""ponte.py: snapshot (read-only) of the StarCode state of one worktree, for the Orca "Ponte" panel.

    python ponte.py snapshot --path <worktree> --json

Prints one JSON object (schemaVersion 1): worktree, starcode, crew, gitMode, feature, workers, errors and
elsewhere (optional: the active mission of another worktree, only when the local feature is done or absent).
Never writes anything (F10-R10): no live folder is created, no file is touched. A source that is
unreadable, invalid JSON or bigger than 1 MiB becomes an `errors` item and its section stays null/empty.
A source that is simply absent and normally optional (sessions.json, progress.json, session.json) is not
an error: it means "nobody is working" / "not recorded". Missing feature artifacts are an error.

Exit: 0 ok, 2 invalid worktree (`{"schemaVersion":1,"error":"worktree inválido: <path>"}`).
Python stdlib only, no network.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "gates"))

import crew_live  # noqa: E402
import handoff  # noqa: E402
import starcode_common as sc  # noqa: E402

SCHEMA_VERSION = 1
MAX_BYTES = 1024 * 1024  # 1 MiB per source (R8)
LINEAR_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9-])[A-Z][A-Z0-9]*-\d+(?:\.\.[A-Z][A-Z0-9]*-\d+)?(?![A-Za-z0-9])")
UNSET = {"", "none", "none yet", "not created"}
USER_CONFIG_SOURCE = "~/.starcode/config.json"
SESSION_SOURCE = "<git-dir>/starcode/session.json"
WORKTREES_SOURCE = "worktrees"


class Snapshot:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.errors: list[dict[str, str]] = []

    def error(self, source: str, message: str) -> None:
        item = {"source": source, "message": message}
        if item not in self.errors:
            self.errors.append(item)

    def read_text(self, path: Path, source: str) -> str | None:
        """Text of a source, or None with an `errors` item (unreadable, too big)."""
        try:
            if path.stat().st_size > MAX_BYTES:
                self.error(source, "arquivo maior que 1 MiB")
                return None
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.error(source, "arquivo ausente")
        except (OSError, UnicodeDecodeError) as exc:
            self.error(source, f"arquivo ilegível ({type(exc).__name__})")
        return None

    def read_json(self, path: Path, source: str, optional: bool = True) -> dict | None:
        if not path.exists():
            if not optional:
                self.error(source, "arquivo ausente")
            return None
        text = self.read_text(path, source)
        if text is None:
            return None
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            self.error(source, "JSON inválido")
            return None
        if not isinstance(data, dict):
            self.error(source, "JSON inválido (esperava um objeto)")
            return None
        return data


def _parse_at(value: object) -> datetime | None:
    return crew_live._parse_at(value)  # noqa: SLF001 - same parsing as the validity rule


def build_crew(snap: Snapshot, now: datetime) -> list[dict]:
    try:
        crew, available = crew_live.crew_members(snap.root)
    except Exception as exc:  # noqa: BLE001
        snap.error("src/crew.yaml", f"tripulação ilegível ({type(exc).__name__})")
        return []
    main = crew_live.main_worktree(snap.root) or snap.root
    sessions_path = main / crew_live.LIVE_DIR / crew_live.SESSIONS_FILE
    sessions = snap.read_json(sessions_path, ".starcode/live/sessions.json") or {}
    counts = crew_live.count_members(sessions, now)
    last: dict[str, tuple[datetime, str]] = {}
    for entry in sessions.values():
        if not crew_live.entry_valid(entry, now) or not isinstance(entry.get("member"), str):
            continue
        at = _parse_at(entry.get("at"))
        member = entry["member"]
        if at is not None and (member not in last or at > last[member][0]):
            last[member] = (at, str(entry["at"]))
    items = []
    for key in available:
        m = crew[key]
        model = "padrão do CLI" if m.get("model") in (None, "cli-default") else m["model"]
        items.append({
            "member": key,
            "emoji": m.get("emoji", ""),
            "name": m.get("name", key),
            "count": counts.get(key, 0),
            "lastAt": last[key][1] if key in last else None,
            "cliModel": f"{m.get('cli')} · {model}",
        })
    return items


def build_git_mode(snap: Snapshot) -> dict | None:
    path = sc.session_path(snap.root)
    if path is None:
        return None
    data = snap.read_json(path, SESSION_SOURCE)
    if not data:
        return None
    mode = data.get("gitMode")
    if mode not in sc.MODES:
        return None
    return {"mode": mode, "label": sc.MODES[mode].split(" (")[0], "recordedAt": data.get("setAt")}


def linear_ids(value: str) -> list[str]:
    return list(dict.fromkeys(LINEAR_TOKEN_RE.findall(value or "")))


def parse_dispatched(value: str) -> list[dict]:
    """`<label> · <issues> · base <hash> · dispatch <ctx> · model <m>`, entries joined by `; `."""
    workers = []
    for entry in handoff.dispatch_entries(value):
        parts = [p.strip() for p in entry.split(" · ")]
        worker = {"label": parts[0], "issues": linear_ids(parts[1]) if len(parts) > 1 else [],
                  "base": None, "dispatch": None, "model": None}
        for part in parts[2:]:
            for key in ("base", "dispatch", "model"):
                if part.startswith(key + " ") and worker[key] is None:
                    worker[key] = part[len(key) + 1:].strip()
        workers.append(worker)
    return workers


def handoff_of(snap: Snapshot, fdir: Path) -> tuple[Path | None, dict[str, str]]:
    """(file that holds `## Handoff`, its fields); read-only; a file too big or unreadable is an `errors` item."""
    for art in handoff.ARTIFACTS:
        f = fdir / art
        if not f.is_file():
            continue
        text = snap.read_text(f, f".specs/features/{fdir.name}/{art}")
        if text is None:
            continue
        lines = text.splitlines()
        bounds = handoff.section_bounds(lines)
        if bounds:
            return f, handoff.read_fields(lines, bounds)
    return None, {}


def choose_feature(snap: Snapshot) -> tuple[Path, Path | None, dict[str, str]] | None:
    """R4: not-done feature with the newest Handoff file (mtime); else the newest done one."""
    base = snap.root / ".specs" / "features"
    if not base.is_dir():
        return None
    candidates = []
    for fdir in sorted(p for p in base.iterdir() if p.is_dir()):
        hf, fields = handoff_of(snap, fdir)
        ref = hf or next((fdir / a for a in handoff.ARTIFACTS if (fdir / a).is_file()), None)
        if ref is None:
            continue
        try:
            mtime = ref.stat().st_mtime
        except OSError:
            continue
        candidates.append((fields.get("phase") == "done", mtime, fdir, hf, fields))
    if not candidates:
        return None
    pool = [c for c in candidates if not c[0]] or candidates
    _, _, fdir, hf, fields = max(pool, key=lambda c: (c[1], c[2].name))
    return fdir, hf, fields


def build_progress(snap: Snapshot, fdir: Path, slug: str) -> dict:
    main = crew_live.main_worktree(snap.root) or snap.root
    data = snap.read_json(main / crew_live.LIVE_DIR / "progress.json", ".starcode/live/progress.json")
    entry = (data or {}).get(slug)
    if isinstance(entry, dict) and all(isinstance(entry.get(k), int) for k in ("done", "total", "percent")):
        return {"done": entry["done"], "total": entry["total"], "percent": entry["percent"]}
    try:
        done, total = crew_live.count_tasks(str(fdir), snap.root)
    except Exception:  # noqa: BLE001 - no tasks.md yet: nothing to count
        return {"done": 0, "total": 0, "percent": 0}
    return {"done": done, "total": total, "percent": round(100 * done / total) if total else 0}


def build_feature(snap: Snapshot) -> tuple[dict | None, list[dict]]:
    chosen = choose_feature(snap)
    if chosen is None:
        return None, []
    fdir, hf, fields = chosen
    slug = fdir.name
    files = {}
    for k in ("context", "spec", "tasks"):
        f = fdir / f"{k}.md"
        files[k] = f.resolve().as_posix() if f.is_file() else None
        if f.is_file() and f.stat().st_size > MAX_BYTES:
            snap.error(f".specs/features/{slug}/{k}.md", "arquivo maior que 1 MiB")
    files["handoff"] = hf.resolve().as_posix() if hf else None
    if not any(files.values()):
        snap.error(f".specs/features/{slug}", "nenhum artefato encontrado")
    phase = fields.get("phase")
    value = lambda k: None if fields.get(k, "").strip().lower() in UNSET else fields[k].strip()  # noqa: E731
    feature = {
        "slug": slug,
        "phase": phase,
        "size": value("size"),
        "done": phase == "done",
        "linear": linear_ids(fields.get("linear", "")),
        "integrationBranch": value("integration branch"),
        "progress": build_progress(snap, fdir, slug),
        "breaker": "open" if fields.get("breaker", "").strip().lower().startswith("open") else "closed",
        "files": files,
    }
    return feature, parse_dispatched(fields.get("dispatched", ""))


def same_path(a: str | Path, b: str | Path) -> bool:
    """Paths compared without case and without slash style (Windows: backslash == slash, any case)."""
    def norm(v: str | Path) -> str:
        s = str(v).replace("\\", "/").lower()
        # a raiz do drive não colapsa para a letra sem barra (que é o cwd do drive, outro caminho)
        if len(s) >= 3 and s[1] == ":" and s[2] == "/" and not s[3:].strip("/"):
            return s[:3]
        return s.rstrip("/")
    return norm(a) == norm(b)


def list_worktrees(root: Path) -> list[dict]:
    """Read-only `git worktree list --porcelain`: [{path, branch, bare, prunable}]. Raises on failure."""
    res = subprocess.run(["git", "-C", str(root), "worktree", "list", "--porcelain"], capture_output=True,
                         text=True, encoding="utf-8", stdin=subprocess.DEVNULL, timeout=15)
    if res.returncode != 0:
        raise OSError((res.stderr or "git worktree list falhou").strip())
    items: list[dict] = []
    cur: dict | None = None
    for line in res.stdout.splitlines() + [""]:
        if not line.strip():
            if cur:
                items.append(cur)
            cur = None
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            cur = {"path": value, "branch": None, "bare": False, "prunable": False}
        elif cur is not None:
            if key == "branch":
                cur["branch"] = value.removeprefix("refs/heads/")
            elif key == "bare":
                cur["bare"] = True
            elif key == "prunable":
                cur["prunable"] = True
    return items


def build_elsewhere(snap: Snapshot) -> dict | None:
    """R1: newest active (not done) feature of another worktree of the same repository."""
    try:
        trees = list_worktrees(snap.root)
    except (OSError, subprocess.SubprocessError) as exc:
        snap.error(WORKTREES_SOURCE, f"git worktree list falhou ({type(exc).__name__})")
        return None
    found = []
    for tree in trees:
        if tree["bare"] or same_path(tree["path"], snap.root):
            continue
        path = Path(tree["path"])
        if tree["prunable"] or not path.is_dir():
            snap.error(WORKTREES_SOURCE, f"worktree ausente: {Path(tree['path']).as_posix()}")
            continue
        other = Snapshot(path)
        try:
            chosen = choose_feature(other)
            if chosen is None or chosen[2].get("phase") == "done":
                continue
            mtime = (chosen[1] or chosen[0]).stat().st_mtime
            feature, _ = build_feature(other)
        except (OSError, ValueError) as exc:
            snap.error(WORKTREES_SOURCE, f"worktree ilegível: {path.as_posix()} ({type(exc).__name__})")
            continue
        finally:
            # erros do outro worktree não se passam por erros das fontes locais
            for item in other.errors:
                snap.error(WORKTREES_SOURCE, f"{path.resolve().as_posix()}: {item['message']}")
        if feature is None:
            continue
        found.append((mtime, feature["slug"], path, tree["branch"], feature))
    if not found:
        return None
    _, _, path, branch, feature = max(found, key=lambda c: (c[0], c[1]))
    return {"worktree": path.resolve().as_posix(), "branch": branch, **feature, "others": len(found) - 1}


def snapshot(path: Path, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    root = path.resolve()
    snap = Snapshot(root)
    out: dict = {"schemaVersion": SCHEMA_VERSION, "worktree": root.as_posix(), "starcode": False,
                 "crew": [], "gitMode": None, "feature": None, "workers": [], "errors": snap.errors,
                 "elsewhere": None}
    cfg_path = root / ".starcode" / "config.json"
    if not cfg_path.exists() and not (root / ".specs").exists():
        return out
    out["starcode"] = True
    if cfg_path.exists():
        snap.read_json(cfg_path, ".starcode/config.json")  # only to report an unreadable/invalid file
    out["crew"] = build_crew(snap, now)
    out["gitMode"] = build_git_mode(snap)
    out["feature"], out["workers"] = build_feature(snap)
    if out["feature"] is None or out["feature"]["done"]:
        out["elsewhere"] = build_elsewhere(snap)
    return out


def main(argv: list[str] | None = None) -> int:
    sc.utf8_stdio()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    p = argparse.ArgumentParser(prog="ponte.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("snapshot")
    ps.add_argument("--path", required=True)
    ps.add_argument("--json", action="store_true")
    try:
        args = p.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    path = Path(args.path)
    if not path.is_dir() or sc.git_dir(path) is None:
        print(json.dumps({"schemaVersion": SCHEMA_VERSION, "error": f"worktree inválido: {args.path}"},
                         ensure_ascii=False))
        return 2
    print(json.dumps(snapshot(path), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
