# impacto-seleciona-real proofs

**HEAD**: 91ac2c7
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 11 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_intervalo_de_feature_ignora_specs ... ok` | pass |
| C2 | `run unit / test_so_specs_roda_tudo ... ok` | pass |
| C3 | `run unit / test_identifica_testes_python_e_ts ... ok` | pass |
| C4 | `run unit / test_apoio_propaga_mas_nao_e_teste ... ok` | pass |
| C5 | `run unit / test_referencia_textual_seleciona_teste ... ok` | pass |
| C6 | `run unit / test_mudado_sem_teste_roda_tudo_mesmo_com_outros ... ok` | pass |
| C7 | `run unit / test_impact_no_repo_starcode ... ok` | pass |
| C8 | `run unit / test_decisions_impacto_seleciona_real ... ok` | pass |
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
Ran 883 tests in 439.661s

OK (skipped=1)
inativo
```
