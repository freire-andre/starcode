# fase-8-uhura-scotty-kirk proofs

**HEAD**: f01208a
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 53 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_profiles_all_seven_with_required_fields ... ok` | pass |
| C2 | `run unit / test_profiles_gate_commands_exact ... ok` | pass |
| C3 | `run unit / test_templates_have_no_hardcoded_versions ... ok` | pass |
| C4 | `run slow / test_flask_template_gates_pass ... ok` | pass |
| C5 | `run slow / test_flask_postgresql_gates_pass ... ok` | pass |
| C6 | `run unit / test_app_templates_have_ci_and_gitignore ... ok` | pass |
| C7 | `run unit / test_registry_stable_latest_per_registry ... ok` | pass |
| C8 | `run unit / test_registry_rejects_prereleases ... ok` | pass |
| C9 | `run unit / test_scaffold_aligns_major_group ... ok` | pass |
| C10 | `run unit / test_scaffold_registry_error_writes_nothing ... ok` | pass |
| C11 | `run unit / test_registry_fixture_marks_source ... ok` | pass |
| C12 | `run unit / test_scaffold_new_renders_and_writes_stack_json ... ok` | pass |
| C13 | `run unit / test_scaffold_rejects_invalid_name ... ok` | pass |
| C14 | `run unit / test_scaffold_rejects_non_empty_dir ... ok` | pass |
| C15 | `run unit / test_scaffold_rejects_unknown_combo ... ok` | pass |
| C16 | `run unit / test_scaffold_cleans_up_on_failure ... ok` | pass |
| C17 | `run unit / test_scaffold_checks_lines ... ok` | pass |
| C18 | `run unit / test_scaffold_gates_pass_fail_lines ... ok` | pass |
| C19 | `run unit / test_scaffold_gates_skip_missing_tool ... ok` | pass |
| C20 | `run unit / test_ephemeral_run_lifecycle_with_fake_docker ... ok` | pass |
| C21 | `run unit / test_ephemeral_docker_unavailable_exit_3 ... ok` | pass |
| C22 | `run unit / test_ephemeral_not_ready_exit_4 ... ok` | pass |
| C23 | `run unit / test_ephemeral_reuse_env_rejects_remote_url ... ok` | pass |
| C24 | `run unit / test_ephemeral_list_and_down ... ok` | pass |
| C25 | `run unit / test_ephemeral_unique_names_and_ports ... ok` | pass |
| C26 | `run unit / test_stack_cache_write_replaces_entry ... ok` | pass |
| C27 | `run unit / test_stack_cache_check_states ... ok` | pass |
| C28 | `run unit / test_uhura_skill_context7_protocol ... ok` | pass |
| C29 | `run unit / test_uhura_pr_and_comment_templates ... ok` | pass |
| C30 | `run unit / test_execute_uses_uhura_for_pr_and_comments ... ok` | pass |
| C31 | `run unit / test_scaffold_detect_and_record_profiles ... ok` | pass |
| C32 | `run unit / test_data_skill_uses_stack_checks ... ok` | pass |
| C33 | `run unit / test_nova_missao_skill_order ... ok` | pass |
| C34 | `run unit / test_nova_missao_gates_fail_no_commit ... ok` | pass |
| C35 | `run unit / test_nova_missao_offers_setup_and_first_mission ... ok` | pass |
| C36 | `run unit / test_build_copies_profiles_and_new_skills ... ok` | pass |
| C37 | `run unit / test_fase8_acceptance_all_scenarios_approved ... ok` | pass |
| C38 | `run unit / test_decisions_f8_and_changelog_1_2_0 ... ok` | pass |
| C39 | `run unit / test_profiles_main_deps_have_tested_series ... ok` | pass |
| C40 | `run unit / test_scaffold_outside_tested_series_exits_5 ... ok` | pass |
| C41 | `run unit / test_scaffold_pin_tested_and_allow_new_series ... ok` | pass |
| C42 | `run unit / test_profiles_main_deps_have_docs_id ... ok` | pass |
| C43 | `run unit / test_nova_missao_series_choice ... ok` | pass |
| C44 | `run unit / test_nova_missao_without_context7 ... ok` | pass |
| C45 | `run unit / test_scaffold_description_validation_and_readme ... ok` | pass |
| C46 | `run slow / test_rust_template_gates_pass ... ok` | pass |
| C47 | `run slow / test_gpui_template_gates_pass ... ok` | pass |
| C48 | `run slow / test_typescript_template_gates_pass ... ok` | pass |
| C49 | `run slow / test_tauri_template_gates_pass ... ok` | pass |
| C50 | `run slow / test_flask_mysql_gates_pass ... ok` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `claude plugin validate dist/claude --strict` | pass |
| Build | `python scripts/check_decisions.py` | pass |

## Output

`Run unit` - exit 0

```
test_all_valid_fixtures_pass (test_validate_config.ValidFixtures.test_all_valid_fixtures_pass) ... ok
test_complete_feature_passes (test_validate_verification.ValidateVerificationTests.test_complete_feature_passes) ... ok
test_degraded_warns_and_strict_fails (test_validate_verification.ValidateVerificationTests.test_degraded_warns_and_strict_fails) ... ok
test_mode1_dirty_tree_only_with_degraded (test_validate_verification.ValidateVerificationTests.test_mode1_dirty_tree_only_with_degraded) ... ok
test_verification_fails_on_missing_or_stale_proofs (test_validate_verification.ValidateVerificationTests.test_verification_fails_on_missing_or_stale_proofs) ... ok
test_verification_fails_on_open_finding_or_missing_approval (test_validate_verification.ValidateVerificationTests.test_verification_fails_on_open_finding_or_missing_approval) ... ok
test_execute_stops_on_codex_hooks_review (test_worker_skills.WorkerSkillTests.test_execute_stops_on_codex_hooks_review) ... ok
test_laforge_calls_mccoy_on_second_failure (test_worker_skills.WorkerSkillTests.test_laforge_calls_mccoy_on_second_failure) ... ok
test_laforge_skill_scope_tdd_commit (test_worker_skills.WorkerSkillTests.test_laforge_skill_scope_tdd_commit) ... ok
test_mccoy_skill_regression_and_report (test_worker_skills.WorkerSkillTests.test_mccoy_skill_regression_and_report) ... ok

----------------------------------------------------------------------
Ran 523 tests in 215.939s

OK
```

`Run slow` - exit 0

```
test_flask_mysql_gates_pass (test_slow_db.SlowDbTests.test_flask_mysql_gates_pass) ... ok
test_flask_postgresql_gates_pass (test_slow_db.SlowDbTests.test_flask_postgresql_gates_pass) ... ok
test_flask_template_gates_pass (test_slow_python_flask.SlowPythonFlaskTests.test_flask_template_gates_pass) ... ok
test_gpui_template_gates_pass (test_slow_rust_gpui.RustGpuiGatesTests.test_gpui_template_gates_pass) ... ok
test_rust_template_gates_pass (test_slow_rust_gpui.RustGpuiGatesTests.test_rust_template_gates_pass) ... ok
test_tauri_template_gates_pass (test_slow_ts_tauri.TsTauriGatesTests.test_tauri_template_gates_pass) ... ok
test_typescript_template_gates_pass (test_slow_ts_tauri.TsTauriGatesTests.test_typescript_template_gates_pass) ... ok

----------------------------------------------------------------------
Ran 7 tests in 451.287s

OK
```
