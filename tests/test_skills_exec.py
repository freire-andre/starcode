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

    def test_execute_descreve_exit_3(self):
        start = REF.index("## 2. Dispatch one ticket")
        sec = REF[start:REF.index("\n## ", start + 1)]
        i = sec.index("**Exit 3**")
        item = sec[i:sec.index("\n4. ", i)]
        self.assertIn("`worker-start` succeeded but the second `Dispatched` write failed", item)
        self.assertIn('python "P/scripts/handoff.py" set <slug> --dispatch-add "<T> · ... · <dispatch id>"', item)
        self.assertIn("no new `start` for the same ticket", item)

    def test_execute_ref_dispatch_steps(self):  # R8, R11, R12
        self.assertAll(REF, "**or reuse `I` if it already exists**", "--integration-branch feature/<slug>` **before\nthe first dispatch**",
                       "dispatch.py\" start <slug> <T> --cli <laforge cli> --model <laforge model> --json",
                       "`worker-start` with a new child worktree", "`worktree set` link",
                       "orca orchestration check --wait --types worker_done --timeout-ms 3600000")
        self.assertAll(SKILL, "### 5b. Execute (Phase 3)", "references/execute.md")

    def test_execute_ref_integration_and_resume(self):  # R13-R17
        self.assertAll(REF, "do **not** integrate", "--attempt worker-<T>=fail",
                       "dispatch.py\" settle <slug> <T> --branch <ticket branch>", "`ticket` gate over the base recorded in the entry",
                       "git merge --no-ff",
                       "`git merge --abort`, `I` stays at the previous commit", "conflicting files",
                       "\"integrado em `feature/<slug>`\"", "**without asking the user**",
                       "orca orchestration worker-show --dispatch <id>",
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
        self.assertAll(REF, "Linear status and `crew:laforge` label",
                       "`review` state of the config", "\"pronto para revisão\"",
                       "`completed` only with the user's explicit confirmation", "**never in mode 1**")

    def test_execute_ref_mode1_and_no_stop(self):  # R32, R33, R37
        self.assertAll(REF, "## 7. Git mode 1 (degraded)", "**One worktree**", "**no integration branch and\n  no commits**",
                       "`git diff <B>` of the working\n  tree", "`degradada (modo 1)`",
                       "end of a ticket is never a stop, D29", "Stops: only the closed list")
        self.assertIn("`**Dispatched:**` not integrated", STATE)

    def test_execute_ref_q_cli_by_family(self):  # R18, R19
        self.assertAll(REF, "dispatch.py\" q-cli --laforge <laforge cli:model>", "`self-verified`",
                       "`**Verification:** self-verified`", "never hard-code")

    def test_execute_ref_opencode_and_q_cli(self):  # R20
        self.assertAll(REF, "orca worktree create --name <T> --base-branch feature/<slug>",
                       "`worker-start --agent opencode --model <laforge model> --worktree <that worktree>`",
                       "dispatch.py\" q-cli --laforge <laforge cli:model>")

    def test_execute_ref_integration_worktree(self):  # R21
        self.assertAll(REF, "worktree of `I`", "Orca worktree for `I`**", "Handoff, `proofs.md` and `verification.md`")

    def test_execute_ref_nested_depth_stop(self):  # R22
        self.assertAll(REF, "nested_worker_depth_exceeded", "Settings → Orchestration", "2 or more",
                       "does **not** count as an attempt", "agent-hooks-review-prompt", "Read the output of `start`")

    def test_execute_fleet_batch_confirmation(self):  # R13
        self.assertAll(REF, "## 2F. Fleet (v1.1)", "dispatch.py\" batch <slug> --json", "**Two or more**",
                       "one line per ticket (ticket, issue, CLI, model, cost tier)", "**one confirmation**",
                       "`--assign <T>=<cli>:<model>`", "**One ticket** → section 2 with that ticket, **no question**",
                       "**The batch comes first**")
        self.assertIn("2F", SKILL)

    def test_execute_fleet_worker_start_flags(self):  # R16
        self.assertAll(REF, "dispatch.py\" start <slug> <T> --cli <cli> --model <model> --json",
                       "writes the `Dispatched` entry before and after the `worker-start`",
                       "links the worktree", "**No `--deps`**",
                       "`model`\n   field of the `worker-start --json` receipt", "crew_live.py\" set laforge <n>")
        fleet = REF[REF.index("## 2F."):]
        self.assertLess(fleet.index("writes the `Dispatched` entry before"), fleet.index("**No `--deps`**"))
        self.assertNotIn("--deps`", fleet.replace("**No `--deps`**", ""))

    def test_execute_fleet_start_failure_isolated(self):  # R17
        self.assertAll(REF, "A `start` that fails", "entry already removed by the command",
                       "**other tickets go on**", "apply **only to that ticket**")

    def test_execute_fleet_start_exit_3(self):
        fleet = REF[REF.index("## 2F."):]
        step3 = fleet[fleet.index("3. **A `start` that fails**"):fleet.index("4. **Wait.**")]
        self.assertAll(step3, "**Exit 3**", "handoff.py\" set <slug> --dispatch-add",
                       "no new `start` for the same ticket", "**other tickets go on**")

    def test_execute_fleet_wait_uses_nearest_deadline(self):  # R20
        self.assertAll(REF, "check --wait --types worker_done,question --timeout-ms <ms until the nearest deadline>",
                       "`fleet.timeoutMinutes`", "only the wait\n   for the worker to **start**")

    def test_execute_fleet_integrates_on_arrival(self):  # R21
        self.assertAll(REF, "**Integrate on arrival.**", "dispatch.py\" settle <slug> <T> --branch <ticket branch>",
                       "`git merge --no-ff`", "**one at a time**", "sets `--last-integrated`",
                       "The other workers **keep running**", "`ticket` gate over the base recorded in that ticket's entry",
                       "never the current `HEAD` of `I`")

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
        self.assertAll(REF, "**Resume:** check each `**Dispatched:**` entry with `orca orchestration worker-show --dispatch <id>`")


if __name__ == "__main__":
    unittest.main()
