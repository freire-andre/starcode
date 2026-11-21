# falhas-start-settle proofs

**HEAD**: 949f18c
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 14 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_recibo_com_texto_antes (test_falhas_start_settle.FalhasStartSettleTests.test_recibo_com_texto_` | pass |
| C2 | `run unit / test_start_sem_id_sai_com_3 (test_falhas_start_settle.FalhasStartSettleTests.test_start_sem_id_sai_` | pass |
| C3 | `run unit / test_merge_falha_sem_conflito (test_falhas_start_settle.FalhasStartSettleTests.test_merge_falha_sem` | pass |
| C3 | `run unit / test_merge_combinacoes (test_falhas_start_settle.FalhasStartSettleTests.test_merge_combinacoes) ...` | pass |
| C4 | `run unit / test_handoff_concorrente (test_falhas_start_settle.FalhasStartSettleTests.test_handoff_concorrente)` | pass |
| C5 | `run unit / test_run_git (test_falhas_start_settle.FalhasStartSettleTests.test_run_git) ... ok` | pass |
| C5 | `run unit / test_run_git_argumentos_invalidos (test_falhas_start_settle.FalhasStartSettleTests.test_run_git_arg` | pass |
| C6 | `run unit / test_scripts_usam_run_git (test_falhas_start_settle.FalhasStartSettleTests.test_scripts_usam_run_gi` | pass |
| C6 | `run unit / test_regressao_diff_head_com_erro (test_falhas_start_settle.FalhasStartSettleTests.test_regressao_d` | pass |
| C6 | `run unit / test_timeout_chega_aos_chamadores (test_falhas_start_settle.FalhasStartSettleTests.test_timeout_che` | pass |
| C7 | `run unit / test_decisions_e_changelog (test_falhas_start_settle.FalhasStartSettleTests.test_decisions_e_change` | pass |
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
Ran 1064 tests in 656.917s

OK (skipped=1)
inativo
```
