"""StarCode Phase 0 probe: session-start banner. Never fails the session start.

Default: additionalContext (Claude Code, Codex). `--agy`: Antigravity CLI injectSteps.
"""
import json
import sys

MARKER = "StarCode banner marker: STARCODE-BANNER-OK"

try:
    sys.stdin.read()
except Exception:
    pass
if "--agy" in sys.argv[1:]:
    print(json.dumps({"injectSteps": [{"ephemeralMessage": MARKER}]}))
else:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": MARKER}}))
