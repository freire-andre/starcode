# cabecalho-robusto proofs

**HEAD**: c5b759e
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 14 pass, 1 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_crew_hook_skill_marks_member_and_shows_header ... ok` | pass |
| C2 | `run unit / test_crew_hook_header_plain_text ... ok` | pass |
| C3 | `run unit / test_crew_hook_post_tool_use_pulses ... ok` | pass |
| C4 | `run unit / test_crew_hook_stop_and_prompt_toggle ... ok` | pass |
| C5 | `run unit / test_crew_hook_session_end_clears ... ok` | pass |
| C6 | `run unit / test_crew_live_expiry_and_laforge_count ... ok` | pass |
| C7 | `run unit / test_crew_hook_never_breaks ... ok` | pass |
| C8 | `run unit / test_build_registers_crew_hook_only_in_claude ... ok` | pass |
| C9 | `run unit / test_build_header_rule_per_cli ... ok` | pass |
| C10 | `run unit / test_statusline_expiry_and_laforge_count ... ok` | pass |
| C11 | `run unit / test_banner_warns_outdated_plugin ... ok` | pass |
| C12 | `run unit / test_decisions_records_f7_12_crew_hook ... ok` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `claude plugin validate dist/claude --strict` | pass |
| Build | `python scripts/check_decisions.py` | fail - check_decisions: FALHOU. skills/, scripts/ ou hooks/ mudaram em fd18f19 fix(cabecalho-robusto): reje |

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
Ran 397 tests in 142.765s

OK
```
