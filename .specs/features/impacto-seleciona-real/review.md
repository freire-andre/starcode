**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
COMMENT. Rodada 1 sobre `main...feature/impacto-seleciona-real` (335f557). O PR cumpre R1 a R4 e R7, e a escada passa.

Fica um defeito real. A referência textual de R5 compara o basename como substring do texto do teste (scripts/impact.py:374). Assim, um teste que cita `data.py` passa a alcançar `a.py`. O mudado sem teste deixa de forçar `run-all` e a seleção sai parcial, o que contraria R6 (W1, should-fix, sonda em repositório temporário).

`dist/` é mecânico: `build --check` em dia, e as 5 cópias são iguais a `scripts/impact.py`. O scan de bypass não achou candidatos.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/impact.py:374 | A referência textual usa `basename in text`, sem fronteira. Na sonda, `a.py` sem teste e `tests/test_data.py` citando `"fixtures/data.py"` dão `selected` com a cadeia `a.py <- tests/test_data.py`, em vez de `run-all: nenhum teste alcança a.py`. O mesmo acontece com `mod.py` dentro de `mymod.py`. A nota da spec de que "colisão de basename só alarga a seleção" não vale com R6. Correção: casar com fronteira (`(?<![\w.-])nome(?![\w.-])`) e acrescentar o teste dessa sonda. | scripts/impact.py:374 | open |

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `claude plugin validate dist/claude --strict`: Validation passed.
- `python scripts/check_decisions.py`: OK.
- `python -m unittest discover -s tests`: Ran 882 tests, OK (skipped=1).
- `git diff main...HEAD | python scripts/review/scan_bypasses.py`: 0 candidatos.

## Pesquisa
nenhuma superfície externa
