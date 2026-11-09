"""Content tests for the Scotty skill and the Data wiring to scaffold.py checks (R24, R31, R32)."""
from __future__ import annotations

import unittest
from pathlib import Path

from helpers import ROOT

CLIS = ("claude", "codex", "antigravity", "opencode")


def _roots() -> list[Path]:
    return [ROOT] + [ROOT / "dist" / cli for cli in CLIS]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


class ScottySkillTests(unittest.TestCase):
    def test_scotty_skill_flows(self):
        for root in _roots():
            text = _read(root, "skills/scotty/SKILL.md")
            self.assertTrue(text.startswith("---\nname: scotty\n"), root)
            self.assertIn("description:", text.split("---", 2)[1])
            for needle in ("scaffold.py\" detect", "scaffold.py\" record", "--yes", "source: manifest",
                           "scaffold.py\" new", "starcode-eph-", "60 minutes", "ephemeral_db.py\" list",
                           "ephemeral_db.py\" down", "only with the user's confirmation", "Non-Goal",
                           "Context7", "Uhura", "crew_live.py", "copies **no** template"):
                self.assertIn(needle, text, f"{root}: {needle}")
            if root != ROOT:  # só o dist tem os marcadores trocados
                self.assertNotIn("{{", text)

    def test_data_skill_uses_stack_checks(self):
        # R32
        for root in _roots():
            skill = _read(root, "skills/data/SKILL.md")
            tpl = _read(root, "skills/data/references/tasks-template.md")
            for text in (skill, tpl):
                self.assertIn(".starcode/stack.json", text, root)
                self.assertIn("scaffold.py", text, root)
                self.assertIn("**Run <name>**", text, root)
            self.assertIn("scaffold.py\" checks", skill)
            self.assertIn("without it", tpl)
            self.assertIn("Without `.starcode/stack.json`", skill)  # sem o arquivo: como hoje


if __name__ == "__main__":
    unittest.main()
