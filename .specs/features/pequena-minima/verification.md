# pequena-minima verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 9978cbe
**HEAD**: c18b1d5
**Verifier**: codex · requested cli-default · effective GPT-6.1 Terra medium (terminal)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_pequena_minima.py` `test_spec_small_minima` | yes |
| C2 | `tests/test_pequena_minima.py` `test_spec_small_limite` | yes |
| C3 | `tests/test_pequena_minima.py` `test_small_sem_aprovacao` | yes |
| C4 | `tests/test_pequena_minima.py` `test_dispatch_small_t1` | no - não executa nem verifica settle. |
| C5 | `tests/test_pequena_minima.py` `test_q_waive` | yes |
| C6 | `tests/test_pequena_minima.py` `test_done_waived` | no - não verifica que apenas o marcador válido dispensa as tabelas. |
| C7 | `tests/test_pequena_minima.py` `test_textos_fluxo_pequena` | no - busca termos isolados sem verificar que Worf ocorre no PR. |
| C8 | `tests/test_pequena_minima.py` `test_decisions_pequena_minima` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| O gate aceita `waivedness` como dispensa e deixa passar uma verificação sem tabelas. | `$env:PYTHONDONTWRITEBYTECODE='1'; python -c "import sys; sys.path[:0]=['tests','scripts','scripts/gates']; import test_pequena_minima as t; x=t.PequenaTests(); x.setUp(); x.done_repo(verification='**Verification:** waivedness'); r=t.validate_verification.evaluate('peq',x.repo); print('errors:',r.errors); print('warnings:',r.warnings); x.tearDown()"` → `errors: []`<br>`warnings: ['Q dispensado (PEQUENA)']` | Delimitar o valor do marcador e testar valores inválidos no gate completo. | e8eb40a |
| A prova citada de C4 não exercita o `settle` nem a ordem do gate antes do merge. | `tests/test_pequena_minima.py:154` | Citar também `test_settle_small_roda_gate_ticket` na prova de C4. | 30cec43 |
| C7 aceita `Worf` em qualquer ponto após o início da seção 8, mesmo sem exigir revisão no PR. | `tests/test_pequena_minima.py:298` | Verificar a relação entre Worf e PR na instrução do caminho SMALL. | d7dc186 |

## Limits

Regressão: `python -m unittest discover -s tests -v` passou: 989 testes, 1 ignorado no Windows por depender do bit executável.
Sonda adicional de R2: `$env:PYTHONDONTWRITEBYTECODE='1'; python -c "import sys; sys.path.insert(0,'scripts/gates'); import validate_spec as v; e=[]; v._check_small(['**Size**: SMALL','**Linear**: SC-1','**May change**: a.py, b.py, CHANGELOG.md, lib/','## Scope','ok','## Checks','**C1** - x','**C2** - x','**C3** - x','**C4** - x'],e); print('errors:',e)"` → `errors: []`.
`spec.md` já estava modificado antes desta verificação; o Handoff foi preservado.
