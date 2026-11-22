"""Content tests for the worker skills laforge and mccoy (R38, R40-R43, R45)."""
from __future__ import annotations

import unittest

from helpers import ROOT
from test_support import execute_text

LAFORGE = (ROOT / "skills" / "laforge" / "SKILL.md").read_text(encoding="utf-8")
MCCOY = (ROOT / "skills" / "mccoy" / "SKILL.md").read_text(encoding="utf-8")


class WorkerSkillTests(unittest.TestCase):
    def test_laforge_skill_scope_tdd_commit(self):
        self.assertTrue(LAFORGE.startswith("---\nname: laforge\n"))
        self.assertIn("**Only the files in `May change`.**", LAFORGE)
        self.assertIn("**stop**: do not edit it; report the file and why", LAFORGE)
        self.assertIn("**TDD.** Write the test first", LAFORGE)
        self.assertIn("**One commit per task**", LAFORGE)
        self.assertIn("`Refs: <ID>`", LAFORGE)
        self.assertIn("run_gates.py\" commit --message", LAFORGE)
        self.assertIn("run_gates.py\" ticket <slug> <ticket> <base>..HEAD", LAFORGE)
        self.assertIn("never write\n`.specs/STATE.md` or any `## Handoff`", LAFORGE)

    def test_laforge_calls_mccoy_on_second_failure(self):
        self.assertIn("**stable error id**", LAFORGE)
        self.assertIn("**2nd failure of the same id: invoke the `mccoy` skill**", LAFORGE)
        self.assertIn("**3rd failure of the same id: stop.** Do not make a 4th attempt.", LAFORGE)

    def test_mccoy_skill_regression_and_report(self):
        self.assertTrue(MCCOY.startswith("---\nname: mccoy\n"))
        self.assertIn("**Regression test first.** Before the fix", MCCOY)
        self.assertIn("**Only files in `May change`.**", MCCOY)
        self.assertIn("Error id · cause", MCCOY)
        self.assertIn("regression test created", MCCOY)
        self.assertIn("`.specs/STATE.md` or any `## Handoff`", MCCOY)
        for text in (LAFORGE, MCCOY):
            self.assertIn("## Report (at most 5 lines)", text)

    def test_execute_stops_on_codex_hooks_review(self):
        for cli in ("claude", "codex", "opencode", "antigravity"):
            text = execute_text(ROOT / "dist" / cli)
            with self.subTest(cli=cli):
                self.assertIn("agent-hooks-review-prompt", text)
                self.assertIn("pending\n   hooks", text)
                self.assertIn("open `/hooks` in Codex and approve the `starcode` hooks", text)
                self.assertIn("Do **not** retry, do **not** use\n   `--dangerously-bypass-hook-trust`", text)


if __name__ == "__main__":
    unittest.main()
