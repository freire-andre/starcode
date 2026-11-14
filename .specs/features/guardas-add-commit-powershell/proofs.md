# guardas-add-commit-powershell proofs

**HEAD**: 3905c1e
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 13 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_add_antes_do_commit_escaneia_novo_e_modificado ... ok` | pass |
| C2 | `run unit / test_add_antes_do_commit_sem_segredo_passa ... ok` | pass |
| C3 | `run unit / test_add_update_ignora_nao_rastreados ... ok` | pass |
| C4 | `run unit / test_add_so_escaneia_caminhos_passados ... ok` | pass |
| C5 | `run unit / test_add_arquivo_novo_env_e_allowlist ... ok` | pass |
| C6 | `run unit / test_add_com_dash_c ... ok` | pass |
| C7 | `run unit / test_claude_hooks_cobrem_powershell ... ok` | pass |
| C8 | `run unit / test_git_guard_nega_push_force_pelo_powershell ... ok` | pass |
| C9 | `run unit / test_secret_scan_nega_commit_pelo_powershell ... ok` | pass |
| C10 | `run unit / test_decisions_guardas_add_commit_powershell ... ok` | pass |
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
Ran 894 tests in 392.202s

OK (skipped=1)
inativo
```
