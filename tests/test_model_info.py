"""Tests for model_info.py (models.dev catalog), its use by dispatch.family and suggest, and the local config."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from helpers import ROOT, TempRepoCase

import banner
import dispatch
import model_info as mi
import setup_helpers as sh
import starcode_common as sc
import validate_config as vc

FIXTURE = ROOT / "tests" / "fixtures" / "models-dev.json"


class CatalogCase(TempRepoCase):
    """Isolated STARCODE_HOME (TempRepoCase) plus the fixture catalog."""

    def setUp(self):
        super().setUp()
        self._old_file = os.environ.get("STARCODE_MODELS_DEV_FILE")
        os.environ["STARCODE_MODELS_DEV_FILE"] = str(FIXTURE)
        self.catalog = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def tearDown(self):
        if self._old_file is None:
            os.environ.pop("STARCODE_MODELS_DEV_FILE", None)
        else:
            os.environ["STARCODE_MODELS_DEV_FILE"] = self._old_file
        super().tearDown()


class ModelInfoTests(CatalogCase):
    def test_tier_by_output_price(self):
        cases = {"anthropic/claude-opus-5-5": "$$$", "opencode/muse-spark-1.2": "$$", "moonshotai/kimi-k3": "$$$",
                 "claude-haiku-5-5": "$", "openrouter/nvidia/nemo-x:free": "grátis"}
        for mid, want in cases.items():
            self.assertEqual(mi.info(self.catalog, mid)["tier"], want, mid)

    def test_family_from_canonical_or_openrouter_vendor(self):
        self.assertEqual(mi.info(self.catalog, "opencode/muse-spark-1.2")["family"], "meta")
        self.assertEqual(mi.info(self.catalog, "zai/glm-5.3")["family"], "zhipu")
        self.assertEqual(mi.info(self.catalog, "openrouter/moonshotai/kimi-k3.1-pro")["family"], "moonshotai")
        self.assertEqual(mi.info(self.catalog, "gpt-6-luna", "codex")["family"], "openai")

    def test_fit_vetoes_and_warnings(self):
        no_tools = mi.info(self.catalog, "zai/glm-notools")["fit"]
        self.assertTrue(all(v.startswith("vetado") for v in no_tools.values()))
        tiny = mi.info(self.catalog, "zai/glm-tiny")["fit"]
        self.assertIn("contexto de 128k", tiny["pesado"])
        self.assertIn("sem modo de raciocínio", tiny["q"])
        self.assertIn("modelo barato", tiny["pesado"])
        self.assertEqual(tiny["repetitivo"], "ok")
        self.assertIn("caro para tarefa repetitiva", mi.info(self.catalog, "moonshotai/kimi-k3")["fit"]["repetitivo"])
        self.assertEqual(set(mi.info(self.catalog, "opencode/muse-spark-1.2")["fit"].values()), {"ok"})

    def test_cli_exit_codes(self):
        script = str(ROOT / "scripts" / "model_info.py")
        env = {**os.environ}
        ok = subprocess.run([sys.executable, script, "zai/glm-5.3"], capture_output=True, text=True,
                            encoding="utf-8", env=env)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("Família: zhipu · faixa $$", ok.stdout)
        missing = subprocess.run([sys.executable, script, "zai/glm-5.3", "nao/existe"], capture_output=True,
                                 text=True, encoding="utf-8", env=env)
        self.assertEqual(missing.returncode, 1)
        self.assertIn("não está no catálogo", missing.stdout)
        env["STARCODE_MODELS_DEV_FILE"] = str(self.tmp / "sem-catalogo.json")
        none = subprocess.run([sys.executable, script, "zai/glm-5.3"], capture_output=True, text=True,
                              encoding="utf-8", env=env)
        self.assertEqual(none.returncode, 3)

    def test_cache_fresh_stale_and_no_fetch(self):
        os.environ.pop("STARCODE_MODELS_DEV_FILE")
        self.assertIsNone(mi.load_catalog(fetch=False))
        cache = mi.cache_path()
        cache.parent.mkdir(parents=True)
        cache.write_text(json.dumps(self.catalog), encoding="utf-8")
        with mock.patch.object(mi, "download", side_effect=AssertionError("não deve baixar")):
            self.assertIn("zai", mi.load_catalog())
        old = time.time() - mi.MAX_AGE_S - 60
        os.utime(cache, (old, old))
        with mock.patch.object(mi, "download", return_value=None) as dl:
            self.assertIn("zai", mi.load_catalog())  # offline: the stale cache still serves
            dl.assert_called_once()
        self.assertEqual(mi.cached_family("zai/glm-5.3"), "zhipu")


class DispatchFamilyTests(CatalogCase):
    def test_opencode_provider_models_get_a_family(self):
        self.assertEqual(dispatch.family("opencode:zai/glm-5.3"), "zhipu")
        self.assertEqual(dispatch.family("opencode:opencode/muse-spark-1.2"), "meta")
        self.assertEqual(dispatch.family("opencode:openrouter/moonshotai/kimi-k3.1-pro"), "moonshotai")
        self.assertEqual(dispatch.family("openrouter/acme/model-x"), "unknown")
        self.assertEqual(dispatch.compare("opencode:zai/glm-5.3", "claude"), "different")

    def test_q_cli_accepts_opencode_model_of_other_family(self):
        pick = dispatch.q_cli("opencode:opencode/muse-spark-1.2", "opencode:zai/glm-5.3", which=lambda b: "/x/" + b)
        self.assertEqual(pick, "opencode:zai/glm-5.3")

    def test_without_catalog_stays_unknown(self):
        os.environ["STARCODE_MODELS_DEV_FILE"] = str(self.tmp / "nada.json")
        self.assertEqual(dispatch.family("opencode:zai/glm-5.3"), "unknown")


RESELLERS = (("github-copilot", "claude-sonnet-5-5"), ("azure", "claude-sonnet-5-5"),
             ("google-vertex-anthropic", "claude-sonnet-5-5"), ("opencode", "claude-sonnet-5-5"),
             ("amazon-bedrock", "anthropic.claude-sonnet-5-5"))


def _entry(mid: str) -> dict:
    return {"id": mid, "name": mid, "tool_call": True, "reasoning": True, "limit": {"context": 200000},
            "cost": {"input": 3, "output": 15}}


class ResellerFamilyTests(CatalogCase):
    def reseller_catalog(self) -> Path:
        cat = {p: {"models": {m: _entry(m)}} for p, m in RESELLERS}
        path = self.tmp / "resellers.json"
        path.write_text(json.dumps(cat), encoding="utf-8")
        os.environ["STARCODE_MODELS_DEV_FILE"] = str(path)
        return path

    def test_revendedor_claude_vira_anthropic(self):
        for p in ("github-copilot", "azure", "google-vertex-anthropic", "opencode"):
            self.assertEqual(mi.vendor(p, {}, "claude-sonnet-5-5"), "anthropic", p)
            self.assertEqual(mi.vendor(p, {}, f"{p}/claude-sonnet-5-5"), "anthropic", p)

    def test_bedrock_prefixo_do_fornecedor(self):
        self.assertEqual(mi.vendor("amazon-bedrock", {}, "anthropic.claude-sonnet-5-5"), "anthropic")
        self.assertEqual(mi.vendor("amazon-bedrock", {}, "amazon-bedrock/anthropic.claude-sonnet-5-5"), "anthropic")

    def test_revendedor_modelo_desconhecido_vira_unknown(self):
        for p in ("github-copilot", "azure", "opencode"):
            self.assertEqual(mi.vendor(p, {}, "acme-x"), "unknown", p)

    def test_fornecedor_e_id_canonico_mantem_familia(self):
        self.assertEqual(mi.info(self.catalog, "zai/glm-notools")["family"], "zhipu")
        self.assertEqual(mi.info(self.catalog, "opencode/muse-spark-1.2")["family"], "meta")
        self.assertEqual(mi.info(self.catalog, "anthropic/claude-opus-5-5")["family"], "anthropic")

    def test_compare_revendedor_claude_e_same(self):
        self.reseller_catalog()
        for p, m in RESELLERS:
            self.assertEqual(dispatch.compare(f"opencode:{p}/{m}", "claude:claude-sonnet-5-5"), "same", p)

    def test_q_cli_recusa_revendedor_claude(self):
        self.reseller_catalog()
        pick = dispatch.q_cli("claude:claude-sonnet-5-5", "opencode:github-copilot/claude-sonnet-5-5",
                              which=lambda b: "/x/" + b)
        self.assertEqual(pick, "codex")

    def test_prefixos_de_modelo_por_revendedor(self):
        table = {"gpt-6-luna": "openai", "o1-pro": "openai", "o3-mini": "openai", "o4-mini": "openai", "codex-mini": "openai", "gemini-3": "google",
                 "deepseek-v4": "deepseek", "glm-5.3": "zhipu", "kimi-k3": "moonshotai", "grok-5": "xai",
                 "mistral-large": "mistral", "codestral-2": "mistral", "devstral-2": "mistral",
                 "llama-5": "meta", "claude-sonnet-5-5": "anthropic"}
        for model, want in table.items():
            self.assertEqual(mi.vendor("azure", {}, model), want, model)
            card = mi.info({"azure": {"models": {model: _entry(model)}}}, f"azure/{model}")
            self.assertEqual(card["family"], want, model)

    def test_sem_catalogo_revendedor_unknown(self):
        os.environ["STARCODE_MODELS_DEV_FILE"] = str(self.tmp / "nada.json")
        self.assertEqual(dispatch.family("opencode:github-copilot/claude-sonnet-5-5"), "unknown")

    def test_decisions_q_familia_revendedor(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = text.partition("### SC-171:")[2].partition("\n### ")[0]
        self.assertTrue(entry, "falta a entrada ### SC-171:")
        for word in ("github-copilot", "amazon-bedrock", "unknown", "Por que não é bug", "**Problema:**",
                     "**Decisão:**", "**Motivo:**"):
            self.assertIn(word, entry)
        decision = entry.partition("**Decisão:**")[2].partition("\n- **Motivo:**")[0]
        self.assertTrue(decision, "falta a seção **Decisão:**")
        resellers = ("github-copilot", "azure", "amazon-bedrock", "google-vertex-anthropic", "opencode")
        suppliers = ("anthropic", "openai", "google", "deepseek", "zai", "zhipuai", "moonshotai", "mistral",
                     "xai", "meta")
        prefixes = ("claude", "gpt", "o1", "o3", "o4", "codex", "gemini", "deepseek", "glm", "kimi", "grok",
                    "mistral", "codestral", "devstral", "llama")
        for word in resellers + suppliers + prefixes:
            self.assertIn(f"`{word}`", decision, word)
        for word in ("canonical_model_id", "anthropic.", "unknown", "same", "codex"):
            self.assertIn(word, decision, word)
        why = entry.partition("**Por que não é bug:**")[2]
        for name in ("test_revendedor_claude_vira_anthropic", "test_bedrock_prefixo_do_fornecedor",
                     "test_revendedor_modelo_desconhecido_vira_unknown",
                     "test_fornecedor_e_id_canonico_mantem_familia", "test_compare_revendedor_claude_e_same",
                     "test_q_cli_recusa_revendedor_claude", "test_prefixos_de_modelo_por_revendedor",
                     "test_sem_catalogo_revendedor_unknown"):
            self.assertIn(name, why)


class SuggestCatalogTests(CatalogCase):
    def test_tier_from_catalog_places_models_by_role(self):
        res = sh.suggest(sc.load_crew(), ["opencode"], {"opencode": [("opencode/muse-spark-1.2", None),
                                                                     ("moonshotai/kimi-k3", None),
                                                                     ("zai/glm-tiny", None)]})
        crew = res["config"]["crew"]
        self.assertEqual(crew["picard"]["model"], "moonshotai/kimi-k3")
        self.assertEqual(crew["laforge"]["model"], "opencode/muse-spark-1.2")
        self.assertEqual(crew["guinan"]["model"], "zai/glm-tiny")
        self.assertNotEqual(dispatch.family("opencode:" + crew["q"]["model"]), "meta")

    def test_manual_tier_and_parse(self):
        self.assertEqual(sh.parse_model_arg("opencode=x/y@$$"), ("opencode", "x/y", "$$"))
        self.assertEqual(sh.parse_model_arg("opencode=x/y:free@gratis"), ("opencode", "x/y:free", "grátis"))
        self.assertEqual(sh.parse_model_arg("opencode=x/y"), ("opencode", "x/y", None))
        for bad in ("opencode=x@$$$$", "foo=x", "opencode=", "opencode"):
            self.assertIsNone(sh.parse_model_arg(bad), bad)
        res = sh.suggest(sc.load_crew(), ["opencode"], {"opencode": [("acme/fora-do-catalogo", "$$$")]})
        self.assertEqual(next(r for r in res["rows"] if r["member"] == "picard")["tier"], "$$$")

    def test_model_for_cli_not_owned_is_noted(self):
        res = sh.suggest(sc.load_crew(), ["claude"], {"opencode": [("zai/glm-5.3", None)]})
        self.assertTrue(any("ignorado: opencode" in n for n in res["notes"]))


class LocalConfigTests(TempRepoCase):
    def test_local_schema_only_crew(self):
        self.assertEqual(vc.validate("local", {"schemaVersion": 1, "crew": {"q": {"cli": "opencode",
                                                                                 "model": "zai/glm-5.3"}}}), [])
        errs = vc.validate("local", {"schemaVersion": 1, "fleet": {"maxBatch": 2}})
        self.assertTrue(any("fleet: chave desconhecida" in e for e in errs), errs)

    def test_write_local_adds_gitignore_once(self):
        folder = self.repo / ".starcode"
        folder.mkdir()
        (folder / ".gitignore").write_text("live/", encoding="utf-8")  # no trailing newline
        dest = folder / "config.local.json"
        data = {"schemaVersion": 1, "crew": {"laforge": {"cli": "opencode", "model": "zai/glm-5.3"}}}
        self.assertEqual(vc.write_validated("local", data, dest), [])
        self.assertEqual(vc.write_validated("local", data, dest), [])
        self.assertEqual((folder / ".gitignore").read_text(encoding="utf-8"), "live/\nconfig.local.json\n")
        out = subprocess.run(["git", "check-ignore", "-q", str(dest)], cwd=self.repo)
        self.assertEqual(out.returncode, 0)

    def test_precedence_local_over_user_over_default(self):
        doc = sc.load_crew()
        user = {"crew": {"laforge": {"cli": "codex", "model": "gpt-6-luna"}, "uhura": {"cli": "codex",
                                                                                      "model": "gpt-6-luna"}}}
        local = {"crew": {"laforge": {"cli": "opencode", "model": "zai/glm-5.3"}}}
        crew = sc.effective_crew(doc, user, local)
        self.assertEqual((crew["laforge"]["cli"], crew["laforge"]["model"], crew["laforge"]["source"]),
                         ("opencode", "zai/glm-5.3", "local"))
        self.assertEqual(crew["uhura"]["source"], "user")
        self.assertEqual((crew["picard"]["source"], crew["picard"]["overridden"]), ("default", False))

    def test_banner_and_crew_table_show_local(self):
        self.write_repo_config()
        local = self.repo / ".starcode" / "config.local.json"
        local.write_text(json.dumps({"schemaVersion": 1, "crew": {"laforge": {"cli": "opencode",
                                                                               "model": "zai/glm-5.3"}}}),
                         encoding="utf-8")
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]):
            text = banner.build_banner(str(self.repo), False)[0]
        self.assertIn("Config local do repositório: ✅ válido", text)
        self.assertIn("🔧 LaForge: opencode · zai/glm-5.3 (config local do repositório)", text)
        local.write_text('{"schemaVersion": 1, "crew": {"laforge": {}}}', encoding="utf-8")
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]):
            text = banner.build_banner(str(self.repo), False)[0]
        self.assertIn("Config local do repositório: ❌ INVÁLIDO", text)
        self.assertNotIn("(config local do repositório)", text)
        local.write_text(json.dumps({"schemaVersion": 1, "crew": {"q": {"cli": "opencode", "model": "zai/glm-5.3"}}}),
                         encoding="utf-8")
        cwd = os.getcwd()
        try:
            os.chdir(self.repo)
            table = sh.crew_table()
        finally:
            os.chdir(cwd)
        self.assertIn("opencode · zai/glm-5.3 (config local do repositório)", table)


if __name__ == "__main__":
    unittest.main()
