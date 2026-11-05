"""Content tests for the Q brief and skill (R22, R44)."""
from __future__ import annotations

import unittest

from helpers import ROOT

BRIEF = (ROOT / "src" / "briefs" / "q-verify.md").read_text(encoding="utf-8")
SKILL = (ROOT / "skills" / "q" / "SKILL.md").read_text(encoding="utf-8")


class QBriefTests(unittest.TestCase):
    def test_q_brief_contract(self):
        for marker in ("{{spec}}", "{{tasks}}", "{{proofs}}", "{{range}}", "{{output}}"):
            self.assertIn(marker, BRIEF)
        self.assertIn("Write only `{{output}}`", BRIEF)
        self.assertIn("Do not edit, create, delete or commit any other file", BRIEF)
        self.assertIn("do not need StarCode", BRIEF)
        self.assertIn("would fail if the claim were false", BRIEF)
        self.assertIn("Examples nobody cited", BRIEF)
        self.assertIn("Assertions looser than the criterion", BRIEF)
        for heading in ("**Verdict**:", "**Proofs**:", "**HEAD**:", "## Checks", "## Findings", "| Closed |"):
            self.assertIn(heading, BRIEF)
        self.assertIn("at most 5 lines", BRIEF)
        # the file is written as UTF-8 without BOM, with real line breaks, through a file-editing tool
        self.assertIn("UTF-8 without BOM", BRIEF)
        self.assertIn("real line breaks", BRIEF)
        self.assertIn("Set-Content", BRIEF)
        self.assertIn("Out-File", BRIEF)
        self.assertIn("-Encoding utf8", BRIEF)
        self.assertNotIn("Handoff", BRIEF)  # the author's reasoning never reaches the verifier

    def test_q_skill_records_model_and_head(self):
        self.assertTrue(SKILL.startswith("---\nname: q\n"))
        self.assertIn("**HEAD**:", SKILL)
        self.assertIn("requested model", SKILL)
        self.assertIn("effective model", SKILL)
        self.assertIn("unconfirmed", SKILL)
        self.assertIn("**CLI**", SKILL)
        self.assertIn("self-verified", SKILL)
        self.assertIn("only**\n`.specs/features/<slug>/verification.md`", SKILL)
        self.assertIn("never touch\n`.specs/STATE.md`", SKILL)


if __name__ == "__main__":
    unittest.main()
