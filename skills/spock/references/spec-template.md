# Spec template (plan 4.5, ADR-0002)

Headings and markers in English (read by `validate_spec.py`); prose in PT-BR; no persona. Sections
marked `*` may be `N/A - <reason>`; the reason is mandatory.

## Full template (LARGE / COMPLEX)

```markdown
# <Feature>: Spec

**Size**: LARGE
**Risk triggers**: <from the sizing block, or none>
**Status**: Draft

## Context
<why the feature exists: the problem, who has it, what success looks like>

## Scope
- <what is in>

## Non-Goals
- <what is out and must not be touched>

## Requirements
- **R1** - WHEN <trigger> THEN the system SHALL <response with a concrete value>.
- **R2** - IF <undesired condition> THEN the system SHALL <response>.

## Data & Contracts*
<schemas, interfaces, input/output payloads, file formats>

## States*
<loading, error, empty, success; partial failures>

## Edge Cases
- <connection loss, concurrency, timeout, invalid input, limits>

## Decisions
| Item | Options | Status |
|---|---|---|
| <decision> | <option A (pros/cons)> · <option B (pros/cons)> | approved - user: "<their words>" |

## Open Questions
None.

## Sources*
<binding reference material, one line each; write `binding` or `non-binding - user: "<words>"`>

## Differences from the Source*
<required when a source is binding: each approved difference, or `None - o produto segue a fonte`>
```

- Decision status: `approved`, `adjusted` (the user changed your option; say how) or `rejected`. Use
  `None - <why there were no alternatives>` when the feature has no real choice.
- `## Checks` is **not** allowed here: for LARGE/COMPLEX the checks live only in `tasks.md` (D24).
- `## Sources` and `## Differences from the Source` are optional; include them only when there is
  reference material the product must follow.

## Brief template (MEDIUM)

```markdown
# <Feature>: Spec

**Size**: MEDIUM
**Risk triggers**: <trigger or none>
**Linear**: <issue ID, written after the approval>
**May change**: <paths separados por vírgula>

## Context
## Scope
## Non-Goals
## Requirements
## Edge Cases
## Open Questions
None.

## Checks

**Build**: `<build>`; `<type check>`; `<lint>`        (or `**Build**: none - <why>`)
**Run unit**: `<the project's command that runs these tests, verbose>`

**C1** - <one observable claim with its concrete value> (R1)
Proof: run unit | <the line the test prints when it passes, pass marker included>
```

`## Decisions` is optional in the brief template; use it when the user chose between alternatives.

## EARS patterns

| Pattern | Template | For |
|---|---|---|
| Ubiquitous | The system SHALL <response> | invariants |
| Event | WHEN <trigger> THEN the system SHALL <response> | a response to an event |
| State | WHILE <state> the system SHALL <response> | behavior during a state |
| Optional | WHERE <feature/flag> the system SHALL <response> | gated behavior |
| Unwanted | IF <condition> THEN the system SHALL <response> | errors, invalid input, timeouts |

Keywords in English capitals, the rest in PT-BR: `WHEN o usuário envia um arquivo maior que 10 MB THEN
the system SHALL responder 413 com "arquivo maior que 10 MB"`. One behavior per requirement.

## Checks (MEDIUM in the spec, LARGE/COMPLEX in tasks.md)

- One check per requirement at least; each check cites its requirement IDs in parentheses.
- The proof names **one test with the project's own command**. Tests that run together share a
  `**Run <name>**:` line; the check writes `Proof: run <name> | <line the test prints when it passes>`
  (copied from a real run, with `PASSED`, `ok` or `✓`). A test that cannot share a run (e2e with its own
  server) is a lone `Proof: <command with a filter that selects it>`.
- `**Build**:` names the repo's build, type check and lint commands from its manifests and CI, never
  invented. When the repo has none, `**Build**: none - <why>`.
- Commands come from the repo (package.json, pyproject.toml, Cargo.toml, Makefile, CI workflows). If the
  repo has no tests at all, ask the user which test types and commands the project will use.
