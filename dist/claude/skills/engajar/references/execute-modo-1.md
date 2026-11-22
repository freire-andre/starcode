# Execute: Modo Git 1

Variables and preconditions: see `execute.md` (sections 0 and 1).

## 7. Git mode 1 (degraded)
- No modo 1 não se usa dispatch.py start nem settle: o `start` exige
  `**Integration branch:**` no Handoff e recusa sem ele (exit 2), e o `settle` mescla um ramo que o modo 1 não tem.
- **One worktree** (the main issue's), tickets in sequence in the same tree, **no integration branch and
  no commits**. Dispatch with `--worktree <that worktree>`; skip `run_gates.py ticket` (no range) and
  the merge; compare `git status` before and after each worker instead.
- **Snapshot before each dispatch (R28):** run
  `python "<plugin-root>/scripts/snapshot.py" take <slug> <ticket>` before every LaForge dispatch and record
  the printed line with `handoff.py set --report`. If `take` fails, the ticket is **not** dispatched.
- **Snapshot drop (R30):** after `--phase done`, run `python "<plugin-root>/scripts/snapshot.py" drop <slug>`.
- `run_gates.py proofs` marks `**Tree**: dirty (modo 1)`. The Q receives `git diff <B>` of the working
  tree: `q-brief --head HEAD`, then append to the brief the line "Modo Git 1: não há commits; use
  `git diff <B>` (árvore de trabalho) no lugar do intervalo."
- `verification.md` gets `**Verification:** degraded`; each finding is closed with
  `degradada (modo 1)` in `Closed`. The result is shown as degraded verification and the issue **never**
  goes to completed.
