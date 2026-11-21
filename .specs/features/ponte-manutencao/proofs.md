# ponte-manutencao proofs

**HEAD**: 48c7320
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 13 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_parse_dispatch_entry (test_ponte_manutencao.PonteManutencaoTests.test_parse_dispatch_entry) ..` | pass |
| C2 | `run unit / test_ponte_modelo_do_start (test_ponte_manutencao.PonteManutencaoTests.test_ponte_modelo_do_start) ` | pass |
| C2 | `run unit / test_dispatch_usa_leitor_unico (test_ponte_manutencao.PonteManutencaoTests.test_dispatch_usa_leitor` | pass |
| C3 | `run unit / test_manifesto_sem_storage (test_ponte_manutencao.PonteManutencaoTests.test_manifesto_sem_storage) ` | pass |
| C4 | `run plugin / ✔ issue.url fora do linear vira null` | pass |
| C5 | `run plugin / ✔ agentFor casa por token inteiro` | pass |
| C6 | `run plugin / ✔ nome do worktree com barra invertida` | pass |
| C7 | `run unit / test_ci_pulo_visivel (test_ponte_manutencao.PonteManutencaoTests.test_ci_pulo_visivel) ... ok` | pass |
| C8 | `run unit / test_decisions_e_changelog (test_ponte_manutencao.PonteManutencaoTests.test_decisions_e_changelog) ` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `claude plugin validate dist/claude --strict` | pass |
| Build | `python scripts/check_decisions.py` | pass |
| Build | `orca plugin validate src/orca --json` | pass |

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
Ran 1052 tests in 612.865s

OK (skipped=1)
inativo
```

`Run plugin` - exit 0

```
✔ url da issue montada só pelo urlKey do worktree quando a consulta falha (15.696ms)
✔ barra de status indica missão em outro worktree (8.2329ms)
✔ atalho foca o worktree da missão ativa (16.3059ms)
✔ host recusa agent.launch sem a capacidade (4.5707ms)
✔ issue.url fora do linear vira null (49.5644ms)
✔ nome do worktree com barra invertida (32.1473ms)
ℹ tests 74
ℹ suites 0
ℹ pass 74
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2285.0214
4 test file(s) passed (node).
```
