from __future__ import annotations

import unittest

from helpers import TempRepoCase, run_git

import dispatch


class QBriefEvidenceTests(TempRepoCase):
    def test_q_brief_exige_comando_e_saida_na_sondagem(self):
        self.write_repo_config()
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        (self.repo / "app.py").write_text("X = 1\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "base")
        (self.repo / "app.py").write_text("X = 2\n", encoding="utf-8")
        run_git(self.repo, "commit", "-q", "-am", "muda app")
        text = dispatch.q_brief("demo", self.repo, "HEAD~1", "HEAD")
        self.assertIn(
            "a finding from a probe carries in Evidence the exact command in backticks and the literal output it printed",
            text,
        )
        self.assertIn(
            "`<file>:<line>` alone is valid only for findings from reading code (steps 1 and 3)",
            text,
        )


if __name__ == "__main__":
    unittest.main()
