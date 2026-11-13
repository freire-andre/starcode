# Despacho da MÉDIA e escopo com DECISIONS.md: Context

**Size**: MEDIUM
**Risk triggers**: Concorrência e estado (entradas `Dispatched` do Handoff)
**Source request**: "PROXIMO PASSO" (passo 2 do primeiro corte da seção 12 de `starcode-triagem-v2-2026-11-13.md`: itens R.7 e R.6)

## Problem
- **R.7:** o brief acrescenta `DECISIONS.md` ao May change de ticket que mexe em `scripts/` (`effective_may_change`, `scripts/dispatch.py:108`), mas `scripts/gates/check_scope.py` lê o May change sem o acréscimo (`task.may_change` em tasks.md; `spec_may_change` na MÉDIA). O worker obedece ao brief, altera o `DECISIONS.md` e o gate do ticket reprova.
- **R.6:** `dispatch.py start` e `settle` chamam `load_tasks`, que exige `tasks.md`. Numa feature MÉDIA (7 de 18 features do repositório), o `FileNotFoundError` não é tratado (`main` só pega `LookupError`, `ValueError` e `ScreenError`) e o comando sai com 1, que o fluxo lê como "worker-start falhou" ou "gate vermelho". No modo 1 o `start` recusa por falta de `**Integration branch:**` sem dizer o caminho certo; e na nova tentativa depois de um `settle` vermelho a entrada mantida faz o `start` recusar com 2, enquanto `execute.md` manda usar o comando nos três casos.
- Nesta sessão (feature `gate-d30-ci`) a MÉDIA foi despachada à mão: `dispatch.py brief` com o ID da issue, `worker-start` manual e `handoff.py --dispatch-add`; a integração foi `run_gates.py ticket` + `git merge --no-ff` manuais.

## Users
O Picard (quem coordena o fluxo) e o dono do repositório, que hoje despacha e integra a MÉDIA à mão.

## Success
- Ticket de `scripts/` que altera `DECISIONS.md` passa no `check_scope`, na MÉDIA e na GRANDE.
- `start` e `settle` nunca terminam em traceback nem em código 1 por falta de `tasks.md`.
- `execute.md` descreve o caminho de cada caso: GRANDE, MÉDIA, modo 1 e nova tentativa.

## Constraints
- Congelamento D-i: nenhum comando, skill ou perfil novo.
- Ticket em `scripts/` lista `DECISIONS.md` no May change (R.7 ainda aberto durante a feature).
- `dist/` só por `python tools/build.py`.
- Artefatos e gates pelo código do repositório.
- `execute.md` é verificado por testes de texto (`tests/test_execute_doc_start_settle.py`, `tests/test_skills_exec.py`): conferir antes de mudar.

## Scope Notes
- Dentro: R.7 (`check_scope` usa a mesma regra do brief) e R.6 (`start`/`settle` na MÉDIA, no modo 1 e na nova tentativa; `execute.md` com o caminho de cada caso).
- Fora: item 3.5 (caminho da PEQUENA), R.8 (mensagens e códigos de outras falhas do `start`/`settle`, trava de arquivo), 3.4 (escrita concorrente de `sessions.json`).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| MÉDIA no `start`/`settle` | aceitar (ticket único lido da spec: `**Linear**:` e `**May change**:`) / recusar com código 2 e mensagem apontando o caminho manual | user: "Aceitar a MÉDIA (Recommended)": ticket único lido da spec; o ID do ticket é o `**Linear**:` da spec (ou `T1`) | 2026-11-13 |
| Modo 1 no `start` | aceitar sem ramo de integração / recusar com código 2 e mensagem que aponta a seção 7 do `execute.md` | recusar com 2 e apontar a seção 7, porque no modo 1 não há commit nem worktree filho · default (não perguntado) | 2026-11-13 |
| Nova tentativa | opção nova no `start` / `execute.md` manda `handoff.py set --dispatch-remove <T>` antes do novo `start`, como já faz a seção 2F passo 8 | só o texto do `execute.md` (seção 3), porque o congelamento D-i não quer opção nova · default (não perguntado) | 2026-11-13 |
| `FileNotFoundError` em outros subcomandos | tratar só no `start`/`settle` / tratar no `main` para todos | tratar no `main`: sai com 2 e `dispatch: <arquivo> não encontrado` · default (não perguntado) | 2026-11-13 |
| Regra de `DECISIONS.md` no `check_scope` | só tasks.md / tasks.md e spec da MÉDIA | as duas, e o `spec_brief` passa a pôr `DECISIONS.md` como o brief da GRANDE (hoje não põe: `scripts/dispatch.py:370`) · default (não perguntado) | 2026-11-13 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Failure and partial failure | Falta de `tasks.md` ou de `spec.md` sai com 2 e mensagem, antes de gravar o Handoff ou chamar a Orca. |
| Retries, idempotency and duplicates | O `start` continua recusando com 2 quando o ticket já tem entrada em `Dispatched`; a mensagem cita o `--dispatch-remove` como saída. |
| State-transition rules | Na MÉDIA, o `settle` remove só a entrada do próprio ticket e grava `Last integrated`, como na GRANDE. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `scripts/dispatch.py:102-124`: `needs_decisions`, `effective_may_change`, `with_decisions`; `spec_brief` (`:355`) já gera o brief da MÉDIA a partir da spec, com `Issue:` do `**Linear**:`.
- `scripts/dispatch.py:662-750` (`start`) e `:758-810` (`settle`) começam com `load_tasks`; `start` recusa sem `**Integration branch:**` (`:683`) e com entrada aberta (`:681`).
- `scripts/gates/check_scope.py:95-111`: a MÉDIA aceita o ticket `T1` ou o ID do Linear da spec e lê `spec_may_change`; a GRANDE lê `task.may_change`. Nenhuma das duas aplica `effective_may_change`.
- `skills/engajar/references/execute.md`: seção 2 (sequencial), 2F passo 8 (falha: `--dispatch-remove`), seção 3 (falha e nova tentativa sem `--dispatch-remove`), seção 7 (modo 1), seção 8 (MÉDIA e PEQUENA: integração "como no passo 3", sem citar `start`/`settle`).
- Decisões relacionadas: F12-11, F12-13, F12-14, F12-15, SC-167 em `DECISIONS.md`.
