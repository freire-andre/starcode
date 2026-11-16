# qStrategy no q-cli: Spec

**Approved**: 2026-11-16 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-185
**May change**: scripts/dispatch.py, tests/test_dispatch.py, skills/engajar/references/execute.md, skills/config/SKILL.md, schemas/config.md, DECISIONS.md, CHANGELOG.md, dist/

## Context
Item 3.6 da triagem v2 (decisão D-b: ligar o `qStrategy` ao `dispatch.py q-cli`). O campo é validado (`scripts/config/validate_config.py:33,57`) e oferecido pela skill `config` (`skills/config/SKILL.md:69`), mas nenhum script o lê. `q_cli` (`scripts/dispatch.py:623`) percorre o Q configurado e depois `Q_CLI_ORDER = ("codex", "antigravity", "opencode")`, e devolve `None` quando nenhum CLI de outra família está disponível. O comando imprime então `self-verified` e sai com 1. Nenhum código implementa `opencode-subagent`. Discovery: `.specs/features/q-strategy/context.md`.

## Scope
- `q_cli` recebe a lista de estratégias por parâmetro e a percorre na ordem dada. O comando `q-cli` lê essa lista do config do usuário válido (`starcode_common.load_user_config`, que respeita `STARCODE_HOME`).
- `orca-worker` = o percurso atual (Q configurado, codex, antigravity, opencode, com a regra de família e o `orca_worker` ok).
- `self-verified` = parar e devolver self-verified.
- `opencode-subagent` = aceito pelo validador, pulado pelo `q-cli` com aviso, e fora da oferta da skill `config`.

## Non-Goals
- Implementar o Q como subagente do OpenCode (congelamento D-i; vira feature própria).
- Mudar o validador, o enum `Q_STRATEGIES`, `Q_CLI_ORDER` ou a regra de família.
- Ler `qStrategy` do config local ou do config do repositório (a chave é só do escopo global).
- Opção nova de linha de comando no `q-cli`.

## Decisions
| Item | Options | User answer |
|---|---|---|
| `opencode-subagent` sem implementação | fica no enum e o q-cli pula / implementar agora / remover do enum | approved - user: "Fica no enum, q-cli pula (Recomendado)" |
| `self-verified` antes de `orca-worker` | a ordem do usuário manda / worker sempre primeiro | approved - user: "Sim, a ordem do usuário manda (Recomendado)" |

## Requirements
- **R1** - IF a lista de estratégias é `None` (config do usuário ausente, inválido ou sem `qStrategy`) THEN `q_cli` SHALL devolver o mesmo que hoje: para LaForge `claude:claude-sonnet-5-5` com codex disponível, `codex`; os testes atuais de `q_cli` passam sem mudança.
- **R2** - WHEN a lista é `["orca-worker"]` ou `["orca-worker", "self-verified"]`, o LaForge é `claude:claude-sonnet-5-5` e codex está disponível THEN `q_cli` SHALL devolver `codex`.
- **R3** - WHEN o primeiro item da lista é `self-verified` (ex.: `["self-verified", "orca-worker"]`) THEN `q_cli` SHALL devolver `None` mesmo com codex disponível, e o comando `q-cli` SHALL imprimir `self-verified` e sair com 1.
- **R4** - WHEN o percurso chega a `opencode-subagent` THEN o comando `q-cli` SHALL escrever no stderr `q-cli: estratégia opencode-subagent ainda não implementada; seguindo para a próxima` e seguir para o item seguinte: `["opencode-subagent", "orca-worker"]` com LaForge Claude e codex disponível devolve `codex`.
- **R5** - IF nenhum item da lista dá um Q (ex.: `["opencode-subagent"]`, ou `["orca-worker"]` sem CLI de outra família disponível) THEN `q_cli` SHALL devolver `None` e o comando `q-cli` SHALL imprimir `self-verified` e sair com 1.
- **R6** - WHEN `STARCODE_HOME` aponta para um config do usuário válido com `"qStrategy": ["self-verified"]` THEN o comando `q-cli --laforge claude:claude-sonnet-5-5` SHALL imprimir `self-verified` e sair com 1; com o config inválido, ou sem o campo, SHALL seguir R1.
- **R7** - The system SHALL deixar `skills/config/SKILL.md` oferecendo `qStrategy` só com `orca-worker` e `self-verified`, `schemas/config.md` dizendo que `opencode-subagent` é aceito mas pulado pelo `q-cli` (ainda não implementado), e o passo 4 de `skills/engajar/references/execute.md` dizendo que o `q-cli` segue o `qStrategy` do config do usuário quando o campo existe.
- **R8** - The system SHALL ter no `DECISIONS.md` a entrada da issue desta feature (`### SC-185:`) com **Problema**, **Decisão**, **Motivo** e **Por que não é bug** citando os testes, e uma linha em `CHANGELOG.md` `[Unreleased]`.

## Edge Cases
- Lista só com `self-verified`: R3 (C3).
- `opencode-subagent` como único item: R5 (C5).
- Config inválido: R6 (C6), cai em R1.
- `self-verified` no fim da lista, sem worker disponível: R5.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Sem lista de estratégias (`None`), `q_cli` devolve `codex` para LaForge Claude com codex disponível, como hoje (R1)
Proof: run unit | test_q_strategy_none_keeps_current_order (test_dispatch.FamilyAndQCliTests.test_q_strategy_none_keeps_current_order) ... ok

**C2** - Teste de tabela: `["orca-worker"]` e `["orca-worker", "self-verified"]` devolvem `codex` (R2)
Proof: run unit | test_q_strategy_orca_worker_walks_cli_order (test_dispatch.FamilyAndQCliTests.test_q_strategy_orca_worker_walks_cli_order) ... ok

**C3** - `["self-verified", "orca-worker"]` devolve `None` com codex disponível (R3)
Proof: run unit | test_q_strategy_self_verified_first_wins (test_dispatch.FamilyAndQCliTests.test_q_strategy_self_verified_first_wins) ... ok

**C4** - `["opencode-subagent", "orca-worker"]` devolve `codex` e o stderr tem o aviso exato de R4 (R4)
Proof: run unit | test_q_strategy_opencode_subagent_skipped_with_warning (test_dispatch.FamilyAndQCliTests.test_q_strategy_opencode_subagent_skipped_with_warning) ... ok

**C5** - `["opencode-subagent"]`, e `["orca-worker"]` sem CLI de outra família, devolvem `None` (R5)
Proof: run unit | test_q_strategy_nothing_available_is_self_verified (test_dispatch.FamilyAndQCliTests.test_q_strategy_nothing_available_is_self_verified) ... ok

**C6** - Comando `q-cli` com `STARCODE_HOME` num config válido `["self-verified"]` imprime `self-verified` com exit 1; com config inválido segue R1 (R6)
Proof: run unit | test_q_cli_command_reads_user_qstrategy (test_dispatch.FamilyAndQCliTests.test_q_cli_command_reads_user_qstrategy) ... ok

**C7** - Skill `config`, schema e execute.md com os textos de R7 (R7)
Proof: run unit | test_q_strategy_docs_match_implementation (test_dispatch.FamilyAndQCliTests.test_q_strategy_docs_match_implementation) ... ok

**C8** - `DECISIONS.md` atualizado depois da mudança em `scripts/` (R8)
Proof: `python scripts/check_decisions.py` | check_decisions: OK

## Handoff

**Phase:** execute
**Size:** MÉDIA
**Git mode:** 3
**Next:** LaForge implementa T1 (SC-185)
**Linear:** SC-185
**Integration branch:** feature/q-strategy
**Last integrated:** none
**Dispatched:** T1 · SC-185 · base 9f16c68 · claude:claude-sonnet-5-5 · 2026-11-16T11:32:00Z · ctx_c3d0b715f49e
**Settled:** 2026-11-16: spec + issue: "sim"
**Attempts:** none
**Reports:** none
**Breaker:** closed
