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
    "Reaceite",
)
RESULT = re.compile(r"^\*\*Resultado\*\*: (aprovado com limitações|aprovado|reprovado)$", re.M)
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
        self.assertIn("aprovado com limitações", parts["Reaceite"])
        self.assertIn("local.starcode-ponte", parts["Instalação"])
        self.assertIn("1.3.0", parts["Instalação"])

    def test_fase10_limitacoes_registradas(self):
        """R49: as duas limitações da Orca ficam em DECISIONS, compatibilidade e aceite."""
        docs = {
            "DECISIONS.md": (ROOT / "DECISIONS.md").read_text(encoding="utf-8"),
            "docs/compatibilidade.md": (ROOT / "docs" / "compatibilidade.md").read_text(encoding="utf-8"),
            "docs/aceite/fase-10.md": DOC.read_text(encoding="utf-8"),
        }
        for nome, texto in docs.items():
            self.assertIn("segundo plano", texto, f"{nome}: falta o Picard em segundo plano")
            self.assertIn("loader:1575", texto, f"{nome}: falta o `orca` falhando no worker")


if __name__ == "__main__":
    unittest.main()

