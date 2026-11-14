# q-familia-revendedor verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at ac13e85
**HEAD**: 32f1b20
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_model_info.py` `test_revendedor_claude_vira_anthropic` | yes |
| C2 | `tests/test_model_info.py` `test_bedrock_prefixo_do_fornecedor` | yes |
| C3 | `tests/test_model_info.py` `test_revendedor_modelo_desconhecido_vira_unknown` | yes |
| C4 | `tests/test_model_info.py` `test_fornecedor_e_id_canonico_mantem_familia` | yes |
| C5 | `tests/test_model_info.py` `test_compare_revendedor_claude_e_same` | yes |
| C6 | `tests/test_model_info.py` `test_q_cli_recusa_revendedor_claude` | yes |
| C7 | `tests/test_model_info.py` `test_prefixos_de_modelo_por_revendedor` | no - não testa os prefixos `o1` e `o4` citados em R7 |
| C8 | `tests/test_model_info.py` `test_sem_catalogo_revendedor_unknown` | yes |
| C9 | `tests/test_model_info.py` `test_decisions_q_familia_revendedor` | no - testa presença de alguns termos e nomes de testes, não se a decisão descreve R1 a R8 |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C7 deixa sem prova dois prefixos exigidos por R7 (`o1` e `o4`), apesar de o código os listar. | `tests/test_model_info.py:164` | Inclua pelo menos um identificador iniciado por `o1` e outro por `o4` na tabela parametrizada e exija a família `openai`. | fa73232 |
| C9 não prova a parte substantiva de R9: pode passar mesmo se o texto da decisão deixar de descrever um ou mais requisitos R1–R8. | `tests/test_model_info.py:178` | Faça a asserção verificar o conteúdo da decisão que cobre os requisitos, além dos títulos e nomes dos testes. | fa73232 |

## Limits

`python -m unittest discover -s tests -v 2>&1`: 856 testes, 0 falhas, 1 skip (bit executável não existe no Windows).
Sondas adicionais de R3/R7 para entrada vazia, letras maiúsculas e limites de prefixo não revelaram quebra; valores desconhecidos retornaram `unknown` e valores iniciados por prefixos retornaram a família correspondente.
Não verifiquei se o catálogo real do models.dev inclui `canonical_model_id` para os cinco revendedores; a spec registra que não há cache disponível nesta máquina.
