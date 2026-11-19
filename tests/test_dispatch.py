"""Tests for scripts/dispatch.py (R9, R10, R19, R21, R38, R45)."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from helpers import FIXTURES, ROOT, TempRepoCase, run_git

import dispatch
import handoff
Q_HANDOFF_RULE = (
    "Never touch the `## Handoff` section of any artifact, and never restore, revert, stash, check out or "
    "delete files: uncommitted changes you did not make are not yours.")
FIXTURES_DIR = FIXTURES / "config" / "valid"

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

    def test_next_open_dispatch_with_multiple_entries(self):  # C19
        self.integrate("feat(model): priority\n\nRefs: PROJ-7")
        e1 = "T1 · PROJ-7 · base abc1234 · claude:claude-sonnet-5-5 · 2026-11-07T16:40:00Z"
        e2 = "T2 · PROJ-8 · base abc1234 · codex:gpt-6-luna · 2026-11-07T16:41:00Z"
        handoff.set_handoff("demo", self.repo, {"dispatched": f"{e1}; {e2}"})
        code, msg = dispatch.next_ticket("demo", self.repo)
        self.assertEqual(code, 3)
        self.assertIn("T2 · PROJ-8", msg)
        self.assertNotIn("T1 · PROJ-7", msg)
        handoff.set_handoff("demo", self.repo, {"dispatched": "T2 · PROJ-8 · x; T3 · PROJ-9 · y"})
        code, msg = dispatch.next_ticket("demo", self.repo)
        self.assertEqual(code, 3)
        self.assertIn("T2 · PROJ-8", msg)
        self.assertIn("T3 · PROJ-9", msg)
        self.integrate("merge: integra T2 em feature/demo")
        handoff.set_handoff("demo", self.repo, {"dispatched": f"{e1}; {e2}"})
        self.assertEqual(dispatch.next_ticket("demo", self.repo),
                         (1, "todos os tickets integrados"))

    def test_overdue_lists_tickets_past_deadline(self):  # C22
        old = "T1 · PROJ-7 · base abc1234 · claude:claude-sonnet-5-5 · 2026-11-07T16:00:00Z · disp_1 · model x"
        new = "T2 · PROJ-8 · base abc1234 · codex:gpt-6-luna · 2026-11-07T16:40:00Z"
        handoff.set_handoff("demo", self.repo, {"dispatched": f"{old}; {new}"})
        code, lines = dispatch.overdue("demo", self.repo, 30, "2026-11-07T16:45:00Z")
        self.assertEqual((code, lines), (0, ["T1 · PROJ-7 · 45 min · disp_1"]))
        code, lines = dispatch.overdue("demo", self.repo, 60, "2026-11-07T16:45:00Z")
        self.assertEqual((code, lines), (1, []))
        code, lines = dispatch.overdue("demo", self.repo, 1, "2026-11-07T16:45:00Z")
        self.assertEqual(lines, ["T1 · PROJ-7 · 45 min · disp_1", "T2 · PROJ-8 · 5 min · -"])
        # default from fleet.timeoutMinutes, else 30
        with mock.patch.object(dispatch.sc, "load_user_config", return_value=({"fleet": {"timeoutMinutes": 50}}, [])):
            self.assertEqual(dispatch.overdue("demo", self.repo, None, "2026-11-07T16:45:00Z")[0], 1)
        with mock.patch.object(dispatch.sc, "load_user_config", return_value=(None, [])):
            self.assertEqual(dispatch.overdue("demo", self.repo, None, "2026-11-07T16:45:00Z")[0], 0)
        # integrated tickets are not active
        self.integrate("feat(model): priority\n\nRefs: PROJ-7")
        self.assertEqual(dispatch.overdue("demo", self.repo, 30, "2026-11-07T16:45:00Z")[0], 1)
        # command
        out = io.StringIO()
        handoff.set_handoff("demo", self.repo, {"dispatched": new})
        with contextlib.redirect_stdout(out):
            code = dispatch.main(["overdue", "demo", "--root", str(self.repo), "--minutes", "10",
                                  "--now", "2026-11-07T17:00:00Z", "--base", "main"])
        self.assertEqual(code, 0)
        self.assertIn("T2 · PROJ-8 · 20 min · -", out.getvalue())

    def test_overdue_skips_blocked_entries(self):  # R22, R23
        blocked = "T1 · PROJ-7 · base abc1234 · claude:claude-sonnet-5-5 · 2026-11-07T16:00:00Z · disp_1 · blocked"
        late = "T2 · PROJ-8 · base abc1234 · codex:gpt-6-luna · 2026-11-07T16:00:00Z · disp_2"
        handoff.set_handoff("demo", self.repo, {"dispatched": f"{blocked}; {late}"})
        code, lines = dispatch.overdue("demo", self.repo, 30, "2026-11-07T16:45:00Z")
        self.assertEqual((code, lines), (0, ["T2 · PROJ-8 · 45 min · disp_2"]))
        handoff.set_handoff("demo", self.repo, {"dispatched": blocked})
        self.assertEqual(dispatch.overdue("demo", self.repo, 30, "2026-11-07T16:45:00Z"), (1, []))

    def test_overdue_unreadable_time_exits_2(self):
        handoff.set_handoff("demo", self.repo, {"dispatched": "T1 · PROJ-7 · base abc1234"})
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = dispatch.main(["overdue", "demo", "--root", str(self.repo), "--now", "2026-11-07T17:00:00Z"])
        self.assertEqual(code, 2)
        self.assertIn("T1 · PROJ-7", err.getvalue())

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
        self.assertIn(Q_HANDOFF_RULE, text.splitlines())
        out = self.tmp / "q.md"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(dispatch.main(["q-brief", "demo", "--base", "main", "--head", "abc1234",
                                            "--out", str(out), "--root", str(self.repo)]), 0)
        self.assertTrue(out.read_text(encoding="utf-8").startswith("Repositório:"))

    def test_q_brief_proibe_tocar_no_handoff(self):
        lines = dispatch.q_brief("demo", self.repo, "main", "abc1234").splitlines()
        start = lines.index("## Rules")
        end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
        self.assertIn(Q_HANDOFF_RULE, lines[start:end])

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

    def test_medium_brief_from_spec(self):
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

    def test_medium_brief_without_checks_exits_2(self):
        self.make(SPEC_MEDIA.split("## Checks")[0])
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = dispatch.main(["brief", "media", "T1", "--out", str(self.tmp / "b.md"),
                                  "--root", str(self.repo)])
        self.assertEqual(code, 2)
        self.assertIn("spec sem ## Checks: não há o que entregar ao worker", err.getvalue())


class FamilyAndQCliTests(TempRepoCase):
    def test_family_deepseek_gptoss_openrouter(self):
        f = dispatch.family
        self.assertEqual(f("deepseek-v4"), "deepseek")
        self.assertEqual(f("opencode:deepseek-chat"), "deepseek")
        self.assertEqual(f("gpt-oss-120b"), "openai")
        self.assertEqual(f("openrouter/anthropic/claude-sonnet-5-5"), "anthropic")
        self.assertEqual(f("openrouter/openai/gpt-5"), "openai")
        self.assertEqual(f("opencode:openrouter/google/gemini-3"), "google")
        self.assertEqual(f("openrouter/deepseek/deepseek-v4"), "deepseek")
        self.assertEqual(f("openrouter/acme/model-x"), "unknown")
        for broken in ("openrouter/anthropic/", "openrouter/anthropic", "openrouter//claude-x",
                       "openrouter/", "openrouter/anthropic/  ", "opencode:openrouter/anthropic/"):
            self.assertEqual(f(broken), "unknown", broken)
        self.assertEqual(dispatch.compare("openrouter/anthropic/claude-x", "claude"), "same")

    def caps(self, **status: str) -> Path:
        d = self.tmp / "caps"
        for cli, st in status.items():
            (d / cli).mkdir(parents=True, exist_ok=True)
            (d / cli / "capabilities.json").write_text(
                '{"extras": {"orca_worker": {"status": "%s"}}}' % st, encoding="utf-8")
        return d

    def test_q_cli_picks_other_family(self):
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

    LF = "claude:claude-sonnet-5-5"

    def test_q_strategy_none_keeps_current_order(self):  # C1
        d = self.caps(codex="ok", antigravity="ok", opencode="ok")
        self.assertEqual(dispatch.q_cli(self.LF, None, d, strategies=None), "codex")
        self.assertEqual(dispatch.q_cli(self.LF, None, d), "codex")

    def test_q_strategy_orca_worker_walks_cli_order(self):  # C2
        d = self.caps(codex="ok", antigravity="ok", opencode="ok")
        for strat in (["orca-worker"], ["orca-worker", "self-verified"]):
            self.assertEqual(dispatch.q_cli(self.LF, None, d, strategies=strat), "codex", strat)
        d = self.caps(codex="unavailable", antigravity="ok")
        self.assertEqual(dispatch.q_cli(self.LF, None, d, strategies=["orca-worker"]), "antigravity")

    def test_q_strategy_self_verified_first_wins(self):  # C3
        d = self.caps(codex="ok")
        self.assertIsNone(dispatch.q_cli(self.LF, None, d, strategies=["self-verified", "orca-worker"]))
        out = io.StringIO()
        user = self.tmp / "starcode-home"
        user.mkdir(parents=True, exist_ok=True)
        (user / "config.json").write_text('{"schemaVersion": 1, "qStrategy": ["self-verified", "orca-worker"]}',
                                          encoding="utf-8")
        with contextlib.redirect_stdout(out):
            code = dispatch.main(["q-cli", "--laforge", self.LF, "--caps-dir", str(d)])
        self.assertEqual((code, out.getvalue().strip()), (1, "self-verified"))

    def test_q_strategy_opencode_subagent_skipped_with_warning(self):  # C4
        d = self.caps(codex="ok")
        warned: list[str] = []
        self.assertEqual(dispatch.q_cli(self.LF, None, d, strategies=["opencode-subagent", "orca-worker"],
                                        warn=warned.append), "codex")
        line = "q-cli: estratégia opencode-subagent ainda não implementada; seguindo para a próxima"
        self.assertEqual(warned, [line])
        self.write_user_config('{"schemaVersion": 1, "qStrategy": ["opencode-subagent", "orca-worker"]}')
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = dispatch.main(["q-cli", "--laforge", self.LF, "--caps-dir", str(d)])
        self.assertEqual((code, out.getvalue(), err.getvalue()), (0, "codex\n", line + "\n"))

    def test_q_strategy_nothing_available_is_self_verified(self):  # C5
        d = self.caps(codex="ok")
        self.assertIsNone(dispatch.q_cli(self.LF, None, d, strategies=["opencode-subagent"]))
        none_ok = self.caps(codex="unavailable", antigravity="unavailable", opencode="unavailable")
        self.assertIsNone(dispatch.q_cli(self.LF, None, none_ok, strategies=["orca-worker"]))
        for cfg, caps in (('["opencode-subagent"]', d), ('["orca-worker"]', none_ok)):
            self.write_user_config('{"schemaVersion": 1, "qStrategy": %s}' % cfg)
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = dispatch.main(["q-cli", "--laforge", self.LF, "--caps-dir", str(caps)])
            self.assertEqual((code, out.getvalue()), (1, "self-verified\n"), cfg)

    def test_q_strategy_worker_before_opencode_subagent_does_not_warn(self):  # ordem
        d = self.caps(codex="ok")
        warned: list[str] = []
        self.assertEqual(dispatch.q_cli(self.LF, None, d, strategies=["orca-worker", "opencode-subagent"],
                                        warn=warned.append), "codex")
        self.assertEqual(warned, [])
        self.write_user_config('{"schemaVersion": 1, "qStrategy": ["orca-worker", "opencode-subagent"]}')
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = dispatch.main(["q-cli", "--laforge", self.LF, "--caps-dir", str(d)])
        self.assertEqual((code, out.getvalue(), err.getvalue()), (0, "codex\n", ""))

    def write_user_config(self, text: str) -> None:
        user = self.tmp / "starcode-home"
        user.mkdir(parents=True, exist_ok=True)
        (user / "config.json").write_text(text, encoding="utf-8")

    def test_q_cli_command_reads_user_qstrategy(self):  # C6
        d = self.caps(codex="ok")

        def run():
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = dispatch.main(["q-cli", "--laforge", self.LF, "--caps-dir", str(d)])
            return code, out.getvalue()

        self.write_user_config('{"schemaVersion": 1, "qStrategy": ["self-verified"]}')
        self.assertEqual(run(), (1, "self-verified\n"))
        self.write_user_config('{"schemaVersion": 1, "qStrategy": ["self-verified", "self-verified"]}')  # invalid
        self.assertEqual(run(), (0, "codex\n"))
        self.write_user_config('{"schemaVersion": 1}')
        self.assertEqual(run(), (0, "codex\n"))
        self.write_user_config("not json")
        self.assertEqual(run(), (0, "codex\n"))

    def test_q_strategy_docs_match_implementation(self):  # C7
        root = Path(dispatch.__file__).resolve().parent.parent
        skill = (root / "skills/config/SKILL.md").read_text(encoding="utf-8")
        line = next(ln for ln in skill.splitlines() if "`qStrategy` (" in ln)
        self.assertIn("`qStrategy` (orca-worker, self-verified)", line)
        self.assertNotIn("opencode-subagent", skill)
        schema = (root / "schemas/config.md").read_text(encoding="utf-8")
        self.assertIn("`opencode-subagent` is accepted but skipped by `q-cli` (not implemented yet)", schema)
        execute = (root / "skills/engajar/references/execute.md").read_text(encoding="utf-8")
        self.assertIn("When the user config has `qStrategy`, `q-cli` follows that list in order", execute)

    def test_q_strategy_decisions_entry_and_changelog(self):  # C8
        root = Path(dispatch.__file__).resolve().parent.parent
        text = (root / "DECISIONS.md").read_text(encoding="utf-8")
        entry = next(e for e in re.split(r"^### ", text, flags=re.M) if e.startswith("SC-185:"))
        for field in ("**Problema**", "**Decisão**", "**Motivo**", "**Por que não é bug**"):
            self.assertIn("- " + field + ":", entry, field)
        decision = re.search(r"- \*\*Decisão\*\*:(.*?)(?=\n- \*\*|\Z)", entry, re.S).group(1)
        for r in range(1, 8):
            self.assertIn("(R%d)" % r, decision, "R%d" % r)
        for part in ("`load_user_config`", "`STARCODE_HOME`", "`self-verified`", "`opencode-subagent`", "`orca-worker`",
                     "q-cli: estratégia opencode-subagent ainda não implementada; seguindo para a próxima"):
            self.assertIn(part, decision, part)
        for name in ("test_q_strategy_none_keeps_current_order", "test_q_strategy_orca_worker_walks_cli_order",
                     "test_q_strategy_self_verified_first_wins",
                     "test_q_strategy_opencode_subagent_skipped_with_warning",
                     "test_q_strategy_nothing_available_is_self_verified", "test_q_cli_command_reads_user_qstrategy",
                     "test_q_strategy_docs_match_implementation", "test_q_strategy_decisions_entry_and_changelog",
                     "test_q_strategy_worker_before_opencode_subagent_does_not_warn"):
            self.assertIn(name, entry, name)
            self.assertTrue(hasattr(type(self), name), name)
        log = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## \[|\Z)", log, re.S | re.M).group(1)
        self.assertTrue([ln for ln in unreleased.splitlines() if ln.startswith("- ") and "qStrategy" in ln])

    def test_q_cli_differs_from_all_laforge_families(self):  # C29
        d = self.caps(codex="ok", antigravity="ok", opencode="ok")
        lfs = ["claude:claude-sonnet-5-5", "codex:gpt-6-luna"]
        self.assertEqual(dispatch.q_cli(lfs, None, d), "antigravity")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = dispatch.main(["q-cli", "--laforge", lfs[0], "--laforge", lfs[1], "--caps-dir", str(d)])
        self.assertEqual((code, out.getvalue().strip()), (0, "antigravity"))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):  # old positional form still works
            code = dispatch.main(["q-cli", lfs[0], "--laforge", lfs[1], "--caps-dir", str(d)])
        self.assertEqual((code, out.getvalue().strip()), (0, "antigravity"))
        d2 = self.caps(codex="ok", antigravity="unavailable", opencode="unavailable")
        self.assertIsNone(dispatch.q_cli(lfs, None, d2))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = dispatch.main(["q-cli", "--laforge", lfs[0], "--laforge", lfs[1], "--caps-dir", str(d2)])
        self.assertEqual((code, out.getvalue().strip()), (1, "self-verified"))

    def test_q_cli_self_verified_when_none(self):  # C19
        d = self.caps(codex="unavailable", antigravity="unavailable", opencode="unavailable")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = dispatch.main(["q-cli", "--laforge", "claude:claude-sonnet-5-5", "--caps-dir", str(d)])
        self.assertEqual((code, out.getvalue().strip()), (1, "self-verified"))

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


def make_tasks(specs: list[dict]) -> str:
    """tasks.md fixture: each spec has tid, deps, paths, alone (optional) and uses Linear PROJ-<n>."""
    out = ["# Demo: Tasks", "", "## Tasks", ""]
    for s in specs:
        n = s["tid"][1:]
        out += [f"### {s['tid']}: Ticket {n}", f"**Depends on**: {s.get('deps', 'none')}", f"**Requirements**: R{n}",
                "**Tests**: unit", "**Gate**: quick", f"**Linear**: PROJ-{n}"]
        if s.get("alone"):
            out.append("**Runs alone**: yes")
        paths = ", ".join(f"`{p}`" for p in s.get("paths", []))
        out += ["", "#### TASK", "Faz.", "", "#### CONTEXT", "Spec.", "", "#### BOUNDARIES"]
        if paths:
            out.append(f"May change: {paths}")
        out += ["", "#### RULES", "TDD.", "", "#### DELIVERY", "Commit.", ""]
    return "\n".join(out)


def entry(tid: str, pair: str = "claude:claude-sonnet-5-5") -> str:
    return f"{tid} · PROJ-{tid[1:]} · base abc1234 · {pair} · 2026-11-07T16:40:00Z"


class BatchTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_repo_config()
        self.fdir = self.repo / ".specs" / "features" / "demo"
        self.fdir.mkdir(parents=True)
        (self.fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        run_git(self.repo, "branch", "feature/demo")

    def tasks(self, specs: list[dict]) -> None:
        (self.fdir / "tasks.md").write_text(make_tasks(specs), encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "--allow-empty", "-m", "specs")
        run_git(self.repo, "branch", "-f", "feature/demo")

    def integrate(self, msg: str) -> None:
        run_git(self.repo, "checkout", "-q", "feature/demo")
        run_git(self.repo, "commit", "-q", "--allow-empty", "-m", msg)
        run_git(self.repo, "checkout", "-q", "main")

    def active(self, *entries: str) -> None:
        handoff.set_handoff("demo", self.repo, {"dispatched": "; ".join(entries)})

    def user_config(self, **fleet) -> None:
        cfg = json.loads((FIXTURES_DIR / "user-full.json").read_text(encoding="utf-8"))
        cfg["fleet"] = {"maxBatch": 3, "timeoutMinutes": 30, **fleet}
        home = Path(os.environ["STARCODE_HOME"])
        home.mkdir(parents=True, exist_ok=True)
        (home / "config.json").write_text(json.dumps(cfg), encoding="utf-8")

    def run_batch(self, **kw) -> dict:
        return dispatch.batch("demo", self.repo, **kw)

    def ids(self, res: dict) -> list[str]:
        return [b["ticket"] for b in res["batch"]]

    def reasons(self, res: dict) -> dict[str, str]:
        return {x["ticket"]: x["reason"] for x in res["excluded"]}

    def test_batch_skips_integrated_active_and_waiting_tickets(self):
        self.tasks([{"tid": "T1", "paths": ["a.py"]}, {"tid": "T2", "paths": ["b.py"]},
                    {"tid": "T3", "deps": "T2", "paths": ["c.py"]}, {"tid": "T4", "paths": ["d.py"]}])
        self.integrate("feat: a\n\nRefs: PROJ-1")
        self.active(entry("T2"))
        res = self.run_batch()
        self.assertEqual(self.ids(res), ["T4"])
        self.assertEqual(self.reasons(res), {"T3": "espera T2"})
        self.assertEqual([a["ticket"] for a in res["active"]], ["T2"])

    def test_batch_excludes_ticket_sharing_path_with_active(self):
        self.tasks([{"tid": "T1", "paths": ["app/a.py"]}, {"tid": "T2", "paths": ["app/a.py"]},
                    {"tid": "T3", "paths": ["app/b.py"]}, {"tid": "T4", "paths": ["app/b.py"]}])
        self.active(entry("T1"))
        res = self.run_batch()
        self.assertEqual(self.ids(res), ["T3"])
        self.assertEqual(self.reasons(res), {"T2": "arquivo em comum com T1: app/a.py",
                                             "T4": "arquivo em comum com T3: app/b.py"})

    def test_batch_sensitive_ticket_runs_alone_only_when_idle(self):
        self.tasks([{"tid": "T1", "paths": ["a.py"]}, {"tid": "T2", "paths": ["package-lock.json"]},
                    {"tid": "T3", "paths": ["c.py"], "alone": True},
                    {"tid": "T4", "paths": ["yarn.lock"], "alone": True}])
        res = self.run_batch()
        self.assertEqual(self.ids(res), ["T1"])
        self.assertEqual(self.reasons(res), {"T2": "roda sozinho: package-lock.json",
                                             "T3": "roda sozinho: Runs alone",
                                             "T4": "roda sozinho: yarn.lock"})
        # idle and first: the batch is that ticket alone
        self.tasks([{"tid": "T1", "paths": ["package-lock.json"]}, {"tid": "T2", "paths": ["b.py"]}])
        res = self.run_batch()
        self.assertEqual(self.ids(res), ["T1"])
        self.assertIn("roda sozinho", self.reasons(res)["T2"])
        # with an active worker the sensitive ticket stays out even when first
        self.tasks([{"tid": "T1", "paths": ["package-lock.json"]}, {"tid": "T2", "paths": ["b.py"]}])
        self.active(entry("T2"))
        res = self.run_batch()
        self.assertEqual(self.ids(res), [])
        self.assertEqual(self.reasons(res), {"T1": "roda sozinho: package-lock.json"})

    def test_batch_limit_counts_active_workers(self):
        self.tasks([{"tid": f"T{i}", "paths": [f"f{i}.py"]} for i in range(1, 5)])
        self.user_config(maxBatch=3)
        self.active(entry("T1"))
        res = self.run_batch()
        self.assertEqual(self.ids(res), ["T2", "T3"])
        self.assertEqual(self.reasons(res), {"T4": "limite de 3 workers ativos"})

    def test_batch_json_contract(self):
        self.tasks([{"tid": "T1", "paths": ["a.py"]}, {"tid": "T2", "deps": "T1", "paths": ["b.py"]}])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = dispatch.main(["batch", "demo", "--root", str(self.repo), "--json"])
        data = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(set(data), {"batch", "costTotal", "excluded", "active", "stalled"})
        self.assertEqual(set(data["batch"][0]), {"ticket", "linear", "title", "cli", "model", "cost"})
        self.assertEqual((data["batch"][0]["ticket"], data["batch"][0]["linear"]), ("T1", "PROJ-1"))
        self.assertEqual(data["excluded"], [{"ticket": "T2", "reason": "espera T1"}])
        self.assertEqual(data["active"], [])
        text = io.StringIO()
        with contextlib.redirect_stdout(text):
            dispatch.main(["batch", "demo", "--root", str(self.repo)])
        lines = text.getvalue().splitlines()
        self.assertTrue(lines[0].startswith("T1 PROJ-1"))
        self.assertTrue(lines[1].startswith("total: "))
        self.assertEqual(lines[2], "T2: espera T1")

    def test_batch_exit_codes(self):
        def code():
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return dispatch.main(["batch", "demo", "--root", str(self.repo)])
        self.assertEqual(code(), 2)  # no tasks.md
        self.tasks([{"tid": "T1", "paths": ["a.py"]}])
        self.assertEqual(code(), 0)
        self.active(entry("T1"))
        self.assertEqual(code(), 1)  # empty batch

    def test_batch_excludes_ticket_without_may_change(self):
        self.tasks([{"tid": "T1"}, {"tid": "T2", "paths": ["b.py"]}])
        res = self.run_batch()
        self.assertEqual(self.ids(res), ["T2"])
        self.assertEqual(self.reasons(res), {"T1": "sem May change"})

    def test_batch_round_robin_from_fleet_workers(self):
        pool = ["claude:claude-sonnet-5-5", "codex:gpt-6-luna", "opencode:opencode/mimo-v2.6-flash-free"]
        self.tasks([{"tid": f"T{i}", "paths": [f"f{i}.py"]} for i in range(1, 4)])
        self.user_config(workers=pool, maxBatch=4)
        self.active(entry("T1", pool[1]))
        res = self.run_batch()
        self.assertEqual([f"{b['cli']}:{b['model']}" for b in res["batch"]], [pool[2], pool[0]])
        # no pool: the effective LaForge (user config > crew.yaml)
        self.user_config()
        self.active("none")
        res = self.run_batch()
        self.assertEqual({(b["cli"], b["model"]) for b in res["batch"]}, {("claude", "claude-opus-5-5")})

    def test_batch_assign_overrides_pair(self):
        self.tasks([{"tid": "T1", "paths": ["a.py"]}, {"tid": "T2", "paths": ["b.py"]}])
        res = self.run_batch(assign=["T2=codex:gpt-6-luna"])
        by = {b["ticket"]: b for b in res["batch"]}
        self.assertEqual((by["T2"]["cli"], by["T2"]["model"]), ("codex", "gpt-6-luna"))
        self.assertNotEqual(by["T1"]["cli"], "codex")
        for bad in ("T2=semcli", "T2=foo:bar"):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = dispatch.main(["batch", "demo", "--root", str(self.repo), "--assign", bad])
            self.assertEqual(code, 2, bad)

    def test_batch_cost_total_counts_tiers(self):
        pool = ["claude:claude-sonnet-5-5", "claude:claude-sonnet-5-5", "opencode:opencode/mimo-v2.6-flash-free"]
        self.tasks([{"tid": f"T{i}", "paths": [f"f{i}.py"]} for i in range(1, 4)])
        res = self.run_batch(assign=[f"T{i}={p}" for i, p in enumerate(pool, 1)])
        self.assertEqual([b["cost"] for b in res["batch"]], ["$$", "$$", "grátis"])
        self.assertEqual(res["costTotal"], "2× $$ + 1× grátis")


class DispatchCliSubprocessTests(unittest.TestCase):
    def test_dispatch_cli_runs_as_subprocess(self):
        root = Path(__file__).resolve().parent.parent
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        for script in (root / "scripts" / "dispatch.py", root / "dist" / "claude" / "scripts" / "dispatch.py"):
            r = subprocess.run([sys.executable, str(script), "--help"], env=env,
                               capture_output=True, text=True, cwd=str(root))
            self.assertEqual(r.returncode, 0, f"{script}: {r.stderr}")


LINE = "travado: só restam workers atrasados (T1, T2): cancele com confirmação (passo 7) ou siga esperando"


class FrotaTravadaTests(BatchTests):
    def run_cli(self, *extra: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = dispatch.main(["batch", "demo", "--root", str(self.repo), *extra])
        return code, out.getvalue()

    def test_batch_travado(self):
        self.tasks([{"tid": "T1", "paths": ["a.py"]}, {"tid": "T2", "paths": ["b.py"]}])
        self.active(entry("T1") + " · disp_1 · blocked", entry("T2") + " · blocked")
        code, text = self.run_cli()
        self.assertEqual(code, 1)
        self.assertEqual(text.splitlines(), [LINE])
        code, js = self.run_cli("--json")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(js)["stalled"], ["T1", "T2"])
        self.assertEqual(json.loads(js)["batch"], [])

    def test_batch_nao_travado(self):
        self.tasks([{"tid": "T1", "paths": ["a.py"]}, {"tid": "T2", "paths": ["b.py"]}])
        # no active entry, batch with a ticket
        code, text = self.run_cli()
        self.assertEqual(code, 0)
        self.assertNotIn("travado:", text)
        self.assertEqual(json.loads(self.run_cli("--json")[1])["stalled"], [])
        # one active without blocked (overdue or not)
        self.active(entry("T1") + " · blocked", entry("T2"))
        code, text = self.run_cli()
        self.assertEqual(code, 1)
        self.assertNotIn("travado:", text)
        self.assertEqual(json.loads(self.run_cli("--json")[1])["stalled"], [])
        # blocked active but a ticket in the batch: not stalled
        self.tasks([{"tid": "T1", "paths": ["a.py"]}, {"tid": "T2", "paths": ["b.py"]}])
        self.active(entry("T1") + " · blocked")
        code, text = self.run_cli()
        self.assertEqual(code, 0)
        self.assertNotIn("travado:", text)
        self.assertEqual(json.loads(self.run_cli("--json")[1])["stalled"], [])
        # every ticket integrated, nothing active
        self.active("none")
        self.integrate("feat: a\n\nRefs: PROJ-1")
        self.integrate("feat: b\n\nRefs: PROJ-2")
        code, text = self.run_cli()
        self.assertEqual(code, 1)
        self.assertNotIn("travado:", text)
        self.assertEqual(json.loads(self.run_cli("--json")[1])["stalled"], [])

    def test_execute_travado(self):
        text = (ROOT / "skills" / "engajar" / "references" / "execute.md").read_text(encoding="utf-8")
        sec = text.split("## 2F.", 1)[1].split("\n## ", 1)[0]
        step1 = sec.split("1. **Batch.**", 1)[1].split("2. **Start", 1)[0]
        step10 = sec.split("10. **Next.**", 1)[1]
        for part in (step1, step10):
            self.assertIn("travado:", part)
            self.assertIn("cancel with confirmation", part)
            self.assertIn("step 7", part)
            self.assertIn("keep waiting", part)
        self.assertIn("recommendation", step1)
        self.assertIn("do not wait", step1)

    def test_decisions_frota_travada(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        m = re.search(r"^### SC-200:.*?(?=^### |\Z)", text, re.M | re.S)
        self.assertIsNotNone(m)
        entry_text = m.group(0)
        fields = {k: re.search(rf"^- \*\*{k}\*\*: (.+)$", entry_text, re.M) for k in
                  ("Problema", "Decisão", "Motivo", "Por que não é bug")}
        for k, v in fields.items():
            self.assertIsNotNone(v, k)
        decisao = fields["Decisão"].group(1)
        for term in ("`\"stalled\": [\"T<n>\", ...]`", "` · blocked`", "lista vazia", LINE.replace("(T1, T2)", "(<T…, separados por vírgula>)"),
                     "o código de saída continua 1", "`execute.md` (seção 2F, passos 1 e 10)", "cancelar com confirmação (passo 7)",
                     "seguir esperando", "recomendação"):
            self.assertIn(term, decisao, term)
        bug = fields["Por que não é bug"].group(1)
        for name in ("test_batch_travado", "test_batch_nao_travado", "test_execute_travado", "test_decisions_frota_travada"):
            self.assertIn(name, bug, name)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
        self.assertIn("(SC-200)", unreleased)
        self.assertIn("stalled", unreleased)
        self.assertIn("travado:", unreleased)


if __name__ == "__main__":
    unittest.main()
