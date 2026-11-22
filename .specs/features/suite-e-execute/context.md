# Suíte rápida, regra de estado e execute.md dividido: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "Missão 7b do passo 4 (MÉDIA), no ramo já criado feature/suite-e-execute (base main 0acdd54, commit 582aa97 com o Handoff de versao-e-retro em done). Itens: N.3 (medir a suíte com --durations; conjunto rápido para o ciclo de correção do worker via impact.py, no lugar da "suíte inteira" em dispatch.py; a suíte inteira só no done e no CI), N.7 (regra no AGENTS.md: estado novo é JSON escrito por script, com markdown gerado) e N.8 (dividir o execute.md, ~3.977 palavras, por etapa: despacho, provas e Q, pós-Q e review, modo 1, retomada)."

## Problem
A suíte leva cerca de 25 min no F: (1.083 testes em 1.519 s, 2026-11-21) e uma MÉDIA a roda de 3 a 4 vezes (fim do LaForge, correção pós-Q, regressão do Q, gate de done): de 75 a 100 min por feature só esperando testes. O `execute.md` tem 3.977 palavras e o Picard o carrega inteiro em toda feature. O estado novo não segue um padrão único (`lessons.py` guarda JSON; `piloto.py` guarda markdown lido por regex).

## Users
O dono do repositório, que roda o fluxo StarCode; o Picard (carrega o `execute.md`); os workers LaForge/McCoy (rodam testes no ciclo de correção).

## Success
- O worker (ticket e correção pós-Q) roda a seleção do `impact.py`, não a suíte inteira; `rodar tudo` ou seleção indisponível continuam caindo na suíte inteira.
- A suíte inteira roda no gate de done (prova `Run unit`) e no CI.
- O tempo da suíte medido com `--durations` fica anotado, com a linha de base de 1.519 s.
- `AGENTS.md` tem a regra de estado novo em JSON escrito por script, com markdown gerado; o Handoff fica como está.
- O `execute.md` vira um índice curto que aponta um arquivo por etapa; o Picard carrega só a etapa em que está.

## Constraints
- `dist/` é gerado por `python tools/build.py`; mudança em `skills/`, `scripts/` ou `hooks/` exige entrada no `DECISIONS.md` (D30).
- Vários testes leem o texto do `execute.md` (test_dispatch, test_flow_f12, test_flow_worf_guinan, test_fecha_achado, test_licoes_no_brief, test_execute_doc_start_settle, test_pequena_minima, test_crew_live, test_dispatch_qcheck, test_brief_media_escopo, test_build); a divisão não pode perder nenhuma frase que eles exigem.
- Referências por seção (`execute.md` seção 6, 7, 8, 2F) em `SKILL.md` do engajar, `state-format.md`, `piloto-automatico/SKILL.md`, `src/context/STARCODE.md` e no texto de `dispatch.py:839` precisam continuar resolvendo.

## Scope Notes
- Dentro: N.3, N.7, N.8 como descritos na fonte.
- Fora (triagem/plano): o Handoff continua markdown (N.7 adiado); o worktree no C: para o gate do Orca; `settle --fix` e regras fixas no `q-brief` (eram da 7.4, fora desta missão).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Alcance da otimização no N.3 | (a) só medir e anotar + trocar a suíte pela seleção no worker; (b) também acelerar os testes mais lentos do `--durations` | "Só medir e trocar" (a); acelerar testes fica para depois da pausa | 2026-11-22 |
| Forma da divisão do N.8 | `execute.md` vira índice (seções 0 e 1 ficam) + arquivos planos `references/execute-<etapa>.md` (despacho, provas-e-q, pos-q-e-review, retomada, modo-1, e media-pequena para a seção 8, que tem 415 palavras); testes passam a ler o conjunto | default (não perguntado) | 2026-11-22 |
| Conjunto rápido | a seleção do `impact.py` (`select --diff <base>`), sem marcar testes à mão | default (não perguntado) | 2026-11-22 |
| Onde a troca entra | `FIX_RULES` (pós-Q) e `WORKER_RULES` (ticket) do `dispatch.py`, mais a linha do McCoy "The gates still run the whole suite" ajustada | default (não perguntado) | 2026-11-22 |
| Onde anotar o tempo | no Handoff da feature e no `DECISIONS.md` | default (não perguntado) | 2026-11-22 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| External dependency failure | `impact.py` falhando ou dizendo `rodar tudo` faz o worker rodar a suíte inteira (nunca conjunto vazio). |
| Observability | o relatório do worker traz a linha de veredito do `impact.py`. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `scripts/dispatch.py:1009` (`FIX_RULES`): "a suíte inteira verde" na correção pós-Q. `WORKER_RULES` (`scripts/dispatch.py:95`) não cita a suíte; o LaForge roda o `Gate` da spec.
- `scripts/dispatch.py:517` (`regression_block`) já calcula a seleção do `impact.py` para o brief do Q, com fallback "rode a suíte inteira".
- `scripts/impact.py`: `select --diff <base>[..<head>]`; dúvida vira "rodar tudo".
- `skills/mccoy/SKILL.md:36-39`: McCoy já usa o `impact.py` (R31).
- Specs recentes põem a suíte inteira como `**Run unit**` (ex.: `.specs/features/versao-e-retro/spec.md:53`), que o gate de proofs/done roda.
- CI: `.github/workflows/ci.yml:46` roda `python -m unittest discover -s tests -v`.
- `execute.md` tem as seções 0–8 mais "Review (Worf)" e "Text for the PR" (`grep '^#'`).
