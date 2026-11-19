# pr-review proofs

**HEAD**: ca5b699
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 10 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_fase_pr_review (test_pr_review.PrReviewTests.test_fase_pr_review) ... ok` | pass |
| C2 | `run unit / test_execute_fase_pr_review (test_pr_review.PrReviewTests.test_execute_fase_pr_review) ... ok` | pass |
| C3 | `run unit / test_execute_gates_apos_correcao_worf (test_pr_review.PrReviewTests.test_execute_gates_apos_correca` | pass |
| C4 | `run unit / test_guinan_licoes_do_review (test_pr_review.PrReviewTests.test_guinan_licoes_do_review) ... ok` | pass |
| C5 | `run unit / test_piloto_encerra_apos_worf (test_pr_review.PrReviewTests.test_piloto_encerra_apos_worf) ... ok` | pass |
| C6 | `run unit / test_state_format_pr_review (test_pr_review.PrReviewTests.test_state_format_pr_review) ... ok` | pass |
| C7 | `run unit / test_decisions_pr_review (test_pr_review.PrReviewTests.test_decisions_pr_review) ... ok` | pass |
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
Ran 996 tests in 502.044s

OK (skipped=1)
inativo
```
