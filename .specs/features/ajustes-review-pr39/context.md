# Ajustes do review do PR #39: Context

**Size**: MEDIUM
**Risk triggers**: Concurrency and state
**Source request**: "segue com a SC-167"

## Problem
O review do PR #39 (`.specs/features/manutencao-retros-f11/review.md`, W1 e W2) apontou duas inconsistências deixadas pela manutenção das retros:

- **W1:** o gate das tasks (`uncovered_citations` em `scripts/gates/validate_tasks.py`) e o `check_scope` (`allowed` em `scripts/gates/check_scope.py`) usam regras de cobertura diferentes. Uma entrada com glob no May change (ex.: `tests/test_*.py`) é aceita pelo `check_scope`, mas uma citação `tests/test_x.py` no TASK é dada como fora do May change pelo gate das tasks.
- **W2:** no `dispatch.py start`, se a segunda gravação do Handoff (a que traz o dispatch id e o modelo do recibo) falhar depois de um `worker-start` bem-sucedido, o `ValueError` vira exit 2, o código de "recusado". O worker já está rodando e a entrada em `Dispatched` fica sem o dispatch id, sem que a saída diga isso.

## Users
O Picard (coordenador), que despacha e retoma tickets com `dispatch.py start` e roda o gate `tasks`; quem escreve tasks com glob no May change (Data).

## Success
- Toda citação do TASK coberta pelo `check_scope.allowed` também é coberta pelo gate das tasks, e vice-versa nas regras de pasta e de caminho exato, mantendo as recusas do R20/R21 (`..`, caminho absoluto) e a regra do nome sem pasta.
- Um `start` cuja segunda gravação falha sai com um código próprio, diferente de 0, 1 e 2, e imprime uma linha que diz que há worker ativo, com ticket, dispatch id e worktree, para o Picard registrar à mão.

## Constraints
- Sem mudar o contrato existente do `start`: 0 sucesso, 1 `worker-start` falhou (entrada removida), 2 recusado antes de gravar ou chamar a Orca.
- `check_scope.py` importa `validate_tasks.py` (`vt`): a regra compartilhada não pode criar import circular.
- Mudanças em `scripts/` exigem entrada no `DECISIONS.md` e `dist/` regenerado (`tools/build.py`).

## Scope Notes
- Dentro: W1 e W2 da SC-167, a documentação do novo código de saída no `skills/engajar/references/execute.md` e os testes.
- Fora: W3 (`noqa` sem link de issue; a main já usa o padrão) e as 6 sugestões da retro da manutencao-retros-f11.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Código de saída do W2 | 3 · outro número | default (não perguntado): exit 3, o mesmo número que o `dispatch.py next` usa para "despacho aberto"; aqui significa "worker ativo com registro incompleto" | 2026-11-13 |
| Entrada em `Dispatched` quando a 2ª gravação falha | manter a 1ª (sem id) · remover | default (não perguntado): manter a entrada da 1ª gravação (o worker existe; removê-la esconderia o worker) | 2026-11-13 |
| Linha impressa no W2 | texto livre · formato fixo | default (não perguntado): `worker ativo sem registro completo: <T> · <dispatch id> · <worktree>: <primeira linha do erro>`, e o passo `worktree set` ainda é tentado | 2026-11-13 |
| Onde fica a regra de cobertura comum | `gate_common` · duplicada | default (não perguntado): uma função em `scripts/gates/gate_common.py` usada pelos dois gates | 2026-11-13 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Failure and partial failure | W2 é exatamente a falha parcial: worker iniciado e registro incompleto; o código 3 e a linha de aviso a tornam visível, e o `--json` traz o `dispatch` mesmo nesse caso. |
| Input validation and limits | W1: o glob segue `fnmatch` sobre o caminho normalizado, como o `check_scope`; `..` e caminho absoluto continuam nunca cobertos. |
| State-transition rules | W2: a entrada fica em `Dispatched` com a base e o `cli:model` pedidos; o Picard completa o id com `handoff.py set --dispatch-add`. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `allowed()` em `scripts/gates/check_scope.py:40-49`: pasta (`/` no fim) por prefixo, senão igualdade ou `fnmatch`.
- `uncovered_citations()` em `scripts/gates/validate_tasks.py:82-100`: igualdade, pasta por prefixo, nome sem pasta; sem `fnmatch`.
- `start()` em `scripts/dispatch.py:647-724`: `record()` levanta `ValueError` quando o `handoff.py` falha; `main()` converte `ValueError` em exit 2 (`scripts/dispatch.py:902-904`).
- Contrato atual do `start` no `execute.md` (linha 44): "Exit 2 = refused; exit 1 = `worker-start` failed (entry removed)".
- `dispatch.py next` já usa exit 3 para "despacho aberto" (`scripts/dispatch.py:174`).
