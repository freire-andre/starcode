"""Tests for the execution stages of scripts/gates/run_gates.py (R7)."""
from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

from helpers import TempRepoCase, run_git

import run_gates

PY = Path(sys.executable).as_posix()
APPROVED = '**Approved**: 2026-11-04 - user: "sim"\n\n'

TASKS = f"""# Demo: Tasks

{APPROVED}## Tasks

### T1: App
**Depends on**: none
**Linear**: PROJ-7

#### BOUNDARIES
May change: `app.py`

## Checks

**Build**: none - sem build
**Run unit**: `"{PY}" -c "print('test_alpha ... ok')"`

**C1** - alpha (R1)
Proof: run unit | test_alpha ... ok
"""


class RunGatesExecutionTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text(f"# Demo: Spec\n\n{APPROVED}**Size**: LARGE\n", encoding="utf-8")
        (fdir / "tasks.md").write_text(TASKS, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "docs(specs): demo\n\nRefs: PROJ-7")
        self.base = run_git(self.repo, "rev-parse", "HEAD")
        self.fdir = fdir

    def run_main(self, *args: str) -> tuple[int, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = run_gates.main([*args, "--root", str(self.repo)])
        return code, buf.getvalue()

    def test_run_gates_execution_stages(self):
        (self.repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feat(app): cria app\n\nRefs: PROJ-7")
        head = run_git(self.repo, "rev-parse", "HEAD")

        code, out = self.run_main("ticket", "demo", "T1", f"{self.base}..{head}")
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith("VEREDITO: VERDE (etapa ticket, 2 gate(s))"), out)

        code, out = self.run_main("proofs", "demo")
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith("VEREDITO: VERDE (etapa proofs"), out)
        self.assertTrue((self.fdir / "proofs.md").exists())

        code, out = self.run_main("done", "demo")
        self.assertEqual(code, 1, out)
        self.assertTrue(out.startswith("VEREDITO: VERMELHO"), out)
        self.assertIn("falta verification.md", out)

    def test_ticket_stage_checks_refs_of_each_commit(self):
        (self.repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feat(app): cria app\n\nRefs: PROJ-99")
        head = run_git(self.repo, "rev-parse", "HEAD")
        code, out = self.run_main("ticket", "demo", "T1", f"{self.base}..{head}")
        self.assertEqual(code, 1, out)
        self.assertIn("não cita PROJ-7", out)

    def test_ticket_stage_needs_ticket_and_range(self):
        code, out = self.run_main("ticket", "demo")
        self.assertEqual(code, 2, out)


if __name__ == "__main__":
    unittest.main()
