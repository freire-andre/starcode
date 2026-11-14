# piloto-decisao-citada proofs

**HEAD**: 514729d
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 12 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_gates_leem_piloto_pelo_piloto_py ... ok` | pass |
| C2 | `run unit / test_aprovacao_com_decisao_registrada_passa_nos_dois_gates ... ok` | pass |
| C3 | `run unit / test_decisao_inexistente_reprova_nos_dois_gates ... ok` | pass |
| C4 | `run unit / test_spec_recusa_piloto_com_decisao_registrada ... ok` | pass |
| C5 | `run unit / test_mandato_sem_user_nao_vale ... ok` | pass |
| C6 | `run unit / test_sem_piloto_md_reprova_sem_excecao ... ok` | pass |
| C7 | `run unit / test_d07_cita_d7 ... ok` | pass |
| C8 | `run unit / test_uma_linha_valida_basta ... ok` | pass |
| C9 | `run unit / test_decisions_piloto_decisao_citada ... ok` | pass |
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
Ran 844 tests in 360.325s

OK (skipped=1)
inativo
```
