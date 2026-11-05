"""C26: each Phase 4 acceptance script has the five required sections (R26)."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

DIR = ROOT / "docs" / "aceite" / "roteiros-fase-4"
SECTIONS = ("Missão", "Respostas", "Aprovações", "Tripulação", "Relatório esperado")
EXPECT = {
    "codex": ("add --vence AAAA-MM-DD", "gpt-6-luna", "gemini-3.8-flash-high"),
    "antigravity": ("buscar TERMO", "gemini-3.8-flash-high", "Q no codex"),
    "opencode": ("exportar-md ARQ", "openrouter/deepseek/deepseek-v4-pro", "Q no codex"),
}


class AcceptanceScriptsF4Tests(unittest.TestCase):
    def test_each_script_has_five_sections(self):
        for cli in EXPECT:
            text = (DIR / f"{cli}.md").read_text(encoding="utf-8")
            headings = re.findall(r"^## (.+?)\s*$", text, flags=re.M)
            for name in SECTIONS:
                self.assertIn(name, headings, f"{cli}: falta '## {name}'")

    def test_mission_crew_and_approvals(self):
        for cli, needles in EXPECT.items():
            text = (DIR / f"{cli}.md").read_text(encoding="utf-8")
            for n in needles:
                self.assertIn(n, text, f"{cli}: falta '{n}'")
            sec = re.split(r"^## ", text, flags=re.M)
            appr = next(s for s in sec if s.startswith("Aprovações"))
            self.assertIn("roteiro pré-aprovado em 2026-11-05", appr)

    def test_sandbox_team_is_proj(self):
        for cli in EXPECT:
            text = (DIR / f"{cli}.md").read_text(encoding="utf-8")
            self.assertIn("PROJ", text)


if __name__ == "__main__":
    unittest.main()
