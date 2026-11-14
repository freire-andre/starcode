"""Tests for setup_helpers suggest/clis and the config skill (models per crew member by what the user has)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest

from helpers import ROOT

import os

import setup_helpers as sh
import starcode_common as sc
import validate_config as vc

CLIS = ("claude", "codex", "antigravity", "opencode")
_OLD = {}


def setUpModule():  # a machine cache of models.dev must not change the suggestions under test
    _OLD["file"] = os.environ.get("STARCODE_MODELS_DEV_FILE")
    os.environ["STARCODE_MODELS_DEV_FILE"] = str(ROOT / "tests" / "fixtures" / "models-dev.json")


def tearDownModule():
    if _OLD["file"] is None:
        os.environ.pop("STARCODE_MODELS_DEV_FILE", None)
    else:
        os.environ["STARCODE_MODELS_DEV_FILE"] = _OLD["file"]


def _doc() -> dict:
    return sc.load_crew()


def _row(res: dict, member: str) -> dict:
    return next(r for r in res["rows"] if r["member"] == member)


class SuggestTests(unittest.TestCase):
    def test_only_claude_keeps_defaults_and_q_degraded(self):
        res = sh.suggest(_doc(), ["claude"])
        self.assertEqual(res["config"], {"schemaVersion": 1})
        self.assertEqual(_row(res, "q")["model"], "self-verified (degradado)")
        self.assertTrue(any("degradada" in n for n in res["notes"]))

    def test_without_claude_keeps_cost_tier_per_role(self):
        res = sh.suggest(_doc(), ["codex", "antigravity"])
        crew = res["config"]["crew"]
        # only $ models: repetitive roles match; the others get the nearest tier, with a note
        self.assertEqual(crew["uhura"], {"cli": "codex", "model": "gpt-6-luna"})
        self.assertEqual(crew["laforge"], {"cli": "codex", "model": "gpt-6-luna"})
        self.assertEqual(crew["picard"]["model"], "gpt-6-luna")
        self.assertTrue(any(n.startswith("Picard: pedia a faixa $$$") for n in res["notes"]))
        self.assertTrue(any(n.startswith("LaForge: pedia a faixa $$") for n in res["notes"]))
        # Q in another family than the LaForge (openai) -> google
        self.assertEqual(crew["q"]["cli"], "antigravity")

    def test_q_moves_off_codex_when_user_has_no_codex(self):
        res = sh.suggest(_doc(), ["claude", "antigravity"])
        self.assertEqual(set(res["config"]["crew"]), {"q"})
        self.assertEqual(res["config"]["crew"]["q"]["cli"], "antigravity")

    def test_q_uses_openrouter_model_of_other_family(self):
        res = sh.suggest(_doc(), ["claude", "opencode"], {"opencode": ["openrouter/openai/gpt-x:free"]})
        self.assertEqual(res["config"]["crew"]["q"], {"cli": "opencode", "model": "openrouter/openai/gpt-x:free"})
        self.assertEqual(_row(res, "q")["tier"], "grátis")

    def test_q_never_same_family_as_laforge(self):
        res = sh.suggest(_doc(), ["codex"])
        self.assertNotIn("q", res["config"]["crew"])
        self.assertEqual(_row(res, "q")["model"], "self-verified (degradado)")

    def test_default_q_kept_when_codex_available(self):
        res = sh.suggest(_doc(), ["claude", "codex"])
        self.assertEqual(res["config"], {"schemaVersion": 1})
        self.assertEqual(_row(res, "q")["cli"], "codex")

    def test_every_suggestion_validates(self):
        for have in (["claude"], ["codex"], ["antigravity"], ["codex", "antigravity"], ["claude", "opencode"],
                     list(CLIS)):
            res = sh.suggest(_doc(), have, {"opencode": ["openrouter/openai/gpt-x:free"]})
            self.assertEqual(vc.validate("user", res["config"]), [], have)

    def test_cli_rejects_unknown_cli_and_bad_model(self):
        script = str(ROOT / "scripts" / "setup_helpers.py")
        for args in (["--have", "xyz"], ["--have", "claude", "--model", "opencode"]):
            res = subprocess.run([sys.executable, script, "suggest", *args], capture_output=True, text=True,
                                 encoding="utf-8")
            self.assertEqual(res.returncode, 2, args)
            self.assertIn("ERRO", res.stdout)
        ok = subprocess.run([sys.executable, script, "suggest", "--have", "claude,antigravity", "--json"],
                            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["config"]["crew"]["q"]["cli"], "antigravity")

    def test_clis_found_uses_binaries(self):
        found = sh.clis_found(which=lambda b: "/bin/" + b if b in ("claude", "agy") else None)
        self.assertEqual(found, {"claude": True, "codex": False, "antigravity": True, "opencode": False})


class ConfigSkillTests(unittest.TestCase):
    def test_skill_flow_and_rules(self):
        for root in [ROOT] + [ROOT / "dist" / cli for cli in CLIS]:
            text = (root / "skills" / "config" / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\nname: config\n"), root)
            desc = text.split("---", 2)[1]
            for trigger in ("configurar os agentes", "não tenho ChatGPT/Codex", "starcode config"):
                self.assertIn(trigger, desc, root)
            for needle in ('setup_helpers.py" clis', 'setup_helpers.py" suggest', 'model_info.py" --cli',
                           "Never invent a model ID", "validate_config.py\" --kind user --write",
                           "validate_config.py\" --kind local --write", "keep every key the user did not change",
                           "Propose a ⛔ vetado model", "family differs from the LaForge"):
                self.assertIn(needle, text, f"{root}: {needle}")
            order = [text.index(h) for h in ("## 1. Current state", "## 2. What the user has",
                                              "## 3. Analyze each model", "## 4. Suggestion", "## 6. Write")]
            self.assertEqual(order, sorted(order), root)

    def test_setup_delegates_user_config_to_config_skill(self):
        text = (ROOT / "skills" / "setup" / "SKILL.md").read_text(encoding="utf-8")
        sec = text.split("## 4. User config", 1)[1].split("\n## ", 1)[0]
        self.assertIn("skills/config/SKILL.md", sec)
        self.assertIn("{{CMD:config}}", sec)

def _setup_section(text: str) -> str:
    return text.split("## 4. User config", 1)[1].split("\n## ", 1)[0]


def interval_diff(setup_text: str, config_text: str) -> tuple[int, int]:
    """(M, N): M is the end of `steps 1–M` cited by the setup, N the number of the `Write` title of config."""
    m = re.search(r"steps 1[–-](\d+)", _setup_section(setup_text))
    titles = re.findall(r"^## (\d+)\. Write$", config_text, re.M)
    if len(titles) != 1:
        raise ValueError(f"a skill config deve ter exatamente um título `## <N>. Write`, achei {len(titles)}")
    if m is None:
        raise ValueError("a seção `## 4. User config` do setup não cita `steps 1–<M>`")
    return int(m.group(1)), int(titles[0])


class SetupIntervaloTests(unittest.TestCase):
    def test_setup_cita_intervalo_ate_a_gravacao(self):
        text = (ROOT / "skills" / "setup" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("(steps 1–6)", _setup_section(text))

    def test_intervalo_do_setup_acompanha_titulo_write(self):
        setup = (ROOT / "skills" / "setup" / "SKILL.md").read_text(encoding="utf-8")
        config = (ROOT / "skills" / "config" / "SKILL.md").read_text(encoding="utf-8")
        m, n = interval_diff(setup, config)
        self.assertEqual(m, n)
        renumbered = config.replace("## 6. Write", "## 7. Write")
        m2, n2 = interval_diff(setup, renumbered)
        self.assertNotEqual(m2, n2)
        sem_write = config.replace("## 6. Write", "## 6. Gravar")
        with self.assertRaisesRegex(ValueError, "Write") as ctx:
            interval_diff(setup, sem_write)
        self.assertIn("achei 0", str(ctx.exception))
        duplicado = config + "\n## 7. Write\n"
        with self.assertRaisesRegex(ValueError, "Write") as ctx:
            interval_diff(setup, duplicado)
        self.assertIn("achei 2", str(ctx.exception))

    def test_dist_setup_cita_steps_1_6(self):
        for cli in CLIS:
            t = (ROOT / "dist" / cli / "skills" / "setup" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("(steps 1–6)", t, cli)
            self.assertNotIn("(steps 1–5)", t, cli)

    def test_decisions_setup_grava_config(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = text.split("### SC-172:", 1)[1].split("\n### ", 1)[0]
        for campo in ("- **Problema:**", "- **Decisão:**", "- **Motivo:**", "- **Por que não é bug:**"):
            self.assertIn(campo, entry)
        self.assertIn("steps 1–6", entry)
        self.assertIn("test_intervalo_do_setup_acompanha_titulo_write", entry.split("Por que não é bug", 1)[1])


if __name__ == "__main__":
    unittest.main()
