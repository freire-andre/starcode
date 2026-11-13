# Ajustes do review do PR #39: Spec

**Approved**: 2026-11-13 - user: "sim"
**Approved**: 2026-11-13 - user: "Mover para gates_common" (R1 e May change: `gates_common.py`, o módulo existente)
**Status**: Approved

**Size**: MEDIUM
**Risk triggers**: Concurrency and state
**Linear**: SC-167
**May change**: `scripts/gates/gates_common.py`, `scripts/gates/validate_tasks.py`, `scripts/gates/check_scope.py`, `scripts/dispatch.py`, `skills/engajar/references/execute.md`, `tests/test_coverage_rule.py`, `tests/test_dispatch_start.py`, `tests/test_skills_exec.py`, `DECISIONS.md`, `dist/`

## Context
O review do PR #39 (`.specs/features/manutencao-retros-f11/review.md`, W1 e W2) achou duas inconsistências. O gate das tasks e o `check_scope` cobrem caminhos com regras diferentes (glob só no `check_scope`). E o `dispatch.py start` sai com 2 ("recusado") quando a segunda gravação do Handoff falha depois de um `worker-start` bem-sucedido, escondendo um worker ativo. Detalhes e fatos: `context.md`.

## Scope
- Uma regra de cobertura de caminho única para os dois gates, com glob.
- Um código de saída e uma linha de aviso próprios para o `start` com worker ativo e registro incompleto, documentados no `execute.md`.

## Non-Goals
- W3 do review (`noqa` sem link de issue).
- As sugestões da retro da manutencao-retros-f11.
- Mudar os códigos 0, 1 e 2 do `start` ou o comportamento do `settle`.

## Requirements
- **R1** - The system SHALL ter em `scripts/gates/gates_common.py` uma função `covers(path, entry)` usada pelo `check_scope` e pelo gate das tasks: com o caminho normalizado (`\` vira `/`, `posixpath.normpath`), uma entrada terminada em `/` cobre o caminho que começa com ela, e uma entrada sem `/` no fim cobre o caminho igual a ela ou que casa com ela por `fnmatch`.
- **R2** - WHEN o bloco `#### TASK` cita `` `tests/test_x.py` `` e o May change tem `` `tests/test_*.py` `` THEN the system SHALL dar a citação como coberta (nenhum erro do R20 no `run_gates.py tasks`).
- **R3** - IF o caminho citado no TASK, normalizado, é `..`, começa com `../` ou com `/` THEN the system SHALL dá-lo como não coberto por qualquer entrada, inclusive por glob como `*` ou `scripts/*`.
- **R4** - The system SHALL manter no gate das tasks a regra do nome sem pasta: a citação `` `snapshot.py` `` é coberta pela entrada `scripts/snapshot.py`.
- **R5** - IF a segunda gravação do Handoff do `dispatch.py start` (a que traz o dispatch id e o modelo do recibo) falha depois de um `worker-start` com exit 0 THEN the system SHALL sair com 3, sem remover a entrada da primeira gravação em `Dispatched`.
- **R6** - WHEN o `start` sai com 3 THEN the system SHALL imprimir a linha `worker ativo sem registro completo: <T> · <dispatch id> · <worktree>: <primeira linha do erro>` (`-` no lugar do id ou do worktree ausente), tentar ainda o `orca worktree set`, e com `--json` imprimir o objeto `{"ticket","issue","base","dispatch","worktree","model"}` com o dispatch id do recibo.
- **R7** - The system SHALL descrever no `skills/engajar/references/execute.md`, junto do contrato do `start` (seção 2), o exit 3 e o que o Picard faz: completar a entrada com `handoff.py set <slug> --dispatch-add "<T> · ... · <dispatch id>"` e esperar o worker normalmente, sem novo `start` para o mesmo ticket.

## Edge Cases
- Glob que cobre só parte do caminho (`scripts/*.py` contra `scripts/gates/x.py`): segue o `fnmatch` do Python, em que `*` casa `/`; é o comportamento atual do `check_scope`, mantido.
- Primeira gravação do `start` falha: continua recusa (exit 2), porque nada foi enviado à Orca.
- Recibo sem dispatch id e segunda gravação falha: exit 3 com `-` no lugar do id.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v`

**C1** - `covers` cobre por pasta, por igualdade e por `fnmatch` sobre o caminho normalizado (R1)
Proof: run unit | test_covers_pasta_igualdade_e_glob ... ok

**C2** - o `check_scope` e o gate das tasks chamam a mesma `covers` (R1)
Proof: run unit | test_gates_usam_a_mesma_regra ... ok

**C3** - citação `tests/test_x.py` com May change `tests/test_*.py` não gera erro no gate das tasks (R2)
Proof: run unit | test_citacao_coberta_por_glob ... ok

**C4** - `scripts/../../outside.py` e `/etc/x.py` não são cobertos nem por `*` nem por `scripts/*` (R3)
Proof: run unit | test_travessia_nao_coberta_por_glob ... ok

**C5** - a citação `snapshot.py` continua coberta por `scripts/snapshot.py` (R4)
Proof: run unit | test_nome_sem_pasta_continua_coberto ... ok

**C6** - segunda gravação falha após `worker-start` ok: exit 3 e a entrada da primeira gravação continua em `Dispatched` (R5)
Proof: run unit | test_start_segunda_gravacao_falha_sai_3 ... ok

**C7** - no exit 3 a linha `worker ativo sem registro completo: T1 · ctx_1 · <worktree>: ...` é impressa, o `worktree set` é chamado e o `--json` traz `"dispatch": "ctx_1"` (R6)
Proof: run unit | test_start_exit_3_avisa_e_liga_worktree ... ok

**C8** - o `execute.md` descreve o exit 3 e o `--dispatch-add` com o dispatch id (R7)
Proof: run unit | test_execute_descreve_exit_3 ... ok

## Handoff

**Phase:** review
**Size:** MEDIUM
**Git mode:** 3
**Next:** Worf rodada 2
**Linear:** SC-167
**Integration branch:** not created
**Last integrated:** de519c0
**Dispatched:** none
**Settled:** 2026-11-13: spec aprovada com exit 3 e entrada mantida (user: "sim"); 2026-11-13: R1/May change: covers em gates_common.py, não gate_common.py (user: "Mover para gates_common")
**Attempts:** none
**Reports:** 2026-11-13: SC-167 1ª entrega 3b31657 (gate ticket verde); pedido: mover covers para gates_common.py; 2026-11-13: SC-167: covers em gates_common.py e exit 3 no start (3b31657, b6c6fbe); suíte 767 ok; integrado em 30f6d31; 2026-11-13: Q (codex, gpt-6-luna, ctx_2a1702566163): FAIL - C2 não exercita o gate das tasks; C8 asserção frouxa; 2026-11-13: fix pós-Q: 22e7907 (C2), 2b4d7e1 (C8); proofs e done verdes; 2026-11-13: retro da Guinan: 49eeb2f (L25-L26, 4 sugestões não aplicadas); 2026-11-13: push e PR confirmados (user: "Push e PR (Recomendado)"): https://github.com/freire-andre/starcode/pull/42, HEAD 424f6e5; 2026-11-13: Worf rodada 1: COMMENT (d909d28); W1 should-fix 2F sem exit 3; W2 nit covers aceita C:/; 2026-11-13: fix Worf r1: W1 8ed1276, W2 2e781bb; suíte 769 ok; proofs e done verdes
**Breaker:** closed
