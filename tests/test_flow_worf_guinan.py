"""Worf and Guinan in the Picard flow (R17, R18, R20, R32)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from helpers import ROOT
from test_support import execute_text

CLIS = ("claude", "codex", "antigravity", "opencode")


def _roots() -> list[Path]:
    return [ROOT] + [ROOT / "dist" / cli for cli in CLIS]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _section(text: str, header: str) -> str:
    m = re.search(rf"^{re.escape(header)}.*?(?=^## |\Z)", text, re.S | re.M)
    assert m, header
    return m.group(0)


class FlowWorfGuinanTests(unittest.TestCase):
    def test_crew_worf_guinan_invocation_both(self):
        # R32
        text = _read(ROOT, "src/crew.yaml")
        for who in ("worf", "guinan"):
            block = _section(text.replace("\n  " + who + ":", "\n## " + who + ":"), "## " + who + ":")
            self.assertIn("invocation: both", block, who)

    def test_execute_review_worf_after_pr(self):
        # R17, R18
        for root in _roots():
            text = execute_text(root)
            self.assertIn("## Review (Worf)", text, root)
            sec = _section(text, "## Review (Worf)")
            self.assertRegex(sec, r"(?i)after (opening )?the PR", root)
            self.assertRegex(sec, r"(?i)before .*merge authori[sz]ation", root)
            self.assertIn("REQUEST_CHANGES", sec)
            self.assertIn("should-fix", sec)
            self.assertRegex(sec, r"(?i)one LaForge dispatch", root)
            self.assertRegex(sec, r"(?i)round 3", root)
            self.assertRegex(sec, r"(?i)without asking for (the )?merge", root)
            self.assertRegex(sec, r"(?i)confirm", root)
            self.assertLess(text.index("## 5."), text.index("## Review (Worf)"))

    def test_execute_guinan_after_done(self):
        # R20
        for root in _roots():
            text = execute_text(root)
            sec = _section(text, "## 5.")
            self.assertIn("Guinan", sec, root)
            self.assertLess(sec.index("run_gates.py done"), sec.index("Guinan"))
            self.assertRegex(sec, r"(?i)before the PR", root)
            self.assertIn("## Text for the PR and the Linear comments (Uhura)", text)

    def test_skill_flow_line_and_starcode_context(self):
        for root in _roots():
            self.assertIn("→ Guinan → PR → Worf → merge authorization",
                          _read(root, "skills/engajar/SKILL.md"), root)
        text = _read(ROOT, "src/context/STARCODE.md")
        self.assertIn("LESSONS.md", text)
        self.assertIn("Worf", text)
        self.assertIn("Guinan", text)


if __name__ == "__main__":
    unittest.main()
