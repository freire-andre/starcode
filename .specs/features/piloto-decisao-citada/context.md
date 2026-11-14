# Aprovação do piloto confere a decisão citada: Context

**Size**: MEDIUM
**Risk triggers**: Autenticação e autorização (gate de aprovação das tasks)
**Source request**: "PROXIMO PASSO" (passo 3 do primeiro corte da seção 12 de `starcode-triagem-v2-2026-11-13.md`: item 0.4)

## Problem
O gate aceita `**Approved**: <data> - piloto: "D<n> ..."` no `tasks.md` quando o piloto está ativo e o mandato foi confirmado, mas só confere o formato `D<n>` (`PILOT_APPROVED_RE`, `scripts/gates/gates_common.py:183-184`). Uma aprovação pode citar uma decisão que nunca foi registrada: o próprio teste aprova `piloto: "D4 tasks cobrem a spec"` sem nenhuma decisão no `piloto.md` (`tests/test_piloto.py:105-111`). Além disso, há dois leitores do `piloto.md` com regras diferentes: `gates_common.py:185-186` exige `**Mandato confirmado:** <data> - user:` e `**Status:** ativo`; `scripts/piloto.py:39-40` lê o status e aceita `**Mandato confirmado:** <data>` sem exigir `- user:`.

## Users
O dono do repositório, que delega a aprovação das tasks ao piloto, e o Picard, que registra a aprovação citando a decisão.

## Success
- `piloto: "D7 ..."` só aprova o `tasks.md` se o `piloto.md` tem a decisão `### D7 · `.
- Os gates leem o `piloto.md` só pelas funções do `piloto.py`; não sobra regex de `Mandato confirmado`, `Status` ou de decisão em `gates_common.py`.
- Teste com ID inexistente reprova.

## Constraints
- A spec continua sem aceitar aprovação do piloto (`allow_pilot` falso para `spec.md`).
- O comportamento depois do `encerrar` não muda neste passo (item 0.5, decisão D-g): continua exigindo `Status: ativo`.
- Ticket em `scripts/` lista `DECISIONS.md` no May change (agora coberto pela regra única, mas a spec lista mesmo assim).
- `dist/` só por `python tools/build.py`.

## Scope Notes
- Dentro: item 0.4 (gate confere a decisão citada; um só leitor do `piloto.md`).
- Fora: 0.5 (aprovação válida depois do `encerrar`, D-g), 0.6 (freio na 3ª decisão `⚠️ revisar`, D-h), 0.7 (decisões de arquitetura não delegáveis, D-h).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Decisão `⚠️ revisar` como base da aprovação | aceitar (só conferir que existe) / recusar | aceitar: o item 0.4 pede só a existência, e o tratamento das decisões sem base é o freio do item 0.6 · default (não perguntado) | 2026-11-14 |
| Regra de "mandato confirmado" no leitor único | a do gate (exige `- user:`) / a do `piloto.py` (só a data) | a do gate, mais estrita; `piloto.py confirmar` já grava `- user: "<palavras>"`, então `piloto.py ativo` não muda para arquivos escritos pelo script · default (não perguntado) | 2026-11-14 |
| Várias linhas `piloto:` no `tasks.md` | basta uma válida / todas válidas | basta uma linha cuja decisão exista, como hoje basta uma linha no formato · default (não perguntado) | 2026-11-14 |
| Decisão citada com ID em outro formato (`d7`, `D07`) | aceitar normalizando / exigir `D<n>` literal | exigir `D<n>` como o `piloto.py registrar` grava; `D07` cita `D7` só se o número for igual · default (não perguntado) | 2026-11-14 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Authorization boundaries | A aprovação do piloto só vale com piloto ativo, mandato confirmado pelo usuário e decisão citada registrada; a spec nunca aceita. |
| Input validation and limits | `piloto.md` ausente ou ilegível: a aprovação do piloto não vale (o gate reprova), sem traceback. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `scripts/gates/gates_common.py:183-203`: `PILOT_APPROVED_RE`, `PILOT_CONFIRMED_RE`, `PILOT_ACTIVE_RE`, `pilot_confirmed`, `approved(lines, fdir, allow_pilot)`.
- Chamadores: `scripts/gates/validate_tasks.py:253` e `scripts/gates/validate_verification.py:195` (só o `tasks.md` com `allow_pilot`).
- `scripts/piloto.py`: `STATUS_RE`, `CONFIRMED_RE` (`:39-40`), `DECISION_RE = ^### D(\d+) · ` (`:42`), `is_active` (`:142`), `confirm` grava `**Mandato confirmado:** <data> - user: "<palavras>"` (`:136-137`).
- `tests/test_piloto.py`: `PilotApprovalGateTests` (`test_pilot_line_needs_confirmed_active_mandate`, `test_user_line_still_accepted`, `test_gates_pass_pilot_only_on_tasks`).
- Precedente: SC-167 (`DECISIONS.md`), uma regra de cobertura compartilhada pelos dois gates.
