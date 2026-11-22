# Execute: Despacho, frota e integração

Variables and preconditions: see `execute.md` (sections 0 and 1).

## 2. Dispatch one ticket (sequential path)
**The batch comes first** (section 2F): run `dispatch.py batch` before this section. With one ticket in the
batch, or in Git mode 1, this section runs as written, without a question.
1. `python "P/scripts/dispatch.py" next <slug>` → the first ticket whose dependencies are integrated.
   Exit 3 (open dispatch) → step 6 (resume). Exit 1 with "todos os tickets integrados" → step 4.
2. `python "P/scripts/dispatch.py" brief <slug> <T> --out <temp>/<slug>-<T>.md`.
3. Start the worker in one command (brief, `Dispatched` entry, Linear status and `crew:laforge` label,
   `worker-start` with a new child worktree, the entry again with the dispatch id and model, and the
   `worktree set` link; OpenCode gets its worktree created first by the command):

       python "P/scripts/dispatch.py" start <slug> <T> --cli <laforge cli> --model <laforge model> --json

   For an OpenCode CLI the command first runs `orca worktree create --name <T> --base-branch feature/<slug> --json`
   and then `worker-start --agent opencode --model <laforge model> --worktree <that worktree>`, because OpenCode
   cannot create the child itself. The effective model of the worker is the `model` field of the
   `worker-start --json` receipt, which `start` records in the `Dispatched` entry. Exit 2 = refused; exit 1 = `worker-start` failed (entry removed).
   **Exit 3** = the worker is running (`worker-start` succeeded but the second `Dispatched` write failed): the
   first entry stays, `start` prints `worker ativo sem registro completo: <T> · <dispatch id> · <worktree>: <error>`
   and still links the worktree; with `--json` it prints the receipt object. Complete the entry with
   `python "P/scripts/handoff.py" set <slug> --dispatch-add "<T> · ... · <dispatch id>"` (the same entry, with the
   dispatch id as the last field) and wait for the worker as usual, with no new `start` for the same ticket.
4. Read the output of `start`. If `worker-start` failed with `nested_worker_depth_exceeded` (Orca: "Sub-worker
   dispatch is not permitted at depth 2 (max 1)"), **stop** with one line: the Orca depth limit must be 2 or more
   (Settings → Orchestration). It does **not** count as an attempt of the breaker and no retry is made.
   If a Codex worker's `worker-start` failed with `agent-hooks-review-prompt` (or `agent_readiness` with pending
   hooks, e.g. "Agent startup blocked: agent-hooks-review-prompt"), **stop** the dispatch and show the trust
   step: open `/hooks` in Codex and approve the `starcode` hooks. Do **not** retry, do **not** use
   `--dangerously-bypass-hook-trust`, and it does **not** count as an attempt of the breaker.
5. Mark the worker as working: `python "P/scripts/crew_live.py" set laforge 1` (F6-7).
6. (Done by `start`: the worktree is already linked to the issue.)
7. Wait: `orca orchestration check --wait --types worker_done --timeout-ms 3600000 --json`. The
   `worker_done` carries the worker's report (≤5 lines); record it with `--report "<T>: <report>"` and run
   `python "P/scripts/crew_live.py" set laforge 0` (also on failure or timeout).

## 2F. Fleet (v1.1): parallel tickets in one batch
**Git mode 1 → say `Frota indisponível no modo 1 (um só worktree)` and go to section 7 (sequential).**
Each worker is still a LaForge in its own child worktree; you coordinate and never edit code (D23).

1. **Batch.** `python "P/scripts/dispatch.py" batch <slug> --json`.
   - Exit 1 (nothing ready) → section 4 when every ticket is integrated, otherwise wait (step 4). **Exception:
     the text has the line `travado:` (JSON `stalled` not empty: only overdue workers are left) → do not wait:
     stop with one message listing the `stalled` tickets and two options, **cancel with confirmation** (step 7)
     or **keep waiting**, with your recommendation, and act on the answer.**
   - **One ticket** → section 2 with that ticket, **no question**.
   - **Two or more** → one message: one line per ticket (ticket, issue, CLI, model, cost tier), the total,
     and the excluded tickets with the reason, then **one confirmation**. A swap the user asks for becomes
     `--assign <T>=<cli>:<model>` and the `batch` is run again.
2. **Start, per ticket:** `python "P/scripts/dispatch.py" start <slug> <T> --cli <cli> --model <model> --json`
   (it writes the `Dispatched` entry before and after the `worker-start`, moves the issue to `started` with
   `crew:laforge` and links the worktree; the brief is made by the command). The effective model is the `model`
   field of the `worker-start --json` receipt, recorded by `start`. A `worker-start` timeout is only the wait
   for the worker to **start**, not for the work.
   1. **No `--deps`**: independence is already decided by `batch`; say so in the line of the reason.
   2. `python "P/scripts/crew_live.py" set laforge <n>` with the number of open entries, at every change.
3. **A `start` that fails** (exit 1, entry already removed by the command) for one ticket: one line with the
   reason, and the **other tickets go on**. The Codex trust stop (`agent-hooks-review-prompt`) and the nesting
   stop (`nested_worker_depth_exceeded`), read in the output of `start`, apply **only to that ticket**; neither
   counts as an attempt.
   **Exit 3** (worker running, entry without the dispatch id, as in section 2) for one ticket: complete the entry
   with `python "P/scripts/handoff.py" set <slug> --dispatch-add "<T> · ... · <dispatch id>"` (the dispatch id as
   the last field), with no new `start` for the same ticket; the **other tickets go on**.
4. **Wait.** `orca orchestration check --wait --types worker_done,question --timeout-ms <ms until the nearest deadline> --json`.
   The deadline of an entry is its dispatch time plus `fleet.timeoutMinutes` (default 30). A `question` is
   answered with `orca orchestration reply`; the others keep running.
5. **Integrate on arrival.** A `worker_done` with success: in the worktree of `I`,
   `python "P/scripts/dispatch.py" settle <slug> <T> --branch <ticket branch>`, **one at a time** (the next
   arrival waits for the previous one). It runs the `ticket` gate over the base recorded in that ticket's entry
   (never the current `HEAD` of `I`), the `git merge --no-ff`, and removes the entry, sets `--last-integrated`
   and `worker-<T>=ok`. Then `python "P/scripts/crew_live.py" progress <slug>`, the comment "integrado em
   `feature/<slug>`" and `crew_live.py set laforge <n>`. The other workers **keep running**.
6. **Overdue.** After each wait run `python "P/scripts/dispatch.py" overdue <slug>`. For each entry: the
   `blocked` state of the config, or, without one, the comment `bloqueado: worker sem resposta após <N> min (dispatch <id>)`.
   Warn in **one line**; the entry stays with ` · blocked`. **No automatic stop, abandon or redispatch.** A late
   `worker_done` is integrated as in step 5 and the issue goes back to `started`.
7. **Cancel** only with the user's confirmation: `orca orchestration worker-stop --dispatch <id>`,
   `--dispatch-remove <T>`, the comment `cancelado; worktree preservado: <path>`. Remove the worktree only
   with a second confirmation.
8. **Failure** (outcome failed, no report, red gate): `--dispatch-remove <T>`, `--attempt worker-<T>=fail`
   (or `gate-<T>=fail`), a comment with the reason, and the ticket **returns to the queue** for the next
   `batch`. The others go on; tickets that depend on it stay out of the batch.
9. **Merge conflict**: `git merge --abort`; the ticket returns to the queue with the conflicting files; the
   others go on. The summary at the end of the batch gives the options of section 3.
10. **Next.** No active entries left → run `batch` again (step 1). If `batch` says `travado:` (only overdue
    workers left), stop with the two options of step 1 (cancel with confirmation, step 7, or keep waiting). Every ticket integrated → section 4 (proofs).

**Resume:** check each `**Dispatched:**` entry with `orca orchestration worker-show --dispatch <id>` (section 6)
before any new `batch`.

## 3. Check and integrate the ticket
- **Failure** (outcome failed, no report, or the wait timed out): do **not** integrate. Comment the reason
  in one line on the issue and count `python "P/scripts/handoff.py" set <slug> --attempt worker-<T>=fail`.
  A breaker error id the worker reported (`gate-...=n`) is counted the same way. Retry the ticket with a
  new dispatch (same brief plus the failure line) until it succeeds or the breaker opens. The failed
  dispatch still has its entry, and `start` refuses a ticket that has one (exit 2), so first remove it:
  `python "P/scripts/handoff.py" set <slug> --dispatch-remove <T>`, and only then run the new
  `dispatch.py start` of step 2.3.
- **Success**: from the worktree of `I`, `python "P/scripts/dispatch.py" settle <slug> <T> --branch <ticket branch>`
  runs the `ticket` gate over the base recorded in the entry and, if green, the `git merge --no-ff` (no extra
  authorization: it is local to the feature, D11). Exit 1 with a red gate → treat as a failure
  (`--attempt gate-<T>=fail`) and redispatch with the gate lines. A `check_scope` error on `.specs/STATE.md` or
  `## Handoff` is never integrated (D28).
- **Conflict** (`settle` exits 1) → it ran `git merge --abort`, `I` stays at the previous commit, and stop with the list of
  conflicting files (options: redispatch the ticket rebased on `I`, or rethink the slicing).
- After `settle` (it already set `--last-integrated`, `worker-<T>=ok` and removed the entry): run
  `python "P/scripts/crew_live.py" progress <slug>` (counts the integrated tickets from Git), comment on the issue
  "integrado em `feature/<slug>`" with the short hash, then go straight to step 2 for the next ticket
  **without asking the user** (end of a ticket is never a stop, D29).
