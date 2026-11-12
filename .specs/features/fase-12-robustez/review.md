**Round**: 2
**Verdict**: APPROVE
**Reviewer**: claude-code · claude-opus-5-5

## TL;DR

APPROVE. Os cinco achados da rodada 1 (W1 a W5) estão resolvidos: cada um foi reproduzido com o caso original e tem teste novo. O diff das correções não traz blocker novo. A escada passa: build --check, check_decisions e 720 testes (1 skip). Fora do review: `dist/` (gerado, conferido por `build.py --check`).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/dispatch.py:447 | Corrigido em f4565f0: a checagem de marcadores agora roda antes de inserir `{{regression}}`. Reprodução: com `profiles/p/template/src/{{module}}/health.py` no intervalo, o brief sai com `rodar tudo: nenhum teste alcança ...{{module}}/health.py`, sem exceção. | scripts/dispatch.py:447, scripts/dispatch.py:450, tests/test_dispatch_regression.py:38 | resolvido |
| W2 | 🟠 should-fix | scripts/impact.py:69 | Corrigido em 61db014: `--no-renames`. Reprodução: `pkg/old.py -> pkg/new.py` agora dá `run-all` com `fora do grafo: pkg/old.py`. | scripts/impact.py:69, tests/test_impact.py:72, https://git-scm.com/docs/git-diff | resolvido |
| W3 | 🟠 should-fix | scripts/dispatch.py:431 | Corrigido em a5abf15: com `--head HEAD` e árvore rastreada suja, a seleção passa a usar `diff=<base>`. Reprodução: `core.py` modificado mais `extra.py` novo, sem commit, seleciona 2 testes (`core.py <- test_core.py` e `test_extra.py`). | scripts/dispatch.py:431, tests/test_dispatch_regression.py:45 | resolvido |
| W4 | 🟠 should-fix | scripts/impact.py:346 | Corrigido em 7fba116: quando um `conftest.py` muda, o resultado é `rodar tudo`. Reprodução: `tests/conftest.py` mudado dá `conftest.py muda fixtures sem import: tests/conftest.py`. | scripts/impact.py:346, tests/test_impact.py:82, https://docs.pytest.org/en/stable/reference/fixtures.html | resolvido |
| W5 | 🟡 nit | scripts/snapshot.py:286 | Corrigido em 3fa4e7b: os `remover` rodam antes dos `voltar`. Reprodução: com a pasta `src/a.txt/` no lugar do arquivo, `restore --yes` sai com 0 e o arquivo volta. `test_restore_falha_parcial_e_retomada` continua verde com a falha injetada. | scripts/snapshot.py:286, tests/test_snapshot_restore.py:161 | resolvido |

## Escada determinística

- `python tools/build.py --check`: OK, dist/ em dia.
- `python scripts/check_decisions.py`: OK.
- `python -m unittest discover -s tests`: 720 testes, OK (1 skip).
- Bypass scan (`scan_bypasses.py`) em `main...HEAD`: 25 candidatos, os mesmos aceitos na rodada 1. No diff das correções (`2d613da..HEAD`): 0.

## Pesquisa

- https://git-scm.com/docs/git-diff
- https://docs.pytest.org/en/stable/reference/fixtures.html
**Posted**: 2026-11-12 - https://github.com/freire-andre/starcode/pull/34#pullrequestreview-5882721812
