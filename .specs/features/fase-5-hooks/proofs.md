# fase-5-hooks proofs

**HEAD**: a89e298
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 33 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_codex_hooks_json_registers_guards_and_banner ... ok` | pass |
| C2 | `run unit / test_antigravity_hooks_json_native_format ... ok` | pass |
| C3 | `run unit / test_dist_has_no_machine_absolute_paths ... ok` | pass |
| C4 | `run unit / test_session_start_banner_runs_in_hook_mode ... ok` | pass |
| C5 | `run unit / test_opencode_plugin_in_dist_is_pure_object ... ok` | pass |
| C6 | `run unit / test_opencode_plugin_throws_on_guard_deny ... ok` | pass |
| C7 | `run unit / test_opencode_plugin_allows_normal_command ... ok` | pass |
| C8 | `run unit / test_opencode_plugin_fails_open_with_warning ... ok` | pass |
| C9 | `run unit / test_force_push_denied_codex_and_antigravity_payloads ... ok` | pass |
| C10 | `run unit / test_secret_commit_denied_codex_and_antigravity_payloads ... ok` | pass |
| C11 | `run unit / test_normal_flow_commands_pass_all_payloads ... ok` | pass |
| C12 | `run unit / test_invalid_payload_fails_open_with_warning ... ok` | pass |
| C13 | `run unit / test_install_writes_absolute_paths_in_installed_copy ... ok` | pass |
| C14 | `run unit / test_install_twice_keeps_single_registration ... ok` | pass |
| C15 | `run unit / test_codex_banner_warns_hooks_without_trust ... ok` | pass |
| C16 | `run unit / test_banner_hook_mode_matches_text_per_cli ... ok` | pass |
| C17 | `run unit / test_setup_codex_shows_trust_step ... ok` | pass |
| C18 | `run unit / test_setup_opencode_confirms_plugin_copy ... ok` | pass |
| C19 | `run unit / test_setup_checks_python_per_cli ... ok` | pass |
| C20 | `run unit / test_conflicts_lists_starcode_hello ... ok` | pass |
| C21 | `run unit / test_execute_stops_on_codex_hooks_review ... ok` | pass |
| C22 | `run unit / test_acceptance_scripts_f5_have_sections ... ok` | pass |
| C23 | `run unit / test_acceptance_doc_f5_codex_filled ... ok` | pass |
| C24 | `run unit / test_acceptance_doc_f5_antigravity_filled ... ok` | pass |
| C25 | `run unit / test_acceptance_doc_f5_opencode_filled ... ok` | pass |
| C26 | `run unit / test_capabilities_match_f5_acceptance ... ok` | pass |
| C27 | `run unit / test_antigravity_hook_commands_without_quotes ... ok` | pass |
| C28 | `run unit / test_antigravity_install_refuses_path_with_space ... ok` | pass |
| C29 | `run unit / test_agy_real_commit_payload_denies_staged_secret ... ok` | pass |
| C30 | `run unit / test_opencode_plugin_uses_event_workdir ... ok` | pass |
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
Ran 275 tests in 90.306s

OK
```
