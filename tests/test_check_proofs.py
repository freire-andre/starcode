"""Tests for scripts/gates/check_proofs.py (R1, R2, R3)."""
from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

from helpers import TempRepoCase, run_git

import check_proofs

PY = Path(sys.executable).as_posix()

SPEC = """# Demo: Spec

**Size**: LARGE
**Status**: Approved
"""


def tasks_md(checks: str, build: str = "none - sem build") -> str:
    return f"""# Demo: Tasks

## Checks

**Build**: {build}
**Run unit**: `"{PY}" -c "print('test_alpha (m.C.test_alpha) ... ok'); print('test_beta ... FAIL')"`

{checks}
"""


class CheckProofsTests(TempRepoCase):
    def make_feature(self, checks: str, build: str = "none - sem build") -> Path:
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text(SPEC, encoding="utf-8")
        (fdir / "tasks.md").write_text(tasks_md(checks, build), encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feature")
        return fdir

    def test_check_proofs_writes_proofs_md(self):
        checks = ("**C1** - alpha passa (R1)\nProof: run unit | test_alpha ... ok\n\n"
                  f"**C2** - comando isolado (R2)\nProof: `\"{PY}\" -c \"print(1)\"`\n")
        fdir = self.make_feature(checks, build=f'`"{PY}" -c "print(2)"`')
        res = check_proofs.evaluate("demo", self.repo)
        self.assertTrue(res.ok, res.report())
        text = (fdir / "proofs.md").read_text(encoding="utf-8")
        head = run_git(self.repo, "rev-parse", "--short", "HEAD")
        self.assertIn(f"**HEAD**: {head}", text)
        self.assertIn("**Tree**: clean", text)
        self.assertIn("**Result**: 3 pass, 0 fail", text)
        self.assertRegex(text, r"\| C1 \| .* \| pass \|")
        self.assertRegex(text, r"\| C2 \| .* \| pass \|")
        self.assertRegex(text, r"\| Build \| .* \| pass \|")
        self.assertIn("## Output", text)

    def test_run_proof_needs_words_in_order_on_one_line(self):
        checks = ("**C1** - ordem certa (R1)\nProof: run unit | test_alpha ... ok\n\n"
                  "**C2** - ordem trocada (R1)\nProof: run unit | ok test_alpha\n\n"
                  "**C3** - filtro que não seleciona nada (R1)\nProof: run unit | test_gamma ... ok\n")
        fdir = self.make_feature(checks)
        res = check_proofs.evaluate("demo", self.repo)
        self.assertFalse(res.ok)
        text = (fdir / "proofs.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"\| C1 \| .* \| pass \|")
        self.assertRegex(text, r"\| C2 \| .* \| fail")
        self.assertRegex(text, r"\| C3 \| .* \| fail - nenhum teste rodou")
        self.assertTrue(check_proofs.sees("a test_x b ... c ok", "test_x ... ok"))
        self.assertFalse(check_proofs.sees("test_x\n... ok", "test_x ... ok"))

    def test_dirty_tree_marks_mode1_and_fails(self):
        fdir = self.make_feature("**C1** - alpha (R1)\nProof: run unit | test_alpha ... ok\n")
        (self.repo / "novo.py").write_text("x = 1\n", encoding="utf-8")
        res = check_proofs.evaluate("demo", self.repo)
        self.assertFalse(res.ok)
        text = (fdir / "proofs.md").read_text(encoding="utf-8")
        self.assertIn("**Tree**: dirty (modo 1)", text)
        self.assertIn("**Result**: 1 pass, 0 fail", text)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_proofs.main(["demo", "--root", str(self.repo)]), 1)

    def test_specs_changes_do_not_count_as_dirty(self):
        fdir = self.make_feature("**C1** - alpha (R1)\nProof: run unit | test_alpha ... ok\n")
        (fdir / "notes.md").write_text("x\n", encoding="utf-8")
        res = check_proofs.evaluate("demo", self.repo)
        self.assertTrue(res.ok, res.report())

    def test_medium_feature_reads_spec_checks(self):
        fdir = self.repo / ".specs" / "features" / "med"
        fdir.mkdir(parents=True)
        body = tasks_md("**C1** - alpha (R1)\nProof: run unit | test_alpha ... ok\n").replace("Tasks", "Spec")
        (fdir / "spec.md").write_text(body, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "med")
        res = check_proofs.evaluate("med", self.repo)
        self.assertTrue(res.ok, res.report())
        self.assertTrue((fdir / "proofs.md").exists())

    def test_missing_feature_is_usage_error(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_proofs.main(["nada", "--root", str(self.repo)]), 2)


if __name__ == "__main__":
    unittest.main()
