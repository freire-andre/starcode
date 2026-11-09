# fase-8-uhura-scotty-kirk verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at `f01208a`
**HEAD**: 6b560bd
**Verifier**: codex · requested padrão do CLI · effective GPT-6-Luna medium (linha de status do terminal do worker)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_profiles.py` `test_profiles_all_seven_with_required_fields` | yes |
| C2 | `tests/test_profiles.py` `test_profiles_gate_commands_exact` | yes |
| C3 | `tests/test_profiles.py` `test_templates_have_no_hardcoded_versions` | yes |
| C4 | `tests_slow/test_slow_python_flask.py` `test_flask_template_gates_pass` | yes |
| C5 | `tests_slow/test_slow_db.py` `test_flask_postgresql_gates_pass` | yes |
| C6 | `tests/test_profiles.py` `test_app_templates_have_ci_and_gitignore` | yes |
| C7 | `tests/test_registry.py` `test_registry_stable_latest_per_registry` | yes |
| C8 | `tests/test_registry.py` `test_registry_rejects_prereleases` | yes |
| C9 | `tests/test_scaffold.py` `test_scaffold_aligns_major_group` | yes |
| C10 | `tests/test_registry.py` `test_scaffold_registry_error_writes_nothing` | no - só exige prefixo da mensagem, não o motivo/comando exatos de R10. |
| C11 | `tests/test_scaffold.py` `test_registry_fixture_marks_source` | yes |
| C12 | `tests/test_scaffold.py` `test_scaffold_new_renders_and_writes_stack_json` | yes |
| C13 | `tests/test_scaffold.py` `test_scaffold_rejects_invalid_name` | no - `assertIn` aceita qualquer sufixo ou texto extra na mensagem contratual. |
| C14 | `tests/test_scaffold.py` `test_scaffold_rejects_non_empty_dir` | yes |
| C15 | `tests/test_scaffold.py` `test_scaffold_rejects_unknown_combo` | no - confere apenas um exemplo da lista válida, não a lista completa de combinações. |
| C16 | `tests/test_scaffold.py` `test_scaffold_cleans_up_on_failure` | yes |
| C17 | `tests/test_scaffold.py` `test_scaffold_checks_lines` | yes |
| C18 | `tests/test_scaffold.py` `test_scaffold_gates_pass_fail_lines` | yes |
| C19 | `tests/test_scaffold.py` `test_scaffold_gates_skip_missing_tool` | yes |
| C20 | `tests/test_ephemeral_db.py` `test_ephemeral_run_lifecycle_with_fake_docker` | yes |
| C21 | `tests/test_ephemeral_db.py` `test_ephemeral_docker_unavailable_exit_3` | yes |
| C22 | `tests/test_ephemeral_db.py` `test_ephemeral_not_ready_exit_4` | yes |
| C23 | `tests/test_ephemeral_db.py` `test_ephemeral_db.py` `test_ephemeral_reuse_env_rejects_remote_url` | yes |
| C24 | `tests/test_ephemeral_db.py` `test_ephemeral_list_and_down` | yes |
| C25 | `tests/test_ephemeral_db.py` `test_ephemeral_unique_names_and_ports` | yes |
| C26 | `tests/test_stack_cache.py` `test_stack_cache_write_replaces_entry` | yes |
| C27 | `tests/test_stack_cache.py` `test_stack_cache_check_states` | no - o caso `desconhecida` é aceito como `outra versão`, tornando o fluxo aprovado de `write` imediatamente inválido. |
| C28 | `tests/test_uhura_skill.py` `test_uhura_skill_context7_protocol` | yes |
| C29 | `tests/test_uhura_skill.py` `test_uhura_pr_and_comment_templates` | yes |
| C30 | `tests/test_uhura_skill.py` `test_execute_uses_uhura_for_pr_and_comments` | yes |
| C31 | `tests/test_scaffold_detect.py` `test_scaffold_detect_and_record_profiles` | yes |
| C32 | `tests/test_data_skill.py` `test_data_skill_uses_stack_checks` | yes |
| C33 | `tests/test_nova_missao_skill.py` `test_nova_missao_skill_order` | yes |
| C34 | `tests/test_nova_missao_skill.py` `test_nova_missao_gates_fail_no_commit` | yes |
| C35 | `tests/test_nova_missao_skill.py` `test_nova_missao_offers_setup_and_first_mission` | yes |
| C36 | `tests/test_build.py` `test_build_copies_profiles_and_new_skills` | yes |
| C37 | `tests/test_acceptance_doc_f8.py` `test_fase8_acceptance_all_scenarios_approved` | no - valida texto com `PASS`/fontes/data, não que os gates/documentados foram realmente executados; uma alegação fictícia passaria. |
| C38 | `tests/test_release_docs_f8.py` `test_decisions_f8_and_changelog_1_2_0` | yes |
| C39 | `tests/test_profiles.py` `test_profiles_main_deps_have_tested_series` | yes |
| C40 | `tests/test_scaffold.py` `test_scaffold_outside_tested_series_exits_5` | yes |
| C41 | `tests/test_scaffold.py` `test_scaffold_pin_tested_and_allow_new_series` | yes |
| C42 | `tests/test_profiles.py` `test_profiles_main_deps_have_docs_id` | yes |
| C43 | `tests/test_nova_missao_skill.py` `test_nova_missao_series_choice` | yes |
| C44 | `tests/test_nova_missao_skill.py` `test_nova_missao_without_context7` | yes |
| C45 | `tests/test_scaffold.py` `test_scaffold_description_validation_and_readme` | yes |
| C46 | `tests_slow/test_slow_rust_gpui.py` `test_rust_template_gates_pass` | yes |
| C47 | `tests_slow/test_slow_rust_gpui.py` `test_gpui_template_gates_pass` | yes |
| C48 | `tests_slow/test_slow_ts_tauri.py` `test_typescript_template_gates_pass` | yes |
| C49 | `tests_slow/test_slow_ts_tauri.py` `test_tauri_template_gates_pass` | yes |
| C50 | `tests_slow/test_slow_db.py` `test_flask_mysql_gates_pass` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| `Doc version` desconhecida torna inválido o cache que o próprio fluxo grava. A classificação retorna `outra versão` e `check` exit 1 logo após `write`; diverge do sucesso esperado para o cache recém-criado e impede o bootstrap conforme o aceite. | `scripts/stack_cache.py:184`; comando de probe: `write --doc-version desconhecida` seguido de `check --today 2026-11-09` → `flask: outra versão`, exit 1; também confirmado em `docs/aceite/fase-8.md:94`. | Definir o tratamento de `desconhecida` compatível com R27 e com o fluxo de bootstrap (ou obter versão documental válida), e cobrir `write` seguido de `check`. || 9534c36 (R27 emendado, user "a" em 2026-11-09; F8-12 em b990c6f) |
| C37 não prova o aceite real exigido por R37; o teste aprova texto que contenha rótulos/linhas `PASS`, sem validar execução, resultado integral dos gates, ou ausência de containers. | `tests/test_acceptance_doc_f8.py:35-54`; `docs/aceite/fase-8.md:94-95` lista pendências apesar do teste declarar todos aprovados. | Ligar o aceite a evidências verificáveis de execução e validar os requisitos completos, incluindo `docker ps -a` sem órfãos. || 99b98a0 (linhas PASS cruzadas com os gates dos perfis, docker ps -a e sem pendência aberta; execução real segue registrada no aceite, não reexecutável em teste de unidade) |

## Limits

- O aceite de R37 foi julgado pelo teste documental e pelo registro em `docs/aceite/fase-8.md`; não reexecutei operações externas/Context7 nem containers reais.
- Biome 2.6.6 sinaliza `linter.rules.recommended` obsoleto (`profiles/typescript/template/biome.json` e `profiles/tauri/template/biome.json`); os gates passam, mas essa regra não tem check que detecte o aviso.
- Probes independentes: tags Docker Hub `['17','17.1','18-rc','9']` retornaram `17`; cache com idade de 30 e 31 dias retornou exit 1 em ambos por `Doc version` desconhecida, então a verificação de limite temporal fica mascarada por essa classificação anterior.
