# licoes-no-brief proofs

**HEAD**: f4842ab
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 8 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_ordem_por_recorrencia (test_licoes_no_brief.LicoesNoBriefTests.test_ordem_por_recorrencia) ...` | pass |
| C2 | `run unit / test_licoes_antes_das_regras (test_licoes_no_brief.LicoesNoBriefTests.test_licoes_antes_das_regras)` | pass |
| C3 | `run unit / test_fix_brief (test_licoes_no_brief.LicoesNoBriefTests.test_fix_brief) ... ok` | pass |
| C3 | `run unit / test_fix_brief_uniao_tickets (test_licoes_no_brief.LicoesNoBriefTests.test_fix_brief_uniao_tickets)` | pass |
| C4 | `run unit / test_execute_e_decisions (test_licoes_no_brief.LicoesNoBriefTests.test_execute_e_decisions) ... ok` | pass |
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
Ran 1039 tests in 537.221s

OK (skipped=1)
inativo
```
