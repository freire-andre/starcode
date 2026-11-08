# Brief e gate de escopo da feature MÉDIA: Spec

**Approved**: 2026-11-07 - user: "sim"
**Status**: Approved

**Size**: MEDIUM
**Risk triggers**: none
**Linear**: SC-83
**May change**: scripts/gates/check_scope.py, scripts/gates/run_gates.py, scripts/gates/validate_spec.py, scripts/dispatch.py, skills/spock/references/spec-template.md, skills/engajar/references/execute.md, DECISIONS.md, tests/, dist/

## Context
Uma feature MÉDIA não tem `tasks.md`. O brief que `dispatch.py brief` monta a partir da spec manda o worker rodar `run_gates.py ticket <slug> <ticket> <base>..HEAD`, mas o `check_scope` resolve a feature por `tasks.md` e falha ("não existe"); o `check_commit` da etapa também não roda. O brief da MÉDIA também não traz a lista de arquivos permitidos: na SC-81 o Picard acrescentou o `May change` à mão e conferiu o escopo manualmente.

Pendência registrada na Fase 7 (SC-14). O usuário aprovou o plano em 2026-11-07 ("(Spock escreve a spec breve)? SIM").

## Scope
- Linha `**May change**:` no cabeçalho da spec breve (template do Spock) e aviso do `validate_spec` quando falta numa MÉDIA.
- `check_scope` e `run_gates.py ticket` funcionando sem `tasks.md`, a partir da spec.
- Bloco de limites no brief da MÉDIA (`dispatch.py`).
- `execute.md` seção 8 passa a integrar a MÉDIA com o gate `ticket`.
- Decisão F7-11 em `DECISIONS.md`; `dist/` regenerado pelo `tools/build.py`.

## Non-Goals
- Mudar a feature PEQUENA (checks inline, sem spec).
- Mudar o formato de `tasks.md` ou o gate `ticket` das features GRANDE/COMPLEXA.
- Tornar a linha `**May change**:` obrigatória (erro) numa MÉDIA: specs antigas sem ela continuam válidas.

## Requirements
- **R1** - The system SHALL ter no template breve do Spock (`skills/spock/references/spec-template.md`) a linha `**May change**: <paths separados por vírgula>` logo depois de `**Linear**:`. IF uma spec com `**Size**: MEDIUM` não tem essa linha THEN `validate_spec.py` SHALL emitir o aviso `MEDIUM sem a linha **May change**: o gate ticket não confere o escopo` e continuar com código 0 quando não houver erro.
- **R2** - WHEN a feature não tem `tasks.md` e tem `spec.md` THEN `check_scope` SHALL usar como lista permitida os paths da linha `**May change**:` da spec, com as mesmas regras de `tasks.md` (path exato, glob, pasta terminada em `/`).
- **R3** - IF a feature não tem `tasks.md` e a spec não tem a linha `**May change**:` THEN `check_scope` SHALL emitir o aviso `spec sem **May change**: escopo não conferido` sem erro de escopo por arquivo, e SHALL manter os erros de `.specs/STATE.md` alterado, `## Handoff` alterado e intervalo sem commit.
- **R4** - WHEN a feature não tem `tasks.md` THEN `check_scope` SHALL aceitar como ticket o ID do Linear da linha `**Linear**:` da spec ou `T1`. IF o ticket é outro valor THEN SHALL sair com erro de uso `ticket <X> não é desta feature MÉDIA (use <ID> ou T1)`.
- **R5** - WHEN a feature não tem `tasks.md` THEN `run_gates.py ticket` SHALL rodar `check_commit` em cada commit do intervalo, esperando no `Refs` o ID do Linear da spec (sem ID, sem expectativa de `Refs`).
- **R6** - WHEN a feature não tem `tasks.md` THEN `dispatch.py brief` SHALL incluir uma seção `## BOUNDARIES` com a linha `May change: <paths>` copiada da spec, ou `May change: não definido na spec; pare e pergunte antes de alterar arquivos fora do Scope` quando a linha falta.
- **R7** - The system SHALL trocar em `skills/engajar/references/execute.md` seção 8 o texto "no `check_scope`: there is no tasks.md" pela integração com `run_gates.py ticket <slug> <ID> <base>..<head>` usando o `May change` da spec.
- **R8** - The system SHALL registrar em `DECISIONS.md` a decisão F7-11 com R1–R7: o `May change` da MÉDIA vive na spec, é aviso (não erro) quando falta, e o gate `ticket` vale para a MÉDIA.

## Edge Cases
- **Feature com `tasks.md`:** comportamento atual, a linha `**May change**:` da spec é ignorada.
- **Linha `**May change**:` vazia:** tratada como ausente (R3, R6).
- **Spec da GRANDE/COMPLEXA com `**May change**:`:** sem aviso nem efeito (a lista vive em `tasks.md`).
- **Ticket em minúsculas (`sc-90`, `t1`):** aceito, como em `tasks.md`.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - O template breve tem a linha `**May change**:` depois de `**Linear**:`, e o `validate_spec` avisa com a mensagem de R1 numa MÉDIA sem ela, com código 0 (R1)
Proof: run unit | test_validate_spec_warns_medium_without_may_change ... ok

**C2** - Numa MÉDIA com `**May change**: a.py, docs/`, o `check_scope` aceita `a.py` e `docs/x.md` e acusa `b.py` como fora do `May change` (R2)
Proof: run unit | test_check_scope_medium_uses_spec_may_change ... ok

**C3** - Numa MÉDIA sem a linha, o `check_scope` avisa `spec sem **May change**: escopo não conferido`, sem erro por arquivo, e ainda acusa `.specs/STATE.md` e `## Handoff` alterados (R3)
Proof: run unit | test_check_scope_medium_without_may_change_warns ... ok

**C4** - Numa MÉDIA com `**Linear**: SC-90`, o `check_scope` aceita `SC-90`, `sc-90` e `T1` e recusa `T2` com a mensagem de R4 (R4)
Proof: run unit | test_check_scope_medium_ticket_id ... ok

**C5** - `run_gates.py ticket` numa MÉDIA com `**Linear**: SC-90` acusa um commit sem `Refs: SC-90` e passa com ele (R5)
Proof: run unit | test_run_gates_ticket_medium_checks_commits ... ok

**C6** - O brief da MÉDIA tem `## BOUNDARIES` com `May change: <paths>` da spec, e o texto de R6 quando a linha falta (R6)
Proof: run unit | test_spec_brief_includes_boundaries ... ok

**C7** - `execute.md` seção 8 cita `run_gates.py ticket` e não tem mais "no `check_scope`" (R7)
Proof: run unit | test_execute_medium_runs_ticket_gate ... ok

**C8** - `DECISIONS.md` tem a decisão F7-11 (R8)
Proof: run unit | test_decisions_records_f7_11_medium_scope ... ok

## Handoff

**Phase:** done
**Size:** MÉDIA
**Git mode:** 3
**Next:** nada (PR #13 com merge em main d4894d5)
**Linear:** SC-83
**Integration branch:** not created
**Last integrated:** f7ab30f
**Dispatched:** none
**Settled:** 2026-11-07: 2026-11-07: plano do ponto 3 aprovado: "(Spock escreve a spec breve)? SIM"; 2026-11-07: 2026-11-07: spec aprovada e issue criada: "sim"
**Attempts:** none
**Reports:** 2026-11-07: 2026-11-07: SC-83: R1–R8 (89bd2ab), gate ticket verde na própria MÉDIA, 385 testes rc 0; 2026-11-07: 2026-11-07: Q (codex): FAIL, 2 achados (C3 sem intervalo vazio; C5 sem vários commits); 2026-11-07: 2026-11-07: Q-fix: 2 achados fechados (bb6494d, a8d6c40; teste C6 apagado por engano e restaurado); 385 testes rc 0
**Breaker:** closed
