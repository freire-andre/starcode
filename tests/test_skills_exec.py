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
        self.assertAll(REF, "do **not** integrate", "--attempt worker-<T>=fail")

    def test_execute_fleet_timeout_blocks_without_relaunch(self):  # R23
        self.assertAll(REF, "dispatch.py\" overdue <slug>", "`blocked` state of the config",
                       "`bloqueado: worker sem resposta após <N> min (dispatch <id>)`", "**one line**",
                       "` · blocked`", "**No automatic stop, abandon or redispatch.**",
                       "A late\n   `worker_done` is integrated", "back to `started`")

    def test_execute_fleet_cancel_preserves_worktree(self):  # R24
        self.assertAll(REF, "**Cancel** only with the user's confirmation", "worker-stop --dispatch <id>",
                       "`cancelado; worktree preservado: <path>`", "only\n   with a second confirmation")

    def test_execute_fleet_failure_returns_ticket_to_queue(self):  # R25
        self.assertAll(REF, "**Failure** (outcome failed, no report, red gate)", "`--attempt worker-<T>=fail`",
                       "`gate-<T>=fail`", "**returns to the queue**", "tickets that depend on it stay out")

    def test_execute_fleet_merge_conflict_continues(self):  # R26
        self.assertAll(REF, "**Merge conflict**: `git merge --abort`", "returns to the queue with the conflicting files",
                       "the\n   others go on", "options of section 3")

    def test_execute_fleet_next_batch_then_proofs(self):  # R27
        self.assertAll(REF, "No active entries left → run `batch` again", "Every ticket integrated → section 4 (proofs)")

    def test_execute_fleet_unavailable_in_mode_1(self):  # R28
        self.assertAll(REF, "`Frota indisponível no modo 1 (um só worktree)`", "go to section 7 (sequential)")
        self.assertAll(REF, "**Resume:** check each `**Dispatched:**` entry with `orca orchestration worker-show <dispatch>`")


if __name__ == "__main__":
    unittest.main()
