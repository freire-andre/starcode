"""R30: roteiro e esqueleto do aceite da Fase 7 (a prova C30 nasce na T8)."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

DOC = ROOT / "docs" / "aceite" / "fase-7.md"
SCRIPT = ROOT / "docs" / "aceite" / "roteiros-fase-7" / "frota.md"


class AcceptanceDocF7Tests(unittest.TestCase):
    def test_roteiro_exists_with_required_parts(self):
        self.assertTrue(SCRIPT.is_file(), "falta frota.md")
        text = SCRIPT.read_text(encoding="utf-8")
        for part in ("starcode-sandbox", "PROJ", "modo Git 2 ou 3", "Runs alone", "roda sozinho",
                     "fleet.timeoutMinutes", "check_scope", "claude:claude-sonnet-5-5", "codex:gpt-6-luna",
                     "opencode/mimo-v2.6-flash-free", "opencode/deepseek-v4.1-flash-free",
                     "opencode/glm-5.3-flash-free", "aninhamento", "trust", "time SC",
                     "input_accepted", "worker_done,question", "UTF-8",
                     "dispatch id", "modelo pedido", "modelo efetivo", "hash"):
            self.assertIn(part, text, f"roteiro sem '{part}'")
        for cenario in ("(a)", "(b)", "(c)", "(d)"):
            self.assertIn(cenario, text, f"roteiro sem o cenário {cenario}")

    def test_skeleton_has_four_sections(self):
        text = DOC.read_text(encoding="utf-8")
        parts = {p.split("\n", 1)[0].strip(): p for p in re.split(r"^## ", text, flags=re.M)[1:]}
        for name in ("Lote paralelo", "Lockfile", "Timeout", "Falha isolada"):
            self.assertIn(name, parts, f"falta a seção {name}")
            self.assertRegex(parts[name], r"\*\*Resultado\*\*: \S", f"{name}: sem **Resultado**")
        self.assertIn("Versões", parts)
        self.assertIn("| Item | Versão |", parts["Versões"])


if __name__ == "__main__":
    unittest.main()
