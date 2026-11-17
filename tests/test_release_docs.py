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
        self.section(r"\[Unreleased\]")  # may list changes made after 1.0.0 (Keep a Changelog)
        sec = self.section(r"\[1\.0\.0\] - \d{4}-\d{2}-\d{2}")
        for heading in ("Adicionado", "Alterado", "Corrigido"):
            m = re.search(rf"^### {heading}\n((?:.*\n?)*?)(?=^### |\Z)", sec, flags=re.M)
            self.assertIsNotNone(m, heading)
            self.assertIn("- ", m.group(1), heading)
        for fase in range(1, 7):
            self.assertRegex(sec, rf"Fase {fase}\b")


class Fase7DocsTests(unittest.TestCase):
    def test_decisions_and_changelog_record_fase_7(self):
        decisions = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        ids = set(re.findall(r"^### (F7-\d+):", decisions, flags=re.M))
        self.assertGreaterEqual(len(ids), 7, ids)
        for termo in ("fleet.workers", "faixa de custo", "serial", "lote", "check --wait", "--deps", "crew.json"):
            self.assertIn(termo, decisions, termo)
        text = CHANGELOG.read_text(encoding="utf-8")
        parts = re.split(r"^## ", text, flags=re.M)
        sec = next(p for p in parts if p.startswith("[1.1.0] - 2026-11-07"))
        self.assertIn("### Adicionado", sec)
        self.assertIn("### Alterado", sec)
        self.assertIn("Frota", sec)
        self.assertLess(text.index("## [1.1.0]"), text.index("## [1.0.0]"))


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

    def test_readme_states_current_version_and_private_access(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        estado = next(l for l in self.text.splitlines() if l.startswith("Estado:"))
        self.assertIn(f"**v{version}**", estado)
        self.assertIn("gh auth login", self.text)
        self.assertIn("docs/compatibilidade.md", self.text)
        self.assertNotIn("Fase 1", self.text)


if __name__ == "__main__":
    unittest.main()
