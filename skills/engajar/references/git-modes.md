# Git modes (D11)

Asked at **every session**, before any Git or Linear execution step, even if a mode was recorded
before (the risk changes between sessions). Recorded per worktree with:

    python "<plugin-root>/scripts/git_mode.py" set <N>

The `git_guard` hook enforces the last recorded mode in that worktree.

| Mode | Allowed | Not allowed |
|---|---|---|
| 1. Local code only | read issues, create/update the worktree, edit files, run tests, comment and move the issue to started/review | `git commit`, `git push`, PR, merge, deploy |
| 2. Local commits | everything in mode 1 + local commits and local branches | push, PR, merge, deploy |
| 3. Branch + PR | everything in mode 2 + push the branch and open the PR, each confirmed right before | merge into base, deploy (separate authorization) |
| 4. Full delivery | everything in mode 3 + move the issue to review, and to completed only with criteria met and evidence | merge into base, deploy, production changes, deleting branches/issues/projects (separate authorization) |

## Rules
- **Mode 1 = degraded verification.** No integration branch and no commits: the whole feature runs in
  the single worktree of the main issue, tickets in sequence in the same tree. Gates run on a dirty
  tree and mark `Tree: dirty (modo 1)`. Q receives `git diff <base>` of the working tree. The issue
  **never** goes to completed in mode 1. Do not create extra branches by hand: the Orca worktree
  already has its own branch.
- Push and PR: right before each one, show the diff summary, the gates/tests with results and the PR
  proposal, and get a yes **for that action**. Approval of the mode is not approval of the push.
- Merging a ticket into the feature integration branch `feature/<slug>` needs no extra authorization
  (it is local to the feature, D22).
- Merge into the base branch, push to the base branch, `gh pr merge` and deploy need a **separate**
  authorization. After the user gives it explicitly, record it (valid for 10 minutes):

      python "<plugin-root>/scripts/git_mode.py" authorize-merge <base-branch>

  Never record an authorization the user did not give.
- Always blocked by the hook, in any mode: `push --force` (and `-f`, `--force-with-lease`, `+refspec`,
  `--mirror`), remote branch deletion, `reset --hard`, `branch -D`, `clean -f`, `checkout -- .` /
  `restore .`. Never work around a block; if the user explicitly wants it, the user runs it.

## How to ask
Present the four modes in one message, with a recommendation and half a line of why (usually mode 2
for exploratory work, mode 3 when the user wants a PR at the end). Ask together with any other pending
decision (D29).
