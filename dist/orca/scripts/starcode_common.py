"""Shared helpers for StarCode scripts and hooks. Python stdlib only.

Layout (source tree and every dist/<cli>/ folder): <root>/scripts/, <root>/hooks/scripts/,
<root>/crew.json (generated; the source tree falls back to src/crew.yaml).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "config"))

import validate_config  # noqa: E402

GIT_TIMEOUT = 5


def utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# --- git ------------------------------------------------------------------------------------

def git(args: list[str], cwd: str | Path | None) -> str | None:
    """Run git and return stripped stdout, or None on any failure."""
    try:
        res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, stdin=subprocess.DEVNULL,
                             encoding="utf-8", errors="replace", timeout=GIT_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    return res.stdout.strip() if res.returncode == 0 else None


def run_git(args: list[str], cwd: str | Path | None, timeout: float = 30, binary: bool = False,
            env: dict | None = None) -> tuple[int, Any, Any]:
    """Run git with a time limit: (code, stdout, stderr), bytes with `binary`. 124 on timeout, 127 if git is
    missing, 126 for invalid arguments or environment; never raises."""
    empty: Any = b"" if binary else ""
    kw: dict[str, Any] = {} if binary else {"text": True, "encoding": "utf-8", "errors": "replace"}
    try:
        res = subprocess.run(["git", *args], cwd=None if cwd is None else str(cwd), capture_output=True,
                             stdin=subprocess.DEVNULL, timeout=timeout,
                             env={**os.environ, **env} if env else None, **kw)
    except subprocess.TimeoutExpired:
        msg = f"git excedeu {timeout:g} s: git {' '.join(args)}"
        return 124, empty, msg.encode("utf-8") if binary else msg
    except OSError:
        msg = "git não encontrado"
        return 127, empty, msg.encode("utf-8") if binary else msg
    except (TypeError, ValueError) as exc:  # argumento ou ambiente inválido (valor não str, byte nulo)
        msg = f"argumentos inválidos para o git: {exc}"
        return 126, empty, msg.encode("utf-8") if binary else msg
    return res.returncode, res.stdout or empty, res.stderr or empty


def repo_root(cwd: str | Path | None) -> Path | None:
    out = git(["rev-parse", "--show-toplevel"], cwd)
    return Path(out) if out else None


def git_dir(cwd: str | Path | None) -> Path | None:
    """Per-worktree git dir (.git or .git/worktrees/<name>), absolute."""
    out = git(["rev-parse", "--absolute-git-dir"], cwd)
    return Path(out) if out else None


def current_branch(cwd: str | Path | None) -> str | None:
    out = git(["symbolic-ref", "--quiet", "--short", "HEAD"], cwd)
    return out or None


# --- configs --------------------------------------------------------------------------------

def starcode_home() -> Path:
    env = os.environ.get("STARCODE_HOME")
    return Path(env) if env else Path.home() / ".starcode"


def user_config_path() -> Path:
    return starcode_home() / "config.json"


def repo_config_path(root: Path) -> Path:
    return root / ".starcode" / "config.json"


def main_worktree(root: Path) -> Path | None:
    """Main worktree folder (parent of the absolute git common dir); None when git fails."""
    out = git(["rev-parse", "--path-format=absolute", "--git-common-dir"], root)
    if not out:
        return None
    return Path(out).parent


def local_config_path(root: Path) -> Path:
    """Local config of this worktree; a linked worktree without one falls back to the main worktree's (SC-206)."""
    own = root / ".starcode" / validate_config.LOCAL_FILE
    if own.exists():
        return own
    main = main_worktree(root)
    if main is not None:
        shared = main / ".starcode" / validate_config.LOCAL_FILE
        if shared.exists():
            return shared
    return own


def load_local_config(root: Path | None) -> tuple[dict | None, list[str]]:
    """Per-repo personal crew models (never versioned); None when absent."""
    if root is None:
        return None, []
    path = local_config_path(root)
    if not path.exists():
        return None, []
    return validate_config.load("local", path)


def load_repo_config(root: Path | None) -> tuple[dict | None, list[str]]:
    if root is None:
        return None, []
    path = repo_config_path(root)
    if not path.exists():
        return None, []
    return validate_config.load("repo", path)


def load_user_config() -> tuple[dict | None, list[str]]:
    path = user_config_path()
    if not path.exists():
        return None, []
    return validate_config.load("user", path)


def base_branches(root: Path | None) -> set[str]:
    """Base branch from a valid repo config; otherwise the usual defaults."""
    cfg, _ = load_repo_config(root)
    if cfg:
        return {cfg["baseBranch"]}
    return {"main", "master"}


# --- git mode session state (per worktree, never committed) ---------------------------------
# <git-dir>/starcode/session.json: {"gitMode": 1-4, "setAt": iso, "mergeAuthorization": {...}}

MODES = {
    1: "somente código local (sem commit)",
    2: "commit local (sem push)",
    3: "branch + PR (push e PR com confirmação)",
    4: "entrega completa (push, PR e Linear; merge e deploy com autorização separada)",
}


LOCK_TIMEOUT = 5.0  # seconds a caller waits for a state-file lock (SC-202)


@contextmanager
def locked(path: str | Path, timeout: float = 5.0):
    """Exclusive OS lock on the neighbour file `<path>.lock`; TimeoutError(str(path)) after `timeout` seconds."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    fh = open(lock_path, "a+b")
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                if os.name == "nt":
                    import msvcrt  # noqa: PLC0415
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl  # noqa: PLC0415
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(str(path)) from None
                time.sleep(0.02)
        try:
            yield
        finally:
            try:
                if os.name == "nt":
                    import msvcrt  # noqa: PLC0415
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl  # noqa: PLC0415
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
    finally:
        fh.close()


def write_json_atomic(path: str | Path, data: Any) -> None:
    """Unique temp file in the same folder + os.replace (5 retries on PermissionError); temp removed on failure."""
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        for attempt in range(6):  # Windows: a reader holding the file can make replace fail for a moment
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if attempt == 5:
                    raise
                time.sleep(0.05)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def session_path(cwd: str | Path | None) -> Path | None:
    gd = git_dir(cwd)
    return gd / "starcode" / "session.json" if gd else None


def read_session(cwd: str | Path | None) -> dict:
    path = session_path(cwd)
    if not path or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def update_session(cwd: str | Path | None, mutate) -> Path:
    """Read session.json, apply `mutate(data)` in place and write it, all under `locked` (SC-202)."""
    path = session_path(cwd)
    if path is None:
        raise RuntimeError("não é um repositório Git")
    with locked(path, LOCK_TIMEOUT):
        data = read_session(cwd)
        mutate(data)
        write_json_atomic(path, data)
    return path


def write_session(cwd: str | Path | None, data: dict) -> Path:
    """Replace the whole session.json with `data` (under `locked`). To change keys use `update_session`."""
    def replace(cur: dict) -> None:
        cur.clear()
        cur.update(data)

    return update_session(cwd, replace)


def git_mode(cwd: str | Path | None) -> int | None:
    mode = read_session(cwd).get("gitMode")
    return mode if mode in MODES else None


def merge_authorized(cwd: str | Path | None, branch: str) -> bool:
    auth = read_session(cwd).get("mergeAuthorization") or {}
    if auth.get("branch") != branch:
        return False
    try:
        expires = datetime.fromisoformat(auth.get("expiresAt", ""))
    except ValueError:
        return False
    return datetime.now(timezone.utc) < expires


# --- crew -----------------------------------------------------------------------------------

def load_crew() -> dict[str, Any]:
    """Generated crew.json in a dist folder; src/crew.yaml in the source tree."""
    generated = PLUGIN_ROOT / "crew.json"
    if generated.exists():
        return json.loads(generated.read_text(encoding="utf-8"))
    sys.path.insert(0, str(PLUGIN_ROOT / "tools"))
    import miniyaml  # noqa: PLC0415

    doc = miniyaml.loads((PLUGIN_ROOT / "src" / "crew.yaml").read_text(encoding="utf-8"))
    doc["available"] = [k for k, m in doc.get("crew", {}).items()
                        if (PLUGIN_ROOT / "skills" / m["skill"] / "SKILL.md").exists()]
    return doc


def effective_crew(crew_doc: dict, user_cfg: dict | None, local_cfg: dict | None = None) -> dict[str, dict]:
    """Crew members with cli/model after the configs (precedence: local repo > user > crew.yaml).
    `source` says where each value came from: local, user or default. Session overrides live in
    tasks.md ## Handoff and are applied by the Picard, not here."""
    user_ov = (user_cfg or {}).get("crew", {})
    local_ov = (local_cfg or {}).get("crew", {})
    out = {}
    for key, member in crew_doc.get("crew", {}).items():
        entry = dict(member)
        default = member.get("default", {})
        # the local entry replaces the user's whole: never the user's cli with the local model (SC-206)
        ov = local_ov[key] if local_ov.get(key) else user_ov.get(key, {})
        entry["cli"] = ov.get("cli", default.get("cli"))
        entry["model"] = ov.get("model", default.get("model"))
        entry["source"] = "local" if local_ov.get(key) else ("user" if user_ov.get(key) else "default")
        entry["overridden"] = entry["source"] != "default"
        out[key] = entry
    return out


def crew_at(root: Path | None, crew_doc: dict | None = None) -> dict[str, dict]:
    """Effective crew for a repo: invalid configs are ignored (the banner reports them)."""
    doc = crew_doc if crew_doc is not None else load_crew()
    user_cfg, user_err = load_user_config()
    local_cfg, local_err = load_local_config(root)
    return effective_crew(doc, None if user_err else user_cfg, None if local_err else local_cfg)


def cost_tier(model: str, tiers: dict[str, str] | None) -> str:
    """Cost tier of a model: the declared map value, else 'grátis' for :free/-free, else '?'."""
    declared = (tiers or {}).get(model)
    if declared:
        return declared
    if isinstance(model, str) and model.endswith((":free", "-free")):
        return "grátis"
    return "?"
