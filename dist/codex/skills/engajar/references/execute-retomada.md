# Execute: Retomada e disjuntor

Variables and preconditions: see `execute.md` (sections 0 and 1).

## 6. Resume and the circuit breaker (D27)
- On resume with a `**Dispatched:**` not integrated: `orca orchestration worker-show --dispatch <id>` before
  anything else. Running → wait (step 2.7). Finished → step 3. **Never start a second worker for the same
  ticket while the first is not closed** (`worker-stop` first, with a line to the user).
- `handoff.py` prints `DISJUNTOR ABERTO` on the 3rd failure of the same error id: record nothing more,
  make no 4th attempt, and stop with the 3 attempts (from `**Reports:**`) and two exits:
  (a) rethink the approach (back to Spock/Data when the problem is design), (b) go back to the last
  integrated commit of `I` (`**Last integrated:**`). With the user's choice, `--breaker closed`.
- **Exit (b) in mode 1 (R29)** is the snapshot of the ticket that failed, not a commit. If `**Dispatched:**`
  is not closed, `worker-stop` first. Run `python "<plugin-root>/scripts/snapshot.py" restore <slug> <ticket>`
  **without `--yes`**, show the user the plan and the "fora do ticket" list, and ask for a yes for this
  restore. Only then run it again with `--yes` and record `--breaker closed`.
- A session that starts with `**Breaker:** open` proposes these two exits before any dispatch.
- Stops: only the closed list (STARCODE.md, D29). Ordinary technical errors are fixed and counted.
