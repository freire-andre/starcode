"""C8: CHANGELOG.md segue o Keep a Changelog e tem a seção [1.0.0] (R13)."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

CHANGELOG = ROOT / "CHANGELOG.md"


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.text = CHANGELOG.read_text(encoding="utf-8")

    def section(self, title_re: str) -> str:
        parts = re.split(r"^## ", self.text, flags=re.M)
        return next(p for p in parts if re.match(title_re, p))

    def test_changelog_has_1_0_0_section(self):
        self.assertIn("Keep a Changelog", self.text)
        self.assertIn("Semantic Versioning", self.text)
        unreleased = self.section(r"\[Unreleased\]")
        self.assertEqual(unreleased.split("\n", 1)[1].strip(), "")
        sec = self.section(r"\[1\.0\.0\] - \d{4}-\d{2}-\d{2}")
        for heading in ("Adicionado", "Alterado", "Corrigido"):
            m = re.search(rf"^### {heading}\n((?:.*\n?)*?)(?=^### |\Z)", sec, flags=re.M)
            self.assertIsNotNone(m, heading)
            self.assertIn("- ", m.group(1), heading)
        for fase in range(1, 7):
            self.assertRegex(sec, rf"Fase {fase}\b")


README = ROOT / "README.md"


class ReadmeTests(unittest.TestCase):
    def setUp(self):
        self.text = README.read_text(encoding="utf-8")

    def test_readme_install_commands_per_cli(self):
        for cmd in (
            "/plugin marketplace add freire-andre/starcode",
            "/plugin install starcode@starcode",
            "codex plugin marketplace add freire-andre/starcode",
            "codex plugin add starcode@starcode",
            "/hooks",
            "git clone https://github.com/freire-andre/starcode.git",
            "python tools/install_local.py --cli antigravity",
            "python tools/install_local.py --cli opencode",
        ):
            self.assertIn(cmd, self.text, cmd)

    def test_readme_states_v1_and_private_access(self):
        self.assertIn("v1.0", self.text)
        self.assertIn("gh auth login", self.text)
        self.assertIn("docs/compatibilidade.md", self.text)
        self.assertNotIn("Fase 1", self.text)


if __name__ == "__main__":
    unittest.main()
