# Ações pendentes da retro da fase 9: Spec

**Approved**: 2026-11-17 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-190
**May change**: scripts/review/review_gate.py, scripts/review/scan_bypasses.py, tests/test_review_gate.py, .specs/features/fase-9-worf-guinan-diagnostico/retro.md, DECISIONS.md, CHANGELOG.md, dist/

## Context
Item 1.6 da triagem v2, só a retro da fase 9. Discovery: `.specs/features/retro-fase9/context.md`.
- As 7 ações de `.specs/features/fase-9-worf-guinan-diagnostico/retro.md` não têm estado.
- A ação 3 pede um helper `require_text` com teste de tabela.
- A ação 7 pede `--help` nos scripts de `scripts/review/`; hoje `review_gate.py --help` sai com 1.

## Scope
- Ação 3: `require_text(value)` no `review_gate.py`, no lugar do `blank()`, com teste de tabela.
- Ação 7: `review_gate.py` com `argparse`, e um smoke test que roda com `--help` cada script de `dist/claude/scripts/review/`.
- Coluna `Estado` na tabela da retro da fase 9, preenchida nas 7 linhas.

## Non-Goals
- Fazer as ações 1, 2, 5 e 6: elas ficam abertas, cada uma com uma issue.
- O mecanismo de estado para todas as retros (N.2) e as outras 20 retros.
- Mudar o comportamento do `review_gate.py` além do `--help` (as mesmas violações, os mesmos códigos de saída).

## Decisions
| Item | Options | User answer |
|---|---|---|
| Escopo do 1.6 | só a fase 9 / fase 9 + mecanismo N.2 / tudo | approved - user: "Só a fase 9 (Recomendado)" |

## Requirements
- **R1** - The system SHALL ter em `scripts/review/review_gate.py` a função `require_text(value) -> bool`, que devolve True só para uma `str` com algum caractere que não seja espaço. Para `None`, `""`, `"   "`, `[]`, `{}`, `0` e `False` ela SHALL devolver False. O `check_finding` SHALL usá-la em todo campo que hoje passa pelo `blank()`, e o `blank()` SHALL deixar de existir.
- **R2** - WHEN `review_gate.py --help` (ou `-h`) roda THEN the system SHALL imprimir o uso, que cita `review.json`, e sair com 0.
- **R3** - WHEN `review_gate.py` roda sem argumento ou com mais de um THEN the system SHALL sair com código diferente de 0, sem gravar nada. WHEN roda com um caminho THEN SHALL manter a mesma saída e os mesmos códigos de hoje (0 sem violação, 1 com violação ou com JSON ilegível).
- **R4** - The system SHALL ter um teste que roda cada `dist/claude/scripts/review/*.py` com `--help` e exige exit 0 para todos. Um script novo na pasta entra no teste sem lista fixa.
- **R5** - The system SHALL ter na tabela de `.specs/features/fase-9-worf-guinan-diagnostico/retro.md` uma coluna `Estado`, preenchida nas 7 linhas com uma das formas: `feito em <commit ou PR>`, `recusado: <motivo>` ou `aberto: SC-<n>`. As linhas 3 e 7 SHALL citar o commit desta feature, a 4 SHALL citar a SC-189 e as linhas 1, 2, 5 e 6 SHALL citar a issue aberta de cada uma: SC-191, SC-192, SC-193 e SC-194, nessa ordem.
- **R6** - The system SHALL ter no `DECISIONS.md` a entrada da issue desta feature (`### SC-190:`) com **Problema**, **Decisão** (R1 a R5, com os valores da tabela de `require_text` e o exit 0 do `--help`), **Motivo** e **Por que não é bug** citando os testes. SHALL ter também uma linha em `CHANGELOG.md` `[Unreleased]`.

## Edge Cases
- `require_text` com `0` ou `False`: False (não é texto), R1 (C1).
- `review_gate.py` com o caminho de um arquivo chamado `--help`: fora do escopo; o `argparse` trata `--help` como opção.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Tabela de `require_text`: True para texto, False para `None`, `""`, espaço, `[]`, `{}`, `0` e `False`; `blank` não existe mais (R1)
Proof: run unit | test_require_text_tabela (test_review_gate.ReviewGateTests.test_require_text_tabela) ... ok

**C2** - `--help` e `-h` saem com 0 e citam `review.json` (R2)
Proof: run unit | test_help_sai_com_zero (test_review_gate.ReviewGateTests.test_help_sai_com_zero) ... ok

**C3** - Sem argumento e com dois argumentos o exit é diferente de 0; com um caminho, a saída e os códigos 0 e 1 continuam os de hoje (R3)
Proof: run unit | test_uso_e_codigos_mantidos (test_review_gate.ReviewGateTests.test_uso_e_codigos_mantidos) ... ok

**C4** - Todo `dist/claude/scripts/review/*.py` responde a `--help` com exit 0 (R4)
Proof: run unit | test_scripts_de_review_respondem_help (test_review_gate.ReviewGateTests.test_scripts_de_review_respondem_help) ... ok

**C5** - A coluna `Estado` da retro da fase 9 tem as 7 linhas em uma das três formas, com 3 e 7 feitas, 4 na SC-189 e 1, 2, 5 e 6 abertas com issue (R5)
Proof: run unit | test_retro_fase9_estado (test_review_gate.ReviewGateTests.test_retro_fase9_estado) ... ok

**C6** - Entrada do `DECISIONS.md` com os quatro campos, os termos de R1 a R5 na Decisão, testes citados e linha no CHANGELOG (R6)
Proof: run unit | test_decisions_retro_fase9 (test_review_gate.ReviewGateTests.test_decisions_retro_fase9) ... ok

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** LaForge implementa T1 (SC-190)
**Linear:** SC-190
**Integration branch:** feature/retro-fase9
**Last integrated:** 65952cc9f2221323462519b6c210622a80570071
**Dispatched:** T1-fix · SC-190 · base ee2562f · claude:claude-sonnet-5-5 · 2026-11-17T23:19:30Z · ctx_729a8b46d9f5
**Settled:** 2026-11-17: spec + 5 issues: "sim" (SC-190; ações abertas SC-191, SC-192, SC-193, SC-194); 2026-11-17: May change ampliado com scripts/review/scan_bypasses.py (Picard: --help lê o stdin depois do uso e trava com stdin aberto, contra R4)
**Attempts:** none
**Reports:** 2026-11-17: T1: 42adc6d, ca07cc9, b2dba54, 897934b (require_text, argparse, --help do scan_bypasses sem ler stdin, coluna Estado); 966 OK; ticket gate verde rodado pelo Picard contra o May change ampliado; 2026-11-17: provas verdes; 2026-11-17: Q: codex · effective unconfirmed · FAIL, 5 achados (caminho iniciado por hífen rejeitado, contra R3; C1, C3, C5, C6 fracos); 966 OK. q-check 1 por docs/fluxograma-starcode.svg não rastreado, criado às 20:14 fora do fluxo (nenhum teste ou script o gera): não é do Q, fica intocado e fora dos commits
**Breaker:** closed
