# retro-fase9 proofs

**HEAD**: 65952cc
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 9 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_require_text_tabela (test_review_gate.ReviewGateTests.test_require_text_tabela) ... ok` | pass |
| C2 | `run unit / test_help_sai_com_zero (test_review_gate.ReviewGateTests.test_help_sai_com_zero) ... ok` | pass |
| C3 | `run unit / test_uso_e_codigos_mantidos (test_review_gate.ReviewGateTests.test_uso_e_codigos_mantidos) ... ok` | pass |
| C4 | `run unit / test_scripts_de_review_respondem_help (test_review_gate.ReviewGateTests.test_scripts_de_review_resp` | pass |
| C5 | `run unit / test_retro_fase9_estado (test_review_gate.ReviewGateTests.test_retro_fase9_estado) ... ok` | pass |
| C6 | `run unit / test_decisions_retro_fase9 (test_review_gate.ReviewGateTests.test_decisions_retro_fase9) ... ok` | pass |
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
Ran 966 tests in 476.371s

OK (skipped=1)
inativo
```
