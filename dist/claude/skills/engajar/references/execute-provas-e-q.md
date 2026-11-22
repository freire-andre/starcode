# Execute: Provas e o Q

Variables and preconditions: see `execute.md` (sections 0 and 1).

## 4. Proofs and the Q
1. After the last ticket: `python "P/scripts/gates/run_gates.py" proofs <slug>` in the worktree of `I`
   (it writes `proofs.md`). Red → one LaForge dispatch with the failing rows, as in step 2.
2. Green → commit `proofs.md` (`docs(specs): provas (<slug>)` + `Refs`), then
   `python "P/scripts/handoff.py" set <slug> --phase review --dispatched "Q · <sha of I>"` and **commit the Handoff** (`docs(specs): handoff antes do Q (<slug>)` + `Refs`)
   before any `worker-start` of the Q, with every other `handoff.py set` of this step in the same commit: the Q must find a clean tree, and no `handoff.py set` runs between this commit and the Q's `worker_done` (SC-181, W2).
   Then dispatch the Q.
3. Q brief: `python "P/scripts/dispatch.py" q-brief <slug> --base <B> --head <sha of I> --out <temp>/<slug>-q.md`.
4. Pick the Q CLI by family: `python "P/scripts/dispatch.py" q-cli --laforge <laforge cli:model> [--configured <q cli:model>]`
   (order: configured Q, codex, antigravity, opencode; first of another family with `orca_worker` ok; never hard-code
   the CLI). When the user config has `qStrategy`, `q-cli` follows that list in order (`orca-worker` = this order, `self-verified` = stop, `opencode-subagent` = skipped with a warning). Output `self-verified` (exit 1) → no worker: run the `q` skill as a clean-context subagent and mark
   `**Verification:** self-verified`. The Q's `Dispatched` entry is already in the Handoff commit of step 2 (no worker: `--dispatch-remove Q` after the subagent ends). Start the Q **in the existing worktree of `I`**; the default order is:

       orca orchestration worker-start --agent codex --worktree <worktree of I> --spec-file <temp>/<slug>-q.md --json
       orca orchestration worker-start --agent antigravity --model <gemini model> --worktree <worktree of I> --spec-file <temp>/<slug>-q.md --json

   **codex** first (check that its hooks are trusted, F0-1). If codex fails to start, **antigravity**
   with a Gemini model (`opencode` with `--model` when `q-cli` picked it). If all fail, run the `q` skill as a clean-context subagent and mark
   `**Verification:** self-verified` (degraded).
   Mark it: `python "P/scripts/crew_live.py" set q 1` after the start, `set q 0` after its `worker_done` (the Q
   brief is self-contained and does not update the panel itself).
5. Wait as in step 2.7. Then read the effective model with
   `orca orchestration worker-read --dispatch <id> --source auto` and write in `verification.md`
   `**Verifier**: <cli> · requested <model field of the result> · effective <model | unconfirmed>` (F0-2);
   same in `--report`.
6. **Screens (F11, R28).** When `python "P/scripts/screens.py" list <slug>` is not empty, right after dispatching the Q:
   generate the judge's brief with `python "P/scripts/dispatch.py" screens-brief <slug> --url <URL> [--serve "<cmd>"] --out <temp>/<slug>-screens.md`
   (URL and serve command come from the `screens` profile of `.starcode/stack.json`; ask the user when it has none)
   and dispatch the screens judge as an Orca worker **in the worktree of `I`**, in the same CLI/family the `q-cli`
   picked for the Q and **never in the LaForge's family**. Fill `**Verifier**:` in `screens.md` as for the Q
   (step 5). Round 1 writes `screens.md`; its `differs` rows go into the single post-Q fix (section 5).
7. Right after the Q's `worker_done`, run
   `python "P/scripts/dispatch.py" q-check <slug>` (it only reports): exit 0 means only the allowed files
   changed; exit 1 lists the extra files. **The Q writes only `verification.md`.** Discard those extra changes (`git restore --source=HEAD -- <file>` for
   tracked files; delete new untracked ones) before committing `verification.md`, and cite the files in the review comment.
