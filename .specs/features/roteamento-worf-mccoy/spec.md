# Roteamento do worf e do mccoy fora do StarCode: Spec

**Approved**: 2026-11-19 - user: "Sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-203
**May change**: skills/worf/SKILL.md, skills/mccoy/SKILL.md, evals/routing/, evals/README.md, tests/test_evals_f9.py, tests/test_worf_skill.py, skills/piloto-automatico/SKILL.md, tests/test_roteamento_worf_mccoy.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Esta spec cobre o item 3.3 da triagem v2. O discovery está em `.specs/features/roteamento-worf-mccoy/context.md`. As descrições do `worf` e do `mccoy` têm gatilhos genéricos, sem StarCode ("review do PR", "revise esse PR", "esse teste não passa", "investigue o bug"), e o eval de roteamento não tem quase-acertos nem os pares `config` × `setup` e `piloto-automatico` × `engajar`.

## Scope
- Descrições do `worf` e do `mccoy` presas ao contexto do StarCode.
- 3 casos novos no `evals/routing/`, o README e o teste de contagem.

## Non-Goals
- Mudar outras descrições.
- Mudar o grader ou o formato dos casos.

## Decisions
| Item | Options | User answer |
|---|---|---|
| `pos-piloto-automatico` falhou no eval (foi para o `engajar`) | dar gatilhos ao piloto / tirar o caso e abrir issue / manter falhando | approved - user: "Dar gatilhos ao piloto (Recomendado)" |
| Causa real: `invocation: user` no `src/crew.yaml` vira `disable-model-invocation: true` | liberar o modelo (both) / manter só o usuário | approved - user: "Manter só o usuário (Recomendado)": o caso sai, o R6 volta à descrição anterior |

Os demais casos novos estão no `context.md` (Gray Areas) e valem com a aprovação desta spec.

## Requirements
- **R1** - The `description` do `skills/worf/SKILL.md` SHALL citar só gatilhos com StarCode, Worf ou o Picard (sem "review do PR" e sem "revise esse PR" sozinhos) e SHALL terminar com uma frase "Not for" que inclua `a generic pull request review outside StarCode`.
- **R2** - The `description` do `skills/mccoy/SKILL.md` SHALL citar só gatilhos com StarCode, McCoy, o LaForge ou um ticket do StarCode (sem "esse teste não passa" e sem "investigue o bug" sozinhos) e SHALL terminar com uma frase "Not for" que inclua `generic debugging outside StarCode`.
- **R3** - The `evals/routing/` SHALL ter 3 casos novos no formato dos atuais (`schema_version`, `name`, `description`, `tags`, `execution.prompt`, `max_turns: 3`, `allowed_tools: [Skill, Read, Glob, Grep]`, `runs: 1`, graders `tool_used`):
  - `neg-worf-generic-pr`: prompt "Revise o PR #42 e me diga o que acha.", grader `starcode:worf` com `max: 0`;
  - `neg-mccoy-generic-test`: prompt "Esse teste não passa: test_soma falha com AssertionError. O que pode ser?", grader `starcode:mccoy` com `max: 0`;
  - `pos-config-model`: prompt "Quero trocar o modelo do LaForge para o Kimi só neste projeto do StarCode.", graders `starcode:config` com `min: 1` e `starcode:setup` com `max: 0`;
- **R4** - The `evals/README.md` SHALL mostrar o novo total de casos de roteamento (`36 frases`) e listar os 3 casos novos. The `tests/test_evals_f9.py` SHALL aceitar o novo caso negativo do `worf` sem perder o que já confere.
- **R6** - The `description` do `skills/piloto-automatico/SKILL.md` SHALL ficar como estava antes desta feature: o piloto é só do usuário (`invocation: user` no `src/crew.yaml`, `disable-model-invocation: true` no `dist/`), e o roteamento por frase não se aplica a ele.
- **R5** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-<n>:` com **Problema**, **Decisão** (os gatilhos tirados das duas descrições, as frases "Not for", os 3 casos e o piloto só do usuário), **Motivo** e **Por que não é bug** (com os testes), mais uma linha em `CHANGELOG.md` `[Unreleased]`.

## Edge Cases
- Os positivos existentes do `worf` e do `mccoy` citam o nome da skill e continuam valendo (R1, R2).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - A descrição do `worf` não tem os gatilhos genéricos, cita StarCode e termina com o "Not for" exigido (R1)
Proof: run unit | test_descricao_worf (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_descricao_worf) ... ok

**C2** - A descrição do `mccoy` não tem os gatilhos genéricos, cita StarCode e termina com o "Not for" exigido (R2)
Proof: run unit | test_descricao_mccoy (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_descricao_mccoy) ... ok

**C3** - Os 3 casos novos existem com o prompt exato, os campos fixos e os graders com `min`/`max` exigidos (R3)
Proof: run unit | test_casos_novos (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_casos_novos) ... ok

**C4** - O README mostra `36 frases` e lista os 3 casos; o `test_evals_f9` continua conferindo worf, guinan e diagnostico com o novo negativo (R4)
Proof: run unit | test_readme_e_contagem (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_readme_e_contagem) ... ok

**C5** - Entrada no `DECISIONS.md` com os quatro campos, os termos da Decisão, os testes e a linha no CHANGELOG (R5)
Proof: run unit | test_decisions_roteamento (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_decisions_roteamento) ... ok

**C6** - A descrição do `piloto-automatico` é a mesma da `main` (R6)
Proof: run unit | test_descricao_piloto (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_descricao_piloto) ... ok

## Handoff

**Phase:** review
**Size:** MEDIUM
**Git mode:** 3
**Next:** proofs e done --strict; Guinan; PR
**Linear:** SC-203
**Integration branch:** feature/roteamento-worf-mccoy
**Last integrated:** c3e9e2f
**Dispatched:** none
**Settled:** 2026-11-19: spec aprovada: Sim; issue SC-203 criada; eval: casos novos e vizinhos
**Attempts:** none
**Reports:** 2026-11-19: eval: 12/13; pos-piloto-automatico foi para o engajar; usuário: dar gatilhos ao piloto (R6); 2026-11-19: piloto: invocation user impede o roteamento; usuário: manter só o usuário (caso sai, R6 reverte); 2026-11-19: R6 revertido em c3e9e2f; eval: 12/12 nos casos novos e vizinhos que ficam; 2026-11-19: Q r1 FAIL: 6 achados (testes frouxos C1-C6; README sobre o alcance dos negativos); 2026-11-19: pós-Q: d5e81b1, 89c1491; achados fechados com close-finding
**Breaker:** closed
