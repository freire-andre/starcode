"""StarCode status line segment: active crew members and the feature progress bar (F6-9).

Reads the live files written by scripts/crew_live.py in the MAIN worktree (.starcode/live/crew.json and
progress.json). Standalone on purpose (stdlib, imports nothing from the plugin) so a personal status line
can import it fast, or Claude Code can run it as the whole status line:

    "statusLine": {"type": "command", "command": "python <plugin>/scripts/statusline.py"}

As a module: `segment(cwd) -> str` ("" when there is nothing to show). Never raises.

Bar: 10 cells; each filled cell takes the color of its position on the gradient
#C5DBFF (0%) -> #75C3FF (50%) -> #0028B3 (100%), so the tip shows the color of the current percent.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RESET = "\x1b[0m"
DIM = "\x1b[2m"
STOPS = ((0.0, (0xC5, 0xDB, 0xFF)), (50.0, (0x75, 0xC3, 0xFF)), (100.0, (0x00, 0x28, 0xB3)))
WIDTH = 10
DONE_WINDOW = timedelta(hours=12)  # a finished feature stays on the line for a while, at 100%
CREW_FILE = Path(__file__).resolve().parent.parent / "crew.json"  # generated, beside the plugin


def gradient(pct: float) -> tuple[int, int, int]:
    pct = max(0.0, min(100.0, pct))
    for (p0, c0), (p1, c1) in zip(STOPS, STOPS[1:]):
        if pct <= p1:
            t = (pct - p0) / (p1 - p0)
            return tuple(round(a + (b - a) * t) for a, b in zip(c0, c1))  # type: ignore[return-value]
    return STOPS[-1][1]


def fg(rgb: tuple[int, int, int]) -> str:
    return f"\x1b[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"


def bar(pct: float, width: int = WIDTH) -> str:
    pct = max(0.0, min(100.0, pct))
    filled = int(round(pct / 100 * width))
    cells = [fg(gradient((i + 1) * 100 / width)) + "█" for i in range(filled)]
    empty = f"{DIM}{'░' * (width - filled)}" if filled < width else ""
    return "".join(cells) + empty + RESET + " " + fg(gradient(pct)) + f"{pct:.0f}%" + RESET


def live_dir(cwd: str) -> Path | None:
    try:
        res = subprocess.run(["git", "--no-optional-locks", "rev-parse", "--path-format=absolute",
                              "--git-common-dir"], cwd=cwd, capture_output=True, text=True, timeout=2,
                             stdin=subprocess.DEVNULL)
    except Exception:  # noqa: BLE001
        return None
    common = Path(res.stdout.strip()) if res.returncode == 0 and res.stdout.strip() else None
    if common is None:
        return None
    root = common.parent if common.name == ".git" else common
    d = root / ".starcode" / "live"
    return d if d.is_dir() else None


def _read(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return data if isinstance(data, dict) else {}


def _names() -> dict:
    """{key: "<emoji> <Name>"} from crew.json (dist) or, in the source tree, src/crew.yaml (crew block only)."""
    crew = _read(CREW_FILE).get("crew", {})
    if not crew:
        try:
            text = (CREW_FILE.parent / "src" / "crew.yaml").read_text(encoding="utf-8")
        except OSError:
            text = ""
        block = text.split("\ncrew:\n", 1)[-1].split("\n\n", 1)[0] if "\ncrew:\n" in text else ""
        key = None
        for line in block.splitlines():
            m = re.match(r"^  (\w[\w-]*):\s*$", line)
            if m:
                key = m.group(1)
                crew[key] = {}
                continue
            m = re.match(r'^    (name|emoji):\s*"?([^"]*)"?\s*$', line)
            if key and m:
                crew[key][m.group(1)] = m.group(2)
    return {k: f"{m.get('emoji', '')} {m.get('name', k)}".strip() for k, m in crew.items() if isinstance(m, dict)}


def _when(entry: dict) -> datetime:
    try:
        return datetime.fromisoformat(str(entry.get("updatedAt")))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def pick_feature(progress: dict, now: datetime) -> tuple[str, dict] | None:
    """Most recently updated feature in progress; a finished one only within DONE_WINDOW."""
    items = [(k, v) for k, v in progress.items() if isinstance(v, dict) and isinstance(v.get("total"), int)]
    running = [kv for kv in items if kv[1].get("phase") != "done" and kv[1].get("percent", 0) < 100]
    if running:
        return max(running, key=lambda kv: _when(kv[1]))
    recent = [kv for kv in items if now - _when(kv[1]) <= DONE_WINDOW]
    return max(recent, key=lambda kv: _when(kv[1])) if recent else None


def segment(cwd: str, now: datetime | None = None) -> str:
    try:
        d = live_dir(cwd)
        if d is None:
            return ""
        now = now or datetime.now(timezone.utc)
        names = _names()
        crew = _read(d / "crew.json")
        active = [names.get(k, k.capitalize()) for k, v in crew.items() if v == 1]
        feat = pick_feature(_read(d / "progress.json"), now)
        parts = []
        if active:
            parts.append(" · ".join(active))
        elif feat:
            parts.append(f"{DIM}🖖 em espera{RESET}")
        if feat:
            slug, e = feat
            parts.append(f"{slug} {bar(float(e.get('percent', 0)))} {DIM}{e.get('done', 0)}/{e['total']}{RESET}")
        return f" {DIM}|{RESET} ".join(parts)
    except Exception:  # noqa: BLE001 - a status line never breaks
        return ""


def main() -> int:
    raw = sys.stdin.buffer.read()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        data = {}
    cwd = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or str(Path.cwd())
    sys.stdout.buffer.write(segment(cwd).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
