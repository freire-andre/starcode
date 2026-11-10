"""F10 T8 (C36): as decisões F10-n, os créditos, o CHANGELOG, a compatibilidade e o README citam o painel Ponte (R36)."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


class ReleaseDocsF10Tests(unittest.TestCase):
    def test_release_docs_f10(self):
        decisions = _read("DECISIONS.md")
        ids = re.findall(r"^### (F10-\d+):", decisions, flags=re.M)
        self.assertGreaterEqual(len(set(ids)), 6, ids)
        self.assertEqual(len(ids), len(set(ids)), "F10-n duplicada")
        for termo in ("ponte.py", "dist/orca", "crew.json", "sidebar.right.toggle", "capabilities",
                      "aprovação", "pixel agents", "habblaud", "miniyaml"):
            self.assertIn(termo.lower(), decisions.lower(), termo)

        credits = _read("CREDITS.md")
        for termo in ("Pixel Agents", "pixel-agents-hq/pixel-agents", "Habblaud", "marmottajr/habblaud", "MIT"):
            self.assertIn(termo, credits, termo)

        changelog = _read("CHANGELOG.md")
        self.assertRegex(changelog, r"(?m)^## \[1\.4\.0\] - não lançada$")
        section = re.split(r"^## ", changelog.split("## [1.4.0] - não lançada", 1)[1], flags=re.M)[0]
        self.assertIn("Ponte", section)

        compat = _read("docs/compatibilidade.md")
        row = next((l for l in compat.splitlines() if "Ponte" in l and "1.4.248" in l), "")
        self.assertTrue(row, "linha do painel Ponte ausente")

        readme = _read("README.md")
        self.assertIn("Ponte", readme)
        self.assertIn("python tools/install_local.py --cli orca", readme)


if __name__ == "__main__":
    unittest.main()
