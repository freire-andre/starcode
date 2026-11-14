# q-familia-revendedor proofs

**HEAD**: 87990ef
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 12 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_revendedor_claude_vira_anthropic ... ok` | pass |
| C2 | `run unit / test_bedrock_prefixo_do_fornecedor ... ok` | pass |
| C3 | `run unit / test_revendedor_modelo_desconhecido_vira_unknown ... ok` | pass |
| C4 | `run unit / test_fornecedor_e_id_canonico_mantem_familia ... ok` | pass |
| C5 | `run unit / test_compare_revendedor_claude_e_same ... ok` | pass |
| C6 | `run unit / test_q_cli_recusa_revendedor_claude ... ok` | pass |
| C7 | `run unit / test_prefixos_de_modelo_por_revendedor ... ok` | pass |
| C8 | `run unit / test_sem_catalogo_revendedor_unknown ... ok` | pass |
| C9 | `run unit / test_decisions_q_familia_revendedor ... ok` | pass |
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
Ran 858 tests in 379.132s

OK (skipped=1)
inativo
```
