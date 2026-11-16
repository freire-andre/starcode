"""Tests for scripts/gates/check_proofs.py (R1, R2, R3)."""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import tempfile
import sys
import time
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


def _pid_vivo(pid: int) -> bool:
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out.split()
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


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

    def test_declared_run_without_proof_still_runs_and_is_recorded(self):
        # C1/R1: a `**Run <nome>**:` that no `Proof:` cites must run once and appear in `## Output`.
        fdir = self.make_feature("**C1** - alpha (R1)\nProof: run unit | test_alpha ... ok\n")
        tasks = fdir / "tasks.md"
        extra = f'**Run extra**: `"{PY}" -c "import sys; print(\'extra-ran\'); sys.exit(3)"`\n'
        tasks.write_text(tasks.read_text(encoding="utf-8").replace("**Run unit**:", extra + "**Run unit**:"),
                         encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "extra")
        res = check_proofs.evaluate("demo", self.repo)
        text = (fdir / "proofs.md").read_text(encoding="utf-8")
        self.assertIn("`Run extra` - exit 3", text)
        self.assertIn("extra-ran", text)
        self.assertRegex(text, r"\| Run extra \| .* \| fail - exit 3 \|")
        self.assertFalse(res.ok)

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


    def test_sees_palavra_inteira(self):  # R2
        s = check_proofs.sees
        self.assertFalse(s("test_login_extra PASSED", "test_login PASSED"))
        self.assertTrue(s("test_login PASSED", "test_login PASSED"))
        self.assertFalse(s("xtest_login PASSED", "test_login PASSED"))
        self.assertTrue(s("a test_login (m.C.test_login) ... ok", "test_login (m.C.test_login) ... ok"))
        self.assertFalse(s("test_login_extra (m.C.test_login_extra) ... ok", "test_login (m.C.test_login) ... ok"))
        self.assertTrue(s("test_x ...ok", "test_x ..."))  # `...` sem borda de palavra
        self.assertFalse(s("test_x okay", "test_x ok"))

    def test_sees_docstring_do_unittest(self):  # R3
        s = check_proofs.sees
        self.assertTrue(s("test_x (m.C.test_x)\nDocstring ... ok", "test_x (m.C.test_x) ... ok"))
        self.assertFalse(s("test_x\n... ok", "test_x ... ok"))
        self.assertFalse(s("outra linha\ntest_x (m.C.test_x)", "test_x (m.C.test_x) ... ok"))
        self.assertFalse(s("x test_x (m.C.test_x)\n... ok", "test_x (m.C.test_x) ... ok"))

    def test_prova_com_tempo_limite(self):  # R4
        tmp = Path(tempfile.mkdtemp(prefix="starcode-pid-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        script = tmp / "dorme.py"  # grava o próprio PID e dorme: o teste confere que o processo foi encerrado
        script.write_text("import os, sys, time\nopen(sys.argv[1], 'w').write(str(os.getpid()))\ntime.sleep(60)\n",
                          encoding="utf-8")
        pidfiles = {n: (tmp / f"{n}.pid").as_posix() for n in ("build", "run", "solo")}

        def sleeper(n):
            return f'"{PY}" {script.as_posix()} {pidfiles[n]}'

        checks = ("**C1** - lenta (R4)\nProof: run slow | test_alpha ... ok\n\n"
                  f"**C2** - avulsa (R4)\nProof: `{sleeper('solo')}`\n")
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text(SPEC, encoding="utf-8")
        (fdir / "tasks.md").write_text(
            f"# Demo: Tasks\n\n## Checks\n\n**Build**: `{sleeper('build')}`\n**Run slow**: `{sleeper('run')}`\n\n{checks}\n",
            encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feature")
        old = check_proofs.PROOF_TIMEOUT
        check_proofs.PROOF_TIMEOUT = 5
        try:
            res = check_proofs.evaluate("demo", self.repo)
        finally:
            check_proofs.PROOF_TIMEOUT = old
        self.assertFalse(res.ok)
        text = (fdir / "proofs.md").read_text(encoding="utf-8")
        for cid in ("C1", "C2", "Run slow", "Build"):
            self.assertRegex(text, rf"\| {cid} \| .* \| fail - tempo limite \(1800 s\) \|")
        self.assertEqual(check_proofs.PROOF_TIMEOUT, 1800)
        for n, f in pidfiles.items():  # o processo que passou do limite foi encerrado (árvore inclusive)
            pid = int(Path(f).read_text())
            for _ in range(50):
                if not _pid_vivo(pid):
                    break
                time.sleep(0.1)
            self.assertFalse(_pid_vivo(pid), f"processo da prova {n} (PID {pid}) continua vivo")


if __name__ == "__main__":
    unittest.main()
