# Roteamento do worf e do mccoy fora do StarCode: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "Sim" (lote 3 da triagem v2, item 3.3: "Descrições de `worf` e `mccoy` [...] Agora são 17 skills. Incluir no eval de roteamento casos de `config` × `setup` e de `piloto-automatico` × `engajar`"; triagem v1: "Casos negativos novos de quase-acerto ('revise o PR #42' num repositório sem `.starcode/`) passam no eval de roteamento rodado localmente")

## Problem
As descrições do `worf` e do `mccoy` trazem gatilhos genéricos, sem StarCode: "review do PR" e "revise esse PR" no `skills/worf/SKILL.md:3`; "esse teste não passa" e "investigue o bug" no `skills/mccoy/SKILL.md:3`. Um pedido comum de review ou de bug, num repositório qualquer, pode carregar a skill da tripulação. O efeito no roteamento nunca foi medido: o eval de roteamento (`evals/routing/`, 33 casos) não tem quase-acerto para essas duas skills, nem casos de `config` × `setup` e de `piloto-automatico` × `engajar`.

## Users
Quem usa o plugin num repositório com ou sem StarCode.

## Success
As duas descrições só disparam com contexto do StarCode (nome da skill, da tripulação ou do fluxo). O eval ganha os quase-acertos e os pares vizinhos, e passa rodado localmente.

## Constraints
- As descrições seguem o padrão das outras skills (inglês, gatilhos entre aspas, "Not for ...").
- Os positivos existentes (`pos-worf-review-pr`, `pos-worf-security`, `pos-mccoy-bug`) continuam passando.
- Entrada no `DECISIONS.md` (D30). O `dist/` é regenerado.

## Scope Notes
- Dentro: as descrições do `worf` e do `mccoy`, 4 casos novos no `evals/routing/`, o `evals/README.md` e o teste de contagem `tests/test_evals_f9.py`.
- Fora: mudar outras descrições; os demais itens do lote 3.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Casos novos | só os quase-acertos / quase-acertos e pares vizinhos | 4 casos: `neg-worf-generic-pr` ("Revise o PR #42 e me diga o que acha."), `neg-mccoy-generic-test` ("Esse teste não passa: test_soma falha com AssertionError. O que pode ser?"), `pos-config-model` (trocar o modelo do LaForge → `config`, nunca `setup`) e `pos-piloto-automatico` (rodar a feature no piloto automático → `piloto-automatico`, nunca `engajar`): default (não perguntado) | 2026-11-19 |
| Rodar o eval | rodar localmente / só estrutura | Rodar `claude plugin eval dist/claude --tag routing --ablation none` localmente (37 casos, `max_turns: 3`) e colar o resultado no PR: perguntado na aprovação | 2026-11-19 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| demais dimensões | N/A para este escopo (texto de descrição e casos de eval) |

## Facts Found
- `skills/worf/SKILL.md:3`, `skills/mccoy/SKILL.md:3` (descrições atuais).
- `evals/routing/<caso>/case.yaml` (grader `tool_used`, `input_match: "starcode:<skill>"`, `min`/`max`).
- `tests/test_evals_f9.py:12-29` conta exatamente 9 casos de worf, guinan e diagnostico; `:31-35` confere `33 frases` no README.
- `skills/piloto-automatico/SKILL.md` não tem `disable-model-invocation`; a descrição diz "Only the user invokes it".
