"""Tests for SC-206: local config read from the main worktree, whole local entry, model validation,
banner warning and `suggest` that keeps what is configured."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT, TempRepoCase, run_git

import banner
import setup_helpers as sh
import starcode_common as sc
import validate_config as vc

_OLD = {}


def setUpModule():  # a machine cache of models.dev must not change the suggestions under test
    _OLD["file"] = os.environ.get("STARCODE_MODELS_DEV_FILE")
    os.environ["STARCODE_MODELS_DEV_FILE"] = str(ROOT / "tests" / "fixtures" / "models-dev.json")


def tearDownModule():
    if _OLD["file"] is None:
        os.environ.pop("STARCODE_MODELS_DEV_FILE", None)
    else:
        os.environ["STARCODE_MODELS_DEV_FILE"] = _OLD["file"]


LOCAL = {"schemaVersion": 1, "crew": {"q": {"cli": "opencode", "model": "zai/glm-5.3"}}}
USER = {"schemaVersion": 1, "crew": {"q": {"cli": "antigravity", "model": "gemini-x"}}}


def write_json(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class ConfigLocalWorktreeTests(TempRepoCase):
    def linked(self) -> Path:
        wt = self.tmp / "linked"
        run_git(self.repo, "worktree", "add", "-q", "-b", "child", str(wt))
        return wt

    def banner_text(self) -> str:
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]):
            return banner.build_banner(str(self.repo), False)[0]

    def test_local_no_worktree_ligado(self):
        write_json(sc.user_config_path(), USER)
        main_file = write_json(self.repo / ".starcode" / "config.local.json", LOCAL)
        wt = self.linked()
        self.assertFalse((wt / ".starcode" / "config.local.json").exists())
        # linked worktree without the file: the main worktree's file
        self.assertEqual(sc.local_config_path(wt).resolve(), main_file.resolve())
        self.assertEqual(sc.local_config_path(self.repo).resolve(), main_file.resolve())
        self.assertEqual(sc.load_local_config(wt), (LOCAL, []))
        main_crew, linked_crew = sc.crew_at(self.repo), sc.crew_at(wt)
        for key in main_crew:
            self.assertEqual((linked_crew[key]["cli"], linked_crew[key]["model"], linked_crew[key]["source"]),
                             (main_crew[key]["cli"], main_crew[key]["model"], main_crew[key]["source"]), key)
        self.assertEqual((linked_crew["q"]["cli"], linked_crew["q"]["model"], linked_crew["q"]["source"]),
                         ("opencode", "zai/glm-5.3", "local"))
        # an invalid file in the main worktree is read (and reported) from the linked one
        main_file.write_text("{", encoding="utf-8")
        data, errors = sc.load_local_config(wt)
        self.assertIsNone(data)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith(f"{main_file}: JSON inválido"), errors[0])
        main_file.write_text(json.dumps(LOCAL), encoding="utf-8")
        # a file in the current worktree wins
        own = write_json(wt / ".starcode" / "config.local.json",
                         {"schemaVersion": 1, "crew": {"q": {"cli": "codex", "model": "gpt-6-luna"}}})
        self.assertEqual(sc.local_config_path(wt), own)
        crew = sc.crew_at(wt)
        self.assertEqual((crew["q"]["cli"], crew["q"]["model"], crew["q"]["source"]),
                         ("codex", "gpt-6-luna", "local"))
        # main without the file: no local config, as before
        own.unlink()
        main_file.unlink()
        self.assertEqual(sc.local_config_path(wt), wt / ".starcode" / "config.local.json")
        self.assertEqual(sc.load_local_config(wt), (None, []))
        # outside a repository, or with git failing: the current read, no error
        outside = Path(tempfile.mkdtemp(prefix="starcode-outside-"))
        try:
            self.assertEqual(sc.local_config_path(outside), outside / ".starcode" / "config.local.json")
            self.assertEqual(sc.load_local_config(outside), (None, []))
            write_json(outside / ".starcode" / "config.local.json", LOCAL)
            self.assertEqual(sc.load_local_config(outside), (LOCAL, []))
        finally:
            import shutil
            shutil.rmtree(outside, ignore_errors=True)
        with mock.patch.object(sc, "git", return_value=None):
            self.assertEqual(sc.local_config_path(wt), wt / ".starcode" / "config.local.json")
        # the banner reads the same file from the linked worktree
        write_json(self.repo / ".starcode" / "config.local.json", LOCAL)
        (wt / ".specs").mkdir()
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]):
            text = banner.build_banner(str(wt), True)[0]
        self.assertIn("Config local do repositório: ✅ válido (modelos só deste repositório)", text.splitlines())

    def test_entrada_local_inteira(self):
        path = self.repo / ".starcode" / "config.local.json"
        for entry in ({"model": "zai/glm-5.3"}, {"cli": "opencode"}):
            write_json(path, {"schemaVersion": 1, "crew": {"q": entry}})
            _, errors = vc.load("local", path)
            self.assertEqual(errors, ["crew.q: a entrada local precisa de cli e model juntos"], entry)
        write_json(path, {"schemaVersion": 1, "crew": {"q": {"cli": "opencode", "model": "zai/glm-5.3"}}})
        self.assertEqual(vc.load("local", path)[1], [])
        # user and repo configs keep the partial entry
        write_json(path, {"schemaVersion": 1, "crew": {"q": {"model": "zai/glm-5.3"}}})
        self.assertEqual(vc.load("user", path)[1], [])
        # the CLI says the same thing
        res = subprocess.run(["python", str(ROOT / "scripts" / "config" / "validate_config.py"), "--kind", "local",
                              str(path)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 1)
        self.assertIn("  - crew.q: a entrada local precisa de cli e model juntos", res.stdout.splitlines())
        # effective_crew: the local entry whole, never the user's cli with the local model
        doc = sc.load_crew()
        user = {"crew": {"q": {"cli": "antigravity", "model": "gemini-x"}}}
        local = {"crew": {"q": {"cli": "opencode", "model": "zai/glm-5.3"}}}
        crew = sc.effective_crew(doc, user, local)
        self.assertEqual((crew["q"]["cli"], crew["q"]["model"], crew["q"]["source"]),
                         ("opencode", "zai/glm-5.3", "local"))
        only_model = sc.effective_crew(doc, user, {"crew": {"q": {"model": "zai/glm-5.3"}}})
        self.assertNotEqual(only_model["q"]["cli"], "antigravity")

    def test_modelo_valido(self):
        valid = ["claude-opus-5-5", "zai/glm-5.3", "openrouter/meta/llama-4:free", "gpt-6-luna", "cli-default",
                 "modelo@2025", "a+b_c.d"]
        invalid = ["", " ", "com espaço", "-flag", "--dangerous", "modelo\n", "mod;elo", "mod$elo", "mód", "a|b"]
        kinds = {
            "user": lambda m: {"schemaVersion": 1, "crew": {"laforge": {"cli": "codex", "model": m}}},
            "local": lambda m: {"schemaVersion": 1, "crew": {"laforge": {"cli": "codex", "model": m}}},
        }
        for kind, build in kinds.items():
            for m in valid:
                self.assertEqual(vc.validate(kind, build(m)), [], (kind, m))
            for m in invalid:
                self.assertEqual(vc.validate(kind, build(m)), [f"crew.laforge.model: modelo inválido {m}"], (kind, m))
        repo_base = json.loads((ROOT / "tests" / "fixtures" / "config" / "valid" / "repo-full.json")
                               .read_text(encoding="utf-8"))
        self.assertEqual(vc.validate("repo", repo_base), [])
        # the repo config has no model field: its schema must stay free of it
        self.assertIn("model: chave desconhecida", vc.validate("repo", {**repo_base, "model": "x"}))
        # error text carries the file path (load)
        path = write_json(self.repo / "u.json", kinds["user"]("-flag"))
        self.assertEqual(vc.load("user", path)[1], ["crew.laforge.model: modelo inválido -flag"])
        # parse_model_arg: `@` of a known tier is split, any other `@` stays in the id
        self.assertEqual(sh.parse_model_arg("opencode=zai/glm-5.3@$$"), ("opencode", "zai/glm-5.3", "$$"))
        self.assertEqual(sh.parse_model_arg("opencode=zai/glm-5.3@gratis"), ("opencode", "zai/glm-5.3", "grátis"))
        self.assertEqual(sh.parse_model_arg("opencode=modelo@2025"), ("opencode", "modelo@2025", None))
        self.assertEqual(sh.parse_model_arg("opencode=modelo@2025@$"), ("opencode", "modelo@2025", "$"))
        self.assertEqual(sh.parse_model_arg("opencode=modelo@"), ("opencode", "modelo@", None))
        self.assertEqual(sh.parse_model_arg("opencode=@$$$"), None)
        self.assertEqual(sh.parse_model_arg("opencode="), None)
        self.assertEqual(sh.parse_model_arg("naoexiste=x"), None)

    def test_aviso_local_versionado(self):
        self.write_repo_config()
        path = write_json(self.repo / ".starcode" / "config.local.json", LOCAL)
        warn = f"⚠️ config local versionado ou fora do .gitignore: {path}"
        # present, not ignored: warns
        self.assertIn(warn, self.banner_text().splitlines())
        # ignored and not tracked: no warning
        vc.ensure_ignored(self.repo / ".starcode")
        self.assertNotIn(warn, self.banner_text().splitlines())
        self.assertFalse(any("config local versionado" in ln for ln in self.banner_text().splitlines()))
        # tracked although ignored: warns
        run_git(self.repo, "add", "-f", ".starcode/config.local.json")
        self.assertIn(warn, self.banner_text().splitlines())
        run_git(self.repo, "rm", "-q", "--cached", ".starcode/config.local.json")
        self.assertNotIn(warn, self.banner_text().splitlines())
        # no local file: no warning
        path.unlink()
        self.assertFalse(any("config local versionado" in ln for ln in self.banner_text().splitlines()))
        # linked worktree reading the main file: the path is the main one
        write_json(self.repo / ".starcode" / "config.local.json", LOCAL)
        (self.repo / ".starcode" / ".gitignore").write_text("", encoding="utf-8")
        wt = self.linked()
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]):
            text = banner.build_banner(str(wt), False)[0]
        self.assertIn(warn, text.splitlines())

    def test_suggest_mantem_configurado(self):
        doc = sc.load_crew()
        crew_names = {k: m["name"] for k, m in doc["crew"].items()}
        have = ["claude", "opencode"]
        plain = sh.suggest(doc, have)
        self.assertEqual(plain["kept"], [])
        current = {k: {"cli": "claude", "model": "x", "source": "default"} for k in doc["crew"]}
        current["laforge"] = {"cli": "opencode", "model": "zai/glm-5.3", "source": "local"}
        current["uhura"] = {"cli": "claude", "model": "claude-haiku-5-5", "source": "user"}
        current["guinan"] = {"cli": "codex", "model": "gpt-6-luna", "source": "user"}  # codex unavailable
        res = sh.suggest(doc, have, None, current)
        rows = {r["member"]: r for r in res["rows"]}
        self.assertEqual((rows["laforge"]["cli"], rows["laforge"]["model"], rows["laforge"]["changed"],
                          rows["laforge"]["kept"]), ("opencode", "zai/glm-5.3", False, True))
        self.assertEqual((rows["uhura"]["cli"], rows["uhura"]["model"], rows["uhura"]["kept"]),
                         ("claude", "claude-haiku-5-5", True))
        self.assertEqual(res["kept"], [crew_names["laforge"], crew_names["uhura"]])
        # codex is unavailable: Guinan is proposed again, not kept
        self.assertFalse(rows["guinan"]["kept"])
        self.assertNotEqual(rows["guinan"]["cli"], "codex")
        # members without config get the same proposal as without `current`
        plain_rows = {r["member"]: r for r in plain["rows"]}
        for key in ("picard", "spock", "troi", "data", "mccoy", "scotty", "kirk", "worf"):
            self.assertEqual((rows[key]["cli"], rows[key]["model"]), (plain_rows[key]["cli"],
                                                                     plain_rows[key]["model"]), key)
            self.assertFalse(rows[key]["kept"])
        # the proposed config keeps the configured members as they are
        self.assertEqual(res["config"]["crew"]["laforge"], {"cli": "opencode", "model": "zai/glm-5.3"})
        self.assertEqual(res["config"]["crew"]["uhura"], {"cli": "claude", "model": "claude-haiku-5-5"})
        # a configured Q with an available CLI stays too
        current["q"] = {"cli": "opencode", "model": "zai/glm-5.3", "source": "local"}
        with_q = sh.suggest(doc, have, None, current)
        q_row = next(r for r in with_q["rows"] if r["member"] == "q")
        self.assertEqual((q_row["cli"], q_row["model"], q_row["kept"]), ("opencode", "zai/glm-5.3", True))
        # rendered output: the exact `mantidos:` line
        self.assertIn(f"mantidos: {crew_names['laforge']}, {crew_names['uhura']}",
                      sh.render_suggestion(res).splitlines())
        self.assertFalse(any(ln.startswith("mantidos:") for ln in sh.render_suggestion(plain).splitlines()))
        # the CLI reads the current config by itself
        write_json(sc.user_config_path(), {"schemaVersion": 1, "crew": {"uhura": {"cli": "claude",
                                                                                    "model": "claude-haiku-5-5"}}})
        proc = subprocess.run(["python", str(ROOT / "scripts" / "setup_helpers.py"), "suggest", "--have",
                               "claude,opencode"], cwd=self.repo, capture_output=True, text=True,
                              encoding="utf-8", env={**os.environ, "STARCODE_HOME": os.environ["STARCODE_HOME"]})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"mantidos: {crew_names['uhura']}", proc.stdout.splitlines())

    def test_skill_e_decisions(self):
        skill = (ROOT / "skills" / "config" / "SKILL.md").read_text(encoding="utf-8")
        flat = " ".join(skill.split())
        self.assertIn("The local entry takes `cli` and `model` together: the validator refuses an entry with only "
                      "one of them.", flat)
        self.assertIn("The local file also applies in linked worktrees: a worktree without its own file reads the "
                      "main worktree's.", flat)
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = next((p for p in text.split("\n### ") if p.startswith("SC-206:")), None)
        self.assertIsNotNone(entry, "falta a entrada ### SC-206:")
        for field in ("**Problema**", "**Decisão**", "**Motivo**", "**Por que não é bug**"):
            self.assertEqual(entry.count(field), 1, field)
        problema = entry.split("**Problema**")[1].split("**Decisão**")[0]
        for frase in ("Reprodução", "`antigravity · zai/glm-5.3`", "`antigravity · gemini-x`", "crew_at(repo_root(...))"):
            self.assertIn(frase, problema, frase)
        decisao = entry.split("**Decisão**")[1].split("**Motivo**")[0]
        for frase in ("R1:", "pasta-mãe de `git rev-parse --path-format=absolute --git-common-dir`",
                      "o arquivo do worktree atual quando existe", "mantém a leitura atual, sem erro",
                      "R2:", "`<caminho>: a entrada local precisa de cli e model juntos`",
                      "nunca o CLI do usuário com o modelo local",
                      "R3:", "`<caminho>: modelo inválido <valor>`", "`[A-Za-z0-9._:/+@-]`",
                      "começando com `-`", "só quando o sufixo é um nível de custo conhecido",
                      "R4:", "`⚠️ config local versionado ou fora do .gitignore: <caminho>`",
                      "`git ls-files --error-unmatch`", "`git check-ignore`",
                      "R5:", "`mantidos: <nomes>`", "o CLI lê a config atual sozinho",
                      "R6:", "`cli` e `model` juntos e vale nos worktrees ligados", "`CHANGELOG.md`"):
            self.assertIn(frase, decisao, frase)
        nao_bug = entry.split("**Por que não é bug**")[1]
        for name in ("test_local_no_worktree_ligado", "test_entrada_local_inteira", "test_modelo_valido",
                     "test_aviso_local_versionado", "test_suggest_mantem_configurado", "test_skill_e_decisions"):
            self.assertIn(name, nao_bug, name)
        unreleased = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("## [Unreleased]")[1].split("\n## [")[0]
        self.assertTrue(any("SC-206" in ln and "Config local nos worktrees" in ln for ln in unreleased.splitlines()))


if __name__ == "__main__":
    unittest.main()
