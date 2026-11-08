# hooks-agy-opencode-tripulacao proofs

**HEAD**: a34dbf3
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 13 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_crew_hook_agy_skill_read_marks_pending ... ok` | pass |
| C2 | `run unit / test_crew_hook_agy_never_decides ... ok` | pass |
| C3 | `run unit / test_crew_hook_agy_post_invocation_injects_header ... ok` | pass |
| C4 | `run unit / test_crew_hook_agy_lifecycle ... ok` | pass |
| C5 | `run unit / test_crew_hook_opencode_events ... ok` | pass |
| C6 | `run unit / test_opencode_plugin_registers_crew_hooks ... ok` | pass |
| C7 | `run unit / test_build_registers_crew_hook_in_antigravity ... ok` | pass |
| C8 | `run unit / test_build_header_rule_agy_opencode ... ok` | pass |
| C9 | `run unit / test_crew_hook_agy_opencode_never_break ... ok` | pass |
| C10 | `run unit / test_decisions_records_f7_16_agy_opencode_hooks ... ok` | pass |
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
Ran 422 tests in 156.409s

OK
```
