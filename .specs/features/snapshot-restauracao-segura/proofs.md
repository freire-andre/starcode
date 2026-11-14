# snapshot-restauracao-segura proofs

**HEAD**: a2d9d3e
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 15 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_take_mantem_snapshot_existente ... ok` | pass |
| C2 | `run unit / test_restore_dry_run_grava_plano ... ok` | pass |
| C3 | `run unit / test_restore_recusa_snapshot_ausente_fora_do_ticket ... ok` | pass |
| C4 | `run unit / test_restore_edicao_fora_do_ticket_nao_recusa ... ok` | pass |
| C5 | `run unit / test_restore_yes_sem_plano_recusa ... ok` | pass |
| C6 | `run unit / test_restore_yes_plano_mudou_recusa ... ok` | pass |
| C7 | `run unit / test_restore_grava_pre_restore_e_apaga_plano ... ok` | pass |
| C8 | `run unit / test_restore_pre_restore_falha_nao_toca_arquivos ... ok` | pass |
| C9 | `run unit / test_restore_falha_parcial_e_retomada ... ok` | pass |
| C10 | `run unit / test_cenario_aceite_disjuntor_modo_1 ... ok` | pass |
| C11 | `run unit / test_drop_remove_pre_restore_e_planos_da_feature ... ok` | pass |
| C12 | `run unit / test_decisions_snapshot_restauracao_segura ... ok` | pass |
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
Ran 872 tests in 374.500s

OK (skipped=1)
inativo
```
