"""Skills use {{CMD}} and the engajar banner passes --cli (R7, R8; checks C4, C5)."""
from __future__ import annotations

import unittest

from helpers import ROOT

DIST = ROOT / "dist"
CLIS = ("claude", "codex", "antigravity", "opencode")


def skill_files(cli: str):
    return sorted((DIST / cli / "skills").rglob("*.md"))


class SkillsCliTests(unittest.TestCase):
    def test_source_has_no_literal_starcode_command(self):  # R7
        for path in sorted((ROOT / "skills").rglob("*.md")):
            self.assertNotIn("/starcode:", path.read_text(encoding="utf-8"), str(path))

    def test_non_claude_dist_has_no_starcode_prefix(self):  # R7, C4
        for cli in CLIS:
            if cli == "claude":
                continue
            files = skill_files(cli)
            self.assertTrue(files, cli)
            for path in files:
                self.assertNotIn("/starcode:", path.read_text(encoding="utf-8"), str(path))

    def test_engajar_banner_gets_cli(self):  # R8, C5
        for cli in CLIS:
            text = (DIST / cli / "skills" / "engajar" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(f"banner.py\" --full --text --cli {cli}", text, cli)


if __name__ == "__main__":
    unittest.main()
