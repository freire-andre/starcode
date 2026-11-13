# gate-d30-ci proofs

**HEAD**: 8e1547f
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 14 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_ci_checkout_historico_completo ... ok` | pass |
| C2 | `run unit / test_clone_raso_sai_2 ... ok` | pass |
| C3 | `run unit / test_raso_indeterminado_sai_2 ... ok` | pass |
| C4 | `run unit / test_flow ... ok` | pass |
| C5 | `run unit / test_decisions_v18_1_piloto ... ok` | pass |
| C6 | `run unit / test_decisions_v18_2_aprovacao_piloto ... ok` | pass |
| C7 | `run unit / test_decisions_v18_3_config_model_info ... ok` | pass |
| C8 | `run unit / test_decisions_v18_4_config_local ... ok` | pass |
| C9 | `run unit / test_decisions_v18_5_menu ... ok` | pass |
| C10 | `run unit / test_decisions_gate_raso ... ok` | pass |
| C11 | `python scripts/check_decisions.py` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `claude plugin validate dist/claude --strict` | pass |
| Build | `python scripts/check_decisions.py` | pass |

## Output

`Run unit` - exit 0

```
test_telas_sem_screens_md (test_validate_verification_screens.ScreensTests.test_telas_sem_screens_md) ... ok
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
Ran 820 tests in 902.698s

OK (skipped=1)
```

`python scripts/check_decisions.py` - exit 0

```
check_decisions: OK (DECISIONS.md atualizado no mesmo commit 7d7fd99c)
```
