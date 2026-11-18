# Ações pendentes da retro da fase 9: Context

**Size**: MEDIUM
**Risk triggers**: none (componentes: gate do review e uma retro; MÉDIA por ter código e teste em mais de um lugar)
**Source request**: "proximo passo" (item 1.6 da triagem v2; escopo escolhido: "Só a fase 9 (Recomendado)")

## Problem
A retro `.specs/features/fase-9-worf-guinan-diagnostico/retro.md` tem 7 ações, e nenhuma tem estado registrado.

## Success
Cada uma das 7 ações aparece como feita (com commit), recusada (com motivo) ou aberta (com issue). A 3 e a 7 ficam feitas.

## Scope Notes
- Entra: ação 3 (`require_text` com teste de tabela) e ação 7 (`--help` nos scripts de `scripts/review/`, com smoke test); conferir 1, 2, 5 e 6 e registrar o estado de todas.
- Fora: o mecanismo de estado para todas as retros (N.2, seção 7) e as outras 20 retros.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Escopo do 1.6 | só a fase 9 / fase 9 + mecanismo N.2 / tudo | "Só a fase 9 (Recomendado)" | 2026-11-17 |
| Onde fica o `require_text` | no próprio `review_gate.py`, no lugar do `blank()` (é o único gate que valida campos de texto livre) | default (não perguntado) |  |
| Onde registrar o estado | coluna `Estado` na tabela da retro da fase 9 (só nela) | default (não perguntado) |  |
| Ações abertas | uma issue no Linear para cada ação aberta, citada na coluna | default (não perguntado) |  |

## Facts Found
- Ação 1: o brief cita `run_gates.py` por `sc.PLUGIN_ROOT` (`scripts/dispatch.py:87`, `:371`, `:453`). Rodando o `dispatch.py` do repo, esse caminho é o checkout principal, que é o problema descrito. Também não há seção "Worktree", e o `run_gates.py ticket` não recusa um HEAD no ramo de integração. **Aberta.**
- Ação 2: nenhum caminho de material de referência no config nem no brief (`schemas/config.md`). **Aberta.**
- Ação 3: o `blank()` de `scripts/review/review_gate.py:87` já trata `[]` (correção 9e7679a), mas falta o helper com nome e o teste de tabela.
- Ação 4: feita na SC-189 (PR #63, merge 7609e5e).
- Ação 5: o `validate_tasks` já recusa caminho do TASK fora do May change (`scripts/gates/validate_tasks.py:224`). A parte do Data (procurar `assertNotIn("<skill>"` nos testes) não existe. **Parcial.**
- Ação 6: o `dispatch.py settle` exige `--branch` (`scripts/dispatch.py settle --help`). **Aberta.**
- Ação 7: `python scripts/review/review_gate.py --help` sai com 1; `post_review.py` e `scan_bypasses.py` saem com 0.
