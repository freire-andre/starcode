# versao-1-9-0 proofs

**HEAD**: 538a193
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 10 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_version_is_1_2_0_in_all_manifests (test_build.BuildTests.test_version_is_1_2_0_in_all_manifest` | pass |
| C2 | `run unit / test_versao_1_9_0_em_todos_os_manifestos (test_versao_1_9_0.Versao190Tests.test_versao_1_9_0_em_tod` | pass |
| C3 | `run unit / test_changelog_fecha_1_9_0 (test_versao_1_9_0.Versao190Tests.test_changelog_fecha_1_9_0) ... ok` | pass |
| C4 | `run unit / test_readme_estado_1_9_0 (test_versao_1_9_0.Versao190Tests.test_readme_estado_1_9_0) ... ok` | pass |
| C5 | `run unit / test_changelog_recent (test_versao_1_9_0.Versao190Tests.test_changelog_recent) ... ok` | pass |
| C5 | `run unit / test_nenhum_teste_le_unreleased_nem_busca_issue_fora_do_helper (test_versao_1_9_0.Versao190Tests.te` | pass |
| C5 | `run unit / test_varredura_pega_cada_forma (test_versao_1_9_0.Versao190Tests.test_varredura_pega_cada_forma) ..` | pass |
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
Ran 1107 tests in 757.718s

OK (skipped=1)
inativo
```
