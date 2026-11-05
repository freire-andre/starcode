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
`git branch feature/<slug> <B>` (no checkout needed). Then
`python "P/scripts/handoff.py" set <slug> --phase execute --integration-branch feature/<slug>` **before
the first dispatch**.

## 2. Dispatch one ticket (one at a time per feature)
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

   Then add the dispatch id and the `model` field of the result to `--dispatched`.
6. Link the new worktree to the issue: `orca worktree set --worktree <new worktree> --linear-issue <ID>`.
7. Wait: `orca orchestration check --wait --types worker_done --timeout-ms 3600000 --json`. The
   `worker_done` carries the worker's report (≤5 lines); record it with `--report "<T>: <report>"`.

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
- After the merge: `--last-integrated <sha> --attempt worker-<T>=ok --dispatched none`, comment on the issue
  "integrado em `feature/<slug>`" with the short hash, then go straight to step 2 for the next ticket
  **without asking the user** (end of a ticket is never a stop, D29).

## 4. Proofs and the Q
1. After the last ticket: `python "P/scripts/gates/run_gates.py" proofs <slug>` in the worktree of `I`
   (it writes `proofs.md`). Red → one LaForge dispatch with the failing rows, as in step 2.
2. Green → commit `proofs.md` (`docs(specs): provas (<slug>)` + `Refs`), then
   `python "P/scripts/handoff.py" set <slug> --phase review` and dispatch the Q.
3. Q brief: `python "P/scripts/dispatch.py" q-brief <slug> --base <B> --head <sha of I> --out <temp>/<slug>-q.md`.
4. Record `--dispatched "Q · <sha of I>"` and start the Q **in the existing worktree of `I`**, in this order:

       orca orchestration worker-start --agent codex --worktree <worktree of I> --spec-file <temp>/<slug>-q.md --json
       orca orchestration worker-start --agent antigravity --model <gemini model> --worktree <worktree of I> --spec-file <temp>/<slug>-q.md --json

   **codex** first (check that its hooks are trusted, F0-1). If codex fails to start, **antigravity**
   with a Gemini model. If both fail, run the `q` skill as a clean-context subagent and mark
   `**Verification:** self-verified` (degraded).
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
- Then `--phase done`.

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
as in step 3 (no `check_scope`: there is no tasks.md), then steps 4–5.
