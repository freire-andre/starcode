# tasks.md template (ADR-0002, D19, D24, plan 5.1)

Headings and markers in English (read by `validate_tasks.py`); prose in PT-BR; no persona.

```markdown
# <Feature>: Tasks

**Spec**: `.specs/features/<slug>/spec.md`
**Status**: Draft
**Integration branch**: `feature/<slug>`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only | `<unit test command>` |
| full | task with integration/e2e tests | `<unit + integration command>` |
| build | config-only task, or after the last task | `<build + lint + all tests>` |

## Tasks

### T1: <short title in PT-BR>
**Depends on**: none
**Requirements**: R1, R2
**Tests**: unit | integration | e2e | none
**Gate**: quick

#### TASK
<one verifiable deliverable, with the exact files when possible>

#### CONTEXT
Spec: `.specs/features/<slug>/spec.md` (R1, R2). Checks: C1, C2.
<what already exists and the repo patterns to follow, with paths>

#### BOUNDARIES
May change: `<file>`, `<test file>`
Do not touch: `<files owned by other tasks that may be active>`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: <n>.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

## Checks

**Build**: `<build>`; `<type check>`; `<lint>`
**Run unit**: `<command that runs this feature's unit tests, verbose>`

**C1** - <one observable claim with its concrete value> (R1)
Proof: run unit | <the line the test prints when it passes, pass marker included>
```

## Rules the gate enforces

| Rule | Why |
|---|---|
| Every task has `Depends on`, `Requirements`, `Tests`, `Gate` and the 5 blocks, none empty | the worker starts with a clean context |
| `Gate` names a level from `## Gate Commands` | one source for the commands |
| `May change` lists every path the task may edit | file ownership (D19) |
| Two tasks without a dependency path never share a path | Fleet may run them together |
| A sensitive file in `May change` requires `**Runs alone**: yes` | plan 4.4 |
| Every spec requirement has a check; every check cites a requirement and has a proof | the checks are the floor of verification |
| `**Build**:` exists; every `run <name>` proof has a `**Run <name>**:` line and an expected line | `check_proofs.py` runs exactly these (Phase 3) |
| No `## Checks` in spec.md of a LARGE/COMPLEX feature | checks live only in tasks.md (D24) |

`**Linear**: <ID>` lines are written by `tasks_export.py record` after the issues exist; never by hand
before that. `<ID-LINEAR>` in RULES stays literal: the worker reads its ticket ID from the worktree link.

## Granularity

| Too big | Split into |
|---|---|
| "Criar o formulário" | campo de e-mail · validação · botão · estado do formulário · envio à API |
| "Implementar auth" | formulário de login · armazenamento do token · serviço de auth · proteção de rota |

A task that creates code it cannot test yet is mis-cut: move the tests to the first task where they run,
or absorb the missing piece into the current task. "Testado em outra task" never justifies `Tests: none`;
`none` is only for layers with no tests (config, docs).
