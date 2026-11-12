# fase-12-robustez verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at `e2c211f`
**HEAD**: 5fd4a31
**Verifier**: codex · requested padrão do CLI · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_snapshot.py test_take_grava_ref_com_rastreados_e_novos` | yes |
| C2 | `tests/test_snapshot.py test_take_nao_altera_indice_arvore_head` | yes |
| C3 | `tests/test_snapshot.py test_take_substitui_snapshot_existente` | yes |
| C4 | `tests/test_snapshot.py test_take_nome_invalido_sai_2` | yes |
| C5 | `tests/test_snapshot.py test_take_sem_head_ou_fora_do_git_sai_1` | yes |
| C6 | `tests/test_snapshot.py test_list_texto_json_e_vazio` | yes |
| C7 | `tests/test_snapshot.py test_drop_remove_refs_da_feature` | yes |
| C8 | `tests/test_snapshot_restore.py test_restore_sem_yes_mostra_plano_e_nao_altera` | yes |
| C9 | `tests/test_snapshot_restore.py test_restore_yes_volta_e_remove_so_no_may_change` | yes |
| C10 | `tests/test_snapshot_restore.py test_restore_lista_fora_do_ticket_com_limite` | yes |
| C11 | `tests/test_snapshot_restore.py test_restore_recusa_head_mudado` | yes |
| C12 | `tests/test_snapshot_restore.py test_restore_sem_snapshot_ou_ticket_sem_may_change` | yes |
| C13 | `tests/test_snapshot_restore.py test_restore_falha_parcial_e_retomada` | yes |
| C14 | `tests/test_impact.py test_select_diff_inclui_nao_rastreados` | yes |
| C15 | `tests/test_impact.py test_identifica_testes_python_e_ts` | yes |
| C16 | `tests/test_impact.py test_python_imports_absolutos_relativos_e_ambiguos` | yes |
| C17 | `tests/test_impact_ts.py test_ts_imports_relativos_extensoes_e_index` | yes |
| C18 | `tests/test_impact.py test_teste_mudado_entra_no_conjunto` | yes |
| C19 | `tests/test_impact.py test_dependentes_transitivos_e_ciclo` | yes |
| C20 | `tests/test_impact.py test_fora_do_grafo_roda_tudo` | yes |
| C21 | `tests/test_impact.py test_grafo_incompleto_roda_tudo` | no - exceção do marcador `{{` aplicada também a TS/JS; caso exploratório selecionou teste apesar do arquivo TS malformado |
| C22 | `tests/test_impact_ts.py test_aliases_ts_roda_tudo` | yes |
| C23 | `tests/test_impact.py test_nenhum_teste_alcanca_roda_tudo` | yes |
| C24 | `tests/test_impact.py test_sem_mudanca_roda_tudo` | yes |
| C25 | `tests/test_impact.py test_saida_texto_selecao_e_rodar_tudo` | yes |
| C26 | `tests/test_impact.py test_saida_json_contrato` | yes |
| C27 | `tests/test_impact.py test_erros_git_e_argumentos` | yes |
| C28 | `tests/test_flow_f12.py test_execute_md_snapshot_antes_do_ticket` | yes |
| C29 | `tests/test_flow_f12.py test_execute_md_saida_b_restaura_snapshot` | yes |
| C30 | `tests/test_flow_f12.py test_execute_md_drop_no_done` | yes |
| C31 | `tests/test_flow_f12.py test_mccoy_skill_raio_de_impacto` | yes |
| C32 | `tests/test_dispatch_regression.py test_q_brief_bloco_regression` | yes |
| C33 | `tests/test_dispatch_regression.py test_q_brief_impact_indisponivel` | yes |
| C34 | `tests/test_dispatch_regression.py test_q_verify_regra_regression_autocontida` | yes |
| C35 | `tests/test_release_docs_f12.py test_build_leva_snapshot_e_impact` | yes |
| C36 | `tests/test_snapshot_restore.py test_cenario_aceite_disjuntor_modo_1` | yes |
| C37 | `tests/test_impact.py test_impact_no_repo_starcode` | yes |
| C38 | `tests/test_impact_ts.py test_impact_fixture_telas` | yes |
| C39 | `tests/test_release_docs_f12.py test_registros_fase_12` | yes |
| C40 | `tests/test_acceptance_doc_f12.py test_acceptance_doc_f12` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R21: arquivo TS/JS malformado que contém `{{` é tratado como template Python e ignorado; a seleção pode omitir testes. | `scripts/impact.py:258`; prova exploratória em repositório temporário: `impact.select(..., changed=["src/a.ts"])` retornou `{'verdict': 'selected', 'tests': ['tests/a.test.ts'], ...}` para `src/a.ts` com `export const a={{broken`. | Aplicar a exceção do marcador somente para arquivos `.py`; erros de análise TS/JS devem produzir `grafo incompleto`. | 3fc0e53 |
| Asserções menos estritas que os critérios: C11 confirma apenas trechos da mensagem de recusa, sem comparar pai e HEAD; C12 confirma fragmentos de motivo; C28–C31 verificam fragmentos/ordem aproximada da documentação, não todas as condições e sequência dos requisitos. | `tests/test_snapshot_restore.py:155-156`, `tests/test_snapshot_restore.py:163-168`, `tests/test_flow_f12.py:22-43` | Acrescentar asserts de saída integral e de cada condição/ordem requerida, incluindo `worker-stop` antes da restauração. | 257e90d |
| C33 aceita qualquer texto começando por `seleção indisponível:` e contendo `; rode a suíte inteira`, sem exigir interpolação do motivo retornado pelo erro. | `tests/test_dispatch_regression.py:43-44` | Comparar o bloco completo com o motivo de falha conhecido, como já é feito no caso de sucesso. | 0cc7c0e |

## Limits

Suíte de regressão HEAD: `python -m unittest discover -s tests -v` — exit 0; 714 testes executados, OK (1 skip: bit executável não existe no Windows).
Exemplo R21: TS malformado com `{{` retornou seleção, contrariando o requisito; saída: `selected`, `tests/a.test.ts`.
Exemplo R21 no limite: arquivo Python exatamente 1 MiB selecionou `tests/test_pkg.py`; com 1 MiB + 1 byte, retornou `run-all: grafo incompleto: pkg.py: arquivo acima de 1 MiB`.
Exemplo R4: `python scripts/snapshot.py take feat 'é1' --root .` imprimiu `nome inválido para o snapshot: é1` e saiu 2.
