# fase-4-paridade verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 0d091d7
**HEAD**: 15cec2d
**Verifier**: codex · gpt-6-luna (config.toml do Codex; dispatch ctx_8c1a34ab40e9)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_build.py` `test_capabilities_json_per_cli` | yes |
| C2 | `tests/test_build.py` `test_unavailable_extra_without_fallback_fails` | yes |
| C3 | `tests/test_build.py` `test_cmd_and_cli_placeholders_per_cli` | yes |
| C4 | `tests/test_skills_cli.py` `test_no_claude_commands_outside_claude_dist` | yes |
| C5 | `tests/test_skills_cli.py` `test_engajar_banner_uses_cli` | yes |
| C6 | `tests/test_banner.py` `test_banner_lists_unavailable_extras` | yes |
| C7 | `tests/test_banner.py` `test_banner_without_cli_keeps_phase3_output` | yes |
| C8 | `tests/test_banner.py` `test_degraded_only_from_marker_line` | yes |
| C9 | `tests/test_install_local.py` `test_install_codex_runs_marketplace_and_install` | yes |
| C10 | `tests/test_install_local.py` `test_install_antigravity_validates_first` | yes |
| C11 | `tests/test_install_local.py` `test_install_opencode_writes_skills_and_commands` | yes |
| C12 | `tests/test_install_local.py` `test_install_is_idempotent` | yes |
| C13 | `tests/test_install_local.py` `test_install_missing_binary_exits_2` | yes |
| C14 | `tests/test_install_local.py` `test_install_dry_run_changes_nothing` | yes |
| C15 | `tests/test_data_skill.py` `test_data_parent_issue_fallback` | no - só procura termos no texto; não prova criação da issue-mãe nem das sub-issues |
| C16 | `tests/test_data_skill.py` `test_publish_gate_accepts_parent_issue` | no - só procura comandos mencionados; não verifica relações blocks nem record dos IDs pelo Data |
| C17 | `tests/test_data_skill.py` `test_data_reports_publish_path` | yes |
| C18 | `tests/test_dispatch.py` `test_q_cli_picks_other_family` | yes |
| C19 | `tests/test_dispatch.py` `test_q_cli_self_verified_when_none` | yes |
| C20 | `tests/test_skills_exec.py` `test_execute_ref_opencode_and_q_cli` | yes |
| C21 | `tests/test_skills_exec.py` `test_execute_ref_integration_worktree` | yes |
| C22 | `tests/test_skills_exec.py` `test_execute_ref_nested_depth_stop` | yes |
| C23 | `tests/test_dispatch.py` `test_medium_brief_from_spec` | yes |
| C24 | `tests/test_dispatch.py` `test_medium_brief_without_checks_exits_2` | yes |
| C25 | `tests/test_dispatch.py` `test_family_deepseek_gptoss_openrouter` | yes |
| C26 | `tests/test_acceptance_scripts_f4.py` `test_acceptance_scripts_have_sections` | yes |
| C27 | `tests/test_acceptance_doc_f4.py` `test_acceptance_doc_f4_has_all_clis` | no - exige só resultado, hash e issue; não valida gates verdes nem modelos efetivos de R27 |
| C28 | `tests/test_acceptance_doc_f4.py` `test_compat_matrix_has_phase4` | yes |
| C29 | `tests/test_acceptance_doc_f4.py` `test_failed_cli_recorded_as_reprovado` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C15 e C16 não falsificam o comportamento do Data; alterações que removam a criação/relacionamento/registro ainda passam por conter as palavras esperadas. | `tests/test_data_skill.py:13` e `tests/test_data_skill.py:24` | Exercitar a sequência de comandos via runner falso e afirmar argumentos, IDs, relações blocks e registro; validar também a aceitação pelo gate. | 8d59c1e (SC-44) |
| R1/R2 aceitam fallback composto apenas por espaços, apesar de exigir texto não vazio. | Comando: cópia temporária de `src/capabilities.yaml` com o primeiro fallback `"   "`; `build.load_capabilities` respondeu `whitespace fallback accepted: '   '`. | Validar `fallback.strip()` como não vazio e cobrir fallback em branco/whitespace. | 8d59c1e (SC-44) |
| R25 classifica como `anthropic` um OpenRouter sem nome de modelo. | Comando: `dispatch.family("openrouter/anthropic/")` => `anthropic`. | Exigir vendor e modelo não vazios antes de atribuir família; cobrir segmentos vazios. | 8d59c1e (SC-44) |
| C27 não verifica toda a evidência exigida por R27: o teste passa sem conferir saída VEREDITO VERDE ou modelos efetivos por papel. | `tests/test_acceptance_doc_f4.py:30` | Asserir no relatório de aceite os gates verdes e os modelos efetivos requeridos para cada CLI. | 8d59c1e (SC-44) |

## Limits

Não reexecutei a suíte: `proofs.md` registra 236 testes e os gates verdes em `0d091d7`; julguei os testes nomeados e fiz sondagens isoladas no HEAD `15cec2d`.
Não executei aceite interativo nas três CLIs nem confirmei externamente os estados do Linear/Orca; considerei os relatos documentados como evidência, não como reprodução independente.
