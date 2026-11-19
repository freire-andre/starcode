"""SC-203: roteamento do worf e do mccoy fora do StarCode (R1 a R6)."""
from __future__ import annotations

import re
import subprocess
import unittest

from helpers import ROOT

ROUTING = ROOT / "evals" / "routing"

CASOS = {
    "neg-worf-generic-pr": ("Revise o PR #42 e me diga o que acha.", [("starcode:worf", 0, 0)]),
    "neg-mccoy-generic-test": ("Esse teste não passa: test_soma falha com AssertionError. O que pode ser?",
                               [("starcode:mccoy", 0, 0)]),
    "pos-config-model": ("Quero trocar o modelo do LaForge para o Kimi só neste projeto do StarCode.",
                         [("starcode:config", 1, None), ("starcode:setup", 0, 0)]),
}

DESCRICAO_PILOTO_MAIN = ("StarCode autopilot (Picard). Only the user invokes it. Runs a feature end to end "
    "with one interview up front: Troi grills the user (no round cap) and builds a decision mandate, the user approves "
    "the spec, and from then on the Picard answers every question of the flow in the user's place, based on the "
    "interview, recording each question and decision in .specs/features/<slug>/piloto.md. Push, PR, merge and deploy "
    "still need the user.")


def descricao(skill: str) -> str:
    text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^description: (.*)$", text, re.M)
    assert m
    return m.group(1)


def gatilhos(d: str) -> list[str]:
    return re.findall(r'"([^"]+)"', d)


def valor(txt: str):
    txt = txt.strip()
    if txt.startswith('"') and txt.endswith('"'):
        return txt[1:-1]
    if txt.startswith("[") and txt.endswith("]"):
        return [x.strip() for x in txt[1:-1].split(",")]
    return int(txt) if re.fullmatch(r"-?\d+", txt) else txt


def ler_case(path) -> dict:
    """Leitor mínimo do case.yaml: mapas de 2 níveis e a lista `graders` de mapas."""
    out: dict = {}
    secao = None
    item: dict = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        ind = len(raw) - len(raw.lstrip())
        linha = raw.strip()
        if ind == 0:
            k, _, v = linha.partition(":")
            if v.strip():
                out[k] = valor(v)
                secao = None
            else:
                secao = k
                out[k] = [] if k == "graders" else {}
        elif secao == "graders":
            if linha.startswith("- "):
                item = {}
                out[secao].append(item)
                linha = linha[2:]
            k, _, v = linha.partition(":")
            item[k.strip()] = valor(v)
        else:
            k, _, v = linha.partition(":")
            out[secao][k.strip()] = valor(v)
    return out


class RoteamentoWorfMccoyTests(unittest.TestCase):
    def test_descricao_worf(self):
        d = descricao("worf")
        g = gatilhos(d)
        self.assertEqual(g, ["Worf, revise o PR", "StarCode, faça o review do PR",
                             "Worf, faça o review de segurança do PR"], d)
        for x in g:
            self.assertTrue(any(t in x for t in ("StarCode", "Worf", "Picard")), x)
        self.assertEqual(d.rsplit("Not for", 1)[1],
                         " fixing code, writing features, reviewing prose or a generic pull request review outside StarCode.")

    def test_descricao_mccoy(self):
        d = descricao("mccoy")
        g = gatilhos(d)
        self.assertEqual(g, ["McCoy, diagnostique", "McCoy, esse teste do ticket não passa",
                             "StarCode, investigue o bug"], d)
        for x in g:
            self.assertTrue(any(t in x for t in ("StarCode", "McCoy", "LaForge", "ticket")), x)
        self.assertEqual(d.rsplit("Not for", 1)[1],
                         " writing new features or generic debugging outside StarCode.")

    def test_descricao_piloto(self):
        atual = (ROOT / "skills" / "piloto-automatico" / "SKILL.md").read_bytes()
        r = subprocess.run(["git", "show", "main:skills/piloto-automatico/SKILL.md"],
                           cwd=ROOT, capture_output=True)
        if r.returncode == 0:
            self.assertEqual(atual, r.stdout)
            ref = re.search(r"^description: (.*)$", r.stdout.decode("utf-8"), re.M).group(1)
        else:
            ref = DESCRICAO_PILOTO_MAIN
        self.assertEqual(descricao("piloto-automatico"), ref)
        self.assertNotIn(b"only when the user asks for the StarCode autopilot", atual)
        crew = (ROOT / "src" / "crew.yaml").read_text(encoding="utf-8")
        bloco = re.search(r"^  piloto-automatico:\n((?:    .*\n)+)", crew, re.M)
        self.assertIsNotNone(bloco)
        self.assertIn("    invocation: user\n", bloco.group(1))
        dist = (ROOT / "dist" / "claude" / "skills" / "piloto-automatico" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("\ndisable-model-invocation: true\n", dist.split("---")[1])

    def test_casos_novos(self):
        self.assertEqual(len(CASOS), 3)
        self.assertFalse((ROUTING / "pos-piloto-automatico").exists())
        for name, (prompt, graders) in CASOS.items():
            tag = "negative" if name.startswith("neg-") else "positive"
            c = ler_case(ROUTING / name / "case.yaml")
            self.assertTrue(c.pop("description"), name)
            esperados = []
            for skill, mn, mx in graders:
                g = {"type": "tool_used", "tool": "Skill", "input_match": skill, "min": mn}
                if mx is not None:
                    g["max"] = mx
                esperados.append(g)
            for g in c["graders"]:
                self.assertTrue(g.pop("name"), name)
            self.assertEqual(c, {
                "schema_version": "1.0",
                "name": f"routing-{name}",
                "tags": ["routing", tag],
                "execution": {"prompt": prompt, "max_turns": 3,
                              "allowed_tools": ["Skill", "Read", "Glob", "Grep"]},
                "runs": 1,
                "graders": esperados,
            }, name)

    def test_readme_e_contagem(self):
        readme = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        cases = [p for p in ROUTING.iterdir() if p.is_dir()]
        self.assertEqual(len(cases), 36)
        self.assertIn("36 frases", readme)
        for name in CASOS:
            self.assertIn(f"`{name}`", readme)
        self.assertNotIn("pos-piloto-automatico", readme)
        todas = geral = uma = 0
        for p in cases:
            if not p.name.startswith("neg-"):
                continue
            todas += 1
            ims = [g["input_match"] for g in ler_case(p / "case.yaml")["graders"]]
            if ims == ["starcode:"]:
                geral += 1
            else:
                self.assertEqual(len(ims), 1, p.name)
                self.assertRegex(ims[0], r"^starcode:[a-z-]+$", p.name)
                uma += 1
        self.assertEqual((todas, geral, uma), (15, 7, 8))
        self.assertIn(f"15 que não devem disparar skill do StarCode: {geral} impedem qualquer skill "
                      f"(`input_match: \"starcode:\"`) e {uma} impedem só uma skill (`starcode:<skill>`)", readme)
        self.assertNotIn("não devem disparar nenhuma skill", readme)
        self._f9_preservado()

    def _f9_preservado(self):
        src = (ROOT / "tests" / "test_evals_f9.py").read_text(encoding="utf-8")
        for trecho in ('SKILLS = ("worf", "guinan", "diagnostico")',
                       'self.assertGreaterEqual(len(pos), 2,', 'self.assertGreaterEqual(len(neg), 1,',
                       'self.assertIn("min: 1", text, name)', 'self.assertIn("max: 0", text, name)',
                       'self.assertEqual(neg, ["neg-worf-fix-code", "neg-worf-generic-pr"])',
                       'self.assertEqual(pos, ["pos-worf-review-pr", "pos-worf-security"])',
                       "self.assertEqual(total, 10)",
                       'self.assertIn("9 casos", readme)'):
            self.assertIn(trecho, src, trecho)
        for name in ("pos-worf-review-pr", "pos-worf-security", "pos-guinan-lessons", "pos-guinan-retro",
                     "pos-diagnostico-harness", "pos-diagnostico-level", "neg-worf-fix-code",
                     "neg-guinan-review-pr", "neg-diagnostico-setup", "neg-worf-generic-pr"):
            self.assertIn(name, src, name)
        import test_evals_f9
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_evals_f9.EvalsF9Tests)
        res = unittest.TestResult()
        suite.run(res)
        self.assertEqual((len(res.failures), len(res.errors)), (0, 0), res.failures + res.errors)

    def test_decisions_roteamento(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = next((p for p in text.split("\n### ")
                      if p.startswith("SC-") and "roteamento do worf e do mccoy" in p.splitlines()[0].lower()), None)
        self.assertIsNotNone(entry, "falta a entrada ### SC-<n> de roteamento-worf-mccoy")
        for field in ("**Problema**", "**Decisão**", "**Motivo**", "**Por que não é bug**"):
            self.assertEqual(entry.count(field), 1, field)
        decisao = entry.split("**Decisão**")[1].split("**Motivo**")[0]
        for frase in (
                'a `description` do `worf` perde "review do PR" e "revise esse PR" sozinhos',
                '("Worf, revise o PR", "StarCode, faça o review do PR", "Worf, faça o review de segurança do PR")',
                'termina com o "Not for" que inclui `a generic pull request review outside StarCode`',
                'a `description` do `mccoy` perde "esse teste não passa" e "investigue o bug" sozinhos',
                'termina com o "Not for" que inclui `generic debugging outside StarCode`',
                "`neg-worf-generic-pr` (`starcode:worf` com `max: 0`)",
                "`neg-mccoy-generic-test` (`starcode:mccoy` com `max: 0`)",
                "`pos-config-model` (`starcode:config` com `min: 1` e `starcode:setup` com `max: 0`)",
                "o `evals/README.md` passa a `36 frases`",
                "o `piloto-automatico` fica só do usuário: o `src/crew.yaml` o marca `invocation: user`, "
                "que o build grava como `disable-model-invocation: true`, então o modelo nunca chama a skill",
                "não há caso de eval para ele"):
            self.assertIn(frase, decisao, frase)
        nao_bug = entry.split("**Por que não é bug**")[1]
        for name in ("test_descricao_worf", "test_descricao_mccoy", "test_descricao_piloto", "test_casos_novos",
                     "test_readme_e_contagem", "test_decisions_roteamento"):
            self.assertIn(name, nao_bug, name)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]")[1].split("\n## [")[0]
        self.assertTrue(any("SC-203" in ln and "Worf" in ln for ln in unreleased.splitlines()))


if __name__ == "__main__":
    unittest.main()
