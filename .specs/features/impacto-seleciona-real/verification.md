# impacto-seleciona-real verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 72d7301
**HEAD**: 320c37c
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_impact.py` `test_intervalo_de_feature_ignora_specs` | yes |
| C2 | `tests/test_impact.py` `test_so_specs_roda_tudo` | yes |
| C3 | `tests/test_impact.py` `test_identifica_testes_python_e_ts` | yes |
| C4 | `tests/test_impact.py` `test_apoio_propaga_mas_nao_e_teste` | yes |
| C5 | `tests/test_impact.py` `test_referencia_textual_seleciona_teste` | yes |
| C6 | `tests/test_impact.py` `test_mudado_sem_teste_roda_tudo_mesmo_com_outros` | yes |
| C7 | `tests/test_impact.py` `test_impact_no_repo_starcode` | no - a asserção `assertIn("fora do grafo", res["reason"])` não fixa o motivo completo exigido, `fora do grafo: README.md`. |
| C8 | `tests/test_impact.py` `test_decisions_impacto_seleciona_real` | no - verifica `F12`, mas não afirma que a entrada cita R15, exigido por R7. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C7 aceita qualquer motivo que contenha “fora do grafo”, mesmo com caminho ou texto incorreto. | `tests/test_impact.py:212` | Asserir o motivo integral `fora do grafo: README.md`. | 3e3824f |
| O teste de R7 não detecta a remoção da referência ao padrão F12 R15. | `tests/test_impact.py:269` | Asserir explicitamente `R15` dentro da entrada SC-176. | 6806606 |

## Limits

A regressão integral foi executada em HEAD: `python -m unittest discover -s tests -v 2>&1` — 882 testes, 0 falhas, 1 ignorado. Sondas extras passaram: `is_test_file` reconheceu teste em diretório aninhado, sufixo `_test.py`, rejeitou near-miss e caminho vazio, e aceitou nome longo; a sonda de R6 deduplicou e ordenou mudanças, retornando `run-all` para `lonely.py`. None.
