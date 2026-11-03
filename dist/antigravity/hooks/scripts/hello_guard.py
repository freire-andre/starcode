"""StarCode Phase 0 probe: blocks any shell command containing STARCODE_BLOCK_TEST.

Reads the hook payload (JSON) from stdin.

Default (Claude Code, Codex): print a PreToolUse JSON deny and exit 0. On Windows, Codex runs
hooks through `pwsh -Command`, which turns a native exit code 2 into 1, so "exit 2 + stderr"
is reported as a failed hook and the command runs anyway (fail-open). The JSON deny survives that.

`--exit2`: write the reason to stderr and exit 2.
`--agy` (Antigravity CLI): read toolCall.args.CommandLine and print {"decision": "deny"}.
"""
import json
import sys

MARKER = "STARCODE_BLOCK_TEST"
REASON = "STARCODE-HOOK-BLOCKED: command blocked by StarCode probe hook"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    agy = "--agy" in sys.argv[1:]
    if agy:
        tool_input = (payload.get("toolCall") or {}).get("args") or {}
        command = tool_input.get("CommandLine") if isinstance(tool_input, dict) else None
    else:
        tool_input = payload.get("tool_input") or {}
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not (isinstance(command, str) and MARKER in command):
        if agy:
            sys.stdout.write(json.dumps({"decision": "allow"}))
        return 0
    if agy:
        sys.stdout.write(json.dumps({"decision": "deny", "reason": REASON}))
        return 0
    if "--exit2" in sys.argv[1:]:
        sys.stderr.write(REASON + "\n")
        return 2
    sys.stdout.write(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": REASON,
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
