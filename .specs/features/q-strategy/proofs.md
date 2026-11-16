# q-strategy proofs

**HEAD**: 664c22a
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 11 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_q_strategy_none_keeps_current_order (test_dispatch.FamilyAndQCliTests.test_q_strategy_none_kee` | pass |
| C2 | `run unit / test_q_strategy_orca_worker_walks_cli_order (test_dispatch.FamilyAndQCliTests.test_q_strategy_orca_` | pass |
| C3 | `run unit / test_q_strategy_self_verified_first_wins (test_dispatch.FamilyAndQCliTests.test_q_strategy_self_ver` | pass |
| C4 | `run unit / test_q_strategy_opencode_subagent_skipped_with_warning (test_dispatch.FamilyAndQCliTests.test_q_str` | pass |
| C5 | `run unit / test_q_strategy_nothing_available_is_self_verified (test_dispatch.FamilyAndQCliTests.test_q_strateg` | pass |
| C6 | `run unit / test_q_cli_command_reads_user_qstrategy (test_dispatch.FamilyAndQCliTests.test_q_cli_command_reads_` | pass |
| C7 | `run unit / test_q_strategy_docs_match_implementation (test_dispatch.FamilyAndQCliTests.test_q_strategy_docs_ma` | pass |
| C8 | `run unit / test_q_strategy_decisions_entry_and_changelog (test_dispatch.FamilyAndQCliTests.test_q_strategy_dec` | pass |
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
Ran 936 tests in 423.781s

OK (skipped=1)
inativo
```
