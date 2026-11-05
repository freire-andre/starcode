import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

import build


def copy_source(dest: Path) -> None:
    for name in ("skills", "hooks", "scripts", "src", "schemas", "tools"):
        shutil.copytree(ROOT / name, dest / name, ignore=shutil.ignore_patterns("__pycache__"))
    if (ROOT / "evals").is_dir():
        shutil.copytree(ROOT / "evals", dest / "evals", ignore=shutil.ignore_patterns("results"))
    shutil.copy(ROOT / "VERSION", dest / "VERSION")


class BuildTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.src = Path(self._tmp.name) / "src"
        self.out = Path(self._tmp.name) / "out"
        copy_source(self.src)

    def tearDown(self):
        self._tmp.cleanup()

    def test_repo_dist_is_up_to_date(self):
        res = subprocess.run([sys.executable, str(ROOT / "tools" / "build.py"), "--check"],
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_layout_per_cli(self):
        build.build(self.src, self.out)
        dist = self.out / "dist"
        self.assertTrue((dist / "claude" / ".claude-plugin" / "plugin.json").exists())
        self.assertTrue((dist / "claude" / "hooks" / "hooks.json").exists())
        self.assertTrue((dist / "codex" / ".codex-plugin" / "plugin.json").exists())
        self.assertTrue((dist / "antigravity" / "plugin.json").exists())
        self.assertTrue((dist / "opencode" / "commands" / "sc-engajar.md").exists())
        # Hooks are registered only for Claude in Phase 1; no CLI gets another CLI's files.
        self.assertFalse((dist / "codex" / "hooks" / "hooks.json").exists())
        self.assertFalse((dist / "antigravity" / "hooks.json").exists())
        self.assertFalse((dist / "claude" / "plugin.json").exists())
        self.assertFalse((dist / "antigravity" / ".claude-plugin").exists())

    def test_placeholders_rendered_per_cli(self):
        build.build(self.src, self.out)
        claude = (self.out / "dist" / "claude" / "skills" / "engajar" / "SKILL.md").read_text(encoding="utf-8")
        codex = (self.out / "dist" / "codex" / "skills" / "engajar" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("${CLAUDE_SKILL_DIR}/../..", claude)
        self.assertNotIn("CLAUDE_SKILL_DIR", codex)
        self.assertIn("Número Um, relatório.", claude)
        for text in (claude, codex):
            self.assertNotIn("{{", text)

    def test_crew_json_lists_only_available(self):
        build.build(self.src, self.out)
        crew = json.loads((self.out / "dist" / "claude" / "crew.json").read_text(encoding="utf-8"))
        self.assertEqual(crew["available"][:4], ["picard", "spock", "troi", "data"])
        self.assertIn("q", crew["available"])  # Phase 3: skills/q exists
        self.assertNotIn("uhura", crew["available"])  # no skills/uhura yet
        self.assertEqual(crew["version"], (ROOT / "VERSION").read_text(encoding="utf-8").strip())

    def test_claude_hooks_use_plugin_root(self):
        build.build(self.src, self.out)
        hooks = json.loads((self.out / "dist" / "claude" / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        cmds = [h["command"] for e in hooks["hooks"]["PreToolUse"] for h in e["hooks"]]
        self.assertTrue(all("${CLAUDE_PLUGIN_ROOT}" in c for c in cmds))
        self.assertTrue(any("git_guard.py" in c for c in cmds) and any("secret_scan.py" in c for c in cmds))

    def test_unknown_placeholder_fails(self):
        skill = self.src / "skills" / "setup" / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "\n{{NOPE}}\n", encoding="utf-8")
        with self.assertRaises(build.BuildError):
            build.build(self.src, self.out)

    def test_plugin_root_placeholder_only_in_skill_md(self):
        ref = self.src / "skills" / "engajar" / "references" / "git-modes.md"
        ref.write_text(ref.read_text(encoding="utf-8") + "\n{{PLUGIN_ROOT}}\n", encoding="utf-8")
        with self.assertRaises(build.BuildError):
            build.build(self.src, self.out)

    def test_undeclared_skill_fails(self):
        (self.src / "skills" / "rogue").mkdir()
        (self.src / "skills" / "rogue" / "SKILL.md").write_text("---\nname: rogue\ndescription: x\n---\n",
                                                                encoding="utf-8")
        with self.assertRaises(build.BuildError):
            build.build(self.src, self.out)

    def test_check_detects_hand_edit(self):
        build.build(self.src, self.out)
        target = self.out / "dist" / "claude" / "skills" / "setup" / "SKILL.md"
        target.write_text("edited by hand", encoding="utf-8")
        expected = Path(self._tmp.name) / "expected"
        build.build(self.src, expected)
        problems = build.compare(expected, self.out)
        self.assertEqual(problems, ["diferente: dist/claude/skills/setup/SKILL.md"])

    def test_user_invocation_adds_claude_frontmatter(self):
        text = build.claude_frontmatter("---\nname: x\ndescription: y\n---\n\nbody\n", "user")
        self.assertIn("disable-model-invocation: true\n---\n", text)
        self.assertEqual(build.claude_frontmatter("---\nname: x\n---\n", "both"), "---\nname: x\n---\n")

    def test_build_emits_execution_skills(self):
        build.build(self.src, self.out)
        claude = self.out / "dist" / "claude"
        for skill in ("laforge", "mccoy", "q"):
            text = (claude / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(f"name: {skill}", text)
            self.assertNotIn("{{", text.split("---", 2)[2].replace("{{spec}}", ""))
        brief = (claude / "briefs" / "q-verify.md").read_text(encoding="utf-8")
        self.assertIn("{{output}}", brief)  # filled at dispatch time by scripts/dispatch.py
        self.assertTrue((claude / "scripts" / "dispatch.py").is_file())
        self.assertTrue((claude / "skills" / "engajar" / "references" / "execute.md").is_file())

    def test_routing_and_decisions_cover_phase3(self):
        routing = ROOT / "evals" / "routing"
        for skill, case in (("laforge", "pos-laforge-ticket"), ("mccoy", "pos-mccoy-bug"), ("q", "pos-q-verify")):
            text = (routing / case / "case.yaml").read_text(encoding="utf-8")
            self.assertIn(f'input_match: "starcode:{skill}"', text)
        decisions = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("## Decisões da Fase 3", decisions)
        self.assertIn("### F3-1:", decisions)


if __name__ == "__main__":
    unittest.main()
