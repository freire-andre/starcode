from __future__ import annotations

import re
import unittest
from unittest import mock

from helpers import ROOT, TempRepoCase, run_git

import dispatch
import impact


class DispatchRegressionTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_repo_config()
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        (self.repo / "app.py").write_text("X = 1\n", encoding="utf-8")
        (self.repo / "test_app.py").write_text("import app\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "base")
        (self.repo / "app.py").write_text("X = 2\n", encoding="utf-8")
        run_git(self.repo, "commit", "-q", "-am", "muda app")

    def test_q_brief_bloco_regression(self):
        text = dispatch.q_brief("demo", self.repo, "HEAD~1", "HEAD")
        self.assertEqual(re.findall(r"\{\{[^}]+\}\}", text), [])
        self.assertIn("selecionados 1 testes", text)
        self.assertIn("app.py <- test_app.py", text)
        (self.repo / "notas.txt").write_text("x\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "nota")
        text = dispatch.q_brief("demo", self.repo, "HEAD~1", "HEAD")
        self.assertIn("rodar tudo: fora do grafo: notas.txt", text)

    def test_q_brief_impact_indisponivel(self):
        with mock.patch.object(impact, "select", side_effect=RuntimeError("quebrou")):
            text = dispatch.q_brief("demo", self.repo, "HEAD~1", "HEAD")
        self.assertIn("seleção indisponível: quebrou; rode a suíte inteira", text)
        text = dispatch.q_brief("demo", self.repo, "main", "naoexiste")
        self.assertIn("seleção indisponível: ", text)
        self.assertIn("; rode a suíte inteira", text)
        self.assertNotIn("{{", text)

    def test_q_verify_regra_regression_autocontida(self):
        brief = (ROOT / "src" / "briefs" / "q-verify.md").read_text(encoding="utf-8")
        self.assertIn("{{regression}}", brief)
        self.assertIn("at HEAD", brief)
        self.assertIn("`## Limits`", brief)
        self.assertIn("rodar tudo", brief)
        for bad in ("scripts/", "PLUGIN_ROOT", "impact.py", "starcode/", ".claude/plugins"):
            self.assertNotIn(bad, brief)


if __name__ == "__main__":
    unittest.main()
