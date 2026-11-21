# catalogo-e-orca proofs

**HEAD**: 7ca9a3c
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 11 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_download_confere_forma (test_catalogo_e_orca.CatalogoEOrcaTests.test_download_confere_forma) .` | pass |
| C2 | `run unit / test_texto_do_catalogo_limpo (test_catalogo_e_orca.CatalogoEOrcaTests.test_texto_do_catalogo_limpo)` | pass |
| C3 | `run unit / test_catalogo_lido_uma_vez (test_catalogo_e_orca.CatalogoEOrcaTests.test_catalogo_lido_uma_vez) ...` | pass |
| C4 | `run unit / test_orca_cli_run_e_env (test_catalogo_e_orca.CatalogoEOrcaTests.test_orca_cli_run_e_env) ... ok` | pass |
| C4 | `run unit / test_saida_127_124_126_do_orca (test_catalogo_e_orca.CatalogoEOrcaTests.test_saida_127_124_126_do_o` | pass |
| C5 | `run unit / test_um_adaptador_da_orca (test_catalogo_e_orca.CatalogoEOrcaTests.test_um_adaptador_da_orca) ... o` | pass |
| C6 | `run unit / test_stack_orca_documentada (test_catalogo_e_orca.CatalogoEOrcaTests.test_stack_orca_documentada) .` | pass |
| C7 | `run unit / test_decisions_e_changelog (test_catalogo_e_orca.CatalogoEOrcaTests.test_decisions_e_changelog) ...` | pass |
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
Ran 1083 tests in 650.510s

OK (skipped=1)
inativo
```
