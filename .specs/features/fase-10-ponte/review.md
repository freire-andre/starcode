# Review: fase-10-ponte (PR #24)

**Round**: 2
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR

APPROVE. O W1 foi resolvido em 03b98d5 (integrado em f8ebbf9): o `runSnapshot` lê o `error` do stdout do `ponte.py` (`src/orca/src/worker.ts:149`). As rodadas que corrigiram o CLI do orca no worker (1a25c7b, d70e69d e d4c6646, F10-14) não trazem blocker novo:
- o CLI roda por caminho explícito e nunca pelo próprio `execPath`;
- o env é completado a partir do `homedir`, sem sobrescrever;
- o log guarda só os nomes das variáveis.

O reaceite da Issue na Orca instalada mostra a SC-17 com título e estado e o botão do Linear habilitado.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟡 nit | `src/orca/src/worker.ts:82` | A mensagem "worktree inválido" do `ponte.py` não chegava ao painel | `src/orca/src/worker.ts:149` | resolvido em 03b98d5 |

## Escada determinística

- `python tools/build.py --check`: exit 0
- `python scripts/check_decisions.py`: exit 0
- `orca plugin test src/orca`: 60/60
- `python -m unittest discover -s tests` (Windows): OK, 599 testes
- `run_gates.py proofs` e `done`: verde
- `git diff a9da1e4..HEAD -- . ':!dist' | scan_bypasses.py`: 2 candidatos, aceitos (casts em teste)

## Pesquisa

- https://nodejs.org/api/child_process.html
**Posted**: 2026-11-11 - https://github.com/freire-andre/starcode/pull/24#pullrequestreview-5864466614
