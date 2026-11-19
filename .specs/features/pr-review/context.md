# Fase pr-review do Worf: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "Próximo passo" (lote 3 da triagem v2, item 3.1: "Fase própria para o review do Worf, gates depois de cada correção, lições do review [...] O nome `review` já é a fase do Q; usar outro (ex.: `pr-review`). Definir junto quando o `piloto.py encerrar` roda em relação às rodadas do Worf (liga ao 0.5)")

## Problem
O `--phase done` é gravado antes do PR (`skills/engajar/references/execute.md:182`). Por isso, uma sessão que retoma no meio das rodadas do Worf não vê a feature em andamento: o banner a dá por concluída. A seção "Review (Worf)" manda uma rodada do LaForge para os achados, mas não manda rodar `run_gates.py proofs` e `done` no novo HEAD. A Guinan roda antes do PR (F9-5), quando ainda não existe `review.md`, então um achado confirmado do Worf nunca vira lição. E o piloto automático não diz se continua ativo durante as rodadas do Worf.

## Users
O Picard (fluxo) e o dono do repositório, que retoma sessões entre as rodadas do Worf.

## Success
Do PR aberto até o merge, o Handoff marca `**Phase:** pr-review`, e a retomada mostra essa fase com a rodada do Worf. Cada correção do Worf termina com `proofs` e `done` verdes no novo HEAD. Depois da última rodada, a Guinan registra as lições dos achados confirmados. O piloto encerra na parada da autorização de merge.

## Constraints
- A F9-5 fica: a Guinan roda antes do PR (retro) e o Worf, depois do PR. `tests/test_flow_worf_guinan.py` confere essa ordem.
- O nome `review` já é a fase do Q (`scripts/handoff.py:45-46`, `execute.md:134`). A fase nova se chama `pr-review`.
- Entrada no `DECISIONS.md` citando a F9-5 (D30). O `dist/` é regenerado.

## Scope Notes
- Dentro: o item 3.1 inteiro e o momento do `piloto.py encerrar`.
- Fora: mudar a ordem da F9-5; o `post_review.py` (422 em APPROVE no próprio PR); o subcomando de `Closed` (item 3.7).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Quando o `piloto.py encerrar` roda | depois da última rodada do Worf / antes do PR | Depois da última rodada: o piloto segue ativo nas rodadas do Worf e encerra na parada da autorização de merge | 2026-11-19 |
| Lições dos achados do Worf | Guinan só lições no fim / Picard registra direto | A Guinan roda de novo depois da última rodada, só para registrar as lições de `review_finding`, sem reescrever o `retro.md` | 2026-11-19 |
| Quando a fase vira `done` | depois do merge / depois do APPROVE | Depois do merge (ou da recusa explícita do merge pelo usuário). Nos modos 1 e 2, sem PR, `done` logo depois da Guinan, como hoje: default (não perguntado) | 2026-11-19 |
| Gates depois da correção do Worf | `proofs` + `done` no novo HEAD / só os testes | `run_gates.py proofs` e `done` no novo HEAD antes da rodada seguinte: default (não perguntado) | 2026-11-19 |
| Rodada do Worf no Handoff | campo novo / `--report` | Uma linha `--report "Worf r<N> <veredito>"` a cada rodada, sem campo novo: default (não perguntado) | 2026-11-19 |
| Guinan só lições sem achado confirmado | roda e não registra / não roda | Não roda quando o `review.md` final não tem blocker nem should-fix confirmado: default (não perguntado) | 2026-11-19 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| State-transition rules | Fases: ... `review` (Q) → `pr-review` (PR aberto, rodadas do Worf) → `done` (merge). O `handoff.py` aceita `pr-review`; o banner e a tabela de retomada do `state-format.md` tratam `pr-review` como em andamento |
| Failure and partial failure | Rodada 3 com achado aberto: para e mostra os achados (regra de hoje), e a fase continua `pr-review` |
| demais dimensões | N/A para este escopo |

## Facts Found
- `scripts/handoff.py:45-46`: `PHASES` termina em `review`, `done`.
- `skills/engajar/references/execute.md:169-196`: pós-Q, Guinan antes do PR, `--phase done` e a seção "Review (Worf)".
- `skills/engajar/references/state-format.md`: formato do Handoff e tabela de retomada.
- `skills/guinan/SKILL.md:32-35`: já lê o `review.md` e mapeia `review_finding`.
- `skills/piloto-automatico/SKILL.md:90-99`: o `encerrar` vem "quando nada resta".
- `DECISIONS.md:644-648` (F9-5) e `tests/test_flow_worf_guinan.py`.
