"""Phase 0 probe generator: writes the "hello" plugin into dist/<cli>/ for all four CLIs.

Throwaway: replaced by tools/build.py in Phase 1. Python stdlib only.
Usage: python tools/build_hello.py
"""
from __future__ import annotations

import json
import shutil
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tests" / "fixtures" / "hello-src"
DIST = ROOT / "dist"
NAME = "starcode-hello"
VERSION = "0.0.1"
DESC = "StarCode Phase 0 probe plugin (format and compatibility tests)."

AGENT_BODY = (
    "You are a StarCode Phase 0 probe subagent.\n"
    "Reply with exactly one line: `STARCODE-AGENT-OK model=<the model id you were told you run on, or unknown>`.\n"
    "Do not run tools.\n"
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


AUTHOR = {"name": "Andre Freire"}


def write_icon(path: Path, size: int = 512) -> None:
    """Square PNG (solid StarCode blue) written with the stdlib only."""
    row = bytes([0]) + bytes((0x1F, 0x4E, 0x9A)) * size
    raw = row * size

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    signature = bytes([137, 80, 78, 71, 13, 10, 26, 10])
    png = (signature + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def write_json(path: Path, data: object) -> None:
    write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def copy_skills(target: Path) -> None:
    shutil.copytree(SRC / "skills", target / "skills")


def copy_hook_scripts(target: Path) -> None:
    dest = target / "hooks" / "scripts"
    dest.mkdir(parents=True, exist_ok=True)
    for script in (SRC / "hooks").glob("*.py"):
        shutil.copy2(script, dest / script.name)


def hooks_block(root_var: str, shell_matcher: str, session_matcher: str | None, guard_args: str = "") -> dict:
    guard = f'python "{root_var}/hooks/scripts/hello_guard.py"{guard_args}'
    banner = f'python "{root_var}/hooks/scripts/hello_banner.py"'
    session_entry: dict = {"hooks": [{"type": "command", "command": banner}]}
    if session_matcher:
        session_entry = {"matcher": session_matcher, **session_entry}
    return {
        "hooks": {
            "PreToolUse" if shell_matcher == "Bash" else "BeforeTool": [
                {"matcher": shell_matcher, "hooks": [{"type": "command", "command": guard}]}
            ],
            "SessionStart": [session_entry],
        }
    }


def build_claude() -> None:
    out = DIST / "claude"
    write_json(out / ".claude-plugin" / "plugin.json",
               {"name": NAME, "version": VERSION, "description": DESC, "author": AUTHOR})
    write_icon(out / ".claude-plugin" / "icon.png")
    copy_skills(out)
    copy_hook_scripts(out)
    write_json(out / "hooks" / "hooks.json", hooks_block("${CLAUDE_PLUGIN_ROOT}", "Bash", "startup|resume|clear|compact"))
    write(out / "agents" / "hello-agent.md",
          "---\nname: hello-agent\ndescription: StarCode Phase 0 probe subagent. Use only when asked to run the hello-agent probe.\n"
          "model: haiku\ntools: []\n---\n\n" + AGENT_BODY)


def build_codex() -> None:
    out = DIST / "codex"
    write_json(out / ".codex-plugin" / "plugin.json",
               {"name": NAME, "version": VERSION, "description": DESC, "author": AUTHOR,
                "interface": {"displayName": "StarCode hello", "shortDescription": "Phase 0 probe"}})
    copy_skills(out)
    # Codex 0.166 reads plugin hooks (after user trust, see DECISIONS F0-1). No plugin-root variable is
    # confirmed yet, so the probe uses absolute paths into dist/codex (provisional; resolved in Phase 4).
    copy_hook_scripts(out)
    scripts = (out / "hooks" / "scripts").as_posix()
    write_json(out / "hooks" / "hooks.json", {"hooks": {
        "SessionStart": [{"matcher": "startup|resume", "hooks": [
            {"type": "command", "command": f"python {scripts}/hello_banner.py"}]}],
        "PreToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": f"python {scripts}/hello_guard.py"}]}],
    }})


def build_antigravity() -> None:
    """Antigravity CLI (agy) native plugin: plugin.json at the root, named hooks, run_command tool."""
    out = DIST / "antigravity"
    write_json(out / "plugin.json",
               {"name": NAME, "version": VERSION, "description": DESC, "author": AUTHOR["name"]})
    copy_skills(out)
    copy_hook_scripts(out)
    # Hook commands run from an unconfirmed working directory: absolute path to the installed copy.
    scripts = (Path.home() / ".gemini" / "config" / "plugins" / NAME / "hooks" / "scripts").as_posix()  # provisional
    write_json(out / "hooks.json", {
        "starcode-guard": {"PreToolUse": [{"matcher": "run_command", "hooks": [
            {"type": "command", "command": f"python {scripts}/hello_guard.py --agy", "timeout": 10}]}]},
        "starcode-banner": {"SessionStart": [
            {"type": "command", "command": f"python {scripts}/hello_banner.py --agy", "timeout": 10}]},
    })
    write(out / "agents" / "hello-agent.md",
          "---\nname: hello-agent\ndescription: StarCode Phase 0 probe subagent. Use only when asked to run the hello-agent probe.\n"
          "subagent: true\nmainAgent: false\nmodel: flash\n---\n\n" + AGENT_BODY)


def build_opencode() -> None:
    out = DIST / "opencode"
    copy_skills(out)
    write(out / "plugins" / "starcode.ts", """// StarCode Phase 0 probe (OpenCode V2 plugin API).
// No import of "@opencode/plugin": an unresolved import makes OpenCode skip the plugin silently.
// The default export is the same object Plugin.define() would receive.
const MARKER = "STARCODE_BLOCK_TEST"

export default {
  id: "starcode.hello",
  async setup(ctx: any) {
    await ctx.tool.hook("execute.before", (event: any) => {
      const input = event.input as { command?: string }
      if (typeof input?.command === "string" && input.command.includes(MARKER)) {
        throw new Error("STARCODE-HOOK-BLOCKED: command blocked by StarCode probe hook")
      }
    })
  },
}
""")
    write(out / "agents" / "hello-agent.md",
          "---\ndescription: StarCode Phase 0 probe subagent. Use only when asked to run the hello-agent probe.\n"
          "mode: subagent\n---\n\n" + AGENT_BODY)


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    build_claude()
    build_codex()
    build_antigravity()
    build_opencode()
    write_json(ROOT / ".claude-plugin" / "marketplace.json", {
        "name": "starcode",
        "description": "StarCode private marketplace.",
        "owner": AUTHOR,
        "plugins": [{"name": NAME, "source": "./dist/claude", "description": DESC}],
    })
    write_json(ROOT / ".agents" / "plugins" / "marketplace.json", {
        "name": "starcode",
        "interface": {"displayName": "StarCode"},
        "plugins": [{"name": NAME, "source": {"source": "local", "path": "./dist/codex"}}],
    })
    print("dist/ generated:", ", ".join(sorted(p.name for p in DIST.iterdir())))


if __name__ == "__main__":
    main()
