# versao-e-retro proofs

**HEAD**: 45365c9
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 11 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_brief_traz_versao_do_plugin (test_versao_e_retro.VersaoERetroTests.test_brief_traz_versao_do_p` | pass |
| C2 | `run unit / test_start_grava_plugin_no_handoff (test_versao_e_retro.VersaoERetroTests.test_start_grava_plugin_n` | pass |
| C3 | `run unit / test_aviso_de_versao_diferente (test_versao_e_retro.VersaoERetroTests.test_aviso_de_versao_diferent` | pass |
| C3 | `run unit / test_aviso_nao_altera_start_bem_sucedido (test_versao_e_retro.VersaoERetroTests.test_aviso_nao_alte` | pass |
| C4 | `run unit / test_retro_da_guinan_tem_estado (test_versao_e_retro.VersaoERetroTests.test_retro_da_guinan_tem_est` | pass |
| C5 | `run unit / test_retros_abertas (test_versao_e_retro.VersaoERetroTests.test_retros_abertas) ... ok` | pass |
| C6 | `run unit / test_retros_estado (test_versao_e_retro.VersaoERetroTests.test_retros_estado) ... ok` | pass |
| C7 | `run unit / test_decisions_e_changelog (test_versao_e_retro.VersaoERetroTests.test_decisions_e_changelog) ... o` | pass |
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
Ran 1091 tests in 698.500s

OK (skipped=1)
inativo
```
