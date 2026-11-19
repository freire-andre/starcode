# pequena-minima proofs

**HEAD**: d7dc186
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 12 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_spec_small_minima (test_pequena_minima.PequenaTests.test_spec_small_minima) ... ok` | pass |
| C2 | `run unit / test_spec_small_limite (test_pequena_minima.PequenaTests.test_spec_small_limite) ... ok` | pass |
| C3 | `run unit / test_small_sem_aprovacao (test_pequena_minima.PequenaTests.test_small_sem_aprovacao) ... ok` | pass |
| C4 | `run unit / test_dispatch_small_t1 (test_pequena_minima.PequenaTests.test_dispatch_small_t1) ... ok` | pass |
| C4 | `run unit / test_settle_small_roda_gate_ticket (test_pequena_minima.PequenaTests.test_settle_small_roda_gate_ti` | pass |
| C5 | `run unit / test_q_waive (test_pequena_minima.PequenaTests.test_q_waive) ... ok` | pass |
| C6 | `run unit / test_done_waived (test_pequena_minima.PequenaTests.test_done_waived) ... ok` | pass |
| C7 | `run unit / test_textos_fluxo_pequena (test_pequena_minima.PequenaTests.test_textos_fluxo_pequena) ... ok` | pass |
| C8 | `run unit / test_decisions_pequena_minima (test_pequena_minima.PequenaTests.test_decisions_pequena_minima) ... ` | pass |
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
Ran 989 tests in 495.928s

OK (skipped=1)
inativo
```
