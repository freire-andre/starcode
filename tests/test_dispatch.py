"""Tests for scripts/dispatch.py (R9, R10, R19, R21, R38, R45)."""
from __future__ import annotations

import contextlib
import io
import unittest
from pathlib import Path
from unittest import mock

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
Spec R1. Checks: C1.

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
Spec R2. Checks: C2.

#### BOUNDARIES
May change: `app/cli.py`

#### RULES
TDD.

#### DELIVERY
Commit.

## Checks

**Build**: `python tools/build.py --check`
**Run unit**: `python -m unittest -v 2>&1`

**C1** - Modelo funciona (R1)
Proof: run unit | test_model_works ... ok

**C2** - Comando funciona (R2)
Proof: run unit | test_cli_works ... ok
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
        self.assertIn("run_gates.py\" ticket demo T2", text)
        self.assertIn("/scripts/gates/run_gates.py", text)  # absolute plugin path: works without the skill
        self.assertNotIn("T1: Modelo", text)

    def test_ticket_brief_has_check_and_proof_lines(self):  # item 3
        text = dispatch.worker_brief("demo", "T2", self.repo)
        ctx = text.split("#### CONTEXT")[1].split("#### BOUNDARIES")[0]
        self.assertIn("**C2** - Comando funciona (R2)", ctx)
        self.assertIn("Proof: run unit | test_cli_works ... ok", ctx)
        self.assertIn("**Run unit**: `python -m unittest -v 2>&1`", ctx)
        self.assertIn("teste deve se chamar exatamente como na linha Proof", ctx)
        self.assertNotIn("**C1**", ctx)
        self.assertNotIn("test_model_works", text)

    def test_brief_requires_committed_planning(self):  # item 4
        fdir = self.repo / ".specs" / "features" / "novo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text("# Novo\n", encoding="utf-8")
        (fdir / "tasks.md").write_text(TASKS, encoding="utf-8")
        err = io.StringIO()
        args = ["brief", "novo", "T1", "--out", str(self.tmp / "b.md"), "--root", str(self.repo)]
        with contextlib.redirect_stderr(err):
            self.assertEqual(dispatch.main(args), 2)
        self.assertIn("commit", err.getvalue())
        self.assertIn(".specs/features/novo/spec.md", err.getvalue())
        self.assertFalse((self.tmp / "b.md").exists())
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "specs")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(dispatch.main(args), 0)
        # spec committed but tasks.md not
        (fdir / "tasks.md").write_text(TASKS + "\n", encoding="utf-8")
        run_git(self.repo, "rm", "-q", "--cached", ".specs/features/novo/tasks.md")
        run_git(self.repo, "commit", "-q", "-m", "tira tasks")
        with contextlib.redirect_stderr(io.StringIO()) as e2:
            self.assertEqual(dispatch.main(args), 2)
        self.assertIn("tasks.md", e2.getvalue())

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


SPEC_MEDIA = """# Média: Spec

**Size**: MEDIUM
**Linear**: PROJ-9

## Scope

- Faz a coisa.

## Requirements

- **R1** - WHEN x THEN y.

## Checks

- **C1** - R1: teste prova y.
"""


class MediaBriefTests(TempRepoCase):
    def make(self, spec: str) -> None:
        self.write_repo_config()
        fdir = self.repo / ".specs" / "features" / "media"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text(spec, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "specs")

    def test_media_brief_from_spec(self):
        self.make(SPEC_MEDIA)
        text = dispatch.worker_brief("media", "T1", self.repo)
        self.assertIn("# Média: Spec", text)
        self.assertIn("Issue: PROJ-9", text)
        for sec in ("## Scope", "## Requirements", "## Checks"):
            self.assertIn(sec, text)
        self.assertIn("Faz a coisa.", text)
        self.assertIn("- **C1** - R1", text)
        self.assertIn("run_gates.py\" ticket media", text)
        self.assertIn("Nunca escreva `.specs/STATE.md`", text)

    def test_media_brief_has_proof_rule(self):
        proof = "- **C1** - R1: teste prova y.\n  Proof: pytest -k test_y"
        self.make(SPEC_MEDIA.replace("- **C1** - R1: teste prova y.", proof))
        text = dispatch.worker_brief("media", "T1", self.repo)
        self.assertIn("Proof: pytest -k test_y", text)
        self.assertIn("teste deve se chamar exatamente como na linha Proof", text)

    def test_media_brief_without_linear(self):
        self.make(SPEC_MEDIA.replace("**Linear**: PROJ-9\n", "**Linear**:\n"))
        self.assertIn("Issue: sem issue", dispatch.worker_brief("media", "T1", self.repo))

    def test_media_brief_without_checks_exits_2(self):
        self.make(SPEC_MEDIA.split("## Checks")[0])
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = dispatch.main(["brief", "media", "T1", "--out", str(self.tmp / "b.md"),
                                  "--root", str(self.repo)])
        self.assertEqual(code, 2)
        self.assertIn("spec sem ## Checks: não há o que entregar ao worker", err.getvalue())


class FamilyAndQCliTests(TempRepoCase):
    def test_new_families(self):
        f = dispatch.family
        self.assertEqual(f("deepseek-v4"), "deepseek")
        self.assertEqual(f("opencode:deepseek-chat"), "deepseek")
        self.assertEqual(f("gpt-oss-120b"), "openai")
        self.assertEqual(f("openrouter/anthropic/claude-sonnet-5-5"), "anthropic")
        self.assertEqual(f("openrouter/openai/gpt-5"), "openai")
        self.assertEqual(f("opencode:openrouter/google/gemini-3"), "google")
        self.assertEqual(f("openrouter/deepseek/deepseek-v4"), "deepseek")
        self.assertEqual(f("openrouter/acme/model-x"), "unknown")
        self.assertEqual(dispatch.compare("openrouter/anthropic/claude-x", "claude"), "same")

    def caps(self, **status: str) -> Path:
        d = self.tmp / "caps"
        for cli, st in status.items():
            (d / cli).mkdir(parents=True, exist_ok=True)
            (d / cli / "capabilities.json").write_text(
                '{"extras": {"orca_worker": {"status": "%s"}}}' % st, encoding="utf-8")
        return d

    def test_q_cli_picks_first_different_family(self):
        d = self.caps(codex="ok", antigravity="ok", opencode="ok")
        self.assertEqual(dispatch.q_cli("claude:claude-sonnet-5-5", None, d), "codex")
        self.assertEqual(dispatch.q_cli("claude:claude-sonnet-5-5", "antigravity", d), "antigravity")
        self.assertEqual(dispatch.q_cli("codex:cli-default", "codex", d), "antigravity")

    def test_q_cli_skips_same_vendor_and_unavailable(self):
        d = self.caps(codex="unavailable", antigravity="ok", opencode="ok")
        self.assertEqual(dispatch.q_cli("claude:claude-sonnet-5-5", None, d), "antigravity")
        # opencode without model is unknown family: not chosen
        d = self.caps(codex="unavailable", antigravity="unavailable", opencode="ok")
        self.assertIsNone(dispatch.q_cli("claude:claude-sonnet-5-5", None, d))
        # LaForge via openrouter/anthropic: same family as claude, skipped
        d = self.caps(codex="ok")
        self.assertEqual(dispatch.q_cli("opencode:openrouter/anthropic/claude-x", "claude:claude-x", d), "codex")

    def test_q_cli_missing_record_uses_available_binary(self):  # item 2
        # Codex LaForge, plugin installed in the Codex cache: no record for the other CLIs.
        empty = self.tmp / "nocaps"
        empty.mkdir()
        with mock.patch.object(dispatch, "_default_caps_dirs", return_value=[empty]):
            self.assertEqual(dispatch.q_cli("codex:cli-default", None, None, lambda b: "/bin/agy" if b == "agy" else None),
                             "antigravity")
            self.assertEqual(dispatch.q_cli("codex:cli-default", "antigravity", None, lambda b: None), "antigravity")
            self.assertIsNone(dispatch.q_cli("codex:cli-default", None, None, lambda b: None))
            # a record that says unavailable still wins over the binary
            d = self.caps(antigravity="unavailable")
            self.assertIsNone(dispatch.q_cli("codex:cli-default", None, d, lambda b: "/bin/" + b))

    def test_q_cli_command(self):
        d = self.caps(codex="ok")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = dispatch.main(["q-cli", "--laforge", "claude:claude-sonnet-5-5", "--caps-dir", str(d)])
        self.assertEqual((code, out.getvalue().strip()), (0, "codex"))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = dispatch.main(["q-cli", "--laforge", "codex:cli-default", "--caps-dir", str(self.caps(codex="ok"))])
        self.assertEqual((code, out.getvalue().strip()), (1, "self-verified"))


if __name__ == "__main__":
    unittest.main()
