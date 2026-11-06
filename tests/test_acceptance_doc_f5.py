"""C23: a seção Codex de docs/aceite/fase-5.md está preenchida com a evidência da sessão real (R19)."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

DOC = ROOT / "docs" / "aceite" / "fase-5.md"


def doc_section(name: str) -> str:
    parts = re.split(r"^## ", DOC.read_text(encoding="utf-8"), flags=re.M)
    return next(p for p in parts if p.startswith(name))


def field(sec: str, label: str) -> str:
    m = re.search(rf"^- \*\*{re.escape(label)}\*\*: (.+(?:\n  .+)*)", sec, flags=re.M)
    assert m, f"falta o campo '{label}'"
    return m.group(1)


class AcceptanceDocF5Tests(unittest.TestCase):
    def test_acceptance_doc_f5_codex_filled(self):
        sec = doc_section("Codex")
        result = re.search(r"\*\*Resultado\*\*: (.+)", sec)
        self.assertIsNotNone(result, "Codex: sem **Resultado**")
        self.assertRegex(result.group(1), r"^(aprovado|reprovado \(.+\))", "Codex: Resultado inválido")
        self.assertRegex(field(sec, "Versão"), r"\d+\.\d+\.\d+", "Codex: sem versão do CLI")
        self.assertIn("/hooks", field(sec, "Trust (`/hooks`)"))
        push = field(sec, "Bloqueio de push forçado")
        self.assertIn("git push --force origin main", push)
        self.assertIn("StarCode bloqueou", push)
        secret = field(sec, "Bloqueio de segredo")
        self.assertIn("possível segredo", secret)
        self.assertNotIn("q8Zr2Lm9Xv4Tn7Wp1Ks6Yd3", sec, "o valor de teste do segredo não vai no doc")
        normal = field(sec, "Comandos normais")
        for cmd in ("git status", "git add .", "git commit", "git switch -c", "git merge --no-ff",
                    "orca linear issue", "run_gates.py", "unittest discover"):
            self.assertIn(cmd, normal, f"Comandos normais sem '{cmd}'")
        self.assertIn("CLI: codex", field(sec, "Banner"))
        for label in ("Versão", "Trust (`/hooks`)", "Bloqueio de push forçado", "Bloqueio de segredo",
                      "Comandos normais", "Banner"):
            self.assertNotIn("pendente", field(sec, label).lower(), f"Codex: '{label}' pendente")
        self.assertNotIn("pendente", result.group(1).lower())


if __name__ == "__main__":
    unittest.main()
