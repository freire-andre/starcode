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

Codex mode (`--cli codex`, F7-14): Codex has no Skill tool nor UserPromptExpansion, so the member is found by
  PreToolUse (tool_name Bash)     tool_input.command reads `...starcode.../skills/<skill>/SKILL.md` (or with backslashes)
  UserPromptSubmit                prompt has `$starcode:<skill>` or `$<skill>` (at the start or after a space);
                                  the mission is the rest of that line; a prompt without the token only reactivates
  The same member already active in the session only renews `at` (no second header). Other events as above.

Antigravity mode (`--cli antigravity --event <Name>`, F7-16): the real agy payload carries no event name, so the
  event comes from `--event` (a payload `hookEventName` is only a fallback). Payload: `conversationId`, `modelName`,
  `workspacePaths`, `invocationNum`, `toolCall {name, args {Path|CommandLine}}`. PreToolUse (read_file, view_file,
  run_command) on a crew SKILL.md marks the session and parks the header in .starcode/live/pending.json;
  PostInvocation prints {"injectSteps": [...ephemeralMessage...]} once. It never prints a decision field.
OpenCode mode (`--cli opencode`, F7-16): {"event": skill|pulse|prompt|idle, "session_id", "skill", "cwd", "mission"};
  `skill` of a crew member prints {"header": "<header>"}; the role line always reads `opencode · padrão do CLI`
  (the session model is unknown to the plugin, so the crew's configured model is never shown).

Never breaks the session: invalid JSON, outside Git, unreadable/unwritable files -> exit 0, no output.
Python stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

MISSION_MAX = 80
SKILL_READ = re.compile(r"starcode[^\n\"']*?[\\/]skills[\\/]([\w-]+)[\\/]SKILL\.md", re.I)
PROMPT_TOKEN = re.compile(r"(?:^|(?<=\s))\$(?:starcode:)?([\w-]+)")


def member_for(name: object, crew: dict[str, dict], prefixed_only: bool = False) -> str | None:
    """Crew key whose skill is `name` ("starcode:<skill>" or, unless prefixed_only, "<skill>")."""
    if not isinstance(name, str):
        return None
    name = name.strip().lower()
    if name.startswith("starcode:"):
        name = name[len("starcode:"):]
    elif prefixed_only:
        return None
    for key, m in crew.items():
        if str(m.get("skill", "")).lower() == name:
            return key
    return None


def plain_header(member: dict, mission: str | None, running: tuple[str, str] | None = None) -> str:
    """The header as plain text: the systemMessage markdown rendering was not verified (R2)."""
    import crew_live  # noqa: PLC0415

    model = "padrão do CLI" if member.get("model") in (None, "cli-default") else member["model"]
    cli = member.get("cli")
    if running:  # Codex mode: show who actually runs, not the crew config (F7-15)
        cli, model = running
    open_line = (member.get("voice") or {}).get("open", "")
    lines = [crew_live.RULE,
             f"{member.get('emoji', '')} {member['name'].upper()} ASSUME A PONTE",
             f"{member.get('role', '')} · {cli} · {model}"]
    text = " ".join(str(mission or "").split())[:MISSION_MAX].strip()
    if text:
        lines.append(f"Missão: {text}")
    if open_line:
        lines.append(f"“{open_line}”")
    lines.append(crew_live.RULE)
    return "\n".join(lines)


def codex_member(event: object, payload: dict, crew: dict[str, dict]) -> tuple[str | None, str | None]:
    """(crew key, mission) the Codex event points at: a Bash read of a crew SKILL.md or a `$skill` prompt token."""
    if event == "PreToolUse":
        tin = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
        command = tin.get("command")
        if payload.get("tool_name") != "Bash" or not isinstance(command, str):
            return None, None
        for m in SKILL_READ.finditer(command):
            member = member_for(m.group(1), crew)
            if member:
                return member, None
    elif event == "UserPromptSubmit":
        prompt = payload.get("prompt")
        if not isinstance(prompt, str):
            return None, None
        for m in PROMPT_TOKEN.finditer(prompt):
            member = member_for(m.group(1), crew)
            if member:
                return member, prompt[m.end():].splitlines()[0] if prompt[m.end():].strip() else None
    return None, None


AGY_ORDER = "Comece sua próxima resposta ao usuário com este cabeçalho, sem mudar nada:\n"
PENDING_FILE = "pending.json"
AGY_READ_TOOLS = ("read_file", "view_file", "run_command")


def agy_event(payload: dict) -> object:
    for key in ("hookEventName", "hook_event_name", "eventName", "event", "evento"):
        if isinstance(payload.get(key), str):
            return payload[key]
    return None


def agy_member(payload: dict, crew: dict[str, dict]) -> str | None:
    call = payload.get("toolCall") if isinstance(payload.get("toolCall"), dict) else {}
    args = call.get("args") if isinstance(call.get("args"), dict) else {}
    if call.get("name") not in AGY_READ_TOOLS:
        return None
    for key in ("Path", "CommandLine"):
        text = args.get(key)
        if isinstance(text, str):
            for m in SKILL_READ.finditer(text):
                member = member_for(m.group(1), crew)
                if member:
                    return member
    return None


def handle_extra(payload: dict, cli: str, now: datetime | None = None, event: str | None = None) -> dict | None:
    """Antigravity / OpenCode (F7-16). Returns the JSON document to print, or None. Raises on I/O failure."""
    import crew_live  # noqa: PLC0415

    now = now or datetime.now(timezone.utc)
    stamp = now.replace(microsecond=0).isoformat()
    agy = cli == "antigravity"
    if agy:
        event, sid = event or agy_event(payload), payload.get("conversationId")
        paths = payload.get("workspacePaths")
        cwd = paths[0] if isinstance(paths, list) and paths and isinstance(paths[0], str) and paths[0] else None
        model = payload.get("modelName")
        running = ("antigravity", model.strip() if isinstance(model, str) and model.strip() else "padrão do CLI")
        if event not in ("PreToolUse", "PostToolUse", "PreInvocation", "PostInvocation", "Stop"):
            return None
    else:
        event, sid = payload.get("event"), payload.get("session_id")
        cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) and payload.get("cwd") else None
        running = None
        if event not in ("skill", "pulse", "prompt", "idle"):
            return None
    if not isinstance(sid, str) or not sid:
        return None
    cwd = cwd or os.getcwd()

    member = mission = None
    if (agy and event == "PreToolUse") or (not agy and event == "skill"):
        crew, _ = crew_live.crew_members()
        if agy:
            member = agy_member(payload, crew)
        else:
            member = member_for(payload.get("skill"), crew)
            mission = payload.get("mission")
        if member is None:
            return None
    d = crew_live.live_dir(cwd)
    if d is None:
        return None
    crew, available = crew_live.crew_members()
    pending = d / PENDING_FILE

    if agy and event == "PostInvocation":
        data = json.loads(pending.read_text(encoding="utf-8")) if pending.exists() else {}
        header = data.get(sid) if isinstance(data, dict) else None
        if not isinstance(header, str) or not header:
            return None
        data.pop(sid)
        crew_live.write_json(pending, data)
        return {"injectSteps": [{"ephemeralMessage": AGY_ORDER + header}]}

    num = payload.get("invocationNum")

    repeat = False

    def mutate(sessions: dict) -> None:
        nonlocal repeat
        entry = sessions.get(sid)
        if member is not None and isinstance(entry, dict) and entry.get("member") == member                 and entry.get("active") is True and crew_live.entry_valid(entry, now):
            entry["at"] = stamp  # same member already working in this session: no second header/pending (R4)
            repeat = True
        elif member is not None:
            sessions[sid] = {"member": member, "active": True, "source": "hook", "at": stamp}
        elif isinstance(entry, dict):
            entry["at"] = stamp
            if event in ("Stop", "idle"):
                entry["active"] = False
            elif event == "prompt" or (event == "PreInvocation" and num == 0 and not isinstance(num, bool)):
                entry["active"] = True

    if member is None:
        spath = d / crew_live.SESSIONS_FILE
        existing = json.loads(spath.read_text(encoding="utf-8")) if spath.exists() else {}
        if not isinstance(existing, dict) or not isinstance(existing.get(sid), dict):
            return None
    crew_live.update_sessions(d, available, mutate, now, strict=True)
    if member is None or repeat:
        return None
    if not agy:
        # the plugin cannot know which model the OpenCode session runs, so never show the configured one
        running = ("opencode", "padrão do CLI")
    header = plain_header(crew[member], mission if isinstance(mission, str) else None, running)
    if agy:
        data = json.loads(pending.read_text(encoding="utf-8")) if pending.exists() else {}
        data = data if isinstance(data, dict) else {}
        data[sid] = header
        crew_live.write_json(pending, data)
        return None
    return {"header": header}


def handle(payload: dict, now: datetime | None = None, cli: str = "claude") -> str | None:
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

    codex = cli == "codex"
    if codex and event in ("PreToolUse", "UserPromptSubmit"):
        crew, _ = crew_live.crew_members()
        member, mission = codex_member(event, payload, crew)
        if member is None and event == "PreToolUse":
            return None
    elif codex and event in ("PostToolUse", "Stop", "SessionEnd"):
        pass
    elif codex:
        return None
    elif event in ("PreToolUse", "UserPromptExpansion"):
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

    repeat = False

    def mutate(sessions: dict) -> None:
        nonlocal repeat
        entry = sessions.get(sid)
        if member is not None and codex and isinstance(entry, dict) and entry.get("member") == member                 and entry.get("active") is True and crew_live.entry_valid(entry, now):
            entry["at"] = stamp  # same member already working in this session: no second header (R4)
            repeat = True
        elif member is not None:
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
    if member is None or repeat:
        return None
    running = None
    if codex:
        pm = payload.get("model")
        running = ("codex", pm.strip() if isinstance(pm, str) and pm.strip() else "padrão do CLI")
    return plain_header(crew[member], mission if isinstance(mission, str) else None, running)


def main() -> int:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        if not isinstance(payload, dict):
            return 0
        argv = sys.argv[1:]
        cli = argv[argv.index("--cli") + 1] if "--cli" in argv and argv.index("--cli") + 1 < len(argv) else "claude"
        if cli in ("antigravity", "opencode"):
            event = argv[argv.index("--event") + 1] if "--event" in argv and argv.index("--event") + 1 < len(argv) else None
            doc = handle_extra(payload, cli, event=event)
            if doc:
                sys.stdout.buffer.write(json.dumps(doc, ensure_ascii=False).encode("utf-8") + b"\n")
            return 0
        message = handle(payload, cli=cli)
        if message:
            sys.stdout.buffer.write(json.dumps({"systemMessage": message}, ensure_ascii=False).encode("utf-8"))
            sys.stdout.buffer.write(b"\n")
    except Exception:  # noqa: BLE001 - a hook never breaks the session (F0-5)
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
