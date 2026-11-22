# Execute: MÉDIA e PEQUENA

Variables and preconditions: see `execute.md` (sections 0 and 1).

## 8. MEDIUM and SMALL
One LaForge worker in a new child worktree from the current branch; the brief is the spec's
`## Checks` (MEDIUM, or the minimal spec of the SMALL task, see below) plus the worker rules of `dispatch.py brief`.
`<ID>` is the spec's `**Linear**:`. MEDIUM, with no `tasks.md`, has one ticket, `T1`, and the same two
commands as the large path (the `Dispatched` entry and the Handoff live in `spec.md`):

    python "P/scripts/dispatch.py" start <slug> <ID> --cli <laforge cli> --model <laforge model> --json
    python "P/scripts/dispatch.py" settle <slug> <ID> --branch <ramo do ticket>

`start` refuses with exit 2 and `start recusado: spec sem **Linear**:` when the spec has no ID, and both
commands refuse a ticket that is neither `<ID>` nor `T1`. `settle` runs the gate
`run_gates.py ticket <slug> T1 <base>..<ramo>` using the spec's `**May change**:` (plus `DECISIONS.md` when it lists
`scripts/`), merges, and removes the `T1` entry; then steps 4–5. Progress without tasks.md is one ticket:
`crew_live.py progress <slug> --done 0 --total 1` at dispatch, `--done 1 --total 1` after the merge.

### SMALL (PEQUENA): minimal spec by the Picard, Q waived (D-a)
Route: "spec mínima do Picard + LaForge (Q dispensado)". No Troi, no Spock, **no approval**: the Picard writes
`.specs/features/<slug>/spec.md` itself, commits it with the Handoff and runs `run_gates.py spec <slug>`
(and `execute`, which accepts it without `**Approved**`). The template has only this:

    # <título>: Spec

    **Size**: SMALL
    **Linear**: <ID>
    **May change**: <até 3 arquivos, sem contar DECISIONS.md, CHANGELOG.md e pastas>

    ## Scope
    - <uma frase>

    ## Checks
    **Build**: `<build>`
    **C1** - <afirmação observável>
    Proof: `<comando de teste que seleciona o teste>`

More than 5 checks or more than 3 files → the gate says `PEQUENA passou do limite (<n> checks, <m> arquivos):
reclassifique para MÉDIA`; reclassify and follow the MEDIUM path.
1. Dispatch and integrate like MEDIUM: `dispatch.py start <slug> <ID> ...` and `dispatch.py settle <slug> <ID> --branch ...`
   (the only ticket is `T1`; `settle` runs the gate `ticket` before the merge).
2. `python "P/scripts/gates/run_gates.py" proofs <slug>` writes `proofs.md`.
3. The Q is waived: `python "P/scripts/dispatch.py" q-waive <slug>` writes `verification.md` with
   `**Verification:** waived (PEQUENA)` (exit 2 for any other class). Commit it; `run_gates.py done <slug>` is green
   and shows the warning `Q dispensado (PEQUENA)`, which stays a warning with `--strict`.
4. PR in modes 3/4 and the Worf on the PR (section "Review (Worf)") stay. The Guinan is **not** invoked: no retro
   for a PEQUENA task.
5. The issue goes to `completed` only with the user's confirmation, like any feature. Mode 1 keeps section 7.
