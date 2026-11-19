"""SC-204: paridade declarada, nível de suporte de cada CLI (C1 a C3)."""
from __future__ import annotations

import unittest

from helpers import ROOT

L_PRINCIPAL = "- **Principal**: Claude Code. Todo recurso nasce e é aceito aqui."
L_SECUNDARIO = "- **Secundário completo**: Codex. Paridade de recursos, com aceite em sessão real."
L_ESFORCO = ("- **Melhor esforço**: Antigravity CLI e OpenCode. Funciona pelo mesmo pacote gerado, "
             "sem lógica própria nova, e problema só é corrigido quando bloqueia o fluxo.")

SIGNIFICA_ESFORCO = ("Funciona pelo mesmo pacote gerado, sem lógica própria nova; "
                     "problema só é corrigido quando bloqueia o fluxo.")
TABELA = [
    "| CLI | Nível | O que significa |",
    "| --- | --- | --- |",
    "| Claude Code | Principal | Todo recurso nasce e é aceito aqui. |",
    "| Codex | Secundário completo | Paridade de recursos, com aceite em sessão real. |",
    f"| Antigravity CLI | Melhor esforço | {SIGNIFICA_ESFORCO} |",
    f"| OpenCode | Melhor esforço | {SIGNIFICA_ESFORCO} |",
]
PENDENCIAS = [
    "- Aceite da Fase 8 (perfis) em sessão real no Codex (nota 14: hoje a prova é de build).",
    "- Aceite da Fase 9 (Worf, Guinan e diagnóstico) em sessão real no Codex (nota 15: hoje a prova é de build).",
]


class ParidadeDeclaradaTests(unittest.TestCase):
    def test_readme_niveis(self):
        linhas = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
        self.assertNotIn("com os 4 CLIs suportados", "\n".join(linhas))
        for linha in (L_PRINCIPAL, L_SECUNDARIO, L_ESFORCO):
            self.assertEqual(linhas.count(linha), 1, linha)
        self.assertLess(linhas.index(L_PRINCIPAL), linhas.index(L_SECUNDARIO))
        self.assertLess(linhas.index(L_SECUNDARIO), linhas.index(L_ESFORCO))

    def test_matriz_niveis(self):
        linhas = (ROOT / "docs" / "compatibilidade.md").read_text(encoding="utf-8").splitlines()
        self.assertEqual(linhas.count("## Nível de suporte"), 1)
        ini = linhas.index("## Nível de suporte")
        self.assertLess(ini, linhas.index("## Matriz"))
        secao = linhas[ini:linhas.index("## Matriz")]
        self.assertEqual([ln for ln in secao if ln.startswith("|")], TABELA)
        self.assertIn("Pendências do dono:", secao)
        pos = secao.index("Pendências do dono:")
        self.assertEqual([ln for ln in secao[pos:] if ln.startswith("- ")], PENDENCIAS)

    def test_decisions_paridade(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = next((p for p in text.split("\n### ") if p.startswith("SC-204:")), None)
        self.assertIsNotNone(entry, "falta a entrada ### SC-204:")
        for field in ("**Problema**", "**Decisão**", "**Motivo**", "**Por que não é bug**"):
            self.assertEqual(entry.count(field), 1, field)
        decisao = entry.split("**Decisão**")[1].split("**Motivo**")[0]
        for frase in (
                "a D-d do dono", "Claude Code **principal**", "Codex **secundário completo**",
                "Antigravity CLI e OpenCode **melhor esforço**",
                "principal = todo recurso nasce e é aceito aqui",
                "secundário completo = paridade de recursos, com aceite em sessão real",
                "melhor esforço = funciona pelo mesmo pacote gerado, sem lógica própria nova, "
                "e problema só é corrigido quando bloqueia o fluxo",
                "`## Nível de suporte` antes de `## Matriz`", "`Pendências do dono`",
                "Fases 8 e 9 em sessão real no Codex"):
            self.assertIn(frase, decisao, frase)
        nao_bug = entry.split("**Por que não é bug**")[1]
        for name in ("test_readme_niveis", "test_matriz_niveis", "test_decisions_paridade"):
            self.assertIn(name, nao_bug, name)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]")[1].split("\n## [")[0]
        self.assertTrue(any("SC-204" in ln and "nível" in ln.lower() or "SC-204" in ln and "níveis" in ln
                            for ln in unreleased.splitlines()))


if __name__ == "__main__":
    unittest.main()
