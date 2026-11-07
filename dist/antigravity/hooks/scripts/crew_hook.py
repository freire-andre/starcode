"""StarCode crew hook for Claude Code (F7-12): shows the crew header and keeps the live status honest.

Registered by tools/build.py in dist/claude/hooks/hooks.json for six events. The payload (stdin JSON) has
`hook_event_name`, `session_id`, `cwd`; per event:

  PreToolUse (matcher Skill)      tool_input.skill = "starcode:<skill>" or "<skill>" of a crew member
  UserPromptExpansion             command_name = "starcode:<skill>" (a typed /starcode:<skill>)
      -> marks the member working in .starcode/live/sessions.json (+ recalculates crew.json) and prints
         {"systemMessage": "<plain-text header>"} (no permission decision field)
  PostToolUse                     renews the session's `at` (silent)
  Stop                            session entry active=false (silent)
  UserPromptSubmit                session entry active=true and renewed, when it exists (silent)
  SessionEnd                      removes the session entry and recalculates crew.json (silent)

Never breaks the session: invalid JSON, outside Git, unreadable/unwritable files -> exit 0, no output.
Python stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

MISSION_MAX = 80


def member_for(name: object, crew: dict[str, dict], prefixed_only: bool = False) -> str | None:
    """Crew key whose skill is `name` ("starcode:<skill>" or, unless prefixed_only, "<skill>")."""
    if not isinstance(name, str):
        return None
    name = name.strip()
    if name.startswith("starcode:"):
        name = name[len("starcode:"):]
    elif prefixed_only:
        return None
    for key, m in crew.items():
        if m.get("skill") == name:
            return key
    return None


def plain_header(member: dict, mission: str | None) -> str:
    """The header as plain text: the systemMessage markdown rendering was not verified (R2)."""
    import crew_live  # noqa: PLC0415

    model = "padrão do CLI" if member.get("model") in (None, "cli-default") else member["model"]
    open_line = (member.get("voice") or {}).get("open", "")
    lines = [crew_live.RULE,
             f"{member.get('emoji', '')} {member['name'].upper()} ASSUME A PONTE",
             f"{member.get('role', '')} · {member.get('cli')} · {model}"]
    text = " ".join(str(mission or "").split())[:MISSION_MAX].strip()
    if text:
        lines.append(f"Missão: {text}")
    if open_line:
        lines.append(f"“{open_line}”")
    lines.append(crew_live.RULE)
    return "\n".join(lines)


def handle(payload: dict, now: datetime | None = None) -> str | None:
    """Apply the event to the live files. Returns the systemMessage text, or None. Raises on I/O failure."""
    import crew_live  # noqa: PLC0415

    event = payload.get("hook_event_name")
    sid = payload.get("session_id")
    if not isinstance(sid, str) or not sid:
        return None
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) and payload.get("cwd") else os.getcwd()
    now = now or datetime.now(timezone.utc)
    stamp = now.replace(microsecond=0).isoformat()
    member = mission = None

    if event in ("PreToolUse", "UserPromptExpansion"):
        crew, _ = crew_live.crew_members()
        if event == "PreToolUse":
            if payload.get("tool_name") != "Skill":
                return None
            tin = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
            member, mission = member_for(tin.get("skill"), crew), tin.get("args")
        else:
            member = member_for(payload.get("command_name"), crew, prefixed_only=True)
            mission = payload.get("command_args", payload.get("args"))
        if member is None:
            return None
    elif event not in ("PostToolUse", "Stop", "UserPromptSubmit", "SessionEnd"):
        return None

    d = crew_live.live_dir(cwd)
    if d is None:
        return None
    crew, available = crew_live.crew_members()

    def mutate(sessions: dict) -> None:
        entry = sessions.get(sid)
        if member is not None:
            sessions[sid] = {"member": member, "active": True, "source": "hook", "at": stamp}
        elif event == "SessionEnd":
            sessions.pop(sid, None)
        elif isinstance(entry, dict):
            entry["at"] = stamp
            if event == "Stop":
                entry["active"] = False
            elif event == "UserPromptSubmit":
                entry["active"] = True

    if member is None and event != "SessionEnd":  # nothing to do without an entry: do not write
        spath = d / crew_live.SESSIONS_FILE
        existing = json.loads(spath.read_text(encoding="utf-8")) if spath.exists() else {}
        if not isinstance(existing, dict) or not isinstance(existing.get(sid), dict):
            return None
    crew_live.update_sessions(d, available, mutate, now, strict=True)
    return plain_header(crew[member], mission if isinstance(mission, str) else None) if member else None


def main() -> int:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        if not isinstance(payload, dict):
            return 0
        message = handle(payload)
        if message:
            sys.stdout.buffer.write(json.dumps({"systemMessage": message}, ensure_ascii=False).encode("utf-8"))
            sys.stdout.buffer.write(b"\n")
    except Exception:  # noqa: BLE001 - a hook never breaks the session (F0-5)
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
