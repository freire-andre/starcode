from __future__ import annotations

import subprocess
import unittest
from types import SimpleNamespace

from helpers import TempRepoCase, run_git

import dispatch
import handoff
from test_dispatch import make_tasks

HANDOFF = "\n## Handoff\n**Phase:** execute\n**Integration branch:** feature/demo\n**Dispatched:** {d}\n"


def entry(tid: str, base: str) -> str:
    return f"{tid} · PROJ-{tid[1:]} · base {base} · claude:claude-sonnet-5-5 · 2026-11-07T16:40:00Z · ctx_{tid}"


class FakeGate:
    """Runs git and handoff.py for real; the gate is scripted and recorded in order with the git calls."""

    def __init__(self, code: int = 0, out: str = "VEREDITO: VERDE"):
        self.calls: list[list[str]] = []
        self.code = code
        self.out = out

    def __call__(self, cmd, **kw):
        self.calls.append(list(cmd))
        if len(cmd) > 1 and "run_gates.py" in cmd[1]:
            return SimpleNamespace(returncode=self.code, stdout=self.out, stderr="")
        return subprocess.run(cmd, **kw)

    def merges(self) -> list[int]:
        return [i for i, c in enumerate(self.calls) if c[:2] == ["git", "merge"] and "--abort" not in c]

    def gates(self) -> list[int]:
        return [i for i, c in enumerate(self.calls) if len(c) > 1 and "run_gates.py" in c[1]]


class SettleTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_repo_config()
        self.fdir = self.repo / ".specs" / "features" / "demo"
        self.fdir.mkdir(parents=True)
        (self.fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        self.base = self.publish("none")
        run_git(self.repo, "checkout", "-q", "-b", "feature/demo")

    def publish(self, dispatched: str) -> str:
        text = make_tasks([{"tid": "T1"}, {"tid": "T2"}]) + HANDOFF.format(d=dispatched)
        (self.fdir / "tasks.md").write_text(text, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "--allow-empty", "-m", "specs")
        return run_git(self.repo, "rev-parse", "--short", "HEAD")

    def set_dispatched(self, value: str) -> None:
        (self.fdir / "tasks.md").write_text(
            make_tasks([{"tid": "T1"}, {"tid": "T2"}]) + HANDOFF.format(d=value), encoding="utf-8")
        run_git(self.repo, "commit", "-q", "-am", "dispatch")

    def ticket_branch(self, name: str, tid: str, fname: str, text: str = "x\n") -> None:
        run_git(self.repo, "checkout", "-q", "-b", name)
        (self.repo / fname).write_text(text, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", f"feat: {tid}", "-m", f"Refs: PROJ-{tid[1:]}")
        run_git(self.repo, "checkout", "-q", "feature/demo")

    def fields(self) -> dict[str, str]:
        lines = (self.fdir / "tasks.md").read_text(encoding="utf-8").splitlines()
        return handoff.read_fields(lines, handoff.section_bounds(lines))

    def go(self, runner, ticket="T1", branch="ticket/t1"):
        out: list[str] = []
        code = dispatch.settle("demo", ticket, branch, self.repo, runner=runner, emit=out.append)
        return code, out

    def open_t1(self) -> None:
        self.set_dispatched(entry("T1", self.base))
        self.ticket_branch("ticket/t1", "T1", "a.txt")

    def test_settle_roda_gate_antes_do_merge(self):
        self.open_t1()
        fake = FakeGate()
        code, _ = self.go(fake)
        self.assertEqual(code, 0)
        self.assertEqual(len(fake.gates()), 1)
        self.assertLess(fake.gates()[0], fake.merges()[0])
        gate = fake.calls[fake.gates()[0]]
        self.assertEqual(gate[2:6], ["ticket", "demo", "T1", f"{self.base}..ticket/t1"])

    def test_settle_verde_integra_e_remove_entrada(self):
        self.open_t1()
        fake = FakeGate()
        code, out = self.go(fake)
        self.assertEqual(code, 0)
        head = run_git(self.repo, "rev-parse", "HEAD")
        short = run_git(self.repo, "rev-parse", "--short", "HEAD")
        self.assertEqual(out[-1], f"integrado T1 em feature/demo: {short}")
        self.assertEqual(run_git(self.repo, "log", "-1", "--format=%B").splitlines(),
                         ["merge: integra T1 (PROJ-1) em feature/demo", "", "Refs: PROJ-1"])
        self.assertEqual(len(run_git(self.repo, "log", "-1", "--format=%P").split()), 2)
        values = self.fields()
        self.assertEqual(values["dispatched"], "none")
        self.assertEqual(values["last integrated"], head)
        self.assertEqual(values["attempts"], "none")
        self.assertEqual(fake.calls[-2][-2:], ["--attempt", "worker-T1=ok"])

    def test_settle_gate_vermelho_nao_integra(self):
        self.open_t1()
        before = run_git(self.repo, "rev-parse", "HEAD")
        fake = FakeGate(1, "VEREDITO: VERMELHO\n  FALHA check_scope  arquivo fora do May change\n")
        code, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertEqual(out[0], "gate vermelho: T1")
        self.assertIn("FALHA check_scope  arquivo fora do May change", out)
        self.assertEqual(fake.merges(), [])
        self.assertEqual(run_git(self.repo, "rev-parse", "HEAD"), before)
        self.assertEqual(len(handoff.dispatch_entries(self.fields()["dispatched"])), 1)

    def test_settle_conflito_aborta(self):
        self.set_dispatched(entry("T1", self.base))
        self.ticket_branch("ticket/t1", "T1", "a.txt", "do ticket\n")
        (self.repo / "a.txt").write_text("do ramo\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "chore: a.txt")
        before = run_git(self.repo, "rev-parse", "HEAD")
        code, out = self.go(FakeGate())
        self.assertEqual(code, 1)
        self.assertEqual(out[-1], "conflito no merge de T1: a.txt")
        self.assertEqual(run_git(self.repo, "rev-parse", "HEAD"), before)
        self.assertEqual(run_git(self.repo, "status", "--porcelain"), "")
        self.assertEqual(len(handoff.dispatch_entries(self.fields()["dispatched"])), 1)

    def test_settle_recusa_sem_entrada_ou_ramo_errado(self):
        self.ticket_branch("ticket/t1", "T1", "a.txt")
        fake = FakeGate()
        code, out = self.go(fake)
        self.assertEqual(code, 2)
        self.assertTrue(out[0].startswith("settle recusado: "))
        self.assertIn("Dispatched", out[0])
        self.set_dispatched(entry("T1", self.base))
        run_git(self.repo, "checkout", "-q", "-b", "outro")
        code, out = self.go(fake)
        self.assertEqual(code, 2)
        self.assertTrue(out[0].startswith("settle recusado: "))
        self.assertIn("feature/demo", out[0])
        self.assertEqual(fake.gates(), [])
        self.assertEqual(fake.merges(), [])

    def test_settle_paralelo_remove_so_o_seu(self):
        self.set_dispatched(f"{entry('T1', self.base)}; {entry('T2', self.base)}")
        self.ticket_branch("ticket/t1", "T1", "a.txt")
        code, _ = self.go(FakeGate())
        self.assertEqual(code, 0)
        entries = handoff.dispatch_entries(self.fields()["dispatched"])
        self.assertEqual([handoff.entry_ticket(e) for e in entries], ["T2"])


if __name__ == "__main__":
    unittest.main()
