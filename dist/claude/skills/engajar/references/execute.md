# Execute: sequential tickets, integration and verification (plan 4, 4.3, 4.6, 4.7; D22, D23)

The Picard **only coordinates** (D23): every ticket is implemented by a LaForge worker with a clean
context, the verification by a Q worker of another model family. You run scripts, Orca and Git; you
never edit the feature's code. Records only through `scripts/handoff.py set` (D28). Report each step in
one line; worker output, gate reports and diffs stay out of the chat (F2-10).

Variables: `<slug>` the feature, `B` the repo config `baseBranch`, `I` = `feature/<slug>`, `P` =
`<plugin-root>`. Timeout of a worker wait: `3600000` ms unless the user asked for another.

## 0. Preconditions
- `python "P/scripts/gates/run_gates.py" execute <slug>` green; Handoff `**Phase:** published` (or
  `execute`/`review` when resuming).
- Git mode 2, 3 or 4 → this file as written. **Git mode 1 → section 7.**
- Models: LaForge and Q from the effective crew (session override > user config > `crew.yaml`). Compare
  them: `python "P/scripts/dispatch.py" family <laforge cli:model> --compare <q cli:model>`. `same` →
  warn in one line and plan `**Verification:** degraded` (step 5).

## 1. Integration branch
Create `I` from `B` **or reuse `I` if it already exists** (Git evidence wins over the Handoff):
`git branch feature/<slug> <B>` (no checkout needed). Then create **or reuse the Orca worktree for `I`**
(`orca worktree list --json`; if none has branch `I`, `orca worktree create --name <slug> --branch feature/<slug>
--base-branch feature/<slug> --json`). Every write of the Handoff, `proofs.md` and `verification.md` happens in
that worktree of `I`, never in the main worktree (the Handoff stays apart from the proofs). Then
`python "P/scripts/handoff.py" set <slug> --phase execute --integration-branch feature/<slug>` **before
the first dispatch**, and `python "P/scripts/crew_live.py" progress <slug>` (0 of N tickets; the live panel's bar,
F6-8).

## 2. Dispatch one ticket (sequential path)
**The batch comes first** (section 2F): run `dispatch.py batch` before this section. With one ticket in the
batch, or in Git mode 1, this section runs as written, without a question.
1. `python "P/scripts/dispatch.py" next <slug>` → the first ticket whose dependencies are integrated.
   Exit 3 (open dispatch) → step 6 (resume). Exit 1 with "todos os tickets integrados" → step 4.
2. `python "P/scripts/dispatch.py" brief <slug> <T> --out <temp>/<slug>-<T>.md`.
3. Record **before sending**: `python "P/scripts/handoff.py" set <slug> --dispatched "<T> · <ID> · base <sha of I>"`.
4. Move the issue to the `started` state of the repo config and add `crew:laforge`
   (`orca linear status set <ID> --to "<started>"`, `orca linear label add <ID> --label crew:laforge`).
5. Start the worker:

       orca orchestration worker-start --agent <laforge cli> --model <laforge model> \
         --worktree new-child --base-branch feature/<slug> --spec-file <temp>/<slug>-<T>.md \
         --task-title "<T>: <title>" --json

   If the LaForge CLI is `opencode`, it cannot create the child itself: first
   `orca worktree create --name <T> --base-branch feature/<slug> --json`, then
   `orca orchestration worker-start --agent opencode --model <laforge model> --worktree <that worktree> --spec-file <temp>/<slug>-<T>.md --task-title "<T>: <title>" --json`.
   If `worker-start` fails with `nested_worker_depth_exceeded` (Orca: "Sub-worker dispatch is not permitted at
   depth 2 (max 1)"), **stop** with one line: the Orca depth limit must be 2 or more (Settings → Orchestration).
   It does **not** count as an attempt of the breaker and no retry is made.
   If a Codex worker's `worker-start` fails with `agent-hooks-review-prompt` (or `agent_readiness` with pending
   hooks, e.g. "Agent startup blocked: agent-hooks-review-prompt"), **stop** the dispatch and show the trust
   step: open `/hooks` in Codex and approve the `starcode` hooks. Do **not** retry, do **not** use
   `--dangerously-bypass-hook-trust`, and it does **not** count as an attempt of the breaker.
   Then add the dispatch id and the `model` field of the result to `--dispatched`, and mark the worker as working:
   `python "P/scripts/crew_live.py" set laforge 1` (F6-7).
6. Link the new worktree to the issue: `orca worktree set --worktree <new worktree> --linear-issue <ID>`.
7. Wait: `orca orchestration check --wait --types worker_done --timeout-ms 3600000 --json`. The
   `worker_done` carries the worker's report (≤5 lines); record it with `--report "<T>: <report>"` and run
   `python "P/scripts/crew_live.py" set laforge 0` (also on failure or timeout).

## 2F. Fleet (v1.1): parallel tickets in one batch
**Git mode 1 → say `Frota indisponível no modo 1 (um só worktree)` and go to section 7 (sequential).**
Each worker is still a LaForge in its own child worktree; you coordinate and never edit code (D23).

1. **Batch.** `python "P/scripts/dispatch.py" batch <slug> --json`.
   - Exit 1 (nothing ready) → section 4 when every ticket is integrated, otherwise wait (step 4).
   - **One ticket** → section 2 with that ticket, **no question**.
   - **Two or more** → one message: one line per ticket (ticket, issue, CLI, model, cost tier), the total,
     and the excluded tickets with the reason, then **one confirmation**. A swap the user asks for becomes
     `--assign <T>=<cli>:<model>` and the `batch` is run again.
2. **Start, per ticket, in this order** (brief as in section 2 step 2):
   1. `python "P/scripts/handoff.py" set <slug> --dispatch-add "<T> · <ID> · base <sha of I> · <cli:model> · <UTC time>"` **before** the `worker-start`.
   2. Issue to `started` plus `crew:laforge`, then `orca orchestration worker-start --agent <cli> --model <model>
      --worktree new-child --base-branch feature/<slug> --spec-file <temp>/<slug>-<T>.md --task-title "<T>: <title>" --json`
      (OpenCode: create the worktree first, as in section 2 step 5). Its `--timeout-ms` is only the wait for the
      worker to **start**, not for the work.
   3. `--dispatch-add` again with the dispatch id and the `model` field of the receipt
      (`"<T> · <ID> · base <sha> · <cli:model> · <UTC time> · <dispatch id>"`).
   4. `orca worktree set --worktree <new worktree> --linear-issue <ID>`.
   5. **No `--deps`**: independence is already decided by `batch`; say so in the line of the reason.
   6. `python "P/scripts/crew_live.py" set laforge <n>` with the number of open entries, at every change.
3. **A `worker-start` that fails** for one ticket: `--dispatch-remove <T>`, one line with the reason, and the
   **other tickets go on**. The Codex trust stop (`agent-hooks-review-prompt`) and the nesting stop
   (`nested_worker_depth_exceeded`) apply **only to that ticket**; neither counts as an attempt.
4. **Wait.** `orca orchestration check --wait --types worker_done,question --timeout-ms <ms until the nearest deadline> --json`.
   The deadline of an entry is its dispatch time plus `fleet.timeoutMinutes` (default 30). A `question` is
   answered with `orca orchestration reply`; the others keep running.
5. **Integrate on arrival.** A `worker_done` with success: `python "P/scripts/gates/run_gates.py" ticket <slug> <T> <base sha recorded in that ticket's entry>..<ticket branch>`
   (the base is the one recorded at dispatch, never the current `HEAD` of `I`, which moves at every merge) and, if green,
   `git merge --no-ff` in the worktree of `I` as in section 3, **one merge at a time** (the next arrival waits
   for the previous merge). Then `--dispatch-remove <T>`, `--last-integrated <sha>`,
   `python "P/scripts/crew_live.py" progress <slug>`, the comment "integrado em `feature/<slug>`" and
   `crew_live.py set laforge <n>`. The other workers **keep running**.
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
10. **Next.** No active entries left → run `batch` again (step 1). Every ticket integrated → section 4 (proofs).

**Resume:** check each `**Dispatched:**` entry with `orca orchestration worker-show <dispatch>` (section 6)
before any new `batch`.

## 3. Check and integrate the ticket
- **Failure** (outcome failed, no report, or the wait timed out): do **not** integrate. Comment the reason
  in one line on the issue and count `python "P/scripts/handoff.py" set <slug> --attempt worker-<T>=fail`.
  A breaker error id the worker reported (`gate-...=n`) is counted the same way. Retry the ticket with a
  new dispatch (same brief plus the failure line) until it succeeds or the breaker opens.
- **Success**: run `python "P/scripts/gates/run_gates.py" ticket <slug> <T> <base sha>..<ticket branch>`
  (base sha = the HEAD of `I` recorded at dispatch). Red → treat as a failure (`--attempt gate-<T>=fail`)
  and redispatch with the gate lines. A `check_scope` error on `.specs/STATE.md` or `## Handoff` is
  never integrated (D28).
- Green → from the worktree of `I`, `git merge --no-ff <ticket branch> -m "merge: integra <T> (<ID>) em feature/<slug>" -m "Refs: <ID>"`
  (no extra authorization: it is local to the feature, D11).
- **Conflict** → `git merge --abort`, `I` stays at the previous commit, and stop with the list of
  conflicting files (options: redispatch the ticket rebased on `I`, or rethink the slicing).
- After the merge: `--last-integrated <sha> --attempt worker-<T>=ok --dispatched none`, then
  `python "P/scripts/crew_live.py" progress <slug>` (counts the integrated tickets from Git), comment on the issue
  "integrado em `feature/<slug>`" with the short hash, then go straight to step 2 for the next ticket
  **without asking the user** (end of a ticket is never a stop, D29).

## 4. Proofs and the Q
1. After the last ticket: `python "P/scripts/gates/run_gates.py" proofs <slug>` in the worktree of `I`
   (it writes `proofs.md`). Red → one LaForge dispatch with the failing rows, as in step 2.
2. Green → commit `proofs.md` (`docs(specs): provas (<slug>)` + `Refs`), then
   `python "P/scripts/handoff.py" set <slug> --phase review` and dispatch the Q.
3. Q brief: `python "P/scripts/dispatch.py" q-brief <slug> --base <B> --head <sha of I> --out <temp>/<slug>-q.md`.
4. Pick the Q CLI by family: `python "P/scripts/dispatch.py" q-cli --laforge <laforge cli:model> [--configured <q cli:model>]`
   (order: configured Q, codex, antigravity, opencode; first of another family with `orca_worker` ok; never hard-code
   the CLI). Output `self-verified` (exit 1) → no worker: run the `q` skill as a clean-context subagent and mark
   `**Verification:** self-verified`. Record `--dispatched "Q · <sha of I>"` and start the Q **in the existing worktree of `I`**; the default order is:

       orca orchestration worker-start --agent codex --worktree <worktree of I> --spec-file <temp>/<slug>-q.md --json
       orca orchestration worker-start --agent antigravity --model <gemini model> --worktree <worktree of I> --spec-file <temp>/<slug>-q.md --json

   **codex** first (check that its hooks are trusted, F0-1). If codex fails to start, **antigravity**
   with a Gemini model (`opencode` with `--model` when `q-cli` picked it). If all fail, run the `q` skill as a clean-context subagent and mark
   `**Verification:** self-verified` (degraded).
   Mark it: `python "P/scripts/crew_live.py" set q 1` after the start, `set q 0` after its `worker_done` (the Q
   brief is self-contained and does not update the panel itself).
5. Wait as in step 2.7. Then read the effective model with
   `orca orchestration worker-read <dispatch> --source auto` and write in `verification.md`
   `**Verifier**: <cli> · requested <model field of the result> · effective <model | unconfirmed>` (F0-2);
   same in `--report`.
6. **The Q writes only `verification.md`.** If its diff touches any other file, discard those extra
   changes (`git restore --source=HEAD -- <file>` for tracked files; delete new untracked ones) before
   committing `verification.md`, and cite the files in the review comment.

## 5. Post-Q cycle (4.6) and the end
- Open findings → **one** LaForge dispatch in the worktree of `I` with **all findings in one brief**;
  each fix is a commit with `Refs: <ID>` citing the finding. Then write the commit in each `Closed` cell.
- Rerun `run_gates.py proofs <slug>` and `run_gates.py done <slug>` on the new HEAD. **There is no second
  Q.** The Q is dispatched again only if a fix changes a requirement of the spec: then stop, propose the
  spec change, and dispatch the Q again only after the new approval.
- A finding still open after the cycle goes to the user with the finding and the evidence; the issues do
  not move to review.
- `run_gates.py done <slug>` green → move the issues to the `review` state of the config or, without one,
  comment "pronto para revisão" with HEAD, the proofs result and the Q verdict.
- Degraded (`self-verified`, `degraded`, same family or mode 1) → comment "verificação degradada" with the
  reason on the issues; the banner shows `Verificação: degradada (<slug>)`.
- `completed` only with the user's explicit confirmation in this session, with `run_gates.py done` green,
  and **never in mode 1**. Modes 3/4: push and PR follow `git-modes.md` (each confirmed right before).
- Then `--phase done` and `python "P/scripts/crew_live.py" progress <slug> --phase done` (100%).

## Text for the PR and the Linear comments (Uhura)
Whenever you open a PR or comment on Linear (start, integrated, blocked, cancelled, done), have the text
drafted by the `uhura` skill instead of writing it yourself, from `skills/uhura/references/pr-body.md` and
`skills/uhura/references/linear-comments.md`, handing it the facts (issue ID, diff summary, gate results,
Q verdict).
- **Claude:** a subagent with Uhura's model (`crew.yaml`) that follows the skill.
- **Other CLIs:** the session itself follows the skill.
In both cases Uhura returns text only: you confirm it and run `gh pr create` and `orca linear comment`
yourself, as `git-modes.md` requires.

## 6. Resume and the circuit breaker (D27)
- On resume with a `**Dispatched:**` not integrated: `orca orchestration worker-show <dispatch>` before
  anything else. Running → wait (step 2.7). Finished → step 3. **Never start a second worker for the same
  ticket while the first is not closed** (`worker-stop` first, with a line to the user).
- `handoff.py` prints `DISJUNTOR ABERTO` on the 3rd failure of the same error id: record nothing more,
  make no 4th attempt, and stop with the 3 attempts (from `**Reports:**`) and two exits:
  (a) rethink the approach (back to Spock/Data when the problem is design), (b) go back to the last
  integrated commit of `I` (`**Last integrated:**`). With the user's choice, `--breaker closed`.
- A session that starts with `**Breaker:** open` proposes these two exits before any dispatch.
- Stops: only the closed list (STARCODE.md, D29). Ordinary technical errors are fixed and counted.

## 7. Git mode 1 (degraded)
- **One worktree** (the main issue's), tickets in sequence in the same tree, **no integration branch and
  no commits**. Dispatch with `--worktree <that worktree>`; skip `run_gates.py ticket` (no range) and
  the merge; compare `git status` before and after each worker instead.
- `run_gates.py proofs` marks `**Tree**: dirty (modo 1)`. The Q receives `git diff <B>` of the working
  tree: `q-brief --head HEAD`, then append to the brief the line "Modo Git 1: não há commits; use
  `git diff <B>` (árvore de trabalho) no lugar do intervalo."
- `verification.md` gets `**Verification:** degraded`; each finding is closed with
  `degradada (modo 1)` in `Closed`. The result is shown as degraded verification and the issue **never**
  goes to completed.

## 8. MEDIUM and SMALL
One LaForge worker in a new child worktree from the current branch; the brief is the spec's
`## Checks` (MEDIUM) or the inline checks (SMALL) plus the worker rules of `dispatch.py brief`. Integrate
as in step 3, with the gate `run_gates.py ticket <slug> <ID> <base>..<head>` using the spec's `**May change**:` (no tasks.md), then steps 4–5. Progress without tasks.md is one ticket:
`crew_live.py progress <slug> --done 0 --total 1` at dispatch, `--done 1 --total 1` after the merge.
