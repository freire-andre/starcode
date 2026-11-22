# suite-e-execute verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 6134418
**HEAD**: 0ec5cf7
**Verifier**: codex · requested padrão do CLI (worker-start sem campo model) · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_suite_e_execute.py` `test_fix_brief_usa_selecao_do_impact` | no - examina a constante, não o brief gerado |
| C2 | `tests/test_suite_e_execute.py` `test_brief_do_ticket_usa_selecao_do_impact` | no - examina a constante, não o brief gerado, e aceita relatório alterado após o trecho |
| C3 | `tests/test_suite_e_execute.py` `test_laforge_e_mccoy_rodam_a_selecao` | no - no McCoy, fragmentos isolados não comprovam a condição completa do fallback |
| C4 | `tests/test_suite_e_execute.py` `test_decisions_registra_a_medicao` | no - aceita contagem, tempos e máquina arbitrários com o formato esperado |
| C5 | `tests/test_suite_e_execute.py` `test_agents_tem_regra_de_estado` | yes |
| C6 | `tests/test_suite_e_execute.py` `test_execute_md_vira_indice` | no - aceita prefixos de seções incorretos nas linhas do índice |
| C7 | `tests/test_suite_e_execute.py` `test_cabecalhos_no_arquivo_certo` | yes |
| C8 | `tests/test_flow_f12.py` `test_execute_md_snapshot_antes_do_ticket` | no - verifica um único teste, não todos os testes de documentação |
| C9 | `tests/test_suite_e_execute.py` `test_referencias_apontam_o_arquivo_novo` | no - exclui arquivos cujo nome começa por execute e só reconhece algumas formas de referência |
| C10 | `tests/test_suite_e_execute.py` `test_decisions_e_changelog` | no - confere rótulos e termos soltos, sem associar os termos aos requisitos na decisão |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C1 e C2 não exercitam os briefs efetivamente gerados: uma omissão das constantes na montagem continuaria passando. | `tests/test_suite_e_execute.py:45` e `tests/test_suite_e_execute.py:52` | Gerar ambos os briefs pela interface real e conferir as linhas completas e sua ordem. | |
| C3 aceita no McCoy o fragmento do fallback fora da regra ou com condição invertida. | `tests/test_suite_e_execute.py:66` | Conferir a frase completa da seleção e do fallback em cada skill. | |
| C4 aceita uma medição inventada que respeite a expressão regular, inclusive tempos e nomes arbitrários. | `tests/test_suite_e_execute.py:79` | Comparar os valores registrados com a saída conservada da medição real. | |
| C6 aceita, por exemplo, uma linha de índice iniciada por `4` seguida de um número ou seção incorreta. | `tests/test_suite_e_execute.py:112` | Comparar exatamente o campo de seções de cada linha com o valor exigido. | |
| C8 cita somente o teste da seção 7; os demais testes podem voltar a ler só o índice sem que a prova citada falhe. | `tests/test_flow_f12.py:29` | Provar que todos os testes afetados usam o helper e citar os testes que demonstram a preservação. | |
| C9 ignora todos os arquivos `execute*` e a expressão regular não cobre todas as formas possíveis de referência; uma referência antiga pode permanecer sem falha. | `tests/test_suite_e_execute.py:136` | Examinar toda a árvore exigida e verificar cada referência alterada e seu destino. | |
| C10 verifica rótulos R1 a R10 e termos espalhados, sem exigir os termos de cada requisito no respectivo trecho da decisão. | `tests/test_suite_e_execute.py:162` | Assegurar o conteúdo de cada requisito dentro de sua parte da decisão. | |

## Limits

Regressão completa em `HEAD`, executada com `python -m unittest discover -s tests -p <arquivo>` para cada `test_*.py`: sem falhas, com uma exclusão (`skipped=1`).
Sondas em `HEAD`: caminho do plugin com espaços manteve as aspas no comando de seleção (R1); nenhum cabeçalho adicional inesperado ou duplicado nos arquivos execute (R7).
As provas registram `6134418`, anterior ao `HEAD` analisado `0ec5cf7`; a diferença posterior a `457e95c` altera somente `spec.md`.
A saída detalhada da medição com os cinco tempos não consta em `proofs.md`; não foi possível confrontar os valores registrados com a medição original.
