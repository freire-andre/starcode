"""Content tests for the Picard execution flow (engajar + references/execute.md)."""
from __future__ import annotations

import unittest

from helpers import ROOT

REF = (ROOT / "skills" / "engajar" / "references" / "execute.md").read_text(encoding="utf-8")
SKILL = (ROOT / "skills" / "engajar" / "SKILL.md").read_text(encoding="utf-8")
STATE = (ROOT / "skills" / "engajar" / "references" / "state-format.md").read_text(encoding="utf-8")


class ExecuteReferenceTests(unittest.TestCase):
    def assertAll(self, text: str, *parts: str) -> None:
        for part in parts:
            self.assertIn(part, text)

    def test_execute_ref_dispatch_steps(self):  # R8, R11, R12
        self.assertAll(REF, "**or reuse `I` if it already exists**", "--integration-branch feature/<slug>` **before\nthe first dispatch**",
                       "Record **before sending**", "orca orchestration worker-start --agent <laforge cli> --model <laforge model>",
                       "--worktree new-child --base-branch feature/<slug> --spec-file",
                       "orca worktree set --worktree <new worktree> --linear-issue <ID>",
                       "orca orchestration check --wait --types worker_done --timeout-ms 3600000")
        self.assertAll(SKILL, "### 5b. Execute (Phase 3)", "references/execute.md")

    def test_execute_ref_integration_and_resume(self):  # R13-R17
        self.assertAll(REF, "do **not** integrate", "--attempt worker-<T>=fail",
                       "run_gates.py\" ticket <slug> <T> <base sha>..<ticket branch>", "git merge --no-ff",
                       "`git merge --abort`, `I` stays at the previous commit", "conflicting files",
                       "\"integrado em `feature/<slug>`\"", "**without asking the user**",
                       "orca orchestration worker-show <dispatch>",
                       "**Never start a second worker for the same\n  ticket while the first is not closed**")

    def test_execute_ref_q_dispatch(self):  # R18, R20, R23
        self.assertAll(REF, "run_gates.py\" proofs <slug>", "--phase review",
                       "**codex** first", "**antigravity**", "`**Verification:** self-verified`",
                       "**The Q writes only `verification.md`.**", "discard those extra\n   changes",
                       "dispatch.py\" q-brief <slug>")

    def test_execute_ref_post_q_cycle(self):  # R24-R27
        self.assertAll(REF, "**all findings in one brief**", "`Refs: <ID>` citing the finding",
                       "**There is no second\n  Q.**", "propose the\n  spec change",
                       "goes to the user with the finding and the evidence")

    def test_execute_ref_linear_states(self):  # R28, R29, R31
        self.assertAll(REF, "`started` state of the repo config and add `crew:laforge`",
                       "`review` state of the config", "\"pronto para revisão\"",
                       "`completed` only with the user's explicit confirmation", "**never in mode 1**")

    def test_execute_ref_mode1_and_no_stop(self):  # R32, R33, R37
        self.assertAll(REF, "## 7. Git mode 1 (degraded)", "**One worktree**", "**no integration branch and\n  no commits**",
                       "`git diff <B>` of the working\n  tree", "`degradada (modo 1)`",
                       "end of a ticket is never a stop, D29", "Stops: only the closed list")
        self.assertIn("`**Dispatched:**` not integrated", STATE)


if __name__ == "__main__":
    unittest.main()
