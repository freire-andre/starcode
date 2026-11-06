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
        sec = self.section(r"\[1\.0\.0\] - AAAA-MM-DD")
        for heading in ("Adicionado", "Alterado", "Corrigido"):
            m = re.search(rf"^### {heading}\n((?:.*\n?)*?)(?=^### |\Z)", sec, flags=re.M)
            self.assertIsNotNone(m, heading)
            self.assertIn("- ", m.group(1), heading)
        for fase in range(1, 7):
            self.assertRegex(sec, rf"Fase {fase}\b")


if __name__ == "__main__":
    unittest.main()
