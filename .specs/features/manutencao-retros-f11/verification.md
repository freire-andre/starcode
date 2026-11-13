# manutencao-retros-f11 verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at `b4be0a9`
**HEAD**: 51e75de
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_handoff_report_date.py` `test_report_com_data_iso_nao_prefixa` | yes |
| C2 | `tests/test_handoff_report_date.py` `test_report_sem_data_prefixa_hoje` | yes |
| C3 | `tests/test_check_proofs_lf.py` `test_proofs_md_gravado_sem_cr` | yes |
| C4 | `tests/test_dispatch_decisions.py` `test_brief_acrescenta_decisions_com_scripts` | yes |
| C5 | `tests/test_dispatch_decisions.py` `test_brief_sem_scripts_ou_com_decisions_nao_muda` | yes |
| C6 | `tests/test_dispatch_decisions.py` `test_batch_separa_tickets_de_scripts` | yes |
| C7 | `tests/test_dispatch_decisions.py` `test_brief_traz_regra_de_assinatura` | yes |
| C8 | `tests/test_validate_tasks_citations.py` `test_task_cita_arquivo_fora_do_may_change_falha` | yes |
| C9 | `tests/test_validate_tasks_citations.py` `test_citacao_coberta_por_pasta_ou_nome` | yes |
| C10 | `tests/test_validate_tasks_citations.py` `test_versao_e_atributo_nao_contam` | yes |
| C11 | `tests/test_dispatch_start.py` `test_start_ordem_dos_passos` | yes |
| C12 | `tests/test_dispatch_start.py` `test_start_regrava_entrada_com_dispatch_e_modelo` | yes |
| C13 | `tests/test_dispatch_start.py` `test_start_opencode_cria_worktree_antes` | yes |
| C14 | `tests/test_dispatch_start.py` `test_start_recusa_sem_gravar` | yes |
| C15 | `tests/test_dispatch_start.py` `test_start_worker_falha_remove_entrada` | yes |
| C16 | `tests/test_dispatch_start.py` `test_start_linear_falha_vira_aviso` | yes |
| C17 | `tests/test_dispatch_start.py` `test_start_json` | yes |
| C18 | `tests/test_dispatch_start.py` `test_start_paralelo_preserva_outra_entrada` | yes |
| C19 | `tests/test_dispatch_settle.py` `test_settle_roda_gate_antes_do_merge` | yes |
| C20 | `tests/test_dispatch_settle.py` `test_settle_verde_integra_e_remove_entrada` | yes |
| C21 | `tests/test_dispatch_settle.py` `test_settle_gate_vermelho_nao_integra` | yes |
| C22 | `tests/test_dispatch_settle.py` `test_settle_conflito_aborta` | yes |
| C23 | `tests/test_dispatch_settle.py` `test_settle_recusa_sem_entrada_ou_ramo_errado` | yes |
| C24 | `tests/test_dispatch_settle.py` `test_settle_paralelo_remove_so_o_seu` | yes |
| C25 | `tests/test_execute_doc_start_settle.py` `test_execute_usa_start_e_settle` | yes |
| C26 | `tests/test_execute_doc_start_settle.py` `test_execute_sem_worker_show_posicional` | yes |
| C27 | `tests/test_execute_doc_start_settle.py` `test_execute_diz_onde_ler_o_modelo` | yes |
| C28 | `tests/test_q_brief_evidence.py` `test_q_brief_exige_comando_e_saida_na_sondagem` | yes |
| C29 | `src/orca/src/worker.test.ts` `host recusa agent.launch sem a capacidade` | yes |
| C30 | `src/orca/src/worker.test.ts` testes com wrapper `test` | yes |
| C31 | `tests/test_registros_retros_f11.py` `test_compatibilidade_cita_limite_do_drive` | yes |
| C32 | `tests/test_registros_retros_f11.py` `test_relato_orca_tem_as_secoes` | no - a proibição de quatro palavras em português não prova que o relato inteiro está em inglês |
| C33 | `tests/test_registros_retros_f11.py` `test_decisions_registra_os_itens_de_scripts` | yes |
| C34 | `tests/test_validate_tasks_citations.py` `test_citacao_em_context_nao_conta` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R23 aceita prefixo de data impossível como data ISO; regra de gravação mantém texto inválido sem prefixo. | `scripts/handoff.py:122-128`; probe Python: `2026-99-99: inválida` resultou em `'2026-99-99: inválida'` | Validar a data com calendário antes de preservar o prefixo, e rejeitar ou prefixar entradas inválidas. || 9403771 |
| R20/R21 consideram caminho de travessia fora da pasta coberto por prefixo textual. | `scripts/gates/validate_tasks.py:91-92`; probe: TASK `` `scripts/../../outside.py` `` com May change `` `scripts/` `` resultou em `[]` (nenhuma citação descoberta) | Normalizar/rejeitar segmentos `..` antes de conferir cobertura por diretório. || 866a9c7 |
| C32 não demonstra que o rascunho inteiro está em inglês; as asserções permitem texto em português que evite as quatro palavras proibidas. | `tests/test_registros_retros_f11.py:18-24` | Verificar idioma de modo robusto ou revisar conteúdo manualmente e registrar a conclusão. || d43870a |

## Limits

- A regressão exigida rodou em HEAD `51e75de`: `python -m unittest discover -s tests -v` — 755 testes, OK (1 skipped).
- `proofs.md` declara HEAD `b4be0a9`, diferente do HEAD analisado (`51e75de`); por isso os proofs registrados não são prova de execução no HEAD atual.
- Não foi executada a suíte do plugin Orca; o teste completo Python não a inclui.
- Os testes de texto C25-C28 e de registros C31-C33 validam presença de fragmentos, não toda a semântica ou qualidade do documento.
