# ajustes-review-pr39 proofs

**HEAD**: 30f6d31
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 10 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_covers_pasta_igualdade_e_glob ... ok` | pass |
| C2 | `run unit / test_gates_usam_a_mesma_regra ... ok` | pass |
| C3 | `run unit / test_citacao_coberta_por_glob ... ok` | pass |
| C4 | `run unit / test_travessia_nao_coberta_por_glob ... ok` | pass |
| C5 | `run unit / test_nome_sem_pasta_continua_coberto ... ok` | pass |
| C6 | `run unit / test_start_segunda_gravacao_falha_sai_3 ... ok` | pass |
| C7 | `run unit / test_start_exit_3_avisa_e_liga_worktree ... ok` | pass |
| C8 | `run unit / test_execute_descreve_exit_3 ... ok` | pass |
| Build | `python tools/build.py --check` | pass |
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
Ran 767 tests in 332.454s

OK (skipped=1)
```
