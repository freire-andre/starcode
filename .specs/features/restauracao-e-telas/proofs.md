# restauracao-e-telas proofs

**HEAD**: bd69d78
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 9 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_restore_le_escopo_do_snapshot (test_restauracao_e_telas.RestauracaoETelasTests.test_restore_le` | pass |
| C2 | `run unit / test_capture_so_host_local (test_restauracao_e_telas.RestauracaoETelasTests.test_capture_so_host_lo` | pass |
| C3 | `run unit / test_capture_out_restrito (test_restauracao_e_telas.RestauracaoETelasTests.test_capture_out_restrit` | pass |
| C4 | `run unit / test_veredito_nome_inteiro (test_restauracao_e_telas.RestauracaoETelasTests.test_veredito_nome_inte` | pass |
| C5 | `run unit / test_png_sem_idat (test_restauracao_e_telas.RestauracaoETelasTests.test_png_sem_idat) ... ok` | pass |
| C6 | `run unit / test_decisions_e_changelog (test_restauracao_e_telas.RestauracaoETelasTests.test_decisions_e_change` | pass |
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
Ran 1074 tests in 610.555s

OK (skipped=1)
inativo
```
