"""R37: aceite real da Fase 10 (Ponte no painel da Orca) registrado em docs/aceite/fase-10.md."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

DOC = ROOT / "docs" / "aceite" / "fase-10.md"
SECTIONS = (
    "Instalação",
    "Worktree A",
    "Worktree B",
    "Evento de agente",
    "Cena",
    "Atalhos",
)
RESULT = re.compile(r"^\*\*Resultado\*\*: (aprovado|reprovado)$", re.M)
SHOT = re.compile(r"`(docs/aceite/fase-10/[\w.-]+\.png)`")


def _parts() -> dict[str, str]:
    text = DOC.read_text(encoding="utf-8")
    return {p.split("\n", 1)[0].strip(): p for p in re.split(r"^## ", text, flags=re.M)[1:]}


class AcceptanceDocF10Tests(unittest.TestCase):
    def test_fase10_acceptance_sections(self):
        parts = _parts()
        for name in SECTIONS:
            self.assertIn(name, parts, f"falta a seção {name}")
            self.assertEqual(len(RESULT.findall(parts[name])), 1,
                             f"{name}: precisa de um **Resultado** aprovado ou reprovado")
            shots = SHOT.findall(parts[name])
            self.assertTrue(shots, f"{name}: sem caminho de captura")
            for rel in shots:
                png = ROOT / rel
                self.assertTrue(png.is_file(), f"{name}: captura ausente {rel}")
                self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n", f"{rel} não é PNG")
        self.assertIn("local.starcode-ponte", parts["Instalação"])
        self.assertIn("1.3.0", parts["Instalação"])


if __name__ == "__main__":
    unittest.main()
