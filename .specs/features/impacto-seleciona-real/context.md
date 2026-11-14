# Raio de impacto que seleciona de verdade: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "Próximo passo" → passo 7 do primeiro corte: R.1 e R.2 de `starcode-triagem-v2-2026-11-13.md`

## Problem
- **R.1:** todo intervalo de feature inclui arquivos de `.specs/` (`proofs.md`, Handoff), que estão fora do grafo. `scripts/impact.py:346-352` manda rodar tudo quando há mudado fora do grafo, e `dispatch.regression_block` (`scripts/dispatch.py:461-470`) passa o intervalo inteiro. Três features já integradas deram "rodar tudo".
- **R.2:** `select` (`:372-374`) só roda tudo quando nenhum teste é alcançado. Se um mudado alcança testes e outro não, o segundo é ignorado. `is_test_file` (`:74-83`) conta qualquer `.py` em `tests/` como teste, inclusive `helpers.py`, `conftest.py` e `__init__.py`. Testes que rodam um script por subprocesso não o importam e ficam fora (mudança em `scripts/scaffold.py` deixa de fora 2 testes).

## Users
O McCoy (seleção antes do gate) e o brief do Q (bloco de regressão). Os gates continuam com a suíte inteira.

## Success
Num intervalo típico de feature de um projeto (código + `.specs/`), a seleção sai com os testes certos em vez de "rodar tudo". Nenhum mudado fica sem teste real sem que o veredito vire "rodar tudo". Testes que citam o script por nome entram na seleção.

## Constraints
- Congelamento D-i: nenhuma opção ou comando novo.
- Regra de dúvida do F12: na dúvida, "rodar tudo"; a seleção só pode ficar mais larga.
- Reabre F12 R15 (`is_test_file`, `DECISIONS.md` ~891) por decisão do usuário.
- Regras de TS/JS (imports e aliases) inalteradas, salvo o padrão de teste já existente.

## Scope Notes
- Dentro: R.1 (`.specs/` fora da lista de mudados), R.2 (rodar tudo se algum mudado não alcança teste real; apoio em `tests/` não conta como teste) e a referência textual para subprocesso.
- Fora: mudanças em TS/JS, nos gates, no McCoy ou no `dispatch.py` (o chamador não muda), e qualquer coisa nova.

## Gray Areas

| Item | Options | User answer | Date |
|---|---|---|---|
| Testes que rodam o script por subprocesso | referência textual / só a regra da triagem | Referência textual: teste cujo texto cita o nome do arquivo mudado entra na seleção ("Referência textual") | 2026-11-14 |
| O que conta como teste real em Python | `test_*.py` ou `*_test.py` / qualquer `.py` em `tests/` menos 3 nomes | `test_*.py` ou `*_test.py`; os demais `.py` de `tests/` são apoio: propagam no grafo, mas não contam como teste ("test_*.py ou *_test.py") | 2026-11-14 |
| Forma da referência textual | nome do arquivo (basename) / caminho relativo | basename do mudado (ex.: `scaffold.py`) aparecendo no texto de um teste real; colisões de nome só alargam a seleção. Default (não perguntado) | 2026-11-14 |
| Referência textual conta para a regra de R.2 | sim / não | sim: um mudado alcançado só por referência textual já alcança teste real. Default (não perguntado) | 2026-11-14 |
| Intervalo que só muda `.specs/` | rodar tudo / seleção vazia | rodar tudo com motivo `nenhuma mudança fora de .specs/` (nunca conjunto vazio). Default (não perguntado) | 2026-11-14 |
| Referência textual em teste TS/JS | vale para todo teste real / só Python | vale para todo teste real (só alarga). Default (não perguntado) | 2026-11-14 |

## Implicit Requirements

| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | Teste real acima de 1 MiB ou ilegível já invalida o grafo (`grafo incompleto`); a leitura para a referência textual segue o mesmo limite |
| Observability | O motivo do "rodar tudo" de R.2 nomeia os mudados sem teste real; a cadeia de um teste achado por referência textual mostra o mudado e o teste |

Demais dimensões: N/A para este escopo.

## Facts Found
- `scripts/impact.py`: `changed_from_diff` (`:67-71`), `is_test_file` (`:74-83`), `select` (`:334-382`); `conftest.py` mudado já roda tudo (`:342-344`).
- `tests/test_impact.py:89-94` `test_identifica_testes_python_e_ts` afirma hoje que `tests/helpers.py` e `test/x/y.py` são testes; muda de sentido por decisão do usuário.
- `tests/test_impact.py:205` `test_impact_no_repo_starcode` usa o repositório real (seleção para `gates_common.py`, "rodar tudo" para `README.md`).
- Nenhum teste lê o `.specs/` real do repositório: os testes com `.specs/` montam repositórios temporários.
- Chamadores de `select`: `dispatch.regression_block` e o McCoy (`skills/mccoy/SKILL.md:37`).
- No repositório do StarCode, toda feature toca `dist/` e `DECISIONS.md` (fora do grafo), e o "rodar tudo" continua correto ali.
