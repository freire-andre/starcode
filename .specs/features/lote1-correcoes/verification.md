# lote1-correcoes verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at a5931d3
**HEAD**: afecd3a
**Verifier**: codex · requested cli-default · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_build.py` `test_nenhuma_skill_do_dist_tem_header_first` | yes |
| C2 | `tests/test_check_proofs.py` `test_sees_palavra_inteira` | yes |
| C3 | `tests/test_check_proofs.py` `test_sees_docstring_do_unittest` | yes |
| C4 | `tests/test_check_proofs.py` `test_prova_com_tempo_limite` | no - não verifica o encerramento do processo que excede o limite |
| C5 | `tests/test_secret_scan.py` `test_frase_binary_files_em_texto_e_escaneada` | yes |
| C6 | `tests/test_secret_scan.py` `test_arquivo_pulado_avisa` | yes |
| C7 | `tests/test_build.py` `test_decisions_lote1_correcoes` | no - termos soltos não comprovam todas as regras R1 a R6 na Decisão |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R5: byte nulo após os primeiros 8.000 caracteres do diff não é reconhecido como binário. | `$env:PYTHONDONTWRITEBYTECODE='1'; python -c "import sys; sys.path.insert(0,'hooks/scripts'); import secret_scan as s; print(s._is_binary('a'*8000 + chr(0)))"` → `False` | Examinar todo o diff pelo byte nulo e testar uma posição além de 8.000. | |
| C4 não comprova que o comando expirado foi encerrado; apenas verifica o resultado escrito e o veredito. | `tests/test_check_proofs.py:141` | Verificar que o processo iniciado deixou de existir após o limite. | |
| C7 aceita uma Decisão que contenha palavras isoladas mas omita condições essenciais de R1 a R6. | `tests/test_build.py:401` | Afirmar cada condição e valor exigidos dentro da seção Decisão. | |
| R6: o teste cobre retorno não zero, mas nenhum check exercita timeout do git diff, sua mensagem e a continuação para outro arquivo. | `tests/test_secret_scan.py:109` | Simular timeout e verificar a mensagem completa e o processamento dos demais arquivos. | |

## Limits

Regressão completa: `python -m unittest discover -s tests -v` passou, 956 testes em 483,285 s, um ignorado; nenhum teste falhou. O teste ignorado não foi verificado nesta execução.
Sondagem R2/R3: `$env:PYTHONDONTWRITEBYTECODE='1'; python -c "import sys; sys.path.insert(0,'scripts/gates'); import check_proofs as p; print(p.sees('test_beta (pkg.C.test_beta)'+chr(10)+'description ... ok','test_beta (pkg.C.test_beta) ... ok')); print(p.sees('prefix_test_beta PASSED','test_beta PASSED'))"` produziu `True` e `False`.
