**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR

APPROVE. O PR acrescenta `dispatch.py start` e `settle`, o DECISIONS.md implícito no brief e no lote, o gate de citações do TASK, a data preservada no `--report`, o proofs.md em LF e a regra de evidência das sondagens do Q. Escada verde. Três nits, nenhum impede o merge. Arquivos mecânicos fora do review: `dist/` (5 alvos) e `.specs/lessons.json`.

| ID | Severity | Where | Finding | Evidence | State |
| --- | --- | --- | --- | --- | --- |
| W1 | 🟡 nit | scripts/gates/validate_tasks.py:95 | `uncovered_citations` não aceita entrada com glob do May change (`tests/test_*.py` x `tests/test_a.py`), que `check_scope.allowed` aceita por `fnmatch`. Correção: reusar `check_scope.allowed` ou somar `fnmatch` ao `any(...)` (ajustar o R21). | scripts/gates/check_scope.py:47 | aberto |
| W2 | 🟡 nit | scripts/dispatch.py:719 | A segunda gravação do `start` levanta `ValueError` se o handoff.py falhar, e o `main` sai com 2 (código de recusa) com o worker já rodando e a entrada sem dispatch id. Correção: tratar como `aviso:` e sair com 0, como o R10. | scripts/dispatch.py:902 | aberto |
| W3 | 🟡 nit | tests/test_handoff_report_date.py:7 | `# noqa: F401  (sys.path)` com justificativa e sem link de issue; padrão já presente em 3 testes da main, sem defeito escondido. | tests/test_handoff_report_date.py:7 | aberto |

## Escada determinística

- `python tools/build.py --check`: OK, dist/ em dia.
- `python scripts/check_decisions.py`: OK.
- `python -m unittest discover -s tests`: OK, 758 testes, 1 skip.
- `git diff main...HEAD | scan_bypasses.py`: 1 candidato (noqa em teste, julgado em W3).

## Pesquisa

nenhuma superfície externa: o diff não acrescenta nem atualiza dependência; as chamadas ao CLI `orca` e ao `git` seguem a forma já usada no repo e nenhum achado depende de comportamento externo.
