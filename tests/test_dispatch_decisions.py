from __future__ import annotations

import re
import unittest
from pathlib import Path

from helpers import TempRepoCase, run_git

import dispatch
from test_dispatch import make_tasks

ROOT = Path(__file__).resolve().parents[1]
RULE = ("- Nunca desligue a assinatura de commits (commit.gpgsign false, --no-gpg-sign) em código de produto; "
        "só repositórios Git temporários de teste podem fazê-lo.")


class DispatchDecisionsTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_repo_config()
        self.fdir = self.repo / ".specs" / "features" / "demo"
        self.fdir.mkdir(parents=True)
        (self.fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        run_git(self.repo, "branch", "feature/demo")

    def publish(self, text: str) -> None:
        (self.fdir / "tasks.md").write_text(text, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "--allow-empty", "-m", "specs")
        run_git(self.repo, "branch", "-f", "feature/demo")

    def may_line(self, ticket: str) -> str:
        text = dispatch.worker_brief("demo", ticket, self.repo)
        return next(ln for ln in text.splitlines() if ln.startswith("May change:"))

    def test_brief_acrescenta_decisions_com_scripts(self):
        text = make_tasks([{"tid": "T1", "paths": []}]).replace(
            "#### BOUNDARIES\n", "#### BOUNDARIES\nMay change: scripts/x.py, dist/\n")
        self.publish(text)
        self.assertEqual(self.may_line("T1"), "May change: scripts/x.py, dist/, DECISIONS.md")
        self.assertIn("May change: scripts/x.py, dist/\n", (self.fdir / "tasks.md").read_text(encoding="utf-8"))
        self.publish(make_tasks([{"tid": "T1", "paths": ["scripts/x.py", "dist/"]}]))
        self.assertEqual(self.may_line("T1"), "May change: `scripts/x.py`, `dist/`, `DECISIONS.md`")

    def test_brief_sem_scripts_ou_com_decisions_nao_muda(self):
        self.publish(make_tasks([{"tid": "T1", "paths": ["app/a.py", "tests/"]},
                                 {"tid": "T2", "paths": ["scripts/y.py", "DECISIONS.md"]}]))
        self.assertEqual(self.may_line("T1"), "May change: `app/a.py`, `tests/`")
        self.assertEqual(self.may_line("T2"), "May change: `scripts/y.py`, `DECISIONS.md`")

    def test_batch_separa_tickets_de_scripts(self):
        self.publish(make_tasks([{"tid": "T1", "paths": ["scripts/a.py"]},
                                 {"tid": "T2", "paths": ["scripts/b.py"]},
                                 {"tid": "T3", "paths": ["app/c.py"]}]))
        res = dispatch.batch("demo", self.repo)
        self.assertEqual([b["ticket"] for b in res["batch"]], ["T1", "T3"])
        reasons = {x["ticket"]: x["reason"] for x in res["excluded"]}
        self.assertEqual(list(reasons), ["T2"])
        self.assertIn("DECISIONS.md", reasons["T2"])
        self.assertIn("T1", reasons["T2"])

    def test_brief_traz_regra_de_assinatura(self):
        self.publish(make_tasks([{"tid": "T1", "paths": ["app/a.py"]}]))
        self.assertIn(RULE, dispatch.worker_brief("demo", "T1", self.repo).splitlines())


class DecisionsFileTests(unittest.TestCase):
    def test_decisions_registra_os_itens_de_scripts(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entries = re.split(r"^### ", text, flags=re.M)
        f12 = "\n".join(e for e in entries if e.startswith("F12-"))
        for item in ("handoff.py", "check_proofs.py", "dispatch.py brief", "dispatch.py start",
                     "dispatch.py settle", "validate_tasks.py"):
            self.assertIn(item, f12, item)


if __name__ == "__main__":
    unittest.main()
