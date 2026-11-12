"""Tests for F7-12 (SC-84): crew_hook.py, sessions.json validity, statusline, banner version warning, build."""
from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from helpers import ROOT, TempRepoCase
import banner
import build
import crew_live
import statusline

HOOK = ROOT / "hooks" / "scripts" / "crew_hook.py"
CREW = crew_live.crew_members()[1]  # whatever has a skill today; does not break when new crew arrives
RULE = "━" * 36


def ago(minutes: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).replace(microsecond=0).isoformat()


class HookCase(TempRepoCase):
    def live(self) -> Path:
        return self.repo / ".starcode" / "live"

    def fire(self, event: str, sid: str = "s1", raw: str | None = None, cwd: Path | None = None, **extra):
        payload = {"hook_event_name": event, "session_id": sid, "cwd": str(cwd or self.repo), **extra}
        res = subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(payload),
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout

    def skill(self, name: str, sid: str = "s1", args: str = "") -> str:
        return self.fire("PreToolUse", sid, tool_name="Skill", tool_input={"skill": name, "args": args})

    def crew(self) -> dict:
        return json.loads((self.live() / "crew.json").read_text(encoding="utf-8"))

    def sessions(self) -> dict:
        return json.loads((self.live() / "sessions.json").read_text(encoding="utf-8"))

    def put_sessions(self, data: dict) -> None:
        self.live().mkdir(parents=True, exist_ok=True)
        (self.live() / "sessions.json").write_text(json.dumps(data), encoding="utf-8")


class CrewHookTest(HookCase):
    def test_crew_hook_skill_marks_member_and_shows_header(self):
        out = self.skill("starcode:spock", args="export-csv")
        doc = json.loads(out)
        self.assertEqual(list(doc), ["systemMessage"])
        self.assertIn("SPOCK ASSUME A PONTE", doc["systemMessage"])
        entry = self.sessions()["s1"]
        self.assertEqual((entry["member"], entry["active"], entry["source"]), ("spock", True, "hook"))
        self.assertTrue(entry["at"])
        self.assertEqual(self.crew()["spock"], 1)
        self.assertEqual(list(self.crew()), CREW)
        out = self.fire("UserPromptExpansion", "s2", command_name="starcode:engajar", command_args="x")
        self.assertEqual(list(json.loads(out)), ["systemMessage"])
        self.assertIn("PICARD ASSUME A PONTE", json.loads(out)["systemMessage"])
        self.assertEqual((self.crew()["picard"], self.crew()["spock"]), (1, 1))
        before = self.sessions()
        self.assertEqual(self.skill("starcode:setup", "s3"), "")
        self.assertEqual(self.fire("UserPromptExpansion", "s3", command_name="starcode:setup"), "")
        self.assertEqual(self.skill("some-other-skill", "s3"), "")
        self.assertEqual(self.sessions(), before)
        self.assertIn("TROI", json.loads(self.skill("troi", "s4"))["systemMessage"])  # bare name

    def test_crew_hook_header_plain_text(self):
        spock = crew_live.crew_members()[0]["spock"]  # the plugin crew, as the hook resolves it
        model = "padrão do CLI" if spock.get("model") in (None, "cli-default") else spock["model"]
        top = [RULE, "🖖 SPOCK ASSUME A PONTE", f"{spock['role']} · {spock['cli']} · {model}"]
        bottom = [f"“{spock['voice']['open']}”", RULE]
        m80, m81 = "m" * 80, "n" * 81
        msg = json.loads(self.skill("starcode:spock", args="# **x** > " + "m" * 120))["systemMessage"]
        lines = msg.splitlines()
        self.assertEqual(lines, top + ["Missão: " + ("# **x** > " + "m" * 120)[:80]] + bottom)
        self.assertEqual(lines[0], RULE)
        self.assertEqual(lines[-1], RULE)
        self.assertIn("Fascinante.", lines[-2])
        exact = json.loads(self.skill("starcode:spock", args=m80))["systemMessage"].splitlines()
        self.assertEqual(exact, top + ["Missão: " + m80] + bottom)
        cut = json.loads(self.skill("starcode:spock", args=m81))["systemMessage"].splitlines()
        self.assertEqual(cut, top + ["Missão: " + "n" * 80] + bottom)
        bare = json.loads(self.skill("starcode:spock"))["systemMessage"].splitlines()
        self.assertEqual(bare, top + bottom)
        self.assertFalse(any(line.startswith("Missão:") for line in bare))
        plain = json.loads(self.skill("starcode:data", "s9", args="# **x** >"))["systemMessage"]
        self.assertNotIn("**", msg.replace("**x**", ""))
        for text in (msg.replace("# **x** > ", ""), plain.replace("# **x** >", "")):
            self.assertNotRegex(text, r">|#|\*\*")
        self.assertNotIn("Missão", json.loads(self.skill("starcode:q", "s8"))["systemMessage"])

    def test_crew_hook_post_tool_use_pulses(self):
        self.assertEqual(self.fire("PostToolUse", tool_name="Bash"), "")
        self.assertFalse((self.live() / "sessions.json").exists())  # no entry: nothing changes
        self.put_sessions({"s1": {"member": "spock", "active": True, "source": "hook", "at": ago(10)}})
        self.assertEqual(self.fire("PostToolUse", tool_name="Bash"), "")
        e = self.sessions()["s1"]
        self.assertEqual((e["member"], e["active"], e["source"]), ("spock", True, "hook"))
        self.assertGreater(datetime.fromisoformat(e["at"]), datetime.now(timezone.utc) - timedelta(minutes=1))

    def test_crew_hook_stop_and_prompt_toggle(self):
        self.skill("starcode:spock")
        self.assertEqual(self.fire("Stop"), "")
        self.assertFalse(self.sessions()["s1"]["active"])
        self.assertEqual(self.crew()["spock"], 0)
        self.assertEqual(self.fire("UserPromptSubmit"), "")
        self.assertTrue(self.sessions()["s1"]["active"])
        self.assertEqual(self.crew()["spock"], 1)
        self.assertEqual(self.fire("UserPromptSubmit", "other"), "")
        self.assertNotIn("other", self.sessions())

    def test_crew_hook_session_end_clears(self):
        self.skill("starcode:spock")
        self.skill("starcode:laforge", "s2")
        self.assertEqual(self.fire("SessionEnd", reason="other"), "")
        self.assertNotIn("s1", self.sessions())
        self.assertEqual((self.crew()["spock"], self.crew()["laforge"]), (0, 1))

    def test_crew_hook_never_breaks(self):
        for raw in ("{not json", "", "[1,2]", "null"):
            self.assertEqual(self.fire("x", raw=raw), "")
        outside = Path(tempfile.mkdtemp(prefix="starcode-nogit-"))
        try:
            self.assertEqual(self.skill_in(outside), "")
        finally:
            shutil.rmtree(outside, ignore_errors=True)
        self.live().mkdir(parents=True)
        (self.live() / "sessions.json").write_text("{broken", encoding="utf-8")
        self.assertEqual(self.skill("starcode:spock"), "")
        (self.live() / "sessions.json").unlink()
        (self.live() / "sessions.json").mkdir()  # unreadable: a folder where the file should be
        self.assertEqual(self.skill("starcode:spock"), "")
        self.assertEqual(self.fire("Stop"), "")

    def skill_in(self, cwd: Path) -> str:
        return self.fire("PreToolUse", cwd=cwd, tool_name="Skill", tool_input={"skill": "starcode:spock"})


class LiveExpiryTest(HookCase):
    def run_cli(self, *args: str) -> int:
        with mock.patch("sys.stdout", io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
            return crew_live.main(["--cwd", str(self.repo), *args])

    def test_crew_live_expiry_and_laforge_count(self):
        self.put_sessions({
            "old-hook": {"member": "spock", "active": True, "source": "hook", "at": ago(16)},
            "old-cli": {"member": "troi", "active": True, "source": "cli", "at": ago(61)},
            "cli-ok": {"member": "data", "active": True, "source": "cli", "at": ago(59)},
            "hook-ok": {"member": "mccoy", "active": True, "source": "hook", "at": ago(14)},
            "future": {"member": "picard", "active": True, "source": "hook", "at": ago(-5)},
            "bad-at": {"member": "picard", "active": True, "source": "hook", "at": "not-a-date"},
            "bad-source": {"member": "picard", "active": True, "source": "other", "at": ago(1)},
            "no-source": {"member": "picard", "active": True, "at": ago(1)},
            "skew-ok": {"member": "troi", "active": False, "source": "hook", "at": ago(-0.5)},
        })
        now = datetime.now(timezone.utc)
        sessions = json.loads((self.live() / "sessions.json").read_text(encoding="utf-8"))
        counts = crew_live.count_members(sessions, now)
        self.assertEqual((counts.get("spock", 0), counts.get("troi", 0)), (0, 0))
        self.assertEqual((counts["data"], counts["mccoy"]), (1, 1))
        self.assertEqual(counts.get("picard", 0), 0)  # future / unreadable `at` / unknown source count 0
        self.assertEqual(self.run_cli("set", "q", "1"), 0)  # any write drops the expired entries
        self.assertEqual(set(self.sessions()), {"cli-ok", "hook-ok", "skew-ok", "cli:q"})
        crew = self.crew()
        self.assertEqual((crew["spock"], crew["troi"], crew["data"], crew["q"]), (0, 0, 1, 1))
        # two LaForge sessions and `set laforge 1` -> 2 (the larger, not the sum)
        self.skill("starcode:laforge", "a")
        self.skill("starcode:laforge", "b")
        self.assertEqual(self.run_cli("set", "laforge", "1"), 0)
        self.assertEqual(self.crew()["laforge"], 2)
        self.assertEqual(self.run_cli("set", "laforge", "4"), 0)
        self.assertEqual(self.crew()["laforge"], 4)
        self.assertEqual(self.run_cli("set", "laforge", "0"), 0)
        self.assertEqual(self.crew()["laforge"], 2)
        self.assertEqual(self.run_cli("reset"), 0)
        self.assertEqual(set(self.crew().values()), {0})
        self.assertEqual(self.sessions(), {})

    def skill(self, name: str, sid: str) -> None:
        self.fire("PreToolUse", sid, tool_name="Skill", tool_input={"skill": name})


class StatuslineTest(HookCase):
    def test_statusline_expiry_and_laforge_count(self):
        self.put_sessions({
            "a": {"member": "spock", "active": True, "source": "hook", "at": ago(16)},
            "b": {"member": "laforge", "active": True, "source": "hook", "at": ago(1)},
            "c": {"member": "laforge", "active": True, "source": "hook", "at": ago(2)},
            "d": {"member": "picard", "active": False, "source": "hook", "at": ago(1)},
        })
        (self.live() / "crew.json").write_text(json.dumps({"spock": 1, "picard": 1, "laforge": 0}), encoding="utf-8")
        before = {p.name: p.read_bytes() for p in self.live().iterdir()}
        out = re.sub(r"\x1b\[[0-9;]*m", "", statusline.segment(str(self.repo)))
        self.assertIn("🔧 LaForge ×2", out)
        self.assertNotIn("Spock", out)
        self.assertNotIn("Picard", out)
        self.assertEqual({p.name: p.read_bytes() for p in self.live().iterdir()}, before)  # nothing written
        self.put_sessions({"b": {"member": "laforge", "active": True, "source": "hook", "at": ago(1)}})
        out = re.sub(r"\x1b\[[0-9;]*m", "", statusline.segment(str(self.repo)))
        self.assertIn("LaForge", out)
        self.assertNotIn("×", out)


class BannerTest(TempRepoCase):
    def source_repo(self, version: str) -> None:
        (self.repo / "VERSION").write_text(version + "\n", encoding="utf-8")
        manifest = self.repo / "dist" / "claude" / ".claude-plugin" / "plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("{}", encoding="utf-8")

    def line(self, running: str | None) -> str | None:
        with mock.patch.object(banner, "plugin_version", return_value=running):
            return banner.outdated_plugin_line(self.repo)

    def test_banner_warns_outdated_plugin(self):
        self.source_repo("1.1.0")
        expected = "⚠️ plugin StarCode instalado 1.0.0, repositório 1.1.0: atualize o plugin e abra uma nova sessão"
        self.assertEqual(self.line("1.0.0"), expected)
        self.assertIsNone(self.line("1.1.0"))
        self.assertIsNone(self.line("1.2.0"))
        self.assertIsNone(self.line(None))
        with mock.patch.object(banner, "plugin_version", return_value="1.0.0"), \
             mock.patch.object(banner, "check_orca", return_value="Orca: ✅"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]):
            for cli in (None, "codex", "opencode"):
                text, _, _ = banner.build_banner(str(self.repo), False, cli)
                self.assertIn(expected, text.splitlines())
        shutil.rmtree(self.repo / "dist")  # not the StarCode source any more
        self.assertIsNone(self.line("1.0.0"))
        (self.repo / "dist" / "claude" / ".claude-plugin").mkdir(parents=True)
        (self.repo / "dist" / "claude" / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
        (self.repo / "VERSION").unlink()
        self.assertIsNone(self.line("1.0.0"))


class BuildTest(TempRepoCase):
    def test_build_registers_crew_hook_only_in_claude(self):
        events = json.loads((ROOT / "dist" / "claude" / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        self.assertEqual(set(events), {"PreToolUse", "SessionStart", "UserPromptExpansion", "PostToolUse", "Stop",
                                       "UserPromptSubmit", "SessionEnd"})

        def crew_entries(name: str) -> list[dict]:
            return [g for g in events[name] if any("crew_hook.py" in h["command"] for h in g["hooks"])]

        wanted = {"PreToolUse": "Skill", "UserPromptExpansion": "starcode:.*", "PostToolUse": "*",
                  "Stop": None, "UserPromptSubmit": None, "SessionEnd": None}
        for name, matcher in wanted.items():
            (group,) = crew_entries(name)
            self.assertEqual(group.get("matcher"), matcher, name)
            self.assertEqual([h["timeout"] for h in group["hooks"]], [10], name)
        text = json.dumps(events)
        for script in ("git_guard.py", "secret_scan.py", "banner.py"):
            self.assertIn(script, text)
        # Codex (F7-14), Antigravity and OpenCode (F7-16) got their own crew_hook registration
        self.assertIn("--cli codex", json.dumps(build.codex_hooks()))
        self.assertIn("crew_hook.py", json.dumps(build.codex_hooks()))
        self.assertIn("--cli antigravity", json.dumps(build.antigravity_hooks()))

    def test_build_header_rule_per_cli(self):
        sentence = build.HEADER_RULE_CLAUDE
        self.assertEqual(sentence, "In Claude Code the StarCode hook already showed your header and marks you as working: "
                                   "do not run crew_live.py start/stop and do not repeat the header.")
        for skill in ("engajar", "troi", "spock", "data", "laforge", "mccoy", "q"):
            text = (ROOT / "dist" / "claude" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(sentence, text, skill)
            self.assertNotIn('crew_live.py" start', text, skill)
            self.assertNotIn("Header first (F6-6)", text, skill)
            for cli in ("codex", "antigravity", "opencode"):
                other = (ROOT / "dist" / cli / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn(sentence, other, f"{cli}/{skill}")
                self.assertNotIn('crew_live.py" start', other, f"{cli}/{skill}")  # F7-14 / F7-16 swap F6-6


class DocsTest(TempRepoCase):
    def test_decisions_records_f7_12_crew_hook(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("### F7-12:", text)
        body = text.split("### F7-12:", 1)[1].split("\n### ", 1)[0]
        for needle in ("crew_hook.py", "sessions.json", "15 min", "60 min", "(R1)", "(R11)", "(R12)"):
            self.assertIn(needle, body)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        release_section = changelog.split("## [1.2.0]", 1)[1].split("\n## [", 1)[0]
        self.assertIn("crew_hook.py", release_section)


CODEX_RULE = ("In Codex the StarCode hook shows your header and marks you as working once its hooks are trusted: "
              "do not run crew_live.py start/stop and do not repeat the header.")
SKILL_PATH = "C:\\x\\starcode\\1.1.0\\skills\\troi\\SKILL.md"


class CodexHookCase(HookCase):
    def fire(self, event: str, sid: str = "s1", raw: str | None = None, cwd: Path | None = None, **extra):
        payload = {"hook_event_name": event, "session_id": sid, "cwd": str(cwd or self.repo), **extra}
        res = subprocess.run([sys.executable, str(HOOK), "--cli", "codex"],
                             input=raw if raw is not None else json.dumps(payload),
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout

    def bash(self, command: str, sid: str = "s1", **extra) -> str:
        return self.fire("PreToolUse", sid, tool_name="Bash", tool_input={"command": command}, **extra)

    def prompt(self, text: str, sid: str = "s1", **extra) -> str:
        return self.fire("UserPromptSubmit", sid, prompt=text, **extra)


class CrewHookCodexTest(CodexHookCase):
    def test_crew_hook_codex_skill_read_marks_member(self):
        out = self.bash(f"Get-Content {SKILL_PATH}")
        self.assertEqual(list(json.loads(out)), ["systemMessage"])
        self.assertIn("TROI ASSUME A PONTE", json.loads(out)["systemMessage"])
        entry = self.sessions()["s1"]
        self.assertEqual((entry["member"], entry["active"], entry["source"]), ("troi", True, "hook"))
        self.assertEqual(self.crew()["troi"], 1)
        # case-insensitive, forward slashes, other crew member
        out = self.bash("cat /home/u/.codex/plugins/StarCode/skills/spock/skill.md", "s2")
        self.assertIn("SPOCK ASSUME A PONTE", json.loads(out)["systemMessage"])
        before = self.sessions()
        out = self.bash("cat C:/x/StarCode/skills/Troi/SKILL.md", "s4")
        self.assertIn("TROI ASSUME A PONTE", json.loads(out)["systemMessage"])
        out = self.bash(r"type C:\x\starcode\1.1.0\skills\SPOCK\SKILL.md", "s5")
        self.assertIn("SPOCK ASSUME A PONTE", json.loads(out)["systemMessage"])
        before = self.sessions()
        self.assertEqual(self.bash("cat C:/x/other-plugin/skills/troi/SKILL.md", "s3"), "")
        self.assertEqual(self.bash("ls C:/x/starcode/skills/troi", "s3"), "")
        self.assertEqual(self.bash("cat C:/x/starcode/skills/unknown/SKILL.md", "s3"), "")
        self.assertEqual(self.fire("PreToolUse", "s3", tool_name="Skill",
                                   tool_input={"skill": "starcode:troi", "command": SKILL_PATH}), "")
        self.assertEqual(self.sessions(), before)

    def test_crew_hook_codex_prompt_token(self):
        out = json.loads(self.prompt("$starcode:spock revisar a spec\noutra linha"))["systemMessage"]
        self.assertIn("SPOCK ASSUME A PONTE", out)
        self.assertIn("Missão: revisar a spec", out.splitlines())
        self.assertNotIn("outra linha", out)
        self.assertEqual(self.sessions()["s1"]["member"], "spock")
        out = json.loads(self.prompt("quero isso: $troi " + "x" * 100, "s2"))["systemMessage"]
        self.assertIn("TROI ASSUME A PONTE", out)
        self.assertIn("Missão: " + "x" * 80, out.splitlines())
        self.assertEqual(self.crew()["troi"], 1)
        before = self.sessions()
        out = json.loads(self.prompt("$Spock revisar", "s4"))["systemMessage"]
        self.assertIn("SPOCK ASSUME A PONTE", out)
        self.assertIn("Missão: revisar", out.splitlines())
        out = json.loads(self.prompt("$TROI", "s5"))["systemMessage"]
        lines = out.splitlines()
        self.assertEqual(len(lines), 5, lines)
        self.assertEqual(lines[0], lines[-1])
        self.assertIn("TROI ASSUME A PONTE", lines[1])
        self.assertTrue(lines[2].endswith(" · codex · padrão do CLI"), lines[2])
        self.assertFalse(any(l.startswith("Missão:") for l in lines))
        before = self.sessions()
        self.assertEqual(self.prompt("custa US$data hoje", "s3"), "")
        self.assertEqual(self.prompt("$starcode sem skill", "s3"), "")
        self.assertEqual(self.sessions(), before)
        # a plain prompt only reactivates an existing entry
        self.fire("Stop")
        self.assertFalse(self.sessions()["s1"]["active"])
        self.assertEqual(self.prompt("e agora?"), "")
        self.assertTrue(self.sessions()["s1"]["active"])
        self.assertEqual(self.prompt("e agora?", "none"), "")
        self.assertNotIn("none", self.sessions())

    def test_crew_hook_codex_header_shows_running_cli(self):
        out = json.loads(self.prompt("$troi", model="gpt-5.5"))["systemMessage"]
        self.assertTrue(out.splitlines()[2].endswith(" · codex · gpt-5.5"), out)
        self.assertNotIn("claude", out.splitlines()[2])
        out = json.loads(self.prompt("$spock", "s2", model=7))["systemMessage"]
        self.assertTrue(out.splitlines()[2].endswith(" · codex · padrão do CLI"), out)
        out = json.loads(self.bash(f"cat {SKILL_PATH}", "s3"))["systemMessage"]
        self.assertTrue(out.splitlines()[2].endswith(" · codex · padrão do CLI"), out)

    def test_crew_hook_codex_lifecycle(self):
        self.assertEqual(self.fire("PostToolUse", tool_name="Bash"), "")
        self.assertFalse((self.live() / "sessions.json").exists())
        self.put_sessions({"s1": {"member": "spock", "active": True, "source": "hook", "at": ago(10)}})
        self.assertEqual(self.fire("PostToolUse", tool_name="Bash"), "")
        self.assertGreater(datetime.fromisoformat(self.sessions()["s1"]["at"]),
                           datetime.now(timezone.utc) - timedelta(minutes=1))
        self.assertEqual(self.fire("Stop"), "")
        self.assertFalse(self.sessions()["s1"]["active"])
        self.assertEqual(self.crew()["spock"], 0)
        self.assertEqual(self.fire("SessionEnd", reason="other"), "")
        self.assertNotIn("s1", self.sessions())
        self.assertEqual(self.fire("UserPromptExpansion", command_name="starcode:spock"), "")  # not a Codex event

    def test_crew_hook_codex_no_repeat_header(self):
        self.assertIn("ASSUME A PONTE", self.bash(f"cat {SKILL_PATH}"))
        self.put_sessions({"s1": {**self.sessions()["s1"], "at": ago(5)}})
        self.assertEqual(self.bash(f"cat {SKILL_PATH}"), "")
        entry = self.sessions()["s1"]
        self.assertGreater(datetime.fromisoformat(entry["at"]), datetime.now(timezone.utc) - timedelta(minutes=1))
        self.assertEqual(self.prompt("$troi de novo"), "")  # same member, same session: no second header
        self.assertIn("SPOCK ASSUME A PONTE", self.prompt("$spock agora"))  # another member shows its own
        self.fire("Stop")
        self.assertIn("SPOCK ASSUME A PONTE", self.prompt("$spock outra vez"))  # inactive: header again

    def test_crew_hook_codex_never_breaks(self):
        for raw in ("{not json", "", "[1,2]", "null"):
            self.assertEqual(self.fire("PreToolUse", raw=raw), "")
        self.assertEqual(self.fire("PreToolUse", tool_name="Bash", tool_input="x"), "")
        self.assertEqual(self.fire("UserPromptSubmit", prompt=5), "")
        outside = Path(tempfile.mkdtemp(prefix="starcode-nogit-"))
        try:
            out = self.fire("PreToolUse", cwd=outside, tool_name="Bash", tool_input={"command": SKILL_PATH})
            self.assertEqual(out, "")
        finally:
            shutil.rmtree(outside, ignore_errors=True)
        self.live().mkdir(parents=True, exist_ok=True)
        (self.live() / "sessions.json").write_text("{broken", encoding="utf-8")
        self.assertEqual(self.bash(SKILL_PATH), "")
        (self.live() / "sessions.json").unlink()
        (self.live() / "sessions.json").mkdir()  # unwritable: a folder where the file should be
        self.assertEqual(self.bash(SKILL_PATH), "")
        self.assertEqual(self.prompt("$troi x"), "")
        self.assertEqual(self.fire("Stop"), "")


class CodexBuildTest(TempRepoCase):
    def test_build_registers_crew_hook_in_codex(self):
        events = json.loads((ROOT / "dist" / "codex" / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        self.assertEqual(set(events), {"PreToolUse", "SessionStart", "PostToolUse", "Stop", "UserPromptSubmit",
                                       "SessionEnd"})

        def crew_groups(name: str) -> list[dict]:
            return [g for g in events[name] if any("crew_hook.py" in h["command"] for h in g["hooks"])]

        wanted = {"PreToolUse": "Bash", "UserPromptSubmit": None, "PostToolUse": None, "Stop": None,
                  "SessionEnd": None}
        for name, matcher in wanted.items():
            (group,) = crew_groups(name)
            self.assertEqual(group.get("matcher"), matcher, name)
            (hook,) = group["hooks"]
            self.assertTrue(hook["command"].endswith('crew_hook.py" --cli codex'), name)
            self.assertEqual(hook["timeout"], 3 if name == "SessionEnd" else 10, name)
        text = json.dumps(events)
        for script in ("git_guard.py", "secret_scan.py", "banner.py"):
            self.assertIn(script, text)
        self.assertEqual(len(events["PreToolUse"]), 2)  # the guards group is kept
        # F7-16: antigravity and opencode now register crew_hook too (see test_crew_hook_agy_opencode.py)

    def test_build_header_rule_codex(self):
        self.assertEqual(build.HEADER_RULE_CODEX, CODEX_RULE)
        for skill in ("engajar", "troi", "spock", "data", "laforge", "mccoy", "q"):
            text = (ROOT / "dist" / "codex" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(CODEX_RULE, text, skill)
            self.assertNotIn('crew_live.py" start', text, skill)
            self.assertNotIn("Header first (F6-6)", text, skill)
            agy = (ROOT / "dist" / "antigravity" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn(CODEX_RULE, agy, skill)


class CodexDocsTest(TempRepoCase):
    def test_decisions_records_f7_14_codex_hooks(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("### F7-14:", text)
        body = text.split("### F7-14:", 1)[1].split("\n### ", 1)[0]
        for needle in ("crew_hook.py --cli codex", "SKILL.md", "$starcode:<skill>", "(R1)", "(R8)", "(R9)"):
            self.assertIn(needle, body)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        release_section = changelog.split("## [1.2.0]", 1)[1].split("\n## [", 1)[0]
        self.assertIn("crew_hook.py --cli codex", release_section)
        compat = (ROOT / "docs" / "compatibilidade.md").read_text(encoding="utf-8")
        row = next(l for l in compat.splitlines() if l.startswith("| Cabeçalho por hook"))
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual(cells[1:3], ["✅", "✅ (após confiança)"])  # F7-16 updated the other two
