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

    def test_no_claude_commands_outside_claude_dist(self):  # R7, C4
        for cli in CLIS:
            if cli == "claude":
                continue
            files = skill_files(cli)
            self.assertTrue(files, cli)
            for path in files:
                self.assertNotIn("/starcode:", path.read_text(encoding="utf-8"), str(path))

    def test_engajar_banner_uses_cli(self):  # R8, C5
        for cli in CLIS:
            text = (DIST / cli / "skills" / "engajar" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(f"banner.py\" --full --text --cli {cli}", text, cli)

    def _setup(self, cli: str) -> str:
        return (DIST / cli / "skills" / "setup" / "SKILL.md").read_text(encoding="utf-8")

    def test_setup_codex_shows_trust_step(self):  # R11, C17
        text = self._setup("codex")
        self.assertIn("/hooks", text)
        self.assertIn("aprovar os hooks do `starcode`", text)
        self.assertRegex(text, r"[Nn]unca (?:dê|dar) o trust")

    def test_setup_opencode_confirms_plugin_copy(self):  # R12, C18
        text = self._setup("opencode")
        self.assertRegex(text, r"(?s)confirma\w+.*python tools/install_local\.py --cli opencode")
        self.assertIn("caminho gravado", text)

    def test_setup_checks_python_per_cli(self):  # R13, C19
        for cli in CLIS:
            text = self._setup(cli)
            self.assertIn("python --version", text, cli)
            self.assertIn("Python não encontrado: os hooks do StarCode não vão rodar neste CLI", text, cli)
            self.assertIn(f"`{cli}`", text, cli)


if __name__ == "__main__":
    unittest.main()
