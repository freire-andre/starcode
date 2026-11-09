"""R37: aceite real da Fase 8 (nova-missao, scaffold e gates) registrado em docs/aceite/fase-8.md."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

DOC = ROOT / "docs" / "aceite" / "fase-8.md"
SECTIONS = (
    "Nova missão: python-flask + postgresql",
    "Nova missão: tauri",
    "Scaffold e gates por perfil",
    "Série fora da testada",
    "Contêineres efêmeros",
)
SOURCES = r"\((?:pypi|npm|crates|dockerhub)[,)]"
DATE = r"\b20\d\d-\d\d-\d\d\b"


def _parts() -> dict[str, str]:
    text = DOC.read_text(encoding="utf-8")
    return {p.split("\n", 1)[0].strip(): p for p in re.split(r"^## ", text, flags=re.M)[1:]}


class AcceptanceDocF8Tests(unittest.TestCase):
    def test_doc_has_five_sections_and_versions_table(self):
        parts = _parts()
        for name in SECTIONS:
            self.assertIn(name, parts, f"falta a seção {name}")
            self.assertRegex(parts[name], r"\*\*Resultado\*\*: \S", f"{name}: sem **Resultado**")
        self.assertIn("Versões", parts)
        self.assertIn("| Item | Versão |", parts["Versões"])

    def test_fase8_acceptance_all_scenarios_approved(self):
        parts = _parts()
        for name in SECTIONS:
            self.assertIn(name, parts, f"falta a seção {name}")
            body = parts[name]
            self.assertRegex(body, r"\*\*Resultado\*\*: aprovado\b", f"{name}: sem **Resultado**: aprovado")
            self.assertNotIn("reprovado", body, f"{name}: reprovado")
            self.assertNotIn("pendente", body, f"{name}: campo pendente")
        for name in SECTIONS[:4]:
            body = parts[name]
            self.assertRegex(body, SOURCES, f"{name}: versões sem fonte")
            self.assertRegex(body, DATE, f"{name}: sem data")
            self.assertRegex(body, r"\bPASS\b", f"{name}: sem linhas PASS")
            self.assertNotRegex(body, r"^\s*(?:- )?FAIL\b", f"{name}: linha FAIL")
        for name in SECTIONS[:2]:
            self.assertIn(".specs/stack/", parts[name], f"{name}: sem as entradas do cache")
        self.assertIn("exit 5", parts["Série fora da testada"])
        self.assertIn("--pin-tested", parts["Série fora da testada"])
        self.assertIn("docker ps -a", parts["Contêineres efêmeros"])
        self.assertNotIn("pendente", parts["Versões"], "tabela de versões incompleta")


if __name__ == "__main__":
    unittest.main()
