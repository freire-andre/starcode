from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
from datetime import datetime, timezone
from unittest import mock
from pathlib import Path
from types import SimpleNamespace

from helpers import TempRepoCase, run_git

import dispatch
import handoff
from test_dispatch import make_tasks

HANDOFF = "\n## Handoff\n**Phase:** execute\n**Integration branch:** feature/demo\n**Dispatched:** {d}\n"
RECEIPT = {"dispatch": {"id": "ctx_abc"}, "model": "claude-sonnet-5-5", "worktree": {"id": "wt-123"}}


class FakeOrca:
    """Runs git and handoff.py for real; scripts the Orca answers."""

    def __init__(self, fail: dict[str, str] | None = None, receipt: dict | None = None):
        self.calls: list[list[str]] = []
        self.fail = fail or {}
        self.receipt = RECEIPT if receipt is None else receipt

    def key(self, cmd: list[str]) -> str:
        if cmd[0] != "orca":
            return "handoff" if "handoff.py" in cmd[1] else "git"
        if cmd[1:3] == ["linear", "status"]:
            return "status"
        if cmd[1:3] == ["linear", "label"]:
            return "label"
        if cmd[1:3] == ["orchestration", "worker-start"]:
            return "worker-start"
        return f"{cmd[1]} {cmd[2]}"

    def __call__(self, cmd, **kw):
        self.calls.append(list(cmd))
        k = self.key(cmd)
        if k in ("handoff", "git"):
            return subprocess.run(cmd, **kw)
        if k in self.fail:
            return SimpleNamespace(returncode=1, stdout="", stderr=self.fail[k] + "\nsegunda linha")
        if k == "worker-start":
            return SimpleNamespace(returncode=0, stdout=json.dumps(self.receipt), stderr="")
        if k == "worktree create":
            return SimpleNamespace(returncode=0, stdout=json.dumps({"worktree": {"id": "wt-new"}}), stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def keys(self) -> list[str]:
        return [self.key(c) for c in self.calls]

    def orca(self) -> list[list[str]]:
        return [c for c in self.calls if c[0] == "orca"]


class FailSecondHandoff(FakeOrca):
    """The second handoff.py write (after worker-start) fails."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.writes = 0

    def __call__(self, cmd, **kw):
        if self.key(cmd) == "handoff" and "--dispatch-add" in cmd:
            self.writes += 1
            if self.writes == 2:
                self.calls.append(list(cmd))
                return SimpleNamespace(returncode=1, stdout="", stderr="disco cheio\nsegunda linha")
        return super().__call__(cmd, **kw)


class StartTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_repo_config()
        self.fdir = self.repo / ".specs" / "features" / "demo"
        self.fdir.mkdir(parents=True)
        (self.fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        self.publish(make_tasks([{"tid": "T1"}, {"tid": "T2"}]), "none")

    def publish(self, text: str, dispatched: str, handoff_text: str | None = None) -> None:
        body = text + (HANDOFF.format(d=dispatched) if handoff_text is None else handoff_text)
        (self.fdir / "tasks.md").write_text(body, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "--allow-empty", "-m", "specs")
        run_git(self.repo, "branch", "-f", "feature/demo")

    def dispatched(self) -> str:
        return handoff.read_fields(*self._lines())["dispatched"]

    def _lines(self):
        lines = (self.fdir / "tasks.md").read_text(encoding="utf-8").splitlines()
        return lines, handoff.section_bounds(lines)

    def go(self, runner, ticket="T1", cli="claude", model="claude-sonnet-5-5"):
        out: list[str] = []
        code, res = dispatch.start("demo", ticket, cli, model, self.repo, runner=runner, emit=out.append)
        return code, res, out

    def test_start_ordem_dos_passos(self):
        fake = FakeOrca()
        code, _, _ = self.go(fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.keys(), ["git", "handoff", "status", "label", "worker-start", "handoff",
                                       "worktree set"])
        sha = run_git(self.repo, "rev-parse", "--short", "feature/demo")
        first = fake.calls[1][fake.calls[1].index("--dispatch-add") + 1]
        self.assertTrue(first.startswith(f"T1 · PROJ-1 · base {sha} · claude:claude-sonnet-5-5 · "))
        self.assertEqual(fake.calls[2][1:], ["linear", "status", "set", "PROJ-1", "--to", "In Progress"])
        self.assertEqual(fake.calls[3][1:], ["linear", "label", "add", "PROJ-1", "--label", "crew:laforge"])
        ws = fake.calls[4]
        self.assertEqual(ws[1:3], ["orchestration", "worker-start"])
        for pair in (("--agent", "claude"), ("--model", "claude-sonnet-5-5"), ("--worktree", "new-child"),
                     ("--base-branch", "feature/demo"), ("--task-title", "T1: Ticket 1")):
            self.assertEqual(ws[ws.index(pair[0]) + 1], pair[1])
        self.assertIn("--json", ws)
        self.assertTrue(Path(ws[ws.index("--spec-file") + 1]).is_file())

    def test_start_regrava_entrada_com_dispatch_e_modelo(self):
        fake = FakeOrca(receipt={**RECEIPT, "model": "claude-opus-5-5"})
        self.go(fake)
        entry = self.dispatched()
        self.assertIn(" · claude:claude-opus-5-5 · ", entry)
        self.assertTrue(entry.endswith(" · ctx_abc"))
        self.assertEqual(len(handoff.dispatch_entries(entry)), 1)
        self.assertEqual(fake.calls[-1][1:], ["worktree", "set", "--worktree", "wt-123", "--linear-issue",
                                              "PROJ-1"])

    def test_start_opencode_cria_worktree_antes(self):
        fake = FakeOrca()
        self.go(fake, cli="opencode", model="m")
        keys = fake.keys()
        self.assertLess(keys.index("worktree create"), keys.index("worker-start"))
        create = fake.calls[keys.index("worktree create")]
        self.assertEqual(create[1:], ["worktree", "create", "--name", "T1", "--base-branch", "feature/demo",
                                      "--json"])
        ws = fake.calls[keys.index("worker-start")]
        self.assertEqual(ws[ws.index("--worktree") + 1], "wt-new")

    def test_start_recusa_sem_gravar(self):
        cases = [("T9", make_tasks([{"tid": "T1"}]), "none", None, "não existe"),
                 ("T1", make_tasks([{"tid": "T1"}]).replace("**Linear**: PROJ-1\n", ""), "none", None, "Linear"),
                 ("T1", make_tasks([{"tid": "T1"}]), "T1 · PROJ-1 · base abc1234 · claude:x · 2026-11-07T16:40:00Z",
                  None, "Dispatched"),
                 ("T1", make_tasks([{"tid": "T1"}]), "none", "\n## Handoff\n**Phase:** execute\n",
                  "Integration branch")]
        for ticket, text, dispatched, handoff_text, reason in cases:
            with self.subTest(reason=reason):
                self.publish(text, dispatched, handoff_text)
                before = (self.fdir / "tasks.md").read_text(encoding="utf-8")
                fake = FakeOrca()
                code, _, out = self.go(fake, ticket=ticket)
                self.assertEqual(code, 2)
                self.assertTrue(out[0].startswith("start recusado: "))
                self.assertIn(reason, out[0])
                self.assertEqual((self.fdir / "tasks.md").read_text(encoding="utf-8"), before)
                self.assertEqual(fake.orca(), [])
                self.assertNotIn("handoff", fake.keys())

    def test_start_worker_falha_remove_entrada(self):
        fake = FakeOrca(fail={"worker-start": "boom"})
        code, _, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertEqual(out[-1], "worker-start falhou: boom")
        self.assertEqual(self.dispatched(), "none")
        self.assertNotIn("worktree set", fake.keys())

    def test_start_executavel_ausente_remove_entrada(self):
        class SemOrca(FakeOrca):
            def __call__(self, cmd, **kw):
                if self.key(cmd) == "worker-start":
                    self.calls.append(list(cmd))
                    raise FileNotFoundError(2, "No such file", "orca")
                return super().__call__(cmd, **kw)

        fake = SemOrca()
        code, _, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertEqual(out[-1], "worker-start falhou: executável não encontrado: orca")
        self.assertEqual(self.dispatched(), "none")

    def test_start_linear_falha_vira_aviso(self):
        fake = FakeOrca(fail={"status": "sem rede", "label": "sem label", "worktree set": "sem vínculo"})
        code, _, out = self.go(fake)
        self.assertEqual(code, 0)
        for line in ("aviso: status In Progress: sem rede", "aviso: label crew:laforge: sem label",
                     "aviso: worktree set: sem vínculo"):
            self.assertIn(line, out)
        self.assertIn("worker-start", fake.keys())
        self.assertTrue(self.dispatched().endswith(" · ctx_abc"))

    def test_start_json(self):
        fake = FakeOrca()
        code, res, _ = self.go(fake)
        self.assertEqual(code, 0)
        self.assertEqual(res, {"ticket": "T1", "issue": "PROJ-1", "base": run_git(
            self.repo, "rev-parse", "--short", "feature/demo"), "dispatch": "ctx_abc",
            "worktree": "wt-123", "model": "claude-sonnet-5-5"})
        self.assertEqual(list(res), ["ticket", "issue", "base", "dispatch", "worktree", "model"])

    def test_start_paralelo_preserva_outra_entrada(self):
        self.go(FakeOrca())
        self.go(FakeOrca(receipt={**RECEIPT, "dispatch": {"id": "ctx_two"}}), ticket="T2")
        entries = handoff.dispatch_entries(self.dispatched())
        self.assertEqual([handoff.entry_ticket(e) for e in entries], ["T1", "T2"])
        values = {"dispatched": self.dispatched()}
        handoff.dispatch_remove(values, "T1")
        self.assertEqual([handoff.entry_ticket(e) for e in handoff.dispatch_entries(values["dispatched"])],
                         ["T2"])

    def test_start_segunda_gravacao_falha_sai_3(self):
        fake = FailSecondHandoff()
        code, _, out = self.go(fake)
        self.assertEqual(code, 3)
        entries = handoff.dispatch_entries(self.dispatched())
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].startswith("T1 · PROJ-1 · base "))
        self.assertNotIn("ctx_abc", entries[0])

    def test_start_exit_3_avisa_e_liga_worktree(self):
        fake = FailSecondHandoff()
        code, res, out = self.go(fake)
        self.assertEqual(code, 3)
        self.assertIn("worker ativo sem registro completo: T1 · ctx_abc · wt-123: handoff.py falhou: disco cheio",
                      out)
        self.assertEqual(fake.calls[-1][1:], ["worktree", "set", "--worktree", "wt-123", "--linear-issue",
                                              "PROJ-1"])
        self.assertEqual(res["dispatch"], "ctx_abc")
        self.assertEqual(list(res), ["ticket", "issue", "base", "dispatch", "worktree", "model"])


SPEC_MEDIA = """# Média: Spec

**Size**: MEDIUM
{linear}
## Scope

- Faz a coisa.

## Requirements

- **R1** - WHEN x THEN y.

## Checks

- **C1** - R1: teste prova y.
"""


class MediaStartTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_repo_config()
        self.fdir = self.repo / ".specs" / "features" / "media"
        self.fdir.mkdir(parents=True)

    def publish(self, linear: str = "**Linear**: PROJ-9\n", handoff_text: str | None = None,
                dispatched: str = "none") -> None:
        body = SPEC_MEDIA.format(linear=linear) + (
            HANDOFF.format(d=dispatched) if handoff_text is None else handoff_text)
        (self.fdir / "spec.md").write_text(body, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "--allow-empty", "-m", "specs")
        run_git(self.repo, "branch", "-f", "feature/media")

    def go(self, runner, ticket="PROJ-9"):
        out: list[str] = []
        code, res = dispatch.start("media", ticket, "claude", "claude-sonnet-5-5", self.repo, runner=runner,
                                   emit=out.append)
        return code, res, out

    def dispatched(self) -> str:
        lines = (self.fdir / "spec.md").read_text(encoding="utf-8").splitlines()
        return handoff.read_fields(lines, handoff.section_bounds(lines))["dispatched"]

    def test_start_media_despacha_t1(self):
        stamp = datetime(2026, 11, 13, 9, 8, 7, tzinfo=timezone.utc)
        for ticket in ("PROJ-9", "T1", "proj-9"):
            self.publish()
            sha = run_git(self.repo, "rev-parse", "--short", "feature/media")
            fake = FakeOrca()
            out: list[str] = []
            code, res = dispatch.start("media", ticket, "claude", "claude-sonnet-5-5", self.repo, runner=fake,
                                       emit=out.append, now=stamp)
            self.assertEqual(code, 0, ticket)
            self.assertEqual(res["ticket"], "T1")
            self.assertEqual(res["issue"], "PROJ-9")
            first = fake.calls[1][fake.calls[1].index("--dispatch-add") + 1]
            self.assertEqual(first, f"T1 · PROJ-9 · base {sha} · claude:claude-sonnet-5-5 · 2026-11-13T09:08:07Z")
            self.assertIn("worker-start", fake.keys())
            self.assertEqual(fake.keys(), ["git", "handoff", "status", "label", "worker-start", "handoff",
                                           "worktree set"])
            ws = fake.calls[fake.keys().index("worker-start")]
            self.assertEqual(ws[ws.index("--task-title") + 1], "T1: Média: Spec")
            self.assertEqual(self.dispatched(),
                             f"T1 · PROJ-9 · base {sha} · claude:claude-sonnet-5-5 · 2026-11-13T09:08:07Z · ctx_abc")

    def test_start_media_sem_linear_recusa(self):
        self.publish(linear="")
        before = (self.fdir / "spec.md").read_text(encoding="utf-8")
        fake = FakeOrca()
        code, _, out = self.go(fake, "T1")
        self.assertEqual(code, 2)
        self.assertEqual(out, ["start recusado: spec sem **Linear**:"])
        self.assertEqual(fake.calls, [])
        self.assertEqual((self.fdir / "spec.md").read_text(encoding="utf-8"), before)

    def test_media_ticket_errado_recusa(self):
        self.publish()
        fake = FakeOrca()
        code, _, out = self.go(fake, "PROJ-8")
        self.assertEqual(code, 2)
        self.assertEqual(out, ["start recusado: ticket PROJ-8 não é desta feature MÉDIA (use PROJ-9 ou T1)"])
        self.assertEqual(fake.calls, [])
        out2: list[str] = []
        code = dispatch.settle("media", "PROJ-8", "ticket/t1", self.repo, runner=fake, emit=out2.append)
        self.assertEqual(code, 2)
        self.assertEqual(out2, ["settle recusado: ticket PROJ-8 não é desta feature MÉDIA (use PROJ-9 ou T1)"])
        self.assertEqual(fake.calls, [])

    def test_main_arquivo_ausente_sai_2(self):
        self.publish()
        missing = self.fdir / "tasks.md"
        root = ["--root", str(self.repo)]
        cases = [(["next", "media", *root], "load_tasks"),
                 (["batch", "media", *root], "batch"),
                 (["brief", "media", "T1", "--out", str(self.repo / "b.md"), *root], "worker_brief"),
                 (["start", "media", "T1", "--cli", "claude", "--model", "m", *root], "start"),
                 (["settle", "media", "T1", "--branch", "ticket/t1", *root], "settle"),
                 (["q-brief", "media", "--base", "main", "--head", "HEAD", "--out", str(self.repo / "q.md"), *root],
                  "q_brief")]
        for argv, target in cases:
            with self.subTest(cmd=argv[0]):
                buf, err = io.StringIO(), io.StringIO()
                boom = FileNotFoundError(2, "No such file", str(missing))
                with mock.patch.object(dispatch, target, side_effect=boom),                         contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                    code = dispatch.main(argv)
                self.assertEqual(code, 2)
                self.assertEqual(err.getvalue().splitlines(), [f"dispatch: arquivo não encontrado: {missing}"])
                self.assertNotIn("Traceback", buf.getvalue() + err.getvalue())
        shutil.rmtree(self.fdir)
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            code = dispatch.main(["next", "media", *root])
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", buf.getvalue() + err.getvalue())

    def test_start_sem_ramo_aponta_modo_1(self):
        self.publish(handoff_text="\n## Handoff\n**Phase:** execute\n")
        fake = FakeOrca()
        code, _, out = self.go(fake)
        self.assertEqual(code, 2)
        self.assertEqual(out, ["start recusado: o Handoff não tem **Integration branch:** "
                               "(modo 1: siga o execute-modo-1.md, sem start)"])
        self.assertEqual(fake.calls, [])

    def test_start_entrada_aberta_aponta_dispatch_remove(self):
        self.publish(dispatched="T1 · PROJ-9 · base abc1234 · claude:claude-sonnet-5-5 · 2026-11-07T16:40:00Z")
        fake = FakeOrca()
        code, _, out = self.go(fake)
        self.assertEqual(code, 2)
        self.assertEqual(out, ["start recusado: T1 já tem entrada em Dispatched "
                               "(nova tentativa: handoff.py set media --dispatch-remove T1)"])
        self.assertEqual(fake.calls, [])

