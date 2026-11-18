# scanner-lote2 proofs

**HEAD**: 30aa45c
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 11 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_heredoc_de_comando_que_publica_e_escaneado (test_secret_scan.TextTargetsTests.test_heredoc_de_` | pass |
| C2 | `run unit / test_gh_issue_e_pr_review_sao_escaneados (test_secret_scan.TextTargetsTests.test_gh_issue_e_pr_revi` | pass |
| C3 | `run unit / test_conexao_placeholder_e_local_passam (test_secret_scan.ScanTextTests.test_conexao_placeholder_e_` | pass |
| C4 | `run unit / test_auth_so_como_parte_inteira (test_secret_scan.ScanTextTests.test_auth_so_como_parte_inteira) ..` | pass |
| C5 | `run unit / test_url_sem_credencial_passa (test_secret_scan.ScanTextTests.test_url_sem_credencial_passa) ... ok` | pass |
| C6 | `run unit / test_lookalikes_pass (test_secret_scan.ScanTextTests.test_lookalikes_pass) ... ok` | pass |
| C6 | `run unit / test_each_fake_secret_is_found (test_secret_scan.ScanTextTests.test_each_fake_secret_is_found) ... ` | pass |
| C7 | `run unit / test_decisions_scanner_lote2 (test_secret_scan.ScanTextTests.test_decisions_scanner_lote2) ... ok` | pass |
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
Ran 972 tests in 484.339s

OK (skipped=1)
inativo
```
