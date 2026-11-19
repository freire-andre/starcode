# Lições no brief: ordem por recorrência, antes das regras, e fix-brief do pós-Q: Spec

**Approved**: 2026-11-19 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-205
**May change**: scripts/dispatch.py, tests/test_dispatch_lessons.py, skills/engajar/references/execute.md, tests/test_licoes_no_brief.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
As retros de fecha-achado, sessions-concorrente e roteamento-worf-mccoy (categoria instructions without effect) pediram que as lições recorrentes fossem para o brief do LaForge. Elas já iam: `lessons_section` (`scripts/dispatch.py`) anexa até 10 lições confirmadas no fim do brief, ordenadas por `updated`. Mesmo assim, L2 se repetiu em 17 features, L32 em 12 e L20 em 9. O brief da correção pós-Q é escrito à mão e não leva lição nenhuma. Começou como PEQUENA e foi reclassificada para MÉDIA (decisão do dono), porque o ajuste de `tests/test_dispatch_lessons.py` levou a 4 arquivos.

## Scope
- Ordem e posição da seção `## Lessons` nos briefs de worker e do Q.
- Novo subcomando `dispatch.py fix-brief`, e o `execute.md` (seção 5) mandando usá-lo.

## Non-Goals
- Mudar o `lessons.py`, a promoção de lições ou o limite de 10.
- Gerar automaticamente o despacho da correção: o Picard continua despachando o worker.

## Decisions
| Item | Options | Status |
|---|---|---|
| Classe | MÉDIA (spec breve, aprovação e Q) · PEQUENA com os testes novos movidos para `test_dispatch_lessons.py` | approved - user: "1" |

## Requirements
- **R1** - The `lessons_section` SHALL ordenar as lições confirmadas por `len(features)` decrescente, depois `updated` decrescente, depois o número do ID decrescente, com no máximo 10, e o corpo da seção SHALL começar pela linha exata `Estas lições se repetiram em features anteriores; o Q reprova um teste que viole alguma delas.`.
- **R2** - The brief de worker (`worker_brief`, tanto pelo `tasks.md` quanto pela spec sem `tasks.md`) SHALL ter a seção `## Lessons` uma vez só, antes de `## Regras fixas do worker (StarCode)`. O brief do Q (`q_brief`) SHALL manter a seção no fim. O `tests/test_dispatch_lessons.py` SHALL ser ajustado ao novo contrato sem perder as outras asserções.
- **R3** - WHEN o Picard roda `dispatch.py fix-brief <slug> [--out <arquivo>]` THEN o sistema SHALL gerar um brief com título, issue (`**Linear**` da spec), cada achado com a célula `Closed` vazia da tabela `## Findings` do `verification.md` como `## Achado <n>` (n = posição na tabela, com Finding, Evidence e Fix), o `May change` da feature (spec ou união dos tickets do `tasks.md`), a seção `## Lessons` e as regras fixas (um commit por achado com `Refs:`, nunca escrever `.specs/`, nunca `git push`/`reset`/`restore`/`stash`, suíte inteira e `run_gates.py ticket` verdes, relatório com o commit e o teste de cada achado). IF nenhum achado está aberto THEN SHALL sair com 2 e `nada a corrigir: <slug> sem achados abertos`.
- **R4** - The `execute.md`, seção 5, SHALL mandar gerar o brief da correção com `dispatch.py" fix-brief <slug>`. The `DECISIONS.md` SHALL ter a entrada `### SC-205:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**, e o `CHANGELOG.md` uma linha em `[Unreleased]`.

## Edge Cases
- Sem lição confirmada: nenhum brief ganha `## Lessons` (R1, R2).
- `verification.md` ausente: `fix-brief` sai com erro dizendo que falta o arquivo (R3).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `lessons_section` ordena as confirmadas por número de features, depois data, depois ID, com no máximo 10, e a primeira linha do corpo é a frase do Q (R1)
Proof: run unit | test_ordem_por_recorrencia (test_licoes_no_brief.LicoesNoBriefTests.test_ordem_por_recorrencia) ... ok

**C2** - No brief de worker (tasks.md e spec sem tasks.md), `## Lessons` vem antes de `## Regras fixas do worker (StarCode)`, uma vez só; no brief do Q, continua no fim (R2)
Proof: run unit | test_licoes_antes_das_regras (test_licoes_no_brief.LicoesNoBriefTests.test_licoes_antes_das_regras) ... ok

**C3** - `fix-brief` lista só os achados com `Closed` vazio, com o número da tabela, o May change, as lições e as regras; sem achado aberto sai com 2 e a mensagem exata (R3)
Proof: run unit | test_fix_brief (test_licoes_no_brief.LicoesNoBriefTests.test_fix_brief) ... ok

**C4** - `execute.md` seção 5 cita `dispatch.py" fix-brief <slug>`; entrada `### SC-205:` com os quatro campos e linha no CHANGELOG (R4)
Proof: run unit | test_execute_e_decisions (test_licoes_no_brief.LicoesNoBriefTests.test_execute_e_decisions) ... ok

## Handoff

**Phase:** review
**Size:** MEDIUM
**Git mode:** 3
**Next:** Q verifica (codex); depois pós-Q, Guinan, PR e Worf
**Linear:** SC-205
**Integration branch:** feature/licoes-no-brief
**Last integrated:** 9d86e1e
**Dispatched:** none
**Settled:** 2026-11-19: sim
**Attempts:** none
**Reports:** 2026-11-19: reclassificada para MÉDIA (4 arquivos); T1 integrado em 9d86e1e; 2026-11-19: provas verdes (4/4)
**Breaker:** closed
