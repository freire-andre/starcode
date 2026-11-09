"""R36: aceite real da Fase 9 (Worf, Guinan e diagnóstico) registrado em docs/aceite/fase-9.md."""
from __future__ import annotations

import os
import re
import unittest

from helpers import ROOT

DOC = ROOT / "docs" / "aceite" / "fase-9.md"
SECTIONS = (
    "Varredura do bypass",
    "Review do PR de teste",
    "Publicação e fallback COMMENT",
    "Lição registrada",
    "Relatório L0–L4",
)
RESULT = re.compile(r"\*\*Resultado\*\*: (\S+)")


def _parts() -> dict[str, str]:
    text = DOC.read_text(encoding="utf-8")
    return {p.split("\n", 1)[0].strip(): p for p in re.split(r"^## ", text, flags=re.M)[1:]}


class AcceptanceDocF9Tests(unittest.TestCase):
    def test_fase9_acceptance_sections(self):
        final = os.environ.get("STARCODE_F9_FINAL") == "1"
        parts = _parts()
        for name in SECTIONS:
            self.assertIn(name, parts, f"falta a seção {name}")
            found = RESULT.search(parts[name])
            self.assertIsNotNone(found, f"{name}: sem **Resultado**")
            status = found.group(1)
            allowed = {"aprovado"} if final else {"aprovado", "pendente"}
            self.assertIn(status, allowed, f"{name}: Resultado {status!r} não aceito")
        scan = parts["Varredura do bypass"]
        self.assertRegex(scan, r"planted_bypass\.py:\d+\ttls-bypass|planted_bypass\.py:\d+.*tls-bypass")
        self.assertRegex(scan, r"test-dodge")
        report = parts["Relatório L0–L4"]
        self.assertRegex(report, r"\bL[0-4]\b")
        self.assertRegex(report, r"\d+/\d+")
        self.assertRegex(report, r"docs/diagnostico/20\d\d-\d\d-\d\d\.md")


if __name__ == "__main__":
    unittest.main()
