"""Shared helpers for StarCode scripts and hooks. Python stdlib only.

Layout (source tree and every dist/<cli>/ folder): <root>/scripts/, <root>/hooks/scripts/,
<root>/crew.json (generated; the source tree falls back to src/crew.yaml).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
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


def write_session(cwd: str | Path | None, data: dict) -> Path:
    path = session_path(cwd)
    if path is None:
        raise RuntimeError("não é um repositório Git")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


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


def effective_crew(crew_doc: dict, user_cfg: dict | None) -> dict[str, dict]:
    """Crew members with cli/model after applying the user config (precedence: user > crew.yaml).
    Session overrides live in tasks.md ## Handoff and are applied by the Picard, not here."""
    overrides = (user_cfg or {}).get("crew", {})
    out = {}
    for key, member in crew_doc.get("crew", {}).items():
        entry = dict(member)
        default = member.get("default", {})
        ov = overrides.get(key, {})
        entry["cli"] = ov.get("cli", default.get("cli"))
        entry["model"] = ov.get("model", default.get("model"))
        entry["overridden"] = bool(ov)
        out[key] = entry
    return out
