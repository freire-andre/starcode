"""C22-C25: Phase 5 acceptance scripts and acceptance doc skeleton (R19)."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

DIR = ROOT / "docs" / "aceite" / "roteiros-fase-5"
DOC = ROOT / "docs" / "aceite" / "fase-5.md"
SECTIONS = ("Instalação", "Bloqueio", "Fluxo normal", "Banner", "Evidência")
CLIS = {"codex": "Codex", "antigravity": "Antigravity", "opencode": "OpenCode"}
COMMON = ("Versão", "Bloqueio de push forçado", "Bloqueio de segredo", "Comandos normais", "Banner", "Resultado")
EXTRA = {
    "Codex": ("Trust (`/hooks`)",),
    "Antigravity": ("Contagem de hooks",),
    "OpenCode": ("Plugin na pasta global",),
}


def doc_section(name: str) -> str:
    text = DOC.read_text(encoding="utf-8")
    parts = re.split(r"^## ", text, flags=re.M)
    return next(p for p in parts if p.startswith(name))


def banner_part(text: str) -> str:
    return text.split("## Banner")[1].split("## Evidência")[0]


class AcceptanceScriptsF5Tests(unittest.TestCase):
    def test_acceptance_scripts_f5_have_sections(self):
        for cli in CLIS:
            text = (DIR / f"{cli}.md").read_text(encoding="utf-8")
            headings = re.findall(r"^## (.+?)\s*$", text, flags=re.M)
            for name in SECTIONS:
                self.assertIn(name, headings, f"{cli}: falta '## {name}'")
            self.assertIn("git push --force origin main", text)
            self.assertIn("python -m unittest discover -s tests -v", text)
            self.assertNotIn("API_KEY=q8Zr", text)
        for cli in ("codex", "antigravity"):
            text = (DIR / f"{cli}.md").read_text(encoding="utf-8")
            self.assertNotIn("n/a", banner_part(text))
        oc = (DIR / "opencode.md").read_text(encoding="utf-8")
        self.assertIn("n/a", banner_part(oc))
        codex = (DIR / "codex.md").read_text(encoding="utf-8")
        self.assertIn("/hooks", codex.split("## Bloqueio")[0])
        headings = re.findall(r"^## (.+?)\s*$", DOC.read_text(encoding="utf-8"), flags=re.M)
        for title in CLIS.values():
            self.assertIn(title, headings)

    def _check_section(self, title: str):
        sec = doc_section(title)
        self.assertIn("**Resultado**: pendente", sec)
        for label in COMMON + EXTRA[title]:
            self.assertIn(f"**{label}**", sec, f"{title}: falta '{label}'")

    def test_acceptance_doc_f5_codex_filled(self):
        self._check_section("Codex")

    def test_acceptance_doc_f5_antigravity_filled(self):
        self._check_section("Antigravity")

    def test_acceptance_doc_f5_opencode_filled(self):
        self._check_section("OpenCode")
        self.assertIn("n/a", doc_section("OpenCode").split("**Banner**")[1])

    def test_decisions_f5_registered(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        for n in ("F5-1", "F5-2", "F5-3"):
            self.assertRegex(text, rf"(?m)^### {n}:", n)
        self.assertIn("StarCode hook:", text)


if __name__ == "__main__":
    unittest.main()
