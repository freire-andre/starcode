# fecha-achado proofs

**HEAD**: 61d7980
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 10 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_close_finding_grava (test_fecha_achado.FechaAchadoTests.test_close_finding_grava) ... ok` | pass |
| C2 | `run unit / test_close_finding_recusa (test_fecha_achado.FechaAchadoTests.test_close_finding_recusa) ... ok` | pass |
| C3 | `run unit / test_close_finding_preserva_bytes (test_fecha_achado.FechaAchadoTests.test_close_finding_preserva_b` | pass |
| C4 | `run unit / test_done_exige_cobertura (test_fecha_achado.FechaAchadoTests.test_done_exige_cobertura) ... ok` | pass |
| C5 | `run unit / test_done_acusa_celulas (test_fecha_achado.FechaAchadoTests.test_done_acusa_celulas) ... ok` | pass |
| C6 | `run unit / test_textos_close_finding (test_fecha_achado.FechaAchadoTests.test_textos_close_finding) ... ok` | pass |
| C7 | `run unit / test_decisions_fecha_achado (test_fecha_achado.FechaAchadoTests.test_decisions_fecha_achado) ... ok` | pass |
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
Ran 1003 tests in 486.941s

OK (skipped=1)
inativo
```
