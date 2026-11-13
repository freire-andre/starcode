# manutencao-retros-f11 proofs

**HEAD**: b4be0a9
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 38 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_report_com_data_iso_nao_prefixa ... ok` | pass |
| C2 | `run unit / test_report_sem_data_prefixa_hoje ... ok` | pass |
| C3 | `run unit / test_proofs_md_gravado_sem_cr ... ok` | pass |
| C4 | `run unit / test_brief_acrescenta_decisions_com_scripts ... ok` | pass |
| C5 | `run unit / test_brief_sem_scripts_ou_com_decisions_nao_muda ... ok` | pass |
| C6 | `run unit / test_batch_separa_tickets_de_scripts ... ok` | pass |
| C7 | `run unit / test_brief_traz_regra_de_assinatura ... ok` | pass |
| C8 | `run unit / test_task_cita_arquivo_fora_do_may_change_falha ... ok` | pass |
| C9 | `run unit / test_citacao_coberta_por_pasta_ou_nome ... ok` | pass |
| C10 | `run unit / test_versao_e_atributo_nao_contam ... ok` | pass |
| C11 | `run unit / test_start_ordem_dos_passos ... ok` | pass |
| C12 | `run unit / test_start_regrava_entrada_com_dispatch_e_modelo ... ok` | pass |
| C13 | `run unit / test_start_opencode_cria_worktree_antes ... ok` | pass |
| C14 | `run unit / test_start_recusa_sem_gravar ... ok` | pass |
| C15 | `run unit / test_start_worker_falha_remove_entrada ... ok` | pass |
| C16 | `run unit / test_start_linear_falha_vira_aviso ... ok` | pass |
| C17 | `run unit / test_start_json ... ok` | pass |
| C18 | `run unit / test_start_paralelo_preserva_outra_entrada ... ok` | pass |
| C19 | `run unit / test_settle_roda_gate_antes_do_merge ... ok` | pass |
| C20 | `run unit / test_settle_verde_integra_e_remove_entrada ... ok` | pass |
| C21 | `run unit / test_settle_gate_vermelho_nao_integra ... ok` | pass |
| C22 | `run unit / test_settle_conflito_aborta ... ok` | pass |
| C23 | `run unit / test_settle_recusa_sem_entrada_ou_ramo_errado ... ok` | pass |
| C24 | `run unit / test_settle_paralelo_remove_so_o_seu ... ok` | pass |
| C25 | `run unit / test_execute_usa_start_e_settle ... ok` | pass |
| C26 | `run unit / test_execute_sem_worker_show_posicional ... ok` | pass |
| C27 | `run unit / test_execute_diz_onde_ler_o_modelo ... ok` | pass |
| C28 | `run unit / test_q_brief_exige_comando_e_saida_na_sondagem ... ok` | pass |
| C29 | `run plugin / ✔ host recusa agent.launch sem a capacidade` | pass |
| C30 | `run plugin / ✔ atalho foca o worktree da missão ativa` | pass |
| C31 | `run unit / test_compatibilidade_cita_limite_do_drive ... ok` | pass |
| C32 | `run unit / test_relato_orca_tem_as_secoes ... ok` | pass |
| C33 | `run unit / test_decisions_registra_os_itens_de_scripts ... ok` | pass |
| C34 | `run unit / test_citacao_em_context_nao_conta ... ok` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `python scripts/check_decisions.py` | pass |
| Build | `orca plugin validate src/orca --json` | pass |
| Build | `orca plugin check src/orca --json` | pass |

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
Ran 755 tests in 334.349s

OK (skipped=1)
```

`Run plugin` - exit 0

```
[starcode-ponte] orca linear issue falhou: cli fora
[starcode-ponte] orca linear issue falhou: cli fora
[starcode-ponte] orca linear issue falhou: cli fora
[starcode-ponte] orca linear issue falhou: cli fora
[starcode-ponte] orca linear issue falhou: cli fora
[starcode-ponte] orca linear issue falhou: cli fora
ℹ tests 71
ℹ suites 0
ℹ pass 71
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2217.3322
4 test file(s) passed (node).
```
