# fase-11-telas proofs

**HEAD**: ca16745
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 42 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_captura_sem_sources ... ok` | pass |
| C2 | `run unit / test_captura_sem_linha_ou_non_binding_sem_citacao ... ok` | pass |
| C3 | `run unit / test_captura_vinculante_sem_requisito ... ok` | pass |
| C4 | `run unit / test_captura_sem_imagem_na_spec ... ok` | pass |
| C5 | `run unit / test_feature_sem_telas_inalterada ... ok` | pass |
| C6 | `run unit / test_telas_sem_screens_md ... ok` | pass |
| C7 | `run unit / test_tela_diverges_reprova ... ok` | pass |
| C8 | `run unit / test_screens_sem_round_ou_round_3 ... ok` | pass |
| C9 | `run unit / test_screens_sem_verifier ... ok` | pass |
| C10 | `run unit / test_captura_sem_running ... ok` | pass |
| C11 | `run unit / test_running_em_outro_tamanho ... ok` | pass |
| C11 | `run unit / test_running_2x_de_captura_1x_passa ... ok` | pass |
| C12 | `run unit / test_imagem_ilegivel_vira_erro ... ok` | pass |
| C13 | `run unit / test_fotos_do_autor_degradada_e_strict ... ok` | pass |
| C14 | `run unit / test_capture_chama_orca_na_ordem ... ok` | pass |
| C15 | `run unit / test_capture_url_data_recusada ... ok` | pass |
| C16 | `run unit / test_capture_falha_fecha_aba ... ok` | pass |
| C17 | `run unit / test_capture_sem_frame_tenta_de_novo ... ok` | pass |
| C18 | `run unit / test_size_imprime_css ... ok` | pass |
| C19 | `run unit / test_list_capturas_da_spec ... ok` | pass |
| C20 | `run unit / test_capture_tamanho_errado_falha ... ok` | pass |
| C21 | `run unit / test_screens_brief_nao_leva_checks_nem_diff ... ok` | pass |
| C22 | `run unit / test_screens_brief_sem_captura_sai_2 ... ok` | pass |
| C22 | `run unit / test_screens_brief_preenche_campos ... ok` | pass |
| C23 | `run unit / test_screens_brief_preenche_campos ... ok` | pass |
| C24 | `run unit / test_screens_brief_regras_de_julgamento ... ok` | pass |
| C25 | `run unit / test_screens_brief_regras_de_julgamento ... ok` | pass |
| C26 | `run unit / test_screens_brief_regras_de_julgamento ... ok` | pass |
| C27 | `run unit / test_screens_brief_rodada_2 ... ok` | pass |
| C28 | `run unit / test_execute_despacha_juiz_de_telas ... ok` | pass |
| C29 | `run unit / test_spock_regras_de_captura_sem_d25 ... ok` | pass |
| C30 | `run unit / test_laforge_foto_do_autor ... ok` | pass |
| C31 | `run unit / test_template_tauri_mockipc_so_em_dev ... ok` | pass |
| C32 | `run unit / test_perfil_tauri_tem_screens ... ok` | pass |
| C33 | `run unit / test_build_leva_telas_aos_4_clis ... ok` | pass |
| C34 | `run unit / test_release_docs_f11 ... ok` | pass |
| C35 | `run unit / test_fase11_acceptance_sections ... ok` | pass |
| C36 | `run unit / test_fase11_acceptance_sections ... ok` | pass |
| C37 | `run unit / test_fase11_acceptance_sections ... ok` | pass |
| C38 | `run unit / test_fase11_acceptance_sections ... ok` | pass |
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
Ran 654 tests in 281.212s

OK
```
