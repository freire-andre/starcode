# pr-review verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 10154e8
**HEAD**: 6e04d7d
**Verifier**: codex · requested cli-default · effective GPT-6.1 Terra medium (terminal)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_pr_review.py` `test_fase_pr_review` | no - confere substring em vez do valor integral da linha de fase. |
| C2 | `tests/test_pr_review.py` `test_execute_fase_pr_review` | no - não detecta a instrução contraditória de pedir merge após a rodada 3 com achados abertos. |
| C3 | `tests/test_pr_review.py` `test_execute_gates_apos_correcao_worf` | no - aceita o fragmento do report sem verificar que ele deve ser gravado após cada rodada. |
| C4 | `tests/test_pr_review.py` `test_guinan_licoes_do_review` | no - não verifica a restrição da seção 1 da Guinan, que exclui achados corrigidos não confirmados. |
| C5 | `tests/test_pr_review.py` `test_piloto_encerra_apos_worf` | yes |
| C6 | `tests/test_pr_review.py` `test_state_format_pr_review` | no - não cobre retomada com PR já mergeado e fase ainda pr-review. |
| C7 | `tests/test_pr_review.py` `test_decisions_pr_review` | no - aceita qualquer linha com SC-198 no changelog e não verifica que os gates são depois de cada correção na Decisão. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Na rodada 3 com achados abertos, o fluxo manda parar sem pedir merge e depois manda pedir a autorização sem condição; C2 não detecta a contradição. | `python -c "from pathlib import Path; t=Path('skills/engajar/references/execute.md').read_text(encoding='utf-8'); s=t.split('## Review (Worf)')[1].split('## Text for')[0]; print('rodada 3 com achados abertos:'); print('para sem pedir merge:', 'without asking for the merge' in s); print('pedido de merge incondicional:', 'Then the merge authorization is asked' in s)"` → `rodada 3 com achados abertos:` / `para sem pedir merge: True` / `pedido de merge incondicional: True` | Condicionar o pedido de merge à ausência de achados impeditivos e testar a rodada 3 aberta. | 48d7055 |
| A retomada não especifica gravar done quando o PR já foi mergeado; a linha cobre somente PR aberto e C6 não testa esse caso. | `python -c "from pathlib import Path; t=Path('skills/engajar/references/state-format.md').read_text(encoding='utf-8'); r=next(x for x in t.splitlines() if x.startswith('&#124; PR open, Phase')); print('retomada com PR ja mergeado:'); print('regra de gravar done na linha:', 'done' in r); print(r)"` → `retomada com PR ja mergeado:` / `regra de gravar done na linha: False` / `&#124; PR open, Phase \`pr-review\` &#124; pr-review &#124; read \`review.md\` (round and verdict); continue with the LaForge fix, or the next Worf round, or the merge authorization request &#124;` | Acrescentar a regra explícita para PR já mergeado e testá-la. | 48d7055 |
| O modo só lições remete à seção 1, que exclui achados não confirmados, embora R4 inclua achados corrigidos ou confirmados; o teste confere somente o trecho novo. | `skills/guinan/SKILL.md:35` | Incluir achados corrigidos na seleção de review_finding e testar os dois estados. | 48d7055 |
| A asserção da fase aceita sufixos indevidos e C3 aceita o report fora da condição de cada rodada. | `tests/test_pr_review.py:46` e `tests/test_pr_review.py:68` | Conferir o valor integral da linha e a instrução completa de registrar o report após cada rodada. | ca5b699 |
| C7 aceita uma linha irrelevante no changelog e uma Decisão sem a frequência dos gates. | `tests/test_pr_review.py:110` e `tests/test_pr_review.py:122` | Conferir a descrição da mudança em Unreleased e a condição de cada correção na Decisão. | ca5b699 |

## Limits

Regressão completa em 6e04d7d: `python -m unittest discover -s tests -v`, 996 testes, OK, 1 dispensado; `test_restore_yes_devolve_bit_executavel` não roda no Windows porque não há bit executável.
As provas registram HEAD 10154e8, anterior ao HEAD verificado 6e04d7d; a regressão foi executada no HEAD atual.
