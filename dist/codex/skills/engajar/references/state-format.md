# State files: STATE.md and the feature Handoff (plan 4.2, D28)

**Single writer:** only the Picard writes `.specs/STATE.md` and the `## Handoff` section, the Handoff always
through `python "<plugin-root>/scripts/handoff.py" set <slug> --<field> "<value>" ...` (F2-10): it moves the
section to the most advanced artifact, keeps the fields not passed and prints one line. Never edit the
Handoff by hand and never paste it or its diff in the chat. `--settle "<text>"` appends a dated entry to
`**Settled:**`; `show <slug>` prints it for a resume. Troi, Spock
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
**Settled:** <each user answer AFTER the spec approval, dated, in their words | none>
**Attempts:** <error-id>=<n>, ... | none          (written by --attempt; a success resets the id)
**Reports:** <date>: <worker report>; ... | none  (written by --report)
**Breaker:** closed | open (<error-id>, attempts 3/3)
```

`**Settled:**` starts empty. Before the spec approval, answers go where they belong (Git mode in its own
field, discovery answers in context.md, decisions in the spec), never in Settled (F2-12).

Events that must be recorded in the same turn: each user answer, each approval (the approval line goes
in the artifact; the Handoff gets the new phase), each Linear write (IDs), each dispatch (before
sending), each integration, each Q finding and its closure. **If the write fails, tell the user and do
not move to the next step.**

## Committing the planning artifacts (modes 2–4, F2-7)

The Picard commits the feature's `.specs/` files (and `.specs/STATE.md`, `.starcode/config.json` when
they changed) at each approved milestone, in the same turn as the Handoff update, **without asking**: the
approval is the authorization. Never create a branch for it. Report it in one line (hash + message):
- MEDIUM: after the spec approval and the issue link (`**Linear**:` written in the spec).
- LARGE/COMPLEX: after the Linear publication (or after approval 2 when the user declined publishing).
- Any re-approval of a spec or tasks (revision) gets its own commit.

Rules: only `.specs/` and `.starcode/` paths, never code; current branch (before the integration branch
exists, that is the base branch: a local commit, never pushed outside modes 3/4); message
`docs(specs): <what was approved> (<slug>)` with the footer `Refs: <issue IDs of the feature>` (the MEDIUM
issue, or the LARGE issues comma-separated), checked with
`python "<plugin-root>/scripts/gates/check_commit.py" --message "<msg>"`. Mode 1: no commit; the files
stay in the working tree and the Handoff says so.

## Approvals

Written in the artifact by its author, right after the user's message:
`**Approved**: <YYYY-MM-DD> - user: "<the user's exact words>"`. Never paraphrased, never written for an
approval the user did not give. "Pode seguir", "aprovado", "ok", "sim" are approvals when they answer the
approval question; a question or a change request is not. The tasks question also asks to publish
(F2-9): a "sim" to it covers both; "só aprovar" covers only the approval.

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

## Live panel files (F6-7, F6-8)

Not state: two small files for a visual panel (e.g. the Fase 10 "Ponte"), in the **main worktree** at
`.starcode/live/` (self-ignored in Git), written only by `scripts/crew_live.py` (atomic writes):
- `crew.json`: `{"<member>": 0 | 1}`, 1 = working. Each skill runs `start`/`stop`; the Picard runs
  `set laforge|q 1|0` around its workers, because a worker may die without its `stop`.
- `progress.json`: `{"<slug>": {"done", "total", "percent", "phase"}}`. `progress <slug>` counts the tickets
  of `tasks.md` integrated in `feature/<slug>` (same rule as `dispatch.py next`); MEDIUM/SMALL pass
  `--done/--total` (one ticket).
Never read them to decide anything: Git and the Handoff stay the source of truth. A failure of these
commands never stops the flow; report it in one line.

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
| `spec.md` approved, MEDIUM | spec-approved | issue + one LaForge worker (`execute.md` section 8) |
| `tasks.md` without `**Approved**` | tasks written | rerun `run_gates.py tasks`, present, wait for approval 2 |
| `tasks.md` approved, tasks without `**Linear**` | tasks-approved | if the approval answer was a yes to publishing, publish; if it was "só aprovar", ask once whether to publish now |
| every task with `**Linear**` | published | integration branch + first ticket (`execute.md`) |
| `**Dispatched:**` not integrated | execute | `orca orchestration worker-show` first; never a second worker for the same ticket |
| all tickets integrated, no `verification.md` | execute / review | `run_gates.py proofs`, then the Q |
| `verification.md` with open findings | review | one LaForge fix pass, then `run_gates.py done` (no second Q) |
| `**Breaker:** open` | any | the two exits of `execute.md` section 6 before anything else |
