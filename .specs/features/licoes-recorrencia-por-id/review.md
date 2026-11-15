**Round**: 2
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE. Os três achados da rodada 1 fecharam. W1: `test_licoes_reprocessadas_n1` agora pula a repetida que a poda já removeu e mantém todas as asserções das canônicas, que conferem as fontes pelo snapshot `orig`, não por `by_id`. W2: o `assertLess` duplicado saiu. W3: `test_lessons_add_id_de_licao_podada_sai_2` envelhece L1 em 60 dias, passa pela primeira busca e cai no ramo da poda, conferindo a saída exata e os bytes intactos de `lessons.json` e `LESSONS.md`. As correções mexem só em testes e na Handoff da spec; nenhum blocker novo. Arquivos mecânicos fora do review: `dist/` (5 CLIs) e `.specs/LESSONS.md` (gerado).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | tests/test_lessons.py:282 | `test_licoes_reprocessadas_n1` quebrava com `KeyError` depois que a poda de 45 dias removesse as repetidas. Agora pula o ID ausente de `by_id` (:295-296); as canônicas seguem conferidas (:289-294). | tests/test_lessons.py:295 | resolvido (a8324a0) |
| W2 | 🟡 nit | tests/test_guinan_skill.py:60 | `assertLess(lst[0], wr[0], root)` duplicado. Removido; fica só o de :55. | tests/test_guinan_skill.py:55 | resolvido (7dca367) |
| W3 | 🟡 nit | scripts/lessons.py:202 | O ramo da lição podada no próprio comando não tinha teste. `test_lessons_add_id_de_licao_podada_sai_2` (tests/test_lessons.py:156-167) o cobre: exit 2, `id inválido: nenhuma lição L1`, bytes intactos. | tests/test_lessons.py:156 | resolvido (a8324a0) |

## Escada determinística
- `python tools/build.py --check`: OK, `dist/` em dia.
- `python scripts/check_decisions.py`: OK.
- `python -m unittest test_lessons test_guinan_skill` (em `tests/`): 15 testes, OK.
- `python -m unittest discover -s tests`: OK (skipped=1).
- Bypass scan (`scan_bypasses.py`): 3 candidatos (sync-hack). O único de código é o mesmo da rodada 1 (`time.sleep(1.1)` em tests/test_lessons.py:93), aceito: espera a resolução de 1 s do carimbo. Os outros 2 são `review.json:4` e `review.md:19` da rodada 1, que só citam esse trecho.

## Pesquisa
nenhuma superfície externa (só stdlib e arquivos do repo).
