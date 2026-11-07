# fase-7-frota proofs

**HEAD**: 972c59c
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 34 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_batch_skips_integrated_active_and_waiting_tickets ... ok` | pass |
| C2 | `run unit / test_batch_excludes_ticket_sharing_path_with_active ... ok` | pass |
| C3 | `run unit / test_batch_sensitive_ticket_runs_alone_only_when_idle ... ok` | pass |
| C4 | `run unit / test_batch_limit_counts_active_workers ... ok` | pass |
| C5 | `run unit / test_batch_json_contract ... ok` | pass |
| C6 | `run unit / test_batch_exit_codes ... ok` | pass |
| C7 | `run unit / test_batch_excludes_ticket_without_may_change ... ok` | pass |
| C8 | `run unit / test_fleet_workers_accepts_valid_pairs_and_rejects_invalid ... ok` | pass |
| C9 | `run unit / test_batch_round_robin_from_fleet_workers ... ok` | pass |
| C10 | `run unit / test_batch_assign_overrides_pair ... ok` | pass |
| C11 | `run unit / test_cost_tier_from_map_free_suffix_and_unknown ... ok` | pass |
| C12 | `run unit / test_batch_cost_total_counts_tiers ... ok` | pass |
| C13 | `run unit / test_execute_fleet_batch_confirmation ... ok` | pass |
| C14 | `run unit / test_dispatch_add_appends_and_replaces_same_ticket ... ok` | pass |
| C15 | `run unit / test_dispatch_remove_keeps_other_entries ... ok` | pass |
| C16 | `run unit / test_execute_fleet_worker_start_flags ... ok` | pass |
| C17 | `run unit / test_execute_fleet_start_failure_isolated ... ok` | pass |
| C18 | `run unit / test_set_laforge_count_up_to_ten ... ok` | pass |
| C19 | `run unit / test_next_open_dispatch_with_multiple_entries ... ok` | pass |
| C20 | `run unit / test_execute_fleet_wait_uses_nearest_deadline ... ok` | pass |
| C21 | `run unit / test_execute_fleet_integrates_on_arrival ... ok` | pass |
| C22 | `run unit / test_overdue_lists_tickets_past_deadline ... ok` | pass |
| C23 | `run unit / test_execute_fleet_timeout_blocks_without_relaunch ... ok` | pass |
| C24 | `run unit / test_execute_fleet_cancel_preserves_worktree ... ok` | pass |
| C25 | `run unit / test_execute_fleet_failure_returns_ticket_to_queue ... ok` | pass |
| C26 | `run unit / test_execute_fleet_merge_conflict_continues ... ok` | pass |
| C27 | `run unit / test_execute_fleet_next_batch_then_proofs ... ok` | pass |
| C28 | `run unit / test_execute_fleet_unavailable_in_mode_1 ... ok` | pass |
| C29 | `run unit / test_q_cli_differs_from_all_laforge_families ... ok` | pass |
| C30 | `run unit / test_fase7_acceptance_all_scenarios_approved ... ok` | pass |
| C31 | `run unit / test_decisions_and_changelog_record_fase_7 ... ok` | pass |
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
Ran 371 tests in 127.050s

OK
```
