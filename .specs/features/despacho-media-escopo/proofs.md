# despacho-media-escopo proofs

**HEAD**: bf95d77
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 16 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_regra_decisions_compartilhada ... ok` | pass |
| C2 | `run unit / test_scope_aceita_decisions_com_scripts ... ok` | pass |
| C3 | `run unit / test_scope_media_aceita_decisions ... ok` | pass |
| C4 | `run unit / test_brief_media_acrescenta_decisions ... ok` | pass |
| C5 | `run unit / test_start_media_despacha_t1 ... ok` | pass |
| C6 | `run unit / test_start_media_sem_linear_recusa ... ok` | pass |
| C7 | `run unit / test_media_ticket_errado_recusa ... ok` | pass |
| C8 | `run unit / test_settle_media_integra_t1 ... ok` | pass |
| C9 | `run unit / test_main_arquivo_ausente_sai_2 ... ok` | pass |
| C10 | `run unit / test_start_sem_ramo_aponta_modo_1 ... ok` | pass |
| C11 | `run unit / test_start_entrada_aberta_aponta_dispatch_remove ... ok` | pass |
| C12 | `run unit / test_execute_media_retry_e_modo_1 ... ok` | pass |
| C13 | `run unit / test_decisions_despacho_media ... ok` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `claude plugin validate dist/claude --strict` | pass |
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
Ran 834 tests in 365.636s

OK (skipped=1)
```
