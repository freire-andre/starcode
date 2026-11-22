# suite-e-execute proofs

**HEAD**: 6134418
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 13 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_fix_brief_usa_selecao_do_impact (test_suite_e_execute.SuiteEExecuteTests.test_fix_brief_usa_se` | pass |
| C2 | `run unit / test_brief_do_ticket_usa_selecao_do_impact (test_suite_e_execute.SuiteEExecuteTests.test_brief_do_t` | pass |
| C3 | `run unit / test_laforge_e_mccoy_rodam_a_selecao (test_suite_e_execute.SuiteEExecuteTests.test_laforge_e_mccoy_` | pass |
| C4 | `run unit / test_decisions_registra_a_medicao (test_suite_e_execute.SuiteEExecuteTests.test_decisions_registra_` | pass |
| C5 | `run unit / test_agents_tem_regra_de_estado (test_suite_e_execute.SuiteEExecuteTests.test_agents_tem_regra_de_e` | pass |
| C6 | `run unit / test_execute_md_vira_indice (test_suite_e_execute.SuiteEExecuteTests.test_execute_md_vira_indice) .` | pass |
| C7 | `run unit / test_cabecalhos_no_arquivo_certo (test_suite_e_execute.SuiteEExecuteTests.test_cabecalhos_no_arquiv` | pass |
| C8 | `run unit / test_execute_md_snapshot_antes_do_ticket (test_flow_f12.FlowF12Tests.test_execute_md_snapshot_antes` | pass |
| C9 | `run unit / test_referencias_apontam_o_arquivo_novo (test_suite_e_execute.SuiteEExecuteTests.test_referencias_a` | pass |
| C10 | `run unit / test_decisions_e_changelog (test_suite_e_execute.SuiteEExecuteTests.test_decisions_e_changelog) ...` | pass |
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
Ran 1100 tests in 667.832s

OK (skipped=1)
inativo
```
