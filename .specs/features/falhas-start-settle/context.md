# Falhas-start-settle: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "próximo passo" (missão 3 do passo 4 da seção 12 da triagem v2: itens R.8 e N.6)

## Problem
- **R.8**: falhas do `dispatch.py start` e do `settle` saem com mensagem ou código errado. A triagem lista quatro casos:
  1. `orca` fora do PATH dava traceback com código 1. **Já resolvido** em `dcadac4`: o `_call` trata `OSError` como código 127, e o `start` remove a entrada (`tests/test_dispatch_start.py:185`).
  2. Recibo do `worker-start` com texto antes do JSON: o `_receipt` (`scripts/dispatch.py:741-749`) devolve recibo vazio, e o `start` sai com 0 e `worker iniciado: T1 · ... · -`, sem id de despacho.
  3. Toda falha do `git merge` no `settle` imprime `conflito no merge de <T>` (`scripts/dispatch.py:924-930`), mesmo sem conflito (árvore suja, ramo inexistente).
  4. Dois `handoff.py set` simultâneos (dois `settle`) leem, mudam e gravam o artefato sem trava (`scripts/handoff.py:213-256`), e um pode apagar a mudança do outro.
- **N.6**: não há helper único de `git` com tempo limite. `snapshot.py:53`, `impact.py:37` e `dispatch.py:137` têm cada um a sua função de `git`, sem `timeout`. `starcode_common.git` (`scripts/starcode_common.py:39`) tem timeout de 5 s, mas devolve só o stdout ou `None`, e perde o código e o erro.

## Users
- O Picard, que lê a saída do `start` e do `settle` para decidir o próximo passo.
- Os scripts do plugin que chamam `git`.

## Success
- Recibo sem id de despacho: o `start` sai com 3 e diz que o worker pode estar ativo sem registro.
- Falha de merge sem conflito: a mensagem traz o erro real do `git`, não `conflito`.
- Dois `handoff.py set` simultâneos não perdem nenhuma mudança.
- Um `git` travado não prende `snapshot.py`, `impact.py` nem `dispatch.py` para sempre.

## Constraints
- N.6, decisão da triagem: a função única é adotada primeiro pelos scripts novos (`snapshot.py`, `impact.py`, `dispatch.py`). Os antigos migram quando forem tocados.
- D30: entrada no `DECISIONS.md`.
- A trava reusa o `starcode_common.locked` da SC-202 (item 3.4).

## Scope Notes
- Dentro:
  - R.8, casos 2, 3 e 4;
  - o caso 1 só ganha confirmação de que segue resolvido;
  - N.6 nos três scripts citados.
- Fora: migrar `check_decisions.py`, `check_proofs.py`, `check_scope.py`, `run_gates.py` e `validate_verification.py` (N.6: só quando forem tocados).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Recibo com texto antes do JSON | ler o objeto JSON a partir do primeiro `{` e, sem id, sair com 3 / só sair com 3 | ler a partir do primeiro `{`; sem id de despacho, código 3 — default (não perguntado) | 2026-11-21 |
| Tempo limite do helper de `git` | 5 s (como `sc.git`) / 30 s / configurável | 30 s por padrão, com parâmetro; o `sc.git` do banner fica com 5 s — default (não perguntado) | 2026-11-21 |
| Retorno do helper | `(código, stdout, stderr)` / exceção | `(código, stdout, stderr)`; tempo esgotado vira código 124 com `git excedeu <n> s: <comando>` no stderr — default (não perguntado) | 2026-11-21 |
| Merge do `settle` | só a mensagem / também o código | conflito (arquivos `U`) segue `conflito no merge de <T>: <arquivos>`; sem arquivo `U`, `merge de <T> falhou: <erro do git>`; código 1 nos dois — default (não perguntado) | 2026-11-21 |
| Trava do Handoff | por artefato / por feature | por feature (um `<pasta da feature>/.handoff.lock`), porque o `set` pode mover a seção entre artefatos — default (não perguntado) | 2026-11-21 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Failure and partial failure | Recibo sem id de despacho: o worker pode estar rodando, então a entrada fica e o código é 3, como no caso já existente de registro incompleto. |
| Concurrency and ordering | O `handoff.py set` lê, muda e grava dentro da trava. Trava ocupada por mais de 5 s: sai com 2 e a mensagem do `locked`. |
| External dependency failure | `git` travado: o helper desiste no tempo limite e devolve 124. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `scripts/dispatch.py:703-709`: `_call` trata `OSError` como 127 (caso 1 resolvido, `dcadac4`).
- `scripts/dispatch.py:741-749`: `_receipt` usa `json.loads(out)` e devolve tudo vazio com `ValueError`.
- `scripts/dispatch.py:856-866`: com recibo sem id, o `start` grava a entrada sem id e devolve 0.
- `scripts/dispatch.py:924-930`: qualquer falha do merge imprime `conflito`.
- `scripts/handoff.py:213-256`: `set_handoff` lê os artefatos, muda e grava sem trava.
- `scripts/starcode_common.py:150`: `locked(path, timeout=5.0)`, trava de SO em `<arquivo>.lock` (SC-202).
- `scripts/starcode_common.py:24,39-45`: `GIT_TIMEOUT = 5` e `git()`, que devolve stdout ou `None`.
- `scripts/snapshot.py:53-63`, `scripts/impact.py:37-46` e `scripts/dispatch.py:137-140`: funções de `git` próprias, sem `timeout`. Há também chamadas soltas de `git` em `snapshot.py:69,217` e `dispatch.py:495,523`.
