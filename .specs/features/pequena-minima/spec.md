# Caminho da PEQUENA (MÉDIA mínima): Spec

**Approved**: 2026-11-19 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-197
**May change**: scripts/gates/validate_spec.py, scripts/gates/validate_verification.py, scripts/gates/gates_common.py, scripts/dispatch.py, skills/engajar/SKILL.md, skills/engajar/references/execute.md, skills/engajar/references/risk-sizing.md, skills/engajar/references/state-format.md, skills/piloto-automatico/SKILL.md, tests/test_pequena_minima.py, tests/test_gates.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Esta spec cobre o item 3.5 da triagem v2 e a decisão do dono D-a. O discovery está em `.specs/features/pequena-minima/context.md`. Hoje a PEQUENA não tem caminho que funcione. O `validate_spec.py` recusa `**Size**: SMALL` (linhas 109-110). O `execute.md` (seção 8) manda o worker usar "checks inline" e o `May change` de uma spec que não existe. O `done` só conhece `degraded` e `self-verified`. Do R.6 resta só isto: o `dispatch.py start`/`settle` já trata uma feature sem `tasks.md` como `T1`, porque decide pela falta do `tasks.md` (`scripts/dispatch.py:746`), então uma spec SMALL entra nesse mesmo caminho.

## Scope
- Spec mínima da PEQUENA, gerada pelo Picard, sem Troi e sem aprovação, aceita pelo gate de spec e pelo `execute`.
- Despacho e integração da PEQUENA pelo `dispatch.py start`/`settle`, como `T1`.
- Q dispensado e registrado por comando, aceito pelo `done`.
- Texto do fluxo (engajar, execute, risk-sizing, state-format, piloto), com o vocabulário PEQUENA no chat e SMALL nos marcadores.

## Non-Goals
- O item 3.1 (fase `pr-review`), que é a próxima missão.
- O modo 1 da PEQUENA, que segue a seção 7 do `execute.md` sem mudança.
- Mudar os critérios de classe do `risk-sizing.md` ou os casos de `evals/risk-sizing/`.

## Decisions
| Item | Options | User answer |
|---|---|---|
| Divisão do 3.1 e do 3.5 | 2 missões, 3.5 antes / 3.1 antes / 1 GRANDE | approved - user: "2 missões, 3.5 antes (Recomendado)" |
| `done` com o Q dispensado | verde, e a issue vai a Done / igual a degradada | approved - user: "Verde, issue vai a Done (Recomendado)" |
| Guinan e Worf na PEQUENA | Worf sim e Guinan não / os dois / nenhum | approved - user: "Worf sim, Guinan não (Recomendado)" |

## Requirements
- **R1** - WHEN a spec tem `**Size**: SMALL` (ou `PEQUENA`) THEN o `validate_spec` SHALL exigir só `## Scope` não vazia, `## Checks` com ao menos um check, `**May change**:` e `**Linear**:` com um ID. Cada item que faltar SHALL gerar um erro que o nomeia. As demais seções do template breve não SHALL ser exigidas.
- **R2** - IF uma spec SMALL tem mais de 5 checks, ou mais de 3 entradas no `**May change**:` sem contar `DECISIONS.md`, `CHANGELOG.md` e entradas terminadas em `/`, THEN o `validate_spec` SHALL dar o erro `PEQUENA passou do limite (<n> checks, <m> arquivos): reclassifique para MÉDIA`.
- **R3** - WHEN a spec é SMALL THEN `run_gates.py execute` e o `validate_verification` (gate `done`) SHALL aceitar a spec sem a linha `**Approved**`. Uma spec MEDIUM, LARGE ou COMPLEX sem a linha SHALL continuar dando erro.
- **R4** - WHEN a feature tem spec SMALL e não tem `tasks.md` THEN `dispatch.py brief`, `start` e `settle` SHALL funcionar como na MÉDIA: o ticket é `T1` ou o ID do `**Linear**:`, o brief traz o `## Checks` e o `## BOUNDARIES` do `May change`, e o `settle` roda o gate `ticket` antes do merge.
- **R5** - WHEN o Picard roda `dispatch.py q-waive <slug>` numa feature com spec SMALL THEN o comando SHALL gravar `verification.md` com a linha `**Verification:** waived (PEQUENA)` e a frase `Q dispensado: tarefa PEQUENA (D-a).`, e sair com 0. IF a spec não é SMALL THEN o comando SHALL sair com 2 e `q-waive recusado: só a PEQUENA dispensa o Q (Size: <size>)`, sem gravar nada.
- **R6** - WHEN o `verification.md` tem `**Verification:** waived` e a spec é SMALL THEN o `validate_verification` SHALL aceitar o arquivo sem tabela de checks nem de achados e dar só o aviso `Q dispensado (PEQUENA)`, que continua aviso com `--strict`. O `proofs.md` SHALL continuar exigido como hoje. IF a spec não é SMALL THEN `waived` SHALL dar o erro `**Verification:** waived só vale para a PEQUENA`.
- **R7** - The system SHALL descrever o caminho da PEQUENA no fluxo. O `execute.md` (seção 8) traz o template da spec mínima, o despacho por `start`/`settle`, `run_gates.py proofs`, `dispatch.py q-waive`, `done`, o Worf no PR e a dispensa da Guinan. A rota do `engajar/SKILL.md` e a linha `Flow` da PEQUENA no `risk-sizing.md` dizem "spec mínima do Picard + LaForge (Q dispensado)". O `state-format.md` aceita `Size: SMALL` no Handoff. O `piloto-automatico/SKILL.md` manda a PEQUENA para esse caminho. Nenhum desses arquivos contém "inline checks" nem "checks inline".
- **R8** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-<n>:` desta issue com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**. A **Decisão** SHALL citar a D-a, a spec mínima sem aprovação, `q-waive`, o marcador `waived (PEQUENA)` e a dispensa da Guinan. O **Por que não é bug** SHALL citar os testes. SHALL ter também uma linha em `CHANGELOG.md` `[Unreleased]`, e o `tests/test_gates.py` SHALL deixar de assertar que SMALL é recusado.

## Edge Cases
- Spec SMALL com `**Approved**`: aceita, porque a linha é opcional (R3).
- `q-waive` rodado duas vezes: grava o mesmo conteúdo de novo, sem erro (R5).
- `waived` junto com `degraded` no mesmo arquivo: vale o `degraded`, com a regra de hoje (R6).
- Spec SMALL num repo com `tasks.md`: o `tasks.md` manda, como na MÉDIA (R4).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Spec SMALL mínima passa no gate de spec, e cada item que falta (Scope, Checks, May change, Linear) dá um erro que o nomeia (R1)
Proof: run unit | test_spec_small_minima (test_pequena_minima.PequenaTests.test_spec_small_minima) ... ok

**C2** - Mais de 5 checks ou mais de 3 arquivos (sem contar DECISIONS, CHANGELOG e pastas) dá o erro de reclassificação (R2)
Proof: run unit | test_spec_small_limite (test_pequena_minima.PequenaTests.test_spec_small_limite) ... ok

**C3** - `execute` e `done` aceitam SMALL sem `**Approved**`; MEDIUM sem a linha continua com erro (R3)
Proof: run unit | test_small_sem_aprovacao (test_pequena_minima.PequenaTests.test_small_sem_aprovacao) ... ok

**C4** - `brief`, `start` (runner falso) e `settle` tratam a spec SMALL como `T1` (R4)
Proof: run unit | test_dispatch_small_t1 (test_pequena_minima.PequenaTests.test_dispatch_small_t1) ... ok

**C5** - `q-waive` grava o marcador na SMALL e recusa com 2 e a mensagem exata em outra classe (R5)
Proof: run unit | test_q_waive (test_pequena_minima.PequenaTests.test_q_waive) ... ok

**C6** - `done` verde com `waived` e spec SMALL, também com `--strict`; erro com `waived` em MEDIUM; `proofs.md` continua exigido (R6)
Proof: run unit | test_done_waived (test_pequena_minima.PequenaTests.test_done_waived) ... ok

**C7** - Os textos do fluxo citam a spec mínima, `q-waive` e a dispensa da Guinan, e nenhum contém "inline checks" nem "checks inline" (R7)
Proof: run unit | test_textos_fluxo_pequena (test_pequena_minima.PequenaTests.test_textos_fluxo_pequena) ... ok

**C8** - Entrada no `DECISIONS.md` com os quatro campos, os termos da Decisão, os testes citados e a linha no CHANGELOG (R8)
Proof: run unit | test_decisions_pequena_minima (test_pequena_minima.PequenaTests.test_decisions_pequena_minima) ... ok

## Handoff

**Phase:** review
**Size:** MEDIUM
**Git mode:** 3
**Next:** Correção pós-Q única (LaForge), depois proofs e done
**Linear:** SC-197
**Integration branch:** feature/pequena-minima
**Last integrated:** 9978cbe
**Dispatched:** none
**Settled:** 2026-11-19: spec aprovada: sim; issue SC-197 criada
**Attempts:** none
**Reports:** 2026-11-19: Q r1 FAIL: 3 achados (waivedness aceito; prova C4 sem settle; C7 Worf sem PR)
**Breaker:** closed
