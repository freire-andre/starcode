# fase-12-robustez proofs

**HEAD**: 3fa4e7b
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 42 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_take_grava_ref_com_rastreados_e_novos ... ok` | pass |
| C2 | `run unit / test_take_nao_altera_indice_arvore_head ... ok` | pass |
| C3 | `run unit / test_take_substitui_snapshot_existente ... ok` | pass |
| C4 | `run unit / test_take_nome_invalido_sai_2 ... ok` | pass |
| C5 | `run unit / test_take_sem_head_ou_fora_do_git_sai_1 ... ok` | pass |
| C6 | `run unit / test_list_texto_json_e_vazio ... ok` | pass |
| C7 | `run unit / test_drop_remove_refs_da_feature ... ok` | pass |
| C8 | `run unit / test_restore_sem_yes_mostra_plano_e_nao_altera ... ok` | pass |
| C9 | `run unit / test_restore_yes_volta_e_remove_so_no_may_change ... ok` | pass |
| C10 | `run unit / test_restore_lista_fora_do_ticket_com_limite ... ok` | pass |
| C11 | `run unit / test_restore_recusa_head_mudado ... ok` | pass |
| C12 | `run unit / test_restore_sem_snapshot_ou_ticket_sem_may_change ... ok` | pass |
| C13 | `run unit / test_restore_falha_parcial_e_retomada ... ok` | pass |
| C14 | `run unit / test_select_diff_inclui_nao_rastreados ... ok` | pass |
| C15 | `run unit / test_identifica_testes_python_e_ts ... ok` | pass |
| C16 | `run unit / test_python_imports_absolutos_relativos_e_ambiguos ... ok` | pass |
| C17 | `run unit / test_ts_imports_relativos_extensoes_e_index ... ok` | pass |
| C18 | `run unit / test_teste_mudado_entra_no_conjunto ... ok` | pass |
| C19 | `run unit / test_dependentes_transitivos_e_ciclo ... ok` | pass |
| C20 | `run unit / test_fora_do_grafo_roda_tudo ... ok` | pass |
| C21 | `run unit / test_grafo_incompleto_roda_tudo ... ok` | pass |
| C22 | `run unit / test_aliases_ts_roda_tudo ... ok` | pass |
| C23 | `run unit / test_nenhum_teste_alcanca_roda_tudo ... ok` | pass |
| C24 | `run unit / test_sem_mudanca_roda_tudo ... ok` | pass |
| C25 | `run unit / test_saida_texto_selecao_e_rodar_tudo ... ok` | pass |
| C26 | `run unit / test_saida_json_contrato ... ok` | pass |
| C27 | `run unit / test_erros_git_e_argumentos ... ok` | pass |
| C28 | `run unit / test_execute_md_snapshot_antes_do_ticket ... ok` | pass |
| C29 | `run unit / test_execute_md_saida_b_restaura_snapshot ... ok` | pass |
| C30 | `run unit / test_execute_md_drop_no_done ... ok` | pass |
| C31 | `run unit / test_mccoy_skill_raio_de_impacto ... ok` | pass |
| C32 | `run unit / test_q_brief_bloco_regression ... ok` | pass |
| C33 | `run unit / test_q_brief_impact_indisponivel ... ok` | pass |
| C34 | `run unit / test_q_verify_regra_regression_autocontida ... ok` | pass |
| C35 | `run unit / test_build_leva_snapshot_e_impact ... ok` | pass |
| C36 | `run unit / test_cenario_aceite_disjuntor_modo_1 ... ok` | pass |
| C37 | `run unit / test_impact_no_repo_starcode ... ok` | pass |
| C38 | `run unit / test_impact_fixture_telas ... ok` | pass |
| C39 | `run unit / test_registros_fase_12 ... ok` | pass |
| C40 | `run unit / test_acceptance_doc_f12 ... ok` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `python scripts/check_decisions.py` | pass |

## Output

`Run unit` - exit 0

```
test_telas_sem_screens_md (test_validate_verification_screens.ScreensTests.test_telas_sem_screens_md) ... ok
test_worf_review_standards_bypass_rule (test_worf_skill.WorfSkillTests.test_worf_review_standards_bypass_rule) ... ok
test_worf_skill_evidence_or_silence (test_worf_skill.WorfSkillTests.test_worf_skill_evidence_or_silence) ... ok
test_worf_skill_never_merges (test_worf_skill.WorfSkillTests.test_worf_skill_never_merges) ... ok
test_worf_skill_review_flow_order (test_worf_skill.WorfSkillTests.test_worf_skill_review_flow_order) ... ok
test_worf_skill_review_md_contract (test_worf_skill.WorfSkillTests.test_worf_skill_review_md_contract) ... ok
test_execute_stops_on_codex_hooks_review (test_worker_skills.WorkerSkillTests.test_execute_stops_on_codex_hooks_review) ... ok
test_laforge_calls_mccoy_on_second_failure (test_worker_skills.WorkerSkillTests.test_laforge_calls_mccoy_on_second_failure) ... ok
test_laforge_skill_scope_tdd_commit (test_worker_skills.WorkerSkillTests.test_laforge_skill_scope_tdd_commit) ... ok
test_mccoy_skill_regression_and_report (test_worker_skills.WorkerSkillTests.test_mccoy_skill_regression_and_report) ... ok

----------------------------------------------------------------------
Ran 720 tests in 324.825s

OK (skipped=1)
```
