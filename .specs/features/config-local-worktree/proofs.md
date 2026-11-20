# config-local-worktree proofs

**HEAD**: 7a64808
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 9 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_local_no_worktree_ligado (test_config_local_worktree.ConfigLocalWorktreeTests.test_local_no_wo` | pass |
| C2 | `run unit / test_entrada_local_inteira (test_config_local_worktree.ConfigLocalWorktreeTests.test_entrada_local_` | pass |
| C3 | `run unit / test_modelo_valido (test_config_local_worktree.ConfigLocalWorktreeTests.test_modelo_valido) ... ok` | pass |
| C4 | `run unit / test_aviso_local_versionado (test_config_local_worktree.ConfigLocalWorktreeTests.test_aviso_local_v` | pass |
| C5 | `run unit / test_suggest_mantem_configurado (test_config_local_worktree.ConfigLocalWorktreeTests.test_suggest_m` | pass |
| C6 | `run unit / test_skill_e_decisions (test_config_local_worktree.ConfigLocalWorktreeTests.test_skill_e_decisions)` | pass |
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
Ran 1045 tests in 582.204s

OK (skipped=1)
inativo
```
