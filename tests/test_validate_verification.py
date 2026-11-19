"""Tests for scripts/gates/validate_verification.py (R4, R5)."""
from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

from helpers import TempRepoCase, run_git

import check_proofs
import validate_verification as vv

PY = Path(sys.executable).as_posix()
APPROVED = '**Approved**: 2026-11-04 - user: "sim"\n\n'

SPEC = "# Demo: Spec\n\n{approved}**Size**: LARGE\n**Status**: Approved\n"
TASKS = f"""# Demo: Tasks

{{approved}}## Checks

**Build**: none - sem build
**Run unit**: `"{PY}" -c "print('test_alpha ... ok'); print('test_beta ... ok')"`

**C1** - alpha (R1)
Proof: run unit | test_alpha ... ok

**C2** - beta (R2)
Proof: run unit | test_beta ... ok
"""


def verification(findings: str = "None.", degraded: str = "", checks: str | None = None) -> str:
    rows = checks if checks is not None else ("| C1 | `tests/t.py` `test_alpha` | yes |\n"
                                              "| C2 | `tests/t.py` `test_beta` | yes |\n")
    return (f"# Demo - verification\n\n**Verdict**: PASS\n**Verifier**: codex · requested gpt · effective unconfirmed\n"
            f"{degraded}\n## Checks\n\n| Check | Test | Holds |\n| --- | --- | --- |\n{rows}\n"
            f"## Findings\n\n{findings}\n")


class ValidateVerificationTests(TempRepoCase):
    def feature(self, approved_spec: bool = True, approved_tasks: bool = True) -> Path:
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text(SPEC.format(approved=APPROVED if approved_spec else ""), encoding="utf-8")
        (fdir / "tasks.md").write_text(TASKS.format(approved=APPROVED if approved_tasks else ""), encoding="utf-8")
        (self.repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feat: app")
        return fdir

    def proofs(self) -> None:
        self.assertTrue(check_proofs.evaluate("demo", self.repo).ok)

    def commit_specs(self, msg: str = "docs: verificação") -> None:
        run_git(self.repo, "add", ".specs")
        run_git(self.repo, "commit", "-q", "-m", msg)

    def test_complete_feature_passes(self):
        fdir = self.feature()
        self.proofs()
        (fdir / "verification.md").write_text(verification(), encoding="utf-8")
        self.commit_specs()  # committing only .specs/ after the proofs keeps them valid
        res = vv.evaluate("demo", self.repo)
        self.assertTrue(res.ok, res.report())
        self.assertEqual(res.warnings, [])

    def test_verification_fails_on_missing_or_stale_proofs(self):
        fdir = self.feature()
        res = vv.evaluate("demo", self.repo)
        self.assertTrue(any("falta proofs.md" in e for e in res.errors), res.report())
        self.assertTrue(any("falta verification.md" in e for e in res.errors), res.report())
        self.proofs()
        (fdir / "verification.md").write_text(verification(), encoding="utf-8")
        (self.repo / "app.py").write_text("x = 2\n", encoding="utf-8")
        run_git(self.repo, "commit", "-qam", "fix: app")  # code changed after the proofs
        res = vv.evaluate("demo", self.repo)
        self.assertTrue(any("foi gravado em" in e for e in res.errors), res.report())
        # a failing row and a dirty tree
        self.proofs()
        p = fdir / "proofs.md"
        p.write_text(p.read_text(encoding="utf-8").replace("| C2 |", "| C2X |").replace("**Tree**: clean",
                     "**Tree**: dirty - app.py"), encoding="utf-8")
        res = vv.evaluate("demo", self.repo)
        self.assertTrue(any("proofs.md sem linha para C2" in e for e in res.errors), res.report())
        self.assertTrue(any("não commitadas" in e for e in res.errors), res.report())

    def test_verification_fails_on_open_finding_or_missing_approval(self):
        fdir = self.feature(approved_tasks=False)
        self.proofs()
        findings = ("| Finding | Evidence | Fix | Closed |\n| --- | --- | --- | --- |\n"
                    "| C1 asserção frouxa | `tests/t.py:4` | assert valor | |\n"
                    "| C2 inventado | `tests/t.py:9` | x | abcdef1234 |\n")
        checks = "| C1 | `tests/t.py` `test_alpha` | yes |\n| C2 | | no |\n"
        (fdir / "verification.md").write_text(verification(findings, checks=checks), encoding="utf-8")
        res = vv.evaluate("demo", self.repo)
        errs = "\n".join(res.errors)
        self.assertIn("tasks.md sem `**Approved**", errs)
        self.assertIn("sem commit em `Closed`", errs)
        self.assertIn("não é commit deste repo", errs)
        self.assertIn("C2 sem o teste", errs)
        # closing with a real commit passes that rule
        sha = run_git(self.repo, "rev-parse", "--short", "HEAD")
        (fdir / "verification.md").write_text(verification(findings.replace("| |\n", f"| {sha} · C1 |\n")
                                                           .replace("abcdef1234", f"{sha} · C2")), encoding="utf-8")
        res = vv.evaluate("demo", self.repo)
        self.assertFalse(any("Closed" in e for e in res.errors), res.report())

    def test_degraded_warns_and_strict_fails(self):
        fdir = self.feature()
        self.proofs()
        (fdir / "verification.md").write_text(verification(degraded="**Verification:** self-verified\n"),
                                              encoding="utf-8")
        res = vv.evaluate("demo", self.repo)
        self.assertTrue(res.ok, res.report())
        self.assertTrue(any("verificação degradada" in w for w in res.warnings))
        strict = vv.evaluate("demo", self.repo, strict=True)
        self.assertFalse(strict.ok)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(vv.main(["demo", "--root", str(self.repo)]), 0)
            self.assertEqual(vv.main(["demo", "--root", str(self.repo), "--strict"]), 1)

    def test_mode1_dirty_tree_only_with_degraded(self):
        fdir = self.feature()
        (self.repo / "app.py").write_text("x = 3\n", encoding="utf-8")  # mode 1: never committed
        self.assertFalse(check_proofs.evaluate("demo", self.repo).ok)
        findings = ("| Finding | Evidence | Fix | Closed |\n| --- | --- | --- | --- |\n"
                    "| C1 frouxa | `t.py:1` | x | degradada (modo 1) |\n")
        (fdir / "verification.md").write_text(verification(findings), encoding="utf-8")
        res = vv.evaluate("demo", self.repo)
        self.assertFalse(res.ok)
        (fdir / "verification.md").write_text(verification(findings, "**Verification:** degraded\n"),
                                              encoding="utf-8")
        res = vv.evaluate("demo", self.repo)
        self.assertTrue(res.ok, res.report())
        self.assertTrue(any("verificação degradada" in w for w in res.warnings))


if __name__ == "__main__":
    unittest.main()
