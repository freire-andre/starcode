# Frota travada só com workers atrasados: Spec

**Size**: SMALL
**Linear**: SC-200
**May change**: scripts/dispatch.py, skills/engajar/references/execute.md, tests/test_dispatch.py, DECISIONS.md, CHANGELOG.md, dist/

## Scope
- Item 3.2 da triagem v2. Quando o `dispatch.py batch` sai vazio, há entradas ativas no `**Dispatched:**` e todas estão marcadas ` · blocked` (atrasadas), o JSON ganha `"stalled": ["T<n>", ...]` (lista vazia nos outros casos). A saída de texto ganha a linha `travado: só restam workers atrasados (<T…, separados por vírgula>): cancele com confirmação (passo 7) ou siga esperando`. O código de saída continua 1. O `execute.md` (seção 2F, passos 6 e 10) manda o Picard parar com essas duas opções, com a recomendação, no lugar de esperar sem fim. Entrada no `DECISIONS.md` `### SC-200:` (**Problema**, **Decisão**, **Motivo**, **Por que não é bug**) e linha no `CHANGELOG.md` `[Unreleased]`.

## Checks
**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Batch vazio com todas as entradas ativas `blocked`: `stalled` lista os tickets, o texto traz a linha `travado:` exata e a saída é 1
Proof: run unit | test_batch_travado (test_dispatch.FrotaTravadaTests.test_batch_travado) ... ok

**C2** - Nenhuma entrada ativa, ao menos uma ativa sem `blocked`, ou um batch com ticket: `stalled` vazio e nenhuma linha `travado:`
Proof: run unit | test_batch_nao_travado (test_dispatch.FrotaTravadaTests.test_batch_nao_travado) ... ok

**C3** - O `execute.md` (2F) manda parar no `travado:` com as opções cancelar com confirmação (passo 7) e seguir esperando
Proof: run unit | test_execute_travado (test_dispatch.FrotaTravadaTests.test_execute_travado) ... ok

**C4** - Entrada `### SC-200:` com os quatro campos, citando `stalled`, `travado:` e os testes, e a linha no CHANGELOG
Proof: run unit | test_decisions_frota_travada (test_dispatch.FrotaTravadaTests.test_decisions_frota_travada) ... ok

## Handoff

**Phase:** spec-approved
**Size:** SMALL
**Git mode:** 3
**Next:** LaForge implementa T1 (SC-200)
**Linear:** SC-200
**Integration branch:** feature/frota-travada
**Last integrated:** none
**Dispatched:** T1 · SC-200 · base 2257294 · claude:claude-sonnet-5-5 · 2026-11-19T16:58:12Z · ctx_76035a8961e3
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
