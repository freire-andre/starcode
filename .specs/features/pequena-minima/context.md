# Caminho da PEQUENA (MÉDIA mínima): Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "Lote 3, começando por 3.1 e 3.5 (seção 6 da triagem). [...] No 3.5, trate junto o item R.6 da triagem (dispatch.py start/settle para MÉDIA, modo 1 e nova tentativa). Antes, confirme o que ainda falha, porque nesta sessão o start já funcionou com MÉDIA."

## Problem
Hoje a PEQUENA não tem caminho que funcione. O `execute.md` (seção 8) manda o worker usar os "checks inline" e o `May change` "da spec", mas a PEQUENA não tem spec. O `validate_spec.py` recusa `**Size**: SMALL` (linhas 109-110). O `dispatch.py start`/`settle` só conhecem `tasks.md` ou spec MÉDIA. Por isso o despacho, o gate `ticket` e o `done` de uma PEQUENA acabam feitos à mão. Na SC-189, por exemplo, os checks ficaram no context.md, o `check_scope` não rodou e o escopo foi conferido à mão. O piloto manda a PEQUENA para esse mesmo caminho.

## Users
O Picard (o fluxo) e o dono do repositório, que pede tarefas pequenas.

## Success
Uma PEQUENA vai do dimensionamento ao `done` só com os comandos do fluxo. A spec mínima é gerada pelo Picard e passa no gate de spec. `dispatch.py start`/`settle` tratam a PEQUENA como T1, igual à MÉDIA. O gate `ticket` confere o `May change`. O `run_gates.py done` aceita o Q dispensado.

## Constraints
- Decisão do dono D-a (triagem v1, linhas 32, 75 e 86): a D23 fica, ou seja, a PEQUENA sempre vai para um worker e o Picard nunca implementa. O Picard gera uma spec de poucas linhas (`Scope`, `Checks`, `**May change**:`) sem Troi e sem aprovação. O gate `ticket` da F7-11 vale para ela. O Q é dispensado, e o `verification.md` registra isso de um jeito que o `done` aceite.
- O `Size` do Handoff aceita a classe. O vocabulário é único: PEQUENA no chat, SMALL nos marcadores (`gates_common.py:38` já mapeia as duas formas).
- Os evals de dimensionamento (`evals/risk-sizing/`) continuam verdes. Os critérios de classe não mudam.
- Entrada no `DECISIONS.md` (D30). O `dist/` é regenerado com `tools/build.py`.

## Scope Notes
- Dentro: o item 3.5 e o resíduo do R.6. O R.6 já foi resolvido no passo 2 do primeiro corte: os 97 testes do dispatch passam, a MÉDIA vira T1, o modo 1 e a nova tentativa recusam com mensagem clara (DECISIONS.md, linhas 1015-1019). Falta a PEQUENA usar o mesmo caminho do T1.
- Fora: o item 3.1 (fase pr-review), que é a missão seguinte. Também fica fora o modo 1 da PEQUENA, que segue as regras da seção 7 já existentes.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Como o `done` trata o Q dispensado | verde, e a issue vai a Done / igual a degradada | Verde, e a issue vai a Done. O marcador é `**Verification:** waived (PEQUENA)`, mostrado como aviso inclusive com `--strict`, e só vale se a spec for SMALL. Com outro Size é erro | 2026-11-19 |
| Guinan e Worf na PEQUENA | Worf sim e Guinan não / os dois / nenhum | O Worf continua (é a única revisão independente). A Guinan é dispensada | 2026-11-19 |
| Quem escreve o `verification.md` da PEQUENA | Picard por script / à mão | Um comando de script grava o arquivo com o marcador, nunca edição à mão: default (não perguntado) | 2026-11-19 |
| Aprovação da spec mínima | sem linha `Approved` / com linha | Sem aprovação (D-a). O gate de spec aceita SMALL sem `**Approved**` e exige `Scope`, `## Checks`, `**May change**:` e `**Linear**:`: default (não perguntado) | 2026-11-19 |
| Issue do Linear | obrigatória / opcional | Obrigatória, porque o `start` exige `**Linear**:`. A criação continua com confirmação, como manda o engajar (PEQUENA: no momento): default (não perguntado) | 2026-11-19 |
| Provas | rodam / dispensadas | `run_gates.py proofs` roda normalmente. Só o Q é dispensado: default (não perguntado) | 2026-11-19 |
| Válvula de segurança | mantém 5 passos / muda | Fica. Uma spec mínima com mais de 5 checks ou mais de 3 arquivos no `May change` reclassifica a tarefa para MÉDIA: default (não perguntado) | 2026-11-19 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| State-transition rules | Na PEQUENA, o caminho é: spec mínima, dispatch, settle, proofs, `waived` no verification.md, done, Worf e merge, sem a fase do Q nem a Guinan. O Handoff grava `Size: SMALL` |
| Input validation and limits | `waived` com spec que não é SMALL vira erro no `done`. Spec SMALL sem `**May change**:` ou sem `**Linear**:` vira erro no gate de spec |
| Failure and partial failure | Um `start` ou `settle` que falha na PEQUENA segue as mesmas regras da MÉDIA (exit 2/1/3) |
| demais dimensões | N/A para este escopo |

## Facts Found
- `scripts/gates/validate_spec.py:109-110`: recusa SMALL.
- `scripts/gates/gates_common.py:38`: mapeia PEQUENA → SMALL.
- `scripts/gates/validate_verification.py:46,202,285`: só conhece `degraded` e `self-verified`.
- `scripts/dispatch.py:353,724`: o caminho da MÉDIA (sem `tasks.md`, T1 vindo do `**Linear**:`).
- `skills/engajar/references/execute.md:242-256` (seção 8), `skills/engajar/SKILL.md:92-105` (rota), `skills/engajar/references/risk-sizing.md:23,45`, `skills/piloto-automatico/SKILL.md:22`.
- `tests/test_gates.py:58-60`: hoje asserta que SMALL é recusado na spec e precisa mudar.
- `evals/risk-sizing/`: 4 casos PEQUENA (só a classe, não o fluxo).
