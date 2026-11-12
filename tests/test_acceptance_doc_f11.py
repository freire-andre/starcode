"""R35 a R38: aceite real da Fase 11 (telas) registrado em docs/aceite/fase-11.md."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

DOC = ROOT / "docs" / "aceite" / "fase-11.md"
SECTIONS = ("App", "Mockup", "Rodada 1", "Rodada 2", "Gate")
RESULT = re.compile(r"^\*\*Resultado\*\*: (aprovado|reprovado)$", re.M)
FILE = re.compile(r"`(docs/aceite/fase-11/[\w.-]+)`")


def _parts() -> dict[str, str]:
    text = DOC.read_text(encoding="utf-8")
    return {p.split("\n", 1)[0].strip(): p for p in re.split(r"^## ", text, flags=re.M)[1:]}


class AcceptanceDocF11Tests(unittest.TestCase):
    def test_fase11_acceptance_sections(self):
        text = DOC.read_text(encoding="utf-8")
        parts = _parts()
        head = text.split("\n## ", 1)[0]
        self.assertEqual(len(RESULT.findall(head)), 1, "falta o **Resultado** geral no topo")
        for name in SECTIONS:
            self.assertIn(name, parts, f"falta a seção {name}")
            self.assertEqual(len(RESULT.findall(parts[name])), 1,
                             f"{name}: precisa de um **Resultado** aprovado ou reprovado")
            for rel in FILE.findall(parts[name]):
                path = ROOT / rel
                self.assertTrue(path.is_file(), f"{name}: arquivo ausente {rel}")
                if rel.endswith(".png"):
                    self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n", f"{rel} não é PNG")
        overall = RESULT.search(head).group(1)
        if overall == "aprovado":
            for name in SECTIONS:
                self.assertIn("**Resultado**: aprovado", parts[name], f"{name} não aprovado")
        # R35: app Tauri novo, issues PROJ e mockup
        self.assertIn(r"F:\Projetos\starcode-telas", parts["App"])
        self.assertIn("PROJ-34", parts["App"])
        self.assertIn("800x600", parts["Mockup"])
        self.assertTrue(FILE.search(parts["Mockup"]), "Mockup: sem cópia do mockup")
        # R36: screens.md todo em matches, fotos running, gate com 0
        self.assertIn("matches", parts["Rodada 2"])
        self.assertIn("running", parts["Rodada 2"])
        self.assertIn("exit 0", parts["Gate"])
        self.assertIn("validate_verification", parts["Gate"])
        # R37: divergência plantada em copy na rodada 1, fechada na 2
        self.assertIn("diverges", parts["Rodada 1"])
        self.assertIn("copy", parts["Rodada 1"])
        self.assertIn("same", parts["Rodada 2"])
        for rel in ("mockup-saudacao.png", "rodada1-saudacao.running.png",
                    "rodada2-saudacao.running.png", "screens-rodada1.md", "screens-rodada2.md"):
            self.assertTrue((ROOT / "docs" / "aceite" / "fase-11" / rel).is_file(), rel)


if __name__ == "__main__":
    unittest.main()
