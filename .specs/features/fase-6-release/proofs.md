# fase-6-release proofs

**HEAD**: 16bc6bc
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 32 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_opencode_install_replaces_starcode_skill_paths_from_other_clones ... ok` | pass |
| C2 | `run unit / test_opencode_install_keeps_foreign_skill_paths_in_order ... ok` | pass |
| C3 | `run unit / test_opencode_install_twice_from_two_clones_no_duplicates ... ok` | pass |
| C4 | `run unit / test_banner_setup_command_per_cli ... ok` | pass |
| C5 | `run unit / test_banner_engajar_command_matches_cmd_ref ... ok` | pass |
| C6 | `run unit / test_version_is_1_0_0_in_all_manifests ... ok` | pass |
| C7 | `run unit / test_check_fails_when_manifest_version_diverges ... ok` | pass |
| C8 | `run unit / test_changelog_has_1_0_0_section ... ok` | pass |
| C9 | `run unit / test_release_check_rejects_tag_diverging_from_version ... ok` | pass |
| C10 | `run unit / test_release_refuses_existing_remote_tag ... ok` | pass |
| C11 | `run unit / test_release_notes_extracted_from_changelog ... ok` | pass |
| C12 | `run unit / test_release_create_requires_yes_flag ... ok` | pass |
| C13 | `run unit / test_ci_triggers ... ok` | pass |
| C14 | `run unit / test_ci_checks_steps_and_commands ... ok` | pass |
| C15 | `run unit / test_ci_matrix_ubuntu_windows_python_312 ... ok` | pass |
| C16 | `run unit / test_ci_plugin_validate_with_pinned_claude_code ... ok` | pass |
| C17 | `run unit / test_ci_has_no_continue_on_error ... ok` | pass |
| C18 | `run unit / test_ci_concurrency_cancels_in_progress ... ok` | pass |
| C19 | `run unit / test_ci_eval_job_only_on_tag_or_dispatch ... ok` | pass |
| C20 | `run unit / test_ci_secret_only_in_eval_job ... ok` | pass |
| C21 | `run unit / test_ci_eval_fails_without_secret ... ok` | pass |
| C22 | `run unit / test_ci_eval_uploads_results_and_summary ... ok` | pass |
| C23 | `run unit / test_ci_release_check_runs_release_py ... ok` | pass |
| C24 | `run unit / test_readme_install_commands_per_cli ... ok` | pass |
| C25 | `run unit / test_readme_states_v1_and_private_access ... ok` | pass |
| C26 | `run unit / test_decisions_f6_1_sandbox_mission_day ... ok` | pass |
| C27 | `run unit / test_acceptance_doc_f6_claude_codex_filled ... ok` | pass |
| C28 | `run unit / test_acceptance_doc_f6_antigravity_opencode_filled ... ok` | pass |
| C29 | `run unit / test_acceptance_doc_f6_mission_day_filled ... ok` | pass |
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
Ran 312 tests in 115.241s

OK
```
