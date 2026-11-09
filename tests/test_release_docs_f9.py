"""F9 T11 (C38): as decisões F9-n e a seção [1.3.0] do CHANGELOG existem (R31)."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT


class ReleaseDocsF9Tests(unittest.TestCase):
    def test_release_docs_f9(self):
        decisions = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        ids = re.findall(r"^### (F9-\d+):", decisions, flags=re.M)
        self.assertGreaterEqual(len(set(ids)), 8, ids)
        self.assertEqual(len(ids), len(set(ids)), "F9-n duplicada")
        for termo in ("publicação confirmada", "review.md", "evidência de segurança", "review_finding",
                      "antes do PR", "depois do PR", "npx", "Track A", "aprovação por execução",
                      "scripts/review/", "scripts/harness/"):
            self.assertIn(termo.lower(), decisions.lower(), termo)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertRegex(changelog, r"(?m)^## \[1\.3\.0\] - 2026-11-09$")
        section = re.split(r"^## ", changelog.split("## [1.3.0] - 2026-11-09", 1)[1], flags=re.M)[0]
        for termo in ("worf", "guinan", "diagnostico", "scripts/review/", "scripts/harness/", "lessons.py"):
            self.assertIn(termo, section, termo)

    def test_compatibilidade_lists_f9_row(self):
        text = (ROOT / "docs" / "compatibilidade.md").read_text(encoding="utf-8")
        row = next((l for l in text.splitlines() if "`worf`" in l and "`guinan`" in l and "`diagnostico`" in l), "")
        self.assertTrue(row, "linha das 3 skills ausente")
        self.assertEqual(row.count("✅"), 4, row)


if __name__ == "__main__":
    unittest.main()
