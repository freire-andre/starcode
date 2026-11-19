# guard-lote2 proofs

**HEAD**: 9ea9cd8
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 11 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_checkout_e_switch_forcados (test_git_guard.NoModeTests.test_checkout_e_switch_forcados) ... ok` | pass |
| C2 | `run unit / test_stash_drop_e_clear (test_git_guard.NoModeTests.test_stash_drop_e_clear) ... ok` | pass |
| C3 | `run unit / test_shell_com_flags_combinadas (test_git_guard.NoModeTests.test_shell_com_flags_combinadas) ... ok` | pass |
| C4 | `run unit / test_modo_1_comandos_que_criam_commit (test_git_guard.ModeTests.test_modo_1_comandos_que_criam_comm` | pass |
| C5 | `run unit / test_heredoc_de_dado_passa (test_git_guard.NoModeTests.test_heredoc_de_dado_passa) ... ok` | pass |
| C6 | `run unit / test_heredoc_para_shell_bloqueia (test_git_guard.NoModeTests.test_heredoc_para_shell_bloqueia) ... ` | pass |
| C7 | `run unit / test_tokenize_inalterado (test_git_guard.TokenizeTests.test_tokenize_inalterado) ... ok` | pass |
| C8 | `run unit / test_decisions_guard_lote2 (test_git_guard.NoModeTests.test_decisions_guard_lote2) ... ok` | pass |
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
Ran 980 tests in 476.831s

OK (skipped=1)
inativo
```
