"""Content tests for the menu skill: it lists every StarCode skill, rendered per CLI."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

CLIS = ("claude", "codex", "antigravity", "opencode")


def _skills() -> list[str]:
    return sorted(p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists())


class MenuSkillTests(unittest.TestCase):
    def test_menu_lists_every_skill(self):
        text = (ROOT / "skills" / "menu" / "SKILL.md").read_text(encoding="utf-8")
        listed = set(re.findall(r"^• \{\{CMD:([a-z-]+)\}\}", text, re.M))
        self.assertEqual(listed, set(_skills()), "menu fora de sincronia com skills/")

    def test_menu_is_read_only_and_triggers(self):
        text = (ROOT / "skills" / "menu" / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: menu\n"))
        desc = text.split("---", 2)[1]
        for trigger in ("#menu", "menu do StarCode", "quais são as ferramentas do StarCode"):
            self.assertIn(trigger, desc)
        self.assertIn("Do not run any\ntool", text)

    def test_menu_rendered_per_cli(self):
        for cli in CLIS:
            text = (ROOT / "dist" / cli / "skills" / "menu" / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("{{", text, cli)
        claude = (ROOT / "dist" / "claude" / "skills" / "menu" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("• /starcode:engajar · 🛸 Picard", claude)
        opencode = (ROOT / "dist" / "opencode" / "skills" / "menu" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("• /sc-menu · ", opencode)


if __name__ == "__main__":
    unittest.main()
