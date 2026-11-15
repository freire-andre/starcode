# licoes-recorrencia-por-id proofs

**HEAD**: 15aaf96
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 10 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_lessons_add_id_registra_recorrencia_e_promove ... ok` | pass |
| C2 | `run unit / test_lessons_add_id_sem_caixa_e_text_ignorado ... ok` | pass |
| C3 | `run unit / test_lessons_add_id_invalido_ou_quarentena_sai_2 ... ok` | pass |
| C4 | `run unit / test_lessons_add_sem_id_exige_text ... ok` | pass |
| C5 | `run unit / test_guinan_lista_licoes_e_reusa_id ... ok` | pass |
| C6 | `run unit / test_licoes_reprocessadas_n1 ... ok` | pass |
| C7 | `run unit / test_decisions_licoes_recorrencia_por_id ... ok` | pass |
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
Ran 921 tests in 466.002s

OK (skipped=1)
inativo
```
