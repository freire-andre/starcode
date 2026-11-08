"""Tests for F7-16 (SC-86): crew_hook.py --cli antigravity|opencode, opencode plugin, build, docs."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from helpers import ROOT, TempRepoCase

HOOK = ROOT / "hooks" / "scripts" / "crew_hook.py"
SKILL_PATH = "C:\\x\\starcode\\skills\\troi\\SKILL.md"
SPOCK_PATH = SKILL_PATH.replace("troi", "spock")
FORBIDDEN = ("decision", "allow", "ask", "deny", "systemMessage", "statusMessage", "displayMessage")
ORDER = "Comece sua próxima resposta ao usuário com este cabeçalho, sem mudar nada:\n"
NODE = shutil.which("node")
BAR = "━" * 36
TROI_AGY = "\n".join([BAR, "💜 TROI ASSUME A PONTE", "Descoberta · antigravity · gemini-3.8-flash-high",
                      "“Sinto que há algo não dito.”", BAR])
SPOCK_AGY = "\n".join([BAR, "🖖 SPOCK ASSUME A PONTE", "Spec e arquitetura · antigravity · gemini-3.8-flash-high",
                       "“Fascinante.”", BAR])
LAFORGE_OC = "\n".join([BAR, "🔧 LAFORGE ASSUME A PONTE", "Implementação · opencode · claude-sonnet-5-5",
                        "Missão: ticket SC-1", "“Motores prontos.”", BAR])


class AgyOpenCodeCase(TempRepoCase):
    def live(self) -> Path:
        return self.repo / ".starcode" / "live"

    def run_hook(self, cli: str, payload: dict | None = None, raw: str | None = None, event: str | None = None) -> str:
        args = ["--event", event] if event else []
        res = subprocess.run([sys.executable, str(HOOK), "--cli", cli, *args],
                             input=raw if raw is not None else json.dumps(payload),
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout

    def agy(self, event: str, cid: str = "c1", cwd: Path | None = None, **extra) -> str:
        # real agy 1.5.2 payload: no event name in stdin; the event travels in --event
        payload = {"conversationId": cid, "modelName": "gemini-3.8-flash-high", "lastUserInput": "x",
                   "transcriptPath": "t", "artifactDirectoryPath": "a",
                   "workspacePaths": [str(cwd or self.repo)], "invocationNum": 0, **extra}
        return self.run_hook("antigravity", payload, event=event)

    def tool(self, name: str, **args) -> dict:
        return {"toolCall": {"name": name, "args": args}}

    def oc(self, event: str, sid: str = "o1", cwd: Path | None = None, **extra) -> str:
        return self.run_hook("opencode", {"event": event, "session_id": sid, "cwd": str(cwd or self.repo), **extra})

    def sessions(self) -> dict:
        return json.loads((self.live() / "sessions.json").read_text(encoding="utf-8"))

    def crew(self) -> dict:
        return json.loads((self.live() / "crew.json").read_text(encoding="utf-8"))

    def pending(self) -> dict:
        return json.loads((self.live() / "pending.json").read_text(encoding="utf-8"))


class CrewHookAgyTest(AgyOpenCodeCase):
    def test_crew_hook_agy_skill_read_marks_pending(self):
        out = self.agy("PreToolUse", **self.tool("read_file", Path=SKILL_PATH))
        self.assertEqual(out, "")
        entry = self.sessions()["c1"]
        self.assertEqual((entry["member"], entry["active"], entry["source"]), ("troi", True, "hook"))
        self.assertEqual(self.crew()["troi"], 1)
        header = self.pending()["c1"]
        self.assertEqual(header, TROI_AGY)
        out = self.agy("PreToolUse", "c2", **self.tool(
            "run_command", CommandLine="Get-Content C:\\x\\starcode\\skills\\spock\\SKILL.md"))
        self.assertEqual(out, "")
        self.assertEqual(self.sessions()["c2"]["member"], "spock")
        self.assertEqual(self.crew()["spock"], 1)
        self.assertEqual(self.pending()["c2"], SPOCK_AGY)
        out = self.agy("PreToolUse", "c3", **self.tool("view_file", Path="C:\\x\\other\\skills\\troi\\SKILL.md"))
        self.assertEqual(out, "")
        self.assertNotIn("c3", self.sessions())
        self.assertNotIn("c3", self.pending())

    def test_crew_hook_agy_never_decides(self):
        events = (("PreToolUse", self.tool("read_file", Path=SKILL_PATH)), ("PostToolUse", {}),
                  ("PreInvocation", {}), ("PostInvocation", {}), ("Stop", {}), ("SessionStart", {}))
        for event, extra in events:
            out = self.agy(event, **extra)
            for word in FORBIDDEN:
                self.assertNotIn(word, out, event)
            if event != "PostInvocation":
                self.assertEqual(out, "", event)
            else:
                self.assertEqual(list(json.loads(out)), ["injectSteps"])

    def test_crew_hook_agy_post_invocation_injects_header(self):
        self.assertEqual(self.agy("PostInvocation"), "")
        self.agy("PreToolUse", **self.tool("read_file", Path=SKILL_PATH))
        doc = json.loads(self.agy("PostInvocation"))
        self.assertEqual(list(doc), ["injectSteps"])
        (step,) = doc["injectSteps"]
        self.assertEqual(list(step), ["ephemeralMessage"])
        self.assertEqual(step["ephemeralMessage"], ORDER + TROI_AGY)
        self.assertNotIn("c1", self.pending())
        self.assertEqual(self.agy("PostInvocation"), "")

    def test_crew_hook_agy_lifecycle(self):
        self.agy("PreToolUse", **self.tool("read_file", Path=SKILL_PATH))
        data = self.sessions()
        data["c1"]["at"] = "2020-01-01T00:00:00+00:00"
        (self.live() / "sessions.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.agy("PostToolUse"), "")
        self.assertNotEqual(self.sessions()["c1"]["at"], "2020-01-01T00:00:00+00:00")
        self.assertEqual(self.agy("Stop"), "")
        self.assertFalse(self.sessions()["c1"]["active"])
        self.assertEqual(self.agy("PreInvocation", invocationNum=1), "")
        self.assertFalse(self.sessions()["c1"]["active"])
        self.assertEqual(self.agy("PreInvocation", invocationNum=0), "")
        self.assertTrue(self.sessions()["c1"]["active"])
        self.assertEqual(self.crew()["troi"], 1)
        self.agy("Stop")
        self.assertEqual(self.crew()["troi"], 0)


class CrewHookAgyEventArgTest(AgyOpenCodeCase):
    def test_crew_hook_agy_event_comes_from_argv(self):
        payload = {"conversationId": "c1", "modelName": "m", "workspacePaths": [str(self.repo)], "invocationNum": 0,
                   **self.tool("read_file", Path=SKILL_PATH)}
        self.assertEqual(self.run_hook("antigravity", payload), "")  # no --event, no event in stdin: ignored
        self.assertFalse((self.live() / "sessions.json").exists())
        self.assertEqual(self.run_hook("antigravity", payload, event="Nada"), "")  # unknown event: ignored
        self.assertFalse((self.live() / "sessions.json").exists())
        self.assertEqual(self.run_hook("antigravity", payload, event="PreToolUse"), "")
        self.assertEqual(self.sessions()["c1"]["member"], "troi")

    def test_crew_hook_agy_stdin_event_is_only_a_fallback(self):
        payload = {"hookEventName": "PreToolUse", "conversationId": "c1", "workspacePaths": [str(self.repo)],
                   **self.tool("read_file", Path=SKILL_PATH)}
        self.assertEqual(self.run_hook("antigravity", payload), "")
        self.assertEqual(self.sessions()["c1"]["member"], "troi")
        # --event wins over the stdin field
        self.assertEqual(self.run_hook("antigravity", {**payload, "conversationId": "c2"}, event="Stop"), "")
        self.assertNotIn("c2", self.sessions())


class CrewHookOpenCodeTest(AgyOpenCodeCase):
    def test_crew_hook_opencode_events(self):
        out = json.loads(self.oc("skill", skill="starcode:laforge", mission="ticket SC-1"))
        self.assertEqual(list(out), ["header"])
        self.assertEqual(out["header"], LAFORGE_OC)
        self.assertEqual(self.sessions()["o1"]["member"], "laforge")
        self.assertEqual(self.crew()["laforge"], 1)
        self.assertEqual(self.oc("idle"), "")
        self.assertFalse(self.sessions()["o1"]["active"])
        self.assertEqual(self.oc("prompt"), "")
        self.assertTrue(self.sessions()["o1"]["active"])
        data = self.sessions()
        data["o1"]["at"] = "2020-01-01T00:00:00+00:00"
        (self.live() / "sessions.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.oc("pulse"), "")
        self.assertNotEqual(self.sessions()["o1"]["at"], "2020-01-01T00:00:00+00:00")
        before = self.sessions()
        self.assertEqual(self.oc("skill", "o2", skill="starcode:nada"), "")
        self.assertEqual(self.sessions(), before)


class CrewHookNeverBreakTest(AgyOpenCodeCase):
    def test_crew_hook_agy_opencode_never_break(self):
        for cli in ("antigravity", "opencode"):
            for raw in ("{not json", "", "[1,2]", "null"):
                self.assertEqual(self.run_hook(cli, raw=raw), "")
        self.assertEqual(self.run_hook("antigravity", {"conversationId": "c1", "toolCall": "x"}, event="PreToolUse"), "")
        self.assertEqual(self.run_hook("opencode", {"event": "skill", "session_id": 5}), "")
        outside = Path(tempfile.mkdtemp(prefix="starcode-nogit-"))
        try:
            self.assertEqual(self.agy("PreToolUse", cwd=outside, **self.tool("read_file", Path=SKILL_PATH)), "")
            self.assertEqual(self.oc("skill", cwd=outside, skill="starcode:troi"), "")
        finally:
            shutil.rmtree(outside, ignore_errors=True)
        self.live().mkdir(parents=True, exist_ok=True)
        (self.live() / "sessions.json").mkdir()  # unwritable: a folder where the file should be
        self.assertEqual(self.agy("PreToolUse", **self.tool("read_file", Path=SKILL_PATH)), "")
        self.assertEqual(self.oc("skill", skill="starcode:troi"), "")
        self.assertEqual(self.agy("Stop"), "")


RUNNER = """
import { pathToFileURL } from "node:url"
const mod = await import(pathToFileURL(process.argv[2]).href)
const reg = {}
const calls = []
const ctx = {
  tool: { hook: async (n, fn) => { reg[n] = fn } },
  session: { hook: (n, fn) => { reg[n] = fn }, synthetic: (a) => { calls.push(a) } },
}
await mod.default.setup(ctx)
await reg["execute.before"]({ tool: "skill", sessionID: "s9", input: { id: "starcode:troi" } })
await reg["execute.after"]({ sessionID: "s9", input: {} })
await reg["prompt"]({ sessionID: "s9" })
await reg["experimental.idle"]({ sessionID: "s9" })
console.log(JSON.stringify({ names: Object.keys(reg), calls }))
"""


class OpenCodePluginCrewTest(AgyOpenCodeCase):
    def test_opencode_plugin_registers_crew_hooks(self):
        text = (ROOT / "dist" / "opencode" / "plugins" / "starcode.js").read_text(encoding="utf-8")
        for needle in ('"execute.before"', '"execute.after"', 'session.hook("prompt"',
                       'session.hook("experimental.idle"', "synthetic", "resume: false",
                       "Comece sua próxima resposta"):
            self.assertIn(needle, text)
        self.assertNotIn("await ctx.session", text)
        self.assertNotIn('await ctx.tool.hook("execute.after', text)
        self.assertGreaterEqual(text.count("catch"), 5)
        self.assertIn("GUARDS", text)
        self.assertIn("throw new Error(reason)", text)
        if not NODE:
            self.skipTest("node not on PATH")
        d = self.tmp / "plugin"
        d.mkdir()
        (d / "starcode.js").write_text(text.replace("{{STARCODE_ROOT}}", ROOT.as_posix()), encoding="utf-8")
        (d / "package.json").write_text('{"type":"module"}', encoding="utf-8")
        (d / "runner.mjs").write_text(RUNNER, encoding="utf-8")
        res = subprocess.run([NODE, str(d / "runner.mjs"), str(d / "starcode.js")], capture_output=True, text=True,
                             encoding="utf-8", cwd=self.repo, stdin=subprocess.DEVNULL)
        self.assertEqual(res.returncode, 0, res.stderr)
        out = json.loads(res.stdout.strip().splitlines()[-1])
        self.assertEqual(sorted(out["names"]),
                         sorted(["execute.before", "execute.after", "prompt", "experimental.idle"]))
        (call,) = out["calls"]
        self.assertEqual((call["sessionID"], call["resume"]), ("s9", False))
        self.assertTrue(call["text"].startswith(ORDER))
        self.assertIn("TROI ASSUME A PONTE", call["text"])


class AgyOpenCodeBuildTest(TempRepoCase):
    def test_build_registers_crew_hook_in_antigravity(self):
        hooks = json.loads((ROOT / "dist" / "antigravity" / "hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(set(hooks), {"starcode-crew", "starcode-guard", "starcode-banner"})
        crew = hooks["starcode-crew"]
        self.assertEqual(set(crew), {"PreToolUse", "PostToolUse", "PreInvocation", "PostInvocation", "Stop"})
        for name, groups in crew.items():
            (group,) = groups
            self.assertEqual(group.get("matcher"), "read_file|view_file|run_command" if name == "PreToolUse" else None)
            (hook,) = group["hooks"]
            self.assertTrue(hook["command"].endswith(f"crew_hook.py --cli antigravity --event {name}"), name)  # C7
            self.assertEqual(hook["timeout"], 10, name)
        self.assertIn("git_guard.py", json.dumps(hooks["starcode-guard"]))
        self.assertIn("banner.py", json.dumps(hooks["starcode-banner"]))

    def test_build_header_rule_agy_opencode(self):
        for cli, label in (("antigravity", "Antigravity"), ("opencode", "OpenCode")):
            rule = (f"In {label} the StarCode hook marks you as working and sends you your header: start your next "
                    "reply with it exactly as sent, and do not run crew_live.py start/stop.")
            for skill in ("engajar", "troi", "spock", "data", "laforge", "mccoy", "q"):
                text = (ROOT / "dist" / cli / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(rule, text, (cli, skill))
                self.assertNotIn('crew_live.py" start', text, (cli, skill))
                self.assertNotIn("Header first (F6-6)", text, (cli, skill))


class AgyOpenCodeDocsTest(TempRepoCase):
    def test_decisions_records_f7_16_agy_opencode_hooks(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("### F7-16:", text)
        body = text.split("### F7-16:", 1)[1].split("\n### ", 1)[0]
        for needle in ("crew_hook.py --cli antigravity", "starcode-crew", "ctx.session.synthetic", "(R1)", "(R11)"):
            self.assertIn(needle, body)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
        self.assertIn("crew_hook.py --cli antigravity|opencode", unreleased)
        compat = (ROOT / "docs" / "compatibilidade.md").read_text(encoding="utf-8")
        row = next(l for l in compat.splitlines() if l.startswith("| Cabeçalho por hook"))
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual(cells[3:], ["✅ (o modelo repete)", "✅ (o modelo repete)"])


if __name__ == "__main__":
    unittest.main()
