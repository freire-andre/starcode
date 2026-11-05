"""Tests for scripts/dispatch.py (R9, R10, R19, R21, R38, R45)."""
from __future__ import annotations

import contextlib
import io
import unittest
from pathlib import Path

from helpers import TempRepoCase, run_git

import dispatch
import handoff

TASKS = """# Demo: Tasks

## Tasks

### T1: Modelo
**Depends on**: none
**Requirements**: R1
**Tests**: unit
**Gate**: quick
**Linear**: PROJ-7

#### TASK
Campo priority.

#### CONTEXT
Spec R1.

#### BOUNDARIES
May change: `app/model.py`

#### RULES
TDD.

#### DELIVERY
Commit.

### T2: CLI
**Depends on**: T1
**Requirements**: R2
**Tests**: unit
**Gate**: quick
**Linear**: PROJ-8

#### TASK
Comando.

#### CONTEXT
Spec R2.

#### BOUNDARIES
May change: `app/cli.py`

#### RULES
TDD.

#### DELIVERY
Commit.
"""


class DispatchTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_repo_config()
        self.fdir = self.repo / ".specs" / "features" / "demo"
        self.fdir.mkdir(parents=True)
        (self.fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        (self.fdir / "tasks.md").write_text(TASKS, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "specs")
        run_git(self.repo, "branch", "feature/demo")

    def integrate(self, msg: str) -> None:
        run_git(self.repo, "checkout", "-q", "feature/demo")
        run_git(self.repo, "commit", "-q", "--allow-empty", "-m", msg)
        run_git(self.repo, "checkout", "-q", "main")

    def test_next_ticket_respects_dependencies(self):
        code, msg = dispatch.next_ticket("demo", self.repo)
        self.assertEqual((code, msg.split()[0]), (0, "T1"))
        self.integrate("feat(model): priority\n\nRefs: PROJ-7")
        code, msg = dispatch.next_ticket("demo", self.repo)
        self.assertEqual((code, msg.split()[:2]), (0, ["T2", "PROJ-8"]))
        # an open dispatch blocks a second worker for the same ticket
        handoff.set_handoff("demo", self.repo, {"dispatched": "T2 · PROJ-8 · base abc1234"})
        code, msg = dispatch.next_ticket("demo", self.repo)
        self.assertEqual(code, 3)
        self.assertIn("despacho aberto", msg)
        self.integrate("merge: integra T2 em feature/demo")
        code, msg = dispatch.next_ticket("demo", self.repo)
        self.assertEqual((code, msg), (1, "todos os tickets integrados"))

    def test_ticket_brief_has_block_and_worker_rules(self):
        text = dispatch.worker_brief("demo", "PROJ-8", self.repo)
        self.assertIn("# Ticket T2: CLI", text)
        self.assertIn("Issue: PROJ-8", text)
        for block in ("#### TASK", "#### CONTEXT", "#### BOUNDARIES", "#### RULES", "#### DELIVERY"):
            self.assertIn(block, text)
        self.assertIn("May change: `app/cli.py`", text)
        self.assertIn("Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`", text)
        self.assertIn("Relatório final (até 5 linhas)", text)
        self.assertIn("run_gates.py ticket demo T2", text)
        self.assertNotIn("T1: Modelo", text)

    def test_q_brief_fills_placeholders(self):
        text = dispatch.q_brief("demo", self.repo, "main", "abc1234")
        self.assertNotIn("{{", text)
        self.assertIn("`.specs/features/demo/spec.md`", text)
        self.assertIn("`.specs/features/demo/tasks.md`", text)
        self.assertIn("`.specs/features/demo/proofs.md`", text)
        self.assertIn("`main..abc1234`", text)
        self.assertIn("Write only `.specs/features/demo/verification.md`", text)
        self.assertNotIn("Handoff", text)
        out = self.tmp / "q.md"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(dispatch.main(["q-brief", "demo", "--base", "main", "--head", "abc1234",
                                            "--out", str(out), "--root", str(self.repo)]), 0)
        self.assertTrue(out.read_text(encoding="utf-8").startswith("Repositório:"))

    def test_family_compare(self):
        self.assertEqual(dispatch.family("claude-sonnet-5-5"), "anthropic")
        self.assertEqual(dispatch.family("codex:cli-default"), "openai")
        self.assertEqual(dispatch.family("antigravity:gemini-3.8-flash-medium"), "google")
        self.assertEqual(dispatch.compare("claude:claude-sonnet-5-5", "claude:claude-opus-5-5"), "same")
        self.assertEqual(dispatch.compare("claude:claude-sonnet-5-5", "codex:cli-default"), "different")
        self.assertEqual(dispatch.compare("claude-sonnet-5-5", "opencode:cli-default"), "unknown")


if __name__ == "__main__":
    unittest.main()
