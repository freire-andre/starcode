from __future__ import annotations

import re
import unittest

from helpers import ROOT


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


class ReleaseDocsF11Tests(unittest.TestCase):
    def test_release_docs_f11(self):
        decisions = _read("DECISIONS.md")
        ids = re.findall(r"^### (F11-\d+):", decisions, flags=re.M)
        self.assertEqual(len(ids), len(set(ids)), "F11-n duplicada")
        self.assertIn("F11-8", ids)
        d25 = next(l for l in decisions.splitlines() if l.startswith("| D25 "))
        self.assertIn("superada pela Fase 11", d25)

        adr = _read("docs/adr/ADR-0002-formato-dos-gates.md")
        row = next(l for l in adr.splitlines() if "captures/" in l and l.startswith("|"))
        self.assertIn("Fase 11", row)
        self.assertNotIn("| removidas |", row)

        changelog = _read("CHANGELOG.md")
        self.assertRegex(changelog, r"(?m)^## \[1\.5\.0\] - 2026-11-12$")
        section = re.split(r"^## ", changelog.split("## [1.5.0] - 2026-11-12", 1)[1], flags=re.M)[0]
        self.assertIn("telas", section)

        compat = _read("docs/compatibilidade.md")
        line = next((l for l in compat.splitlines() if "erificação de telas" in l), "")
        self.assertTrue(line, "linha da verificação de telas ausente")
        self.assertIn("navegador da Orca", line)

        credits = _read("CREDITS.md")
        row = next((l for l in credits.splitlines() if "tlc-spec-driven" in l and "captura" in l.lower()), "")
        self.assertTrue(row, "crédito do tlc para as regras de captura ausente")
        for termo in ("Felipe Rodrigues", "CC-BY-4.0", "screens.py"):
            self.assertIn(termo, row)


if __name__ == "__main__":
    unittest.main()
