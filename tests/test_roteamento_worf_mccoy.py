"""SC-203: roteamento do worf e do mccoy fora do StarCode (R1 a R5)."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

ROUTING = ROOT / "evals" / "routing"

CASOS = {
    "neg-worf-generic-pr": ("Revise o PR #42 e me diga o que acha.", [("starcode:worf", 0, 0)]),
    "neg-mccoy-generic-test": ("Esse teste não passa: test_soma falha com AssertionError. O que pode ser?",
                               [("starcode:mccoy", 0, 0)]),
    "pos-config-model": ("Quero trocar o modelo do LaForge para o Kimi só neste projeto do StarCode.",
                         [("starcode:config", 1, None), ("starcode:setup", 0, 0)]),
    "pos-piloto-automatico": ("StarCode, toque a feature de exportar CSV no piloto automático: me entreviste uma vez e decida o resto por mim.",
                              [("starcode:piloto-automatico", 1, None), ("starcode:engajar", 0, 0)]),
}


def descricao(skill: str) -> str:
    text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^description: (.*)$", text, re.M)
    assert m
    return m.group(1)


class RoteamentoWorfMccoyTests(unittest.TestCase):
    def test_descricao_worf(self):
        d = descricao("worf")
        for gatilho in ('"review do PR"', '"revise esse PR"'):
            self.assertNotIn(gatilho, d)
        for termo in ("StarCode", "Worf", "Picard"):
            self.assertIn(termo, d)
        self.assertTrue(d.endswith("Not for fixing code, writing features, reviewing prose or a generic pull request review outside StarCode."), d)
        self.assertIn("a generic pull request review outside StarCode", d.split("Not for")[-1])

    def test_descricao_mccoy(self):
        d = descricao("mccoy")
        for gatilho in ('"esse teste não passa"', '"investigue o bug"'):
            self.assertNotIn(gatilho, d)
        for termo in ("StarCode", "McCoy", "LaForge", "ticket"):
            self.assertIn(termo, d)
        self.assertTrue(d.endswith("Not for writing new features or generic debugging outside StarCode."), d)
        self.assertIn("generic debugging outside StarCode", d.split("Not for")[-1])

    def test_casos_novos(self):
        for name, (prompt, graders) in CASOS.items():
            text = (ROUTING / name / "case.yaml").read_text(encoding="utf-8")
            lines = text.splitlines()
            for linha in ('schema_version: "1.0"', f"name: routing-{name}", "  max_turns: 3",
                          "  allowed_tools: [Skill, Read, Glob, Grep]", "runs: 1",
                          f'  prompt: "{prompt}"'):
                self.assertIn(linha, lines, (name, linha))
            self.assertTrue(any(l.startswith("description: ") for l in lines), name)
            tag = "negative" if name.startswith("neg-") else "positive"
            self.assertIn(f"tags: [routing, {tag}]", lines, name)
            self.assertEqual(text.count("  - type: tool_used"), len(graders), name)
            for skill, mn, mx in graders:
                i = lines.index(f'    input_match: "{skill}"')
                self.assertEqual(lines[i - 1], "    tool: Skill", name)
                self.assertEqual(lines[i + 1], f"    min: {mn}", (name, skill))
                if mx is None:
                    self.assertTrue(i + 2 >= len(lines) or not lines[i + 2].startswith("    max:"), (name, skill))
                else:
                    self.assertEqual(lines[i + 2], f"    max: {mx}", (name, skill))

    def test_readme_e_contagem(self):
        readme = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        cases = [p for p in ROUTING.iterdir() if p.is_dir()]
        self.assertEqual(len(cases), 37)
        self.assertIn("37 frases", readme)
        for name in CASOS:
            self.assertIn(f"`{name}`", readme)

    def test_decisions_roteamento(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = next((p for p in text.split("\n### ")
                      if p.startswith("SC-") and "roteamento do worf e do mccoy" in p.splitlines()[0].lower()), None)
        self.assertIsNotNone(entry, "falta a entrada ### SC-<n> de roteamento-worf-mccoy")
        for field in ("**Problema**", "**Decisão**", "**Motivo**", "**Por que não é bug**"):
            self.assertEqual(entry.count(field), 1, field)
        decisao = entry.split("**Decisão**")[1].split("**Motivo**")[0]
        for term in ("review do PR", "revise esse PR", "esse teste não passa", "investigue o bug",
                     "a generic pull request review outside StarCode", "generic debugging outside StarCode",
                     "neg-worf-generic-pr", "neg-mccoy-generic-test", "pos-config-model", "pos-piloto-automatico",
                     "37 frases"):
            self.assertIn(term, decisao, term)
        nao_bug = entry.split("**Por que não é bug**")[1]
        for name in ("test_descricao_worf", "test_descricao_mccoy", "test_casos_novos",
                     "test_readme_e_contagem", "test_decisions_roteamento"):
            self.assertIn(name, nao_bug, name)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]")[1].split("\n## [")[0]
        self.assertTrue(any("SC-203" in ln and "Worf" in ln for ln in unreleased.splitlines()))


if __name__ == "__main__":
    unittest.main()
