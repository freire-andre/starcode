# roteamento-worf-mccoy proofs

**HEAD**: c3e9e2f
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 9 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_descricao_worf (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_descricao_worf) ... o` | pass |
| C2 | `run unit / test_descricao_mccoy (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_descricao_mccoy) ...` | pass |
| C3 | `run unit / test_casos_novos (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_casos_novos) ... ok` | pass |
| C4 | `run unit / test_readme_e_contagem (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_readme_e_contagem)` | pass |
| C5 | `run unit / test_decisions_roteamento (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_decisions_rotea` | pass |
| C6 | `run unit / test_descricao_piloto (test_roteamento_worf_mccoy.RoteamentoWorfMccoyTests.test_descricao_piloto) .` | pass |
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
Ran 1031 tests in 539.903s

OK (skipped=1)
inativo
```
