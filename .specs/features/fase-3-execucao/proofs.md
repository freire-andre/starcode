# fase-3-execucao proofs

**HEAD**: 5d85ab1
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 35 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_check_proofs_writes_proofs_md ... ok` | pass |
| C2 | `run unit / test_run_proof_needs_words_in_order_on_one_line ... ok` | pass |
| C3 | `run unit / test_dirty_tree_marks_mode1_and_fails ... ok` | pass |
| C4 | `run unit / test_verification_fails_on_missing_or_stale_proofs ... ok` | pass |
| C5 | `run unit / test_verification_fails_on_open_finding_or_missing_approval ... ok` | pass |
| C6 | `run unit / test_degraded_warns_and_strict_fails ... ok` | pass |
| C7 | `run unit / test_check_scope_flags_outside_may_change ... ok` | pass |
| C8 | `run unit / test_check_scope_flags_state_and_handoff ... ok` | pass |
| C9 | `run unit / test_run_gates_execution_stages ... ok` | pass |
| C10 | `run unit / test_handoff_execution_fields ... ok` | pass |
| C11 | `run unit / test_attempts_count_and_reset ... ok` | pass |
| C12 | `run unit / test_third_failure_opens_breaker ... ok` | pass |
| C13 | `run unit / test_banner_shows_open_breaker ... ok` | pass |
| C14 | `run unit / test_banner_shows_degraded_verification ... ok` | pass |
| C15 | `run unit / test_q_brief_contract ... ok` | pass |
| C16 | `run unit / test_q_skill_records_model_and_head ... ok` | pass |
| C17 | `run unit / test_laforge_skill_scope_tdd_commit ... ok` | pass |
| C18 | `run unit / test_laforge_calls_mccoy_on_second_failure ... ok` | pass |
| C19 | `run unit / test_mccoy_skill_regression_and_report ... ok` | pass |
| C20 | `run unit / test_next_ticket_respects_dependencies ... ok` | pass |
| C21 | `run unit / test_ticket_brief_has_block_and_worker_rules ... ok` | pass |
| C22 | `run unit / test_q_brief_fills_placeholders ... ok` | pass |
| C23 | `run unit / test_family_compare ... ok` | pass |
| C24 | `run unit / test_execute_ref_dispatch_steps ... ok` | pass |
| C25 | `run unit / test_execute_ref_integration_and_resume ... ok` | pass |
| C26 | `run unit / test_execute_ref_q_dispatch ... ok` | pass |
| C27 | `run unit / test_execute_ref_post_q_cycle ... ok` | pass |
| C28 | `run unit / test_execute_ref_linear_states ... ok` | pass |
| C29 | `run unit / test_execute_ref_mode1_and_no_stop ... ok` | pass |
| C30 | `run unit / test_build_emits_execution_skills ... ok` | pass |
| C31 | `run unit / test_routing_and_decisions_cover_phase3 ... ok` | pass |
| C32 | `run unit / test_acceptance_doc_has_all_scripts ... ok` | pass |
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
Ran 173 tests in 50.760s

OK
```
