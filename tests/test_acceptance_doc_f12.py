"""R36 a R38: aceite real da Fase 12 registrado em docs/aceite/fase-12.md."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

DOC = ROOT / "docs" / "aceite" / "fase-12.md"


class AcceptanceDocF12Tests(unittest.TestCase):
    def test_acceptance_doc_f12(self):
        self.assertTrue(DOC.is_file())
        text = DOC.read_text(encoding="utf-8")
        self.assertRegex(text, re.compile(r"^\*\*Resultado\*\*: aprovado$", re.M))
        for trecho in (
            "refs/starcode/snapshots/aceite/T1",
            "DISJUNTOR ABERTO",
            "fora do ticket",
            "rodar tudo: fora do grafo",
            "src/greeting.test.ts",
        ):
            self.assertIn(trecho, text)


if __name__ == "__main__":
    unittest.main()
