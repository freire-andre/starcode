# piloto-freios proofs

**HEAD**: b6cc208
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 14 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_aprovacao_vale_depois_de_encerrar (test_piloto.PilotFreiosTests.test_aprovacao_vale_depois_de_` | pass |
| C2 | `run unit / test_decisao_depois_do_encerramento_reprova (test_piloto.PilotFreiosTests.test_decisao_depois_do_en` | pass |
| C3 | `run unit / test_mandato_sem_user_reprova_ativo_e_encerrado (test_piloto.PilotFreiosTests.test_mandato_sem_user` | pass |
| C4 | `run unit / test_freio_na_terceira_revisar (test_piloto.PilotFreiosTests.test_freio_na_terceira_revisar) ... ok` | pass |
| C5 | `run unit / test_segunda_revisar_segue (test_piloto.PilotFreiosTests.test_segunda_revisar_segue) ... ok` | pass |
| C6 | `run unit / test_freio_fica_e_alta_segue (test_piloto.PilotFreiosTests.test_freio_fica_e_alta_segue) ... ok` | pass |
| C7 | `run unit / test_devolvido_ao_usuario_fora_do_freio (test_piloto.PilotFreiosTests.test_devolvido_ao_usuario_for` | pass |
| C8 | `run unit / test_categoria_exige_mandato (test_piloto.PilotFreiosTests.test_categoria_exige_mandato) ... ok` | pass |
| C9 | `run unit / test_categoria_invalida_sai_2 (test_piloto.PilotFreiosTests.test_categoria_invalida_sai_2) ... ok` | pass |
| C10 | `run unit / test_skill_descreve_freio_e_categoria (test_piloto.PilotFreiosTests.test_skill_descreve_freio_e_cat` | pass |
| C11 | `run unit / test_decisions_piloto_freios (test_piloto.PilotFreiosTests.test_decisions_piloto_freios) ... ok` | pass |
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
Ran 949 tests in 440.532s

OK (skipped=1)
inativo
```
