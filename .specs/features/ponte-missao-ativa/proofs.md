# ponte-missao-ativa proofs

**HEAD**: 61fec64
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 12 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_elsewhere_picks_newest_active_worktree ... ok` | pass |
| C2 | `run unit / test_elsewhere_null_when_local_active ... ok` | pass |
| C3 | `run unit / test_elsewhere_worktree_errors_do_not_break_snapshot ... ok` | pass |
| C4 | `run unit / test_elsewhere_snapshot_is_read_only ... ok` | pass |
| C5 | `run plugin / ✔ painel mostra a missão ativa de outro worktree` | pass |
| C6 | `run plugin / ✔ barra de status indica missão em outro worktree` | pass |
| C7 | `run plugin / ✔ atalho foca o worktree da missão ativa` | pass |
| C8 | `run unit / test_decisions_records_p151_2_elsewhere ... ok` | pass |
| Build | `orca plugin validate src/orca --json` | pass |
| Build | `orca plugin check src/orca --json` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `python scripts/check_decisions.py` | pass |

## Output

`Run unit` - exit 0

```
test_telas_sem_screens_md (test_validate_verification_screens.ScreensTests.test_telas_sem_screens_md) ... ok
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
Ran 669 tests in 262.008s

OK
```

`Run plugin` - exit 0

```
✔ orca.log lista quais variáveis de base estão definidas, sem valores (5.3331ms)
✔ env do CLI ganha as pastas do usuário quando faltam, sem sobrescrever (17.3512ms)
✔ worktree sem vínculo consulta a issue do snapshot (7.818ms)
✔ url da issue montada só pelo urlKey do worktree quando a consulta falha (15.8323ms)
✔ barra de status indica missão em outro worktree (7.5065ms)
✔ atalho foca o worktree da missão ativa (15.5647ms)
ℹ tests 69
ℹ suites 0
ℹ pass 69
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2128.7826
4 test file(s) passed (node).
```
