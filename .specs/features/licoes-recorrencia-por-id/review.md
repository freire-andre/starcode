**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
COMMENT. O `add --id` cobre R1 a R8 como a spec pede: ausente (`None`) e vazio são tratados separadamente, a caixa não importa, a quarentena e o ID inexistente saem com 2 sem tocar nos bytes (sondado em pasta temporária, inclusive a candidata podada no próprio comando), e a promoção e a idempotência estão certas. As cópias de `dist/` estão em dia. O reprocessamento de L2, L10 e L32 bate com o Scope e as repetidas ficaram intactas. Um should-fix: `test_licoes_reprocessadas_n1` exige que as repetidas existam para sempre, mas a poda de 45 dias vai removê-las no primeiro `add` depois de 2026-12-27, e aí a suíte quebra. Dois nits nos testes. Arquivos mecânicos fora do review: `dist/` (5 CLIs) e `.specs/LESSONS.md` (gerado).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | tests/test_lessons.py:282 | `test_licoes_reprocessadas_n1` lê `by_id[rid]` das repetidas (candidate, 1 feature). A poda de 45 dias (`_prune`) as remove no primeiro `add` depois de 2026-12-27 (L18 e L21 têm `updated` 2026-11-12), e o teste quebra com `KeyError`. A sonda numa cópia com L18 envelhecida confirmou que um `add` a remove. Correção: pular a repetida que não está mais em `by_id` e manter as asserções das canônicas. | tests/test_lessons.py:282, scripts/lessons.py:125 | aberto |
| W2 | 🟡 nit | tests/test_guinan_skill.py:60 | `assertLess(lst[0], wr[0], root)` aparece duas vezes (:55 e :60). | tests/test_guinan_skill.py:60 | aberto |
| W3 | 🟡 nit | scripts/lessons.py:202 | O ramo da lição podada no próprio comando não tem teste (a sonda mostrou que ele sai com 2 sem tocar nos bytes). | scripts/lessons.py:202 | aberto |

## Escada determinística
- `python tools/build.py --check`: OK, `dist/` em dia.
- `claude plugin validate dist/claude --strict`: Validation passed.
- `python scripts/check_decisions.py`: OK.
- `python -m unittest discover -s tests`: 921 testes, OK (skipped=1).
- Bypass scan (`scan_bypasses.py`): 1 candidato (`time.sleep(1.1)` em tests/test_lessons.py:93, sync-hack). Aceito: o teste espera a resolução de 1 s do carimbo e não esconde uma corrida.

## Pesquisa
nenhuma superfície externa (só stdlib e arquivos do repo).
