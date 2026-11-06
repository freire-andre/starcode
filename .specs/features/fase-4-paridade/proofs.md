# fase-4-paridade proofs

**HEAD**: 6c2470b
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 32 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_capabilities_json_per_cli ... ok` | pass |
| C2 | `run unit / test_unavailable_extra_without_fallback_fails ... ok` | pass |
| C3 | `run unit / test_cmd_and_cli_placeholders_per_cli ... ok` | pass |
| C4 | `run unit / test_no_claude_commands_outside_claude_dist ... ok` | pass |
| C5 | `run unit / test_engajar_banner_uses_cli ... ok` | pass |
| C6 | `run unit / test_banner_lists_unavailable_extras ... ok` | pass |
| C7 | `run unit / test_banner_without_cli_keeps_phase3_output ... ok` | pass |
| C8 | `run unit / test_degraded_only_from_marker_line ... ok` | pass |
| C9 | `run unit / test_install_codex_runs_marketplace_and_install ... ok` | pass |
| C10 | `run unit / test_install_antigravity_validates_first ... ok` | pass |
| C11 | `run unit / test_install_opencode_writes_skills_and_commands ... ok` | pass |
| C12 | `run unit / test_install_is_idempotent ... ok` | pass |
| C13 | `run unit / test_install_missing_binary_exits_2 ... ok` | pass |
| C14 | `run unit / test_install_dry_run_changes_nothing ... ok` | pass |
| C15 | `run unit / test_data_parent_issue_fallback ... ok` | pass |
| C16 | `run unit / test_publish_gate_accepts_parent_issue ... ok` | pass |
| C17 | `run unit / test_data_reports_publish_path ... ok` | pass |
| C18 | `run unit / test_q_cli_picks_other_family ... ok` | pass |
| C19 | `run unit / test_q_cli_self_verified_when_none ... ok` | pass |
| C20 | `run unit / test_execute_ref_opencode_and_q_cli ... ok` | pass |
| C21 | `run unit / test_execute_ref_integration_worktree ... ok` | pass |
| C22 | `run unit / test_execute_ref_nested_depth_stop ... ok` | pass |
| C23 | `run unit / test_medium_brief_from_spec ... ok` | pass |
| C24 | `run unit / test_medium_brief_without_checks_exits_2 ... ok` | pass |
| C25 | `run unit / test_family_deepseek_gptoss_openrouter ... ok` | pass |
| C26 | `run unit / test_acceptance_scripts_have_sections ... ok` | pass |
| C27 | `run unit / test_acceptance_doc_f4_has_all_clis ... ok` | pass |
| C28 | `run unit / test_compat_matrix_has_phase4 ... ok` | pass |
| C29 | `run unit / test_failed_cli_recorded_as_reprovado ... ok` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `claude plugin validate dist/claude --strict` | pass |
| Build | `python scripts/check_decisions.py` | pass |

## Output

`Run unit` - exit 0

```
test_each_invalid_fixture_fails_with_clear_message (test_validate_config.InvalidFixtures.test_each_invalid_fixture_fails_with_clear_message) ... ok
test_all_valid_fixtures_pass (test_validate_config.ValidFixtures.test_all_valid_fixtures_pass) ... ok
test_complete_feature_passes (test_validate_verification.ValidateVerificationTests.test_complete_feature_passes) ... ok
test_degraded_warns_and_strict_fails (test_validate_verification.ValidateVerificationTests.test_degraded_warns_and_strict_fails) ... ok
test_mode1_dirty_tree_only_with_degraded (test_validate_verification.ValidateVerificationTests.test_mode1_dirty_tree_only_with_degraded) ... ok
test_verification_fails_on_missing_or_stale_proofs (test_validate_verification.ValidateVerificationTests.test_verification_fails_on_missing_or_stale_proofs) ... ok
test_verification_fails_on_open_finding_or_missing_approval (test_validate_verification.ValidateVerificationTests.test_verification_fails_on_open_finding_or_missing_approval) ... ok
test_laforge_calls_mccoy_on_second_failure (test_worker_skills.WorkerSkillTests.test_laforge_calls_mccoy_on_second_failure) ... ok
test_laforge_skill_scope_tdd_commit (test_worker_skills.WorkerSkillTests.test_laforge_skill_scope_tdd_commit) ... ok
test_mccoy_skill_regression_and_report (test_worker_skills.WorkerSkillTests.test_mccoy_skill_regression_and_report) ... ok

----------------------------------------------------------------------
Ran 237 tests in 68.581s

OK
```
