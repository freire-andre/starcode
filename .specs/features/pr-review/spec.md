# Fase pr-review do Worf: Spec

**Approved**: 2026-11-19 - user: "Sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-198
**May change**: scripts/handoff.py, skills/engajar/references/execute.md, skills/engajar/references/state-format.md, skills/guinan/SKILL.md, skills/piloto-automatico/SKILL.md, tests/test_pr_review.py, tests/test_flow_worf_guinan.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Esta spec cobre o item 3.1 da triagem v2. O discovery está em `.specs/features/pr-review/context.md`. Hoje o `--phase done` é gravado antes do PR (`skills/engajar/references/execute.md:182`), e o banner trata `done` como concluída (`hooks/scripts/banner.py:118-120`). Por isso a retomada no meio do Worf não vê a feature. A correção do Worf não manda rodar os gates de novo, e a Guinan roda antes de existir `review.md`. A F9-5 (Guinan antes do PR, Worf depois do PR) fica como está.

## Scope
- Fase `pr-review` no Handoff, entre o PR aberto e o merge.
- Gates `proofs` e `done` no novo HEAD depois de cada correção do Worf.
- Guinan em modo só lições depois da última rodada do Worf.
- `piloto.py encerrar` na parada da autorização de merge.

## Non-Goals
- Mudar a ordem da F9-5.
- O `post_review.py` e o subcomando da coluna `Closed` (item 3.7).
- Mudar o banner: qualquer fase diferente de `done` já aparece como em andamento.

## Decisions
| Item | Options | User answer |
|---|---|---|
| Quando o `piloto.py encerrar` roda | depois da última rodada do Worf / antes do PR | approved - user: "Depois da última rodada (Recomendado)" |
| Lições dos achados do Worf | Guinan só lições no fim / Picard registra direto | approved - user: "Guinan só lições no fim (Recomendado)" |

## Requirements
- **R1** - The system SHALL aceitar `pr-review` em `handoff.py set --phase`, na ordem de `PHASES` entre `review` e `done`. Uma fase fora da lista SHALL continuar sendo recusada como hoje.
- **R2** - WHEN o PR é aberto (modos 3 e 4) THEN o `execute.md` SHALL mandar gravar `--phase pr-review`, e `--phase done` SHALL vir só depois do merge, ou da recusa explícita do merge pelo usuário. Nos modos 1 e 2, sem PR, o `--phase done` SHALL continuar logo depois da Guinan.
- **R3** - WHEN uma correção do LaForge para achados do Worf é integrada THEN a seção "Review (Worf)" do `execute.md` SHALL mandar rodar `run_gates.py proofs <slug>` e `run_gates.py done <slug>` no novo HEAD antes da rodada seguinte do Worf, e gravar `--report "Worf r<N> <veredito>"` a cada rodada.
- **R4** - WHEN a última rodada do Worf termina (APPROVE, ou rodada 3) e o `review.md` tem achado `blocker` ou `should-fix` corrigido ou confirmado em qualquer rodada THEN o `execute.md` SHALL mandar invocar a Guinan em modo só lições. O `skills/guinan/SKILL.md` SHALL ter esse modo: registra só as lições de `review_finding` pelo `lessons.py` e não reescreve o `retro.md`. Sem esse achado, a Guinan não SHALL ser invocada.
- **R5** - WHILE o piloto automático está ativo the `piloto-automatico/SKILL.md` SHALL manter o piloto durante as rodadas do Worf e mandar rodar `piloto.py encerrar` na parada da autorização de merge, depois da última rodada e das lições.
- **R6** - The `state-format.md` SHALL listar `pr-review` na linha `**Phase:**` e ter na tabela de retomada uma linha para `pr-review`: ler o `review.md` (rodada e veredito) e seguir com a correção do LaForge ou a próxima rodada do Worf, ou com o pedido da autorização de merge.
- **R7** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-<n>:` desta issue com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**. A **Decisão** SHALL citar a F9-5 (mantida), a fase `pr-review`, os gates depois de cada correção, a Guinan só lições e o momento do `piloto.py encerrar`. O **Por que não é bug** SHALL citar os testes. SHALL ter também uma linha em `CHANGELOG.md` `[Unreleased]`.

## Edge Cases
- Rodada 3 com achado aberto: para sem pedir o merge, e a fase continua `pr-review` (R2, R3).
- Feature PEQUENA: o Worf continua e a Guinan está dispensada, então as lições do Worf também não rodam (R4 segue a dispensa da D-a).
- Retomada com `pr-review` e o PR já mergeado: o Git manda, então grava `done` (R6).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `handoff.py set --phase pr-review` grava a fase, `PHASES` tem `pr-review` entre `review` e `done`, e uma fase desconhecida é recusada (R1)
Proof: run unit | test_fase_pr_review (test_pr_review.PrReviewTests.test_fase_pr_review) ... ok

**C2** - O `execute.md` grava `pr-review` na abertura do PR e `done` só depois do merge; modos 1 e 2 seguem com `done` depois da Guinan (R2)
Proof: run unit | test_execute_fase_pr_review (test_pr_review.PrReviewTests.test_execute_fase_pr_review) ... ok

**C3** - A seção "Review (Worf)" manda `proofs` e `done` no novo HEAD depois de cada correção e o `--report` da rodada (R3)
Proof: run unit | test_execute_gates_apos_correcao_worf (test_pr_review.PrReviewTests.test_execute_gates_apos_correcao_worf) ... ok

**C4** - Guinan só lições depois da última rodada, no `execute.md` e no `guinan/SKILL.md`, sem reescrever o `retro.md` e só com achado blocker ou should-fix (R4)
Proof: run unit | test_guinan_licoes_do_review (test_pr_review.PrReviewTests.test_guinan_licoes_do_review) ... ok

**C5** - O piloto encerra na parada da autorização de merge, depois da última rodada do Worf (R5)
Proof: run unit | test_piloto_encerra_apos_worf (test_pr_review.PrReviewTests.test_piloto_encerra_apos_worf) ... ok

**C6** - O `state-format.md` lista `pr-review` e tem a linha de retomada (R6)
Proof: run unit | test_state_format_pr_review (test_pr_review.PrReviewTests.test_state_format_pr_review) ... ok

**C7** - Entrada no `DECISIONS.md` com os quatro campos, os termos da Decisão, os testes citados e a linha no CHANGELOG (R7)
Proof: run unit | test_decisions_pr_review (test_pr_review.PrReviewTests.test_decisions_pr_review) ... ok

## Handoff

**Phase:** review
**Size:** MEDIUM
**Git mode:** 3
**Next:** Correção pós-Q única (LaForge)
**Linear:** SC-198
**Integration branch:** feature/pr-review
**Last integrated:** 10154e8
**Dispatched:** none
**Settled:** 2026-11-19: spec aprovada: Sim; issue SC-198 criada
**Attempts:** none
**Reports:** 2026-11-19: Q r1 FAIL: 5 achados (merge após r3 aberta; retomada com PR mergeado; Guinan exclui corrigidos; asserções frouxas C1/C3/C7)
**Breaker:** closed
