"""F8 T12 (C38): as decisões F8-n e a seção [1.2.0] do CHANGELOG existem (R38)."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT


class ReleaseDocsF8Tests(unittest.TestCase):
    def test_decisions_f8_and_changelog_1_2_0(self):
        decisions = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        ids = re.findall(r"^### (F8-\d+):", decisions, flags=re.M)
        self.assertGreaterEqual(len(set(ids)), 8, ids)
        self.assertEqual(len(ids), len(set(ids)), "F8-n duplicada")
        for termo in ("templates fixos", "registros", "tested", "Context7", ".starcode/stack.json", "Docker",
                      "Biome", "GPUI", "grill-me", "ci-db.yml", "ruff.toml", "--reuse-env"):
            self.assertIn(termo.lower(), decisions.lower(), termo)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertRegex(changelog, r"(?m)^## \[1\.2\.0\] - não lançada$")
        section = re.split(r"^## ", changelog.split("## [1.2.0] - não lançada", 1)[1], flags=re.M)[0]
        for termo in ("uhura", "scotty", "nova-missao", "profiles/"):
            self.assertIn(termo, section, termo)

    def test_compatibilidade_lists_profiles_row(self):
        text = (ROOT / "docs" / "compatibilidade.md").read_text(encoding="utf-8")
        self.assertIn("Perfis de stack", text)
        for tool in ("uv", "cargo", "npm", "docker"):
            self.assertIn(f"`{tool}`", text)


if __name__ == "__main__":
    unittest.main()
