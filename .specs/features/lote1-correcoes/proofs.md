# lote1-correcoes proofs

**HEAD**: a5931d3
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 10 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_nenhuma_skill_do_dist_tem_header_first (test_build.BuildTests.test_nenhuma_skill_do_dist_tem_h` | pass |
| C2 | `run unit / test_sees_palavra_inteira (test_check_proofs.CheckProofsTests.test_sees_palavra_inteira) ... ok` | pass |
| C3 | `run unit / test_sees_docstring_do_unittest (test_check_proofs.CheckProofsTests.test_sees_docstring_do_unittest` | pass |
| C4 | `run unit / test_prova_com_tempo_limite (test_check_proofs.CheckProofsTests.test_prova_com_tempo_limite) ... ok` | pass |
| C5 | `run unit / test_frase_binary_files_em_texto_e_escaneada (test_secret_scan.CommitTests.test_frase_binary_files_` | pass |
| C6 | `run unit / test_arquivo_pulado_avisa (test_secret_scan.CommitTests.test_arquivo_pulado_avisa) ... ok` | pass |
| C7 | `run unit / test_decisions_lote1_correcoes (test_build.BuildTests.test_decisions_lote1_correcoes) ... ok` | pass |
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
Ran 956 tests in 463.481s

OK (skipped=1)
inativo
```
