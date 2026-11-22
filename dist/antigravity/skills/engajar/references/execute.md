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
- Git mode 2, 3 or 4 → this file as written. **Git mode 1 → section 7 (`execute-modo-1.md`).**
- Models: LaForge and Q from the effective crew (session override > local repo config > user config > `crew.yaml`; `setup_helpers.py crew-table` shows it). Compare
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

## Index: load only the file of the step in progress
Do not load the other files. The section numbers and headings are unchanged; each file keeps them.

| Sections | File |
|---|---|
| 2, 2F, 3 (dispatch, fleet, integrate) | `execute-despacho.md` |
| 4 (proofs and the Q) | `execute-provas-e-q.md` |
| 5, Review (Worf), Text for the PR | `execute-pos-q-e-review.md` |
| 6 (resume, circuit breaker) | `execute-retomada.md` |
| 7 (Git mode 1) | `execute-modo-1.md` |
| 8 (MEDIUM and SMALL) | `execute-media-pequena.md` |
