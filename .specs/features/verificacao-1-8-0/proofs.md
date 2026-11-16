# verificacao-1-8-0 proofs

**HEAD**: 222a2cb
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 30 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_start_is_idempotent_and_fixed_format (test_piloto.PilotoScriptTests.test_start_is_idempotent_a` | pass |
| C2 | `run unit / test_mandate_numbered_and_locked_after_confirm (test_piloto.PilotoScriptTests.test_mandate_numbered` | pass |
| C3 | `run unit / test_no_decision_before_confirmed_mandate (test_piloto.PilotoScriptTests.test_no_decision_before_co` | pass |
| C3 | `run unit / test_finish_stops_decisions (test_piloto.PilotoScriptTests.test_finish_stops_decisions) ... ok` | pass |
| C3 | `run unit / test_registrar_exige_mandato_com_user (test_piloto.PilotDecisaoCitadaTests.test_registrar_exige_man` | pass |
| C4 | `run unit / test_record_decisions_confidence_and_review (test_piloto.PilotoScriptTests.test_record_decisions_co` | pass |
| C5 | `run unit / test_cli_exit_codes (test_piloto.PilotoScriptTests.test_cli_exit_codes) ... ok` | pass |
| C6 | `run unit / test_banner_shows_active_autopilot (test_piloto.PilotBannerTests.test_banner_shows_active_autopilot` | pass |
| C7 | `run unit / test_aprovacao_com_decisao_registrada_passa_nos_dois_gates (test_piloto.PilotDecisaoCitadaTests.tes` | pass |
| C7 | `run unit / test_d07_cita_d7 (test_piloto.PilotDecisaoCitadaTests.test_d07_cita_d7) ... ok` | pass |
| C7 | `run unit / test_uma_linha_valida_basta (test_piloto.PilotDecisaoCitadaTests.test_uma_linha_valida_basta) ... o` | pass |
| C8 | `run unit / test_decisao_inexistente_reprova_nos_dois_gates (test_piloto.PilotDecisaoCitadaTests.test_decisao_i` | pass |
| C8 | `run unit / test_sem_piloto_md_reprova_sem_excecao (test_piloto.PilotDecisaoCitadaTests.test_sem_piloto_md_repr` | pass |
| C8 | `run unit / test_mandato_sem_user_nao_vale (test_piloto.PilotDecisaoCitadaTests.test_mandato_sem_user_nao_vale)` | pass |
| C8 | `run unit / test_spec_recusa_piloto_com_decisao_registrada (test_piloto.PilotDecisaoCitadaTests.test_spec_recus` | pass |
| C9 | `run unit / test_tier_by_output_price (test_model_info.ModelInfoTests.test_tier_by_output_price) ... ok` | pass |
| C10 | `run unit / test_fit_vetoes_and_warnings (test_model_info.ModelInfoTests.test_fit_vetoes_and_warnings) ... ok` | pass |
| C11 | `run unit / test_cache_fresh_stale_and_no_fetch (test_model_info.ModelInfoTests.test_cache_fresh_stale_and_no_f` | pass |
| C11 | `run unit / test_cli_exit_codes (test_model_info.ModelInfoTests.test_cli_exit_codes) ... ok` | pass |
| C12 | `run unit / test_opencode_provider_models_get_a_family (test_model_info.DispatchFamilyTests.test_opencode_provi` | pass |
| C12 | `run unit / test_q_cli_accepts_opencode_model_of_other_family (test_model_info.DispatchFamilyTests.test_q_cli_a` | pass |
| C12 | `run unit / test_without_catalog_stays_unknown (test_model_info.DispatchFamilyTests.test_without_catalog_stays_` | pass |
| C13 | `run unit / test_precedence_local_over_user_over_default (test_model_info.LocalConfigTests.test_precedence_loca` | pass |
| C13 | `run unit / test_local_schema_only_crew (test_model_info.LocalConfigTests.test_local_schema_only_crew) ... ok` | pass |
| C13 | `run unit / test_banner_and_crew_table_show_local (test_model_info.LocalConfigTests.test_banner_and_crew_table_` | pass |
| C14 | `run unit / test_piloto_skill_rules (test_piloto.PilotSkillTests.test_piloto_skill_rules) ... ok` | pass |
| C14 | `run unit / test_troi_grill_mode (test_piloto.PilotSkillTests.test_troi_grill_mode) ... ok` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `claude plugin validate dist/claude --strict` | pass |
| Build | `python scripts/check_decisions.py` | pass |

## Output

`Run unit` - exit 0

```
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
Ran 936 tests in 449.181s

OK (skipped=1)
inativo
```
