"""R22: roteiros e esqueleto do aceite da Fase 6."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

DOC = ROOT / "docs" / "aceite" / "fase-6.md"
SCRIPTS = ROOT / "docs" / "aceite" / "roteiros-fase-6"


class AcceptanceDocF6Tests(unittest.TestCase):
    def test_roteiros_exist_with_required_parts(self):
        for name in ("claude", "codex", "antigravity", "opencode"):
            f = SCRIPTS / f"{name}.md"
            self.assertTrue(f.is_file(), f"falta {f.name}")
            text = f.read_text(encoding="utf-8")
            for part in ("Remoção", "Instalação", "Banner", "Skills carregadas", "git push --force origin main",
                         "1.0.0", "feature/fase-6-release"):
                self.assertIn(part, text, f"{name}: sem '{part}'")
        self.assertIn("marketplace remove starcode", (SCRIPTS / "codex.md").read_text(encoding="utf-8"))
        mission = SCRIPTS / "dia-de-missao.md"
        self.assertTrue(mission.is_file())
        self.assertIn("modo Git 2", mission.read_text(encoding="utf-8"))

    def test_skeleton_has_five_sections_pending(self):
        text = DOC.read_text(encoding="utf-8")
        parts = {p.split("\n", 1)[0].strip(): p for p in re.split(r"^## ", text, flags=re.M)[1:]}
        for name in ("Claude", "Codex", "Antigravity", "OpenCode", "Dia de missão"):
            self.assertIn(name, parts, f"falta a seção {name}")
            self.assertIn("**Resultado**: pendente", parts[name], f"{name}: Resultado pendente ausente")
        self.assertIn("Versões", parts)
        self.assertIn("| Item | Versão |", parts["Versões"])


if __name__ == "__main__":
    unittest.main()
