# State files: STATE.md and the feature Handoff (plan 4.2, D28)

**Single writer:** only the Picard writes `.specs/STATE.md` and the `## Handoff` section. Troi, Spock
and Data write their own artifacts (`context.md`, `spec.md`, `tasks.md` except the Handoff); after each
of them finishes a step, the Picard updates the Handoff **in the same turn**. Workers never touch either.

## Feature layout

```
.specs/
├── STATE.md                     project decisions (AD-NNN)
└── features/<slug>/
    ├── context.md               Troi (discovery)
    ├── spec.md                  Spock (approval 1)
    ├── tasks.md                 Data (approval 2), with ## Checks and the ticket briefings
    ├── proofs.md, verification.md   Phase 3
```

`<slug>`: lowercase, digits and hyphens, from the feature name (e.g. `export-csv`). The same slug names
the integration branch `feature/<slug>` (D22).

## Where the Handoff lives

In the **most advanced artifact** of the feature: `tasks.md` when it exists, else `spec.md`, else
`context.md`. When a more advanced artifact is created, the Picard moves the Handoff there (and removes
it from the older file) in the same turn. The banner reads all three.

## Handoff format

```markdown
## Handoff

**Phase:** discovery | spec | spec-approved | tasks | tasks-approved | published | execute | review | done
**Size:** MEDIUM | LARGE | COMPLEX
**Git mode:** <1-4>
**Next:** <one sentence: exactly what happens next>
**Linear:** <issue ID (MEDIUM) | project URL + issue IDs (LARGE/COMPLEX) | none yet>
**Integration branch:** <feature/<slug> | n/a (mode 1) | not created>
**Last integrated:** <commit | none>
**Dispatched:** <worker, dispatch id, HEAD, written BEFORE sending | none>
**Settled:** <each user answer after the spec approval, dated, in their words | none>
**Breaker:** closed | open (<error-id>, attempts 3/3)
```

Events that must be recorded in the same turn: each user answer, each approval (the approval line goes
in the artifact; the Handoff gets the new phase), each Linear write (IDs), each dispatch (before
sending), each integration, each Q finding and its closure. **If the write fails, tell the user and do
not move to the next step.**

## Approvals

Written in the artifact by its author, right after the user's message:
`**Approved**: <YYYY-MM-DD> - user: "<the user's exact words>"`. Never paraphrased, never written for an
approval the user did not give. "Pode seguir", "aprovado", "ok" are approvals when they answer the
approval question; a question or a change request is not.

## STATE.md

```markdown
# STATE

## Decisions

### AD-001
- **Decision**: <one sentence>
- **Reason**: <why>
- **Trade-off**: <what was given up>
- **Scope**: <features/areas it governs>
- **Date**: YYYY-MM-DD
- **Status**: active | superseded by AD-NNN
```

Only project-level decisions that are hard to reverse, surprising without context and the result of a
real trade-off. Feature-local decisions stay in the spec's `## Decisions`. Create the file with the
`## Decisions` header the first time one is needed. Never delete entries; supersede them.

## Resume

Read STATE.md, the feature files (approval lines and the Handoff), `git log` / `git status` and the
Linear issues. Reconcile: **Git evidence beats notes**; an artifact with an approval line beats a
Handoff that says the approval is pending. Propose the next step before writing anything. After a
compaction mid-flow, continue when files and Git agree; on a conflict, stop and ask.

| Files you find | You are at | Next |
|---|---|---|
| `context.md` only | discovery done or in progress | Troi finishes, or Spock writes the spec |
| `spec.md` without `**Approved**` | spec written | rerun `run_gates.py spec`, present, wait for approval 1 |
| `spec.md` approved, no `tasks.md` (LARGE) | spec-approved | Data writes the tasks |
| `spec.md` approved, MEDIUM | spec-approved | issue + LaForge (Phase 3) |
| `tasks.md` without `**Approved**` | tasks written | rerun `run_gates.py tasks`, present, wait for approval 2 |
| `tasks.md` approved, tasks without `**Linear**` | tasks-approved | Linear publication (confirmation) |
| every task with `**Linear**` | published | integration branch + first ticket (Phase 3) |
