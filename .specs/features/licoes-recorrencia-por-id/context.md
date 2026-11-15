# Lições com recorrência por ID: Context

**Size**: MEDIUM
**Risk triggers**: dados persistidos
**Source request**: "PROXIMO PASSO do primeiro corte da triagem (@starcode-triagem-v2-2026-11-13.md): passo 10, N.1"

Item N.1 da triagem v2: "As lições nunca são promovidas. O ciclo Guinan → lições → briefs não fecha (...) A Guinan lista as candidatas antes de escrever (`lessons.py list --status candidate`) e, quando o achado é o mesmo, registra a recorrência pelo ID (`lessons.py add --id L<n> --feature <slug> --source ...`). Reprocessar as 26 atuais uma vez, juntando as repetidas."

## Problem
A recorrência de uma lição só é reconhecida quando o texto normalizado é idêntico (`scripts/lessons.py:190-191`). A Guinan escreve uma frase nova a cada retro, então o mesmo achado vira uma candidata nova em vez de somar features à lição existente. As candidatas não entram nos briefs (`scripts/dispatch.py:417-424` usa só `confirmed`) e são podadas em 45 dias sem recorrência. O ciclo Guinan → lições → briefs quase não fecha.

## Users
A Guinan, que registra as lições; os workers LaForge, que recebem as lições confirmadas no brief; o dono do repositório, que lê `.specs/LESSONS.md`.

## Success
- A Guinan consegue registrar a recorrência de um achado numa lição que já existe pelo ID, mesmo com uma frase diferente, e a lição é promovida ao chegar a 2 features distintas.
- A Guinan consulta as candidatas antes de escrever e reusa o ID quando o achado é o mesmo.
- As lições atuais repetidas são reprocessadas uma vez, e as recorrências reais viram `confirmed`.

## Constraints
- Congelamento D-i (triagem, linha 99): nenhuma skill, comando ou perfil novo até o fim do primeiro corte. A opção `--id` no `add` é a que a triagem prevê; um subcomando novo não cabe.
- Só o `lessons.py` escreve `.specs/lessons.json` e `.specs/LESSONS.md`; nada à mão.
- Mudança em `scripts/` e `skills/` exige entrada no `DECISIONS.md` (check_decisions) e o `dist` regenerado.

## Scope Notes
- Dentro: `lessons.py add --id L<n>`; o passo 3 da Guinan (`skills/guinan/SKILL.md`) passa a listar as candidatas antes e a reusar o ID; o reprocessamento único das lições atuais.
- Fora: mudar o limiar (`promote_threshold` = 2), a janela de poda (45 dias), o formato do `lessons.json` ou a seção de lições do brief.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Destino das lições repetidas no reprocessamento | (a) `add --id` no ID canônico e as repetidas ficam como candidatas até a poda; (b) remover as repetidas, o que exige um comando novo ou editar o JSON | (a) "Ficam até a poda" | 2026-11-15 |
| `add --id` com ID inexistente | sai com 2 (`id inválido`), nada escrito | default (não perguntado) | 2026-11-15 |
| `add --id` com lição `quarantined` | sai com 2; uma lição em quarentena não volta por recorrência | default (não perguntado) | 2026-11-15 |
| `--text` junto com `--id` | opcional e ignorado para a busca; o texto da lição existente não muda | default (não perguntado) | 2026-11-15 |
| `--signal` junto com `--id` | continua obrigatório e validado, mas não muda o sinal gravado | default (não perguntado) | 2026-11-15 |
| Quais grupos juntar | o Spock lista os grupos na spec (ID canônico = o menor ID do grupo) e o usuário aprova junto com a spec | default (não perguntado) | 2026-11-15 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | `--id` aceita só `L<n>` existente (sem diferença de caixa, como no `penalize`); a validação de `--feature`, `--source` e `--signal` fica igual |
| Retries, idempotency and duplicates | repetir o mesmo `add --id` com a mesma feature e a mesma fonte não muda nada além de `updated`; uma feature já registrada não conta duas vezes |
| Failure and partial failure | `lessons.json` inválido continua saindo com 2 sem sobrescrever |
| Demais dimensões | N/A para este escopo |

## Facts Found
- `.specs/lessons.json` tem 40 lições: 4 `confirmed` (L2 x3, L20 x4, L4 x2, L25 x2) e 36 `candidate`. A triagem dizia 26 e nenhuma confirmed; isso está desatualizado.
- Grupos visíveis de repetição: asserção por trecho em vez do texto inteiro (L2, L20, L18, L21, L24, L26, L37, L38, L39), entrada do DECISIONS.md com termos incompletos (L32, L34), DECISIONS.md fora do ciclo (L3).
- `cmd_penalize` já procura o ID sem diferença de caixa (`scripts/lessons.py:216-219`).
- Os testes ficam em `tests/test_lessons.py` e `tests/test_dispatch_lessons.py`.
