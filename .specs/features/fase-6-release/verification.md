# fase-6-release verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 16bc6bc
**HEAD**: 92a89cc
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_install_local.py` `test_opencode_install_replaces_starcode_skill_paths_from_other_clones` | no - comparação de sufixo diferencia maiúsculas/minúsculas; caminhos válidos no Windows podem sobreviver. |
| C2 | `tests/test_install_local.py` `test_opencode_install_keeps_foreign_skill_paths_in_order` | yes |
| C3 | `tests/test_install_local.py` `test_opencode_install_twice_from_two_clones_no_duplicates` | yes |
| C4 | `tests/test_banner.py` `test_banner_setup_command_per_cli` | yes |
| C5 | `tests/test_banner.py` `test_banner_engajar_command_matches_cmd_ref` | yes |
| C6 | `tests/test_build.py` `test_version_is_1_0_0_in_all_manifests` | yes |
| C7 | `tests/test_build.py` `test_check_fails_when_manifest_version_diverges` | yes |
| C8 | `tests/test_release_docs.py` `test_changelog_has_1_0_0_section` | yes |
| C9 | `tests/test_release.py` `test_release_check_rejects_tag_diverging_from_version` | yes |
| C10 | `tests/test_release.py` `test_release_refuses_existing_remote_tag` | yes |
| C11 | `tests/test_release.py` `test_release_notes_extracted_from_changelog` | yes |
| C12 | `tests/test_release.py` `test_release_create_requires_yes_flag` | yes |
| C13 | `tests/test_ci_workflow.py` `test_ci_triggers` | yes |
| C14 | `tests/test_ci_workflow.py` `test_ci_checks_steps_and_commands` | yes |
| C15 | `tests/test_ci_workflow.py` `test_ci_matrix_ubuntu_windows_python_312` | yes |
| C16 | `tests/test_ci_workflow.py` `test_ci_plugin_validate_with_pinned_claude_code` | yes |
| C17 | `tests/test_ci_workflow.py` `test_ci_has_no_continue_on_error` | yes |
| C18 | `tests/test_ci_workflow.py` `test_ci_concurrency_cancels_in_progress` | yes |
| C19 | `tests/test_ci_workflow.py` `test_ci_eval_job_only_on_tag_or_dispatch` | yes |
| C20 | `tests/test_ci_workflow.py` `test_ci_secret_only_in_eval_job` | yes |
| C21 | `tests/test_ci_workflow.py` `test_ci_eval_fails_without_secret` | yes |
| C22 | `tests/test_ci_workflow.py` `test_ci_eval_uploads_results_and_summary` | yes |
| C23 | `tests/test_ci_workflow.py` `test_ci_release_check_runs_release_py` | yes |
| C24 | `tests/test_release_docs.py` `test_readme_install_commands_per_cli` | yes |
| C25 | `tests/test_release_docs.py` `test_readme_states_v1_and_private_access` | yes |
| C26 | `tests/test_check_decisions.py` `test_decisions_f6_1_sandbox_mission_day` | yes |
| C27 | `tests/test_acceptance_doc_f6.py` `test_acceptance_doc_f6_claude_codex_filled` | yes |
| C28 | `tests/test_acceptance_doc_f6.py` `test_acceptance_doc_f6_antigravity_opencode_filled` | yes |
| C29 | `tests/test_acceptance_doc_f6.py` `test_acceptance_doc_f6_mission_day_filled` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| O instalador não remove caminhos StarCode com diferenças de caixa, apesar de caminhos Windows não diferenciarem caixa. | `tools/install_local.py:107-108`; `python -` com `C:\x\DIST\OpenCode\Skills\engajar` e `/tmp/DIST/opencode/skills/engajar` imprimiu `False` para ambos os reconhecimentos. | Normalizar os componentes (p.ex., `casefold`) antes de comparar e cobrir variações de caixa em teste. | a19bdda |
| A checagem de release não valida que a tag está sendo criada em `main` com CI verde nem que os aceites estão aprovados; `--yes` é a única barreira antes da criação/publicação. Isso pode publicar release fora dos pré-requisitos de R23. | `tools/release.py:36-39, 61-68` | Validar os pré-requisitos do R23 antes de executar tag, push e `gh release create`, ou restringir o script ao fluxo que os verifica. | 337978e |
| Asserções abaixo são mais fracas que os critérios: C9 usa `assertIn` para a mensagem, sem exigir igualdade; C10 usa `assertIn("já existe no remoto")`, sem confirmar a mensagem completa; C21 verifica a presença da frase, não que seja a mensagem emitida exatamente. | `tests/test_release.py` `test_release_check_rejects_tag_diverging_from_version`, `test_release_refuses_existing_remote_tag`; `tests/test_ci_workflow.py` `test_ci_eval_fails_without_secret` | Comparar o texto completo esperado, além do código de saída. | 7b3fe18 |

## Limits

Não verifiquei execução real dos workflows no GitHub nem o comportamento dos quatro CLIs em instalações limpas; usei as provas registradas e inspecionei os testes e o código.
A prova registrada aponta para 16bc6bc, enquanto o HEAD analisado é 92a89cc; não há prova de testes executados nesse HEAD.
