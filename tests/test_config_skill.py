"""Tests for setup_helpers suggest/clis and the config skill (models per crew member by what the user has)."""
from __future__ import annotations

import json
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


if __name__ == "__main__":
    unittest.main()
