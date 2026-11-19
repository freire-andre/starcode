# Lições no brief: ordem por recorrência, antes das regras, e fix-brief do pós-Q: Spec

**Size**: SMALL
**Linear**: SC-205
**May change**: scripts/dispatch.py, tests/test_dispatch_lessons.py, skills/engajar/references/execute.md, tests/test_licoes_no_brief.py, DECISIONS.md, CHANGELOG.md, dist/

## Scope
- Sugestão repetida nas retros de fecha-achado, sessions-concorrente e roteamento-worf-mccoy (categoria instructions without effect). Hoje `lessons_section` (`scripts/dispatch.py`) põe no fim do brief até 10 lições confirmadas ordenadas por `updated`, e o brief da correção pós-Q é escrito à mão, sem lição nenhuma. Mudanças: (1) `lessons_section` ordena por `len(features)` decrescente, depois `updated` decrescente, depois o número do ID, e mantém o limite de 10; (2) a seção começa com a linha exata `Estas lições se repetiram em features anteriores; o Q reprova um teste que viole alguma delas.` e, no brief de worker (`worker_brief`, nos dois caminhos: tasks.md e spec sem tasks.md), entra **antes** de `## Regras fixas do worker (StarCode)`; o brief do Q (`q_brief`) mantém a seção no fim; (3) novo subcomando `dispatch.py fix-brief <slug> [--out <arquivo>]`: lê a tabela `## Findings` do `verification.md` (reusando o leitor de tabelas de `scripts/gates/validate_verification.py`) e gera um brief com título, issue (`**Linear**` da spec), cada achado com a célula `Closed` vazia numerado pela posição na tabela (`Achado <n>`, com Finding, Evidence e Fix), o `May change` da feature (spec ou união dos tickets do tasks.md), `## Lessons` e regras fixas: um commit por achado com `Refs:`, nunca escrever `.specs/`, nunca `git push`/`reset`/`restore`/`stash`, suíte inteira e `run_gates.py ticket` verdes, relatório com o commit e o teste de cada achado; sem achado aberto, sai com 2 e `nada a corrigir: <slug> sem achados abertos`; (4) `execute.md`, seção 5, manda gerar o brief da correção com `dispatch.py fix-brief`. Entrada `### SC-205:` no `DECISIONS.md` (quatro campos) e linha no `CHANGELOG.md`.

## Checks
**Build**: `python tools/build.py --check`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `lessons_section` ordena as confirmadas por número de features, depois data, depois ID, com no máximo 10, e a primeira linha do corpo é a frase do Q
Proof: run unit | test_ordem_por_recorrencia (test_licoes_no_brief.LicoesNoBriefTests.test_ordem_por_recorrencia) ... ok

**C2** - No brief de worker (tasks.md e spec sem tasks.md), `## Lessons` vem antes de `## Regras fixas do worker (StarCode)`, uma vez só; no brief do Q, continua no fim
Proof: run unit | test_licoes_antes_das_regras (test_licoes_no_brief.LicoesNoBriefTests.test_licoes_antes_das_regras) ... ok

**C3** - `fix-brief` lista só os achados com `Closed` vazio, com o número da tabela, o May change, as lições e as regras; sem achado aberto sai com 2 e a mensagem exata
Proof: run unit | test_fix_brief (test_licoes_no_brief.LicoesNoBriefTests.test_fix_brief) ... ok

**C4** - `execute.md` seção 5 cita `dispatch.py" fix-brief <slug>`; entrada `### SC-205:` com os quatro campos e linha no CHANGELOG
Proof: run unit | test_execute_e_decisions (test_licoes_no_brief.LicoesNoBriefTests.test_execute_e_decisions) ... ok

## Handoff

**Phase:** spec-approved
**Size:** SMALL
**Git mode:** 3
**Next:** LaForge implementa T1 (SC-205)
**Linear:** SC-205
**Integration branch:** feature/licoes-no-brief
**Last integrated:** none
**Dispatched:** T1 · SC-205 · base 6f028b2 · claude:claude-sonnet-5-5 · 2026-11-19T22:36:11Z · ctx_4e87ac2a3b63
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
