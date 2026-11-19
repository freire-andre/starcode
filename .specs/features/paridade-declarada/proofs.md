# paridade-declarada proofs

**HEAD**: 2a31040
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 5 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_readme_niveis (test_paridade_declarada.ParidadeDeclaradaTests.test_readme_niveis) ... ok` | pass |
| C2 | `run unit / test_matriz_niveis (test_paridade_declarada.ParidadeDeclaradaTests.test_matriz_niveis) ... ok` | pass |
| C3 | `run unit / test_decisions_paridade (test_paridade_declarada.ParidadeDeclaradaTests.test_decisions_paridade) ..` | pass |
| Build | `python tools/build.py --check` | pass |
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
Ran 1034 tests in 540.628s

OK (skipped=1)
inativo
```
