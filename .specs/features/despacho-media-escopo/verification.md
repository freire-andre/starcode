# despacho-media-escopo verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 2c37c9d
**HEAD**: d8507bf
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_dispatch_decisions.py` `test_regra_decisions_compartilhada` | yes |
| C2 | `tests/test_check_scope.py` `test_scope_aceita_decisions_com_scripts` | yes |
| C3 | `tests/test_check_scope.py` `test_scope_media_aceita_decisions` | yes |
| C4 | `tests/test_dispatch_decisions.py` `test_brief_media_acrescenta_decisions` | yes |
| C5 | `tests/test_dispatch_start.py` `test_start_media_despacha_t1` | no - `startswith` não verifica o sufixo da entrada nem o formato da hora UTC exigidos por R5. |
| C6 | `tests/test_dispatch_start.py` `test_start_media_sem_linear_recusa` | yes |
| C7 | `tests/test_dispatch_start.py` `test_media_ticket_errado_recusa` | yes |
| C8 | `tests/test_dispatch_settle.py` `test_settle_media_integra_t1` | yes |
| C9 | `tests/test_dispatch_start.py` `test_main_arquivo_ausente_sai_2` | no - exercita `next` e não verifica os outros subcomandos que R9 inclui. |
| C10 | `tests/test_dispatch_start.py` `test_start_sem_ramo_aponta_modo_1` | yes |
| C11 | `tests/test_dispatch_start.py` `test_start_entrada_aberta_aponta_dispatch_remove` | yes |
| C12 | `tests/test_execute_doc_start_settle.py` `test_execute_media_retry_e_modo_1` | yes |
| C13 | `tests/test_dispatch_decisions.py` `test_decisions_despacho_media` | no - verifica termos representativos e nomes dos testes, não que a entrada descreva R1 a R14. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C5 aceita uma entrada com qualquer conteúdo depois do prefixo; não prova a hora UTC nem a entrada completa fixada por R5. | `tests/test_dispatch_start.py:277` | Asserir a entrada integral, incluindo os campos e o formato `YYYY-MM-DDTHH:MM:SSZ`. | 8c5fb8e |
| C9 seleciona só o caminho `next`; não verifica a garantia para cada subcomando de R9. | `tests/test_dispatch_start.py:308` | Exercitar falha de arquivo ausente em cada subcomando que lê arquivos ou testar explicitamente o handler comum para todos eles. | 8c5fb8e |
| C13 pode passar se a entrada SC-169 omitir requisitos de R1 a R14, pois só busca palavras e nomes de testes. | `tests/test_dispatch_decisions.py:120` | Verificar na entrada a descrição de cada requisito R1 a R14, além dos campos e referências de teste. | 0010fd1 |
| A comparação de ID de ticket sem diferença de maiúsculas é implementada, mas nenhum check a fixa como regra; uma regressão silenciosa pode rejeitar um ID em minúsculas. | `scripts/dispatch.py:661` | Acrescentar um teste de start e settle com o ID Linear em minúsculas. | e0a81e9 |

## Limits

Suíte completa no HEAD `d8507bf`: `python -m unittest discover -s tests -v 2>&1` — 833 testes, 1 skipped, `OK` (390.128s). O HEAD é descendente do commit de proofs `6bf9014`; as proofs registram a suíte em `2c37c9d`.

Probes adicionais passaram: `effective_may_change` com `./DECISIONS.md` não duplicou o caminho; `medium_ticket` aceitou `sc-169` para uma spec com `SC-169`.
