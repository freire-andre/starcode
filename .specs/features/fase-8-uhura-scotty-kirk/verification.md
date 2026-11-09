# fase-8-uhura-scotty-kirk verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at `3c7a412`
**HEAD**: fde3c42
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
| C10 | `tests/test_registry.py` `test_scaffold_registry_error_writes_nothing` | yes |
| C11 | `tests/test_scaffold.py` `test_registry_fixture_marks_source` | yes |
| C12 | `tests/test_scaffold.py` `test_scaffold_new_renders_and_writes_stack_json` | yes |
| C13 | `tests/test_scaffold.py` `test_scaffold_rejects_invalid_name` | yes |
| C14 | `tests/test_scaffold.py` `test_scaffold_rejects_non_empty_dir` | yes |
| C15 | `tests/test_scaffold.py` `test_scaffold_rejects_unknown_combo` | yes |
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
| C27 | `tests/test_stack_cache.py` `test_stack_cache_unknown_doc_version_flow` | yes |
| C28 | `tests/test_uhura_skill.py` `test_uhura_skill_context7_protocol` | yes |
| C29 | `tests/test_uhura_skill.py` `test_uhura_pr_and_comment_templates` | yes |
| C30 | `tests/test_uhura_skill.py` `test_execute_uses_uhura_for_pr_and_comments` | yes |
| C31 | `tests/test_scaffold_detect.py` `test_scaffold_detect_and_record_profiles` | yes |
| C32 | `tests/test_data_skill.py` `test_data_skill_uses_stack_checks` | yes |
| C33 | `tests/test_nova_missao_skill.py` `test_nova_missao_skill_order` | yes |
| C34 | `tests/test_nova_missao_skill.py` `test_nova_missao_gates_fail_no_commit` | yes |
| C35 | `tests/test_nova_missao_skill.py` `test_nova_missao_offers_setup_and_first_mission` | yes |
| C36 | `tests/test_build.py` `test_build_copies_profiles_and_new_skills` | yes |
| C37 | `tests/test_acceptance_doc_f8.py` `test_fase8_acceptance_all_scenarios_approved` | yes |
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
| `stack_cache.py` aceita qualquer `doc-version` sem dígitos como se fosse o valor especial `desconhecida`. Um cache escrito com `--doc-version abc` recebe `ok (doc sem versão)` e exit 0, embora R27 só autorize pular essa comparação para `desconhecida`. | `scripts/stack_cache.py:195`; probe em diretório temporário: `write --doc-version abc` → exit 0; `check --today 2026-11-09` → `flask: ok (doc sem versão)`, exit 0. | Tratar como sem versão apenas o valor literal `desconhecida`; validar ou classificar os demais valores. | b58bfd6 (user "a" em 2026-11-09; probe do Picard em 68e12f5: write abc → exit 2 sem arquivo; check com abc → inválida, exit 1; desconhecida → ok (doc sem versão)) |
| Achado anterior: `Doc version` desconhecida tornava inválido o cache gravado pelo próprio fluxo. R27 agora especifica a exceção e o teste/probes confirmam o fluxo. | `scripts/stack_cache.py:184-197`; probes: `desconhecida` recém-gravada → `ok (doc sem versão)`, exit 0; aos 30 dias → exit 0; aos 31 → `velha`, exit 1; manifesto 4.0.0 contra projeto 3.1.3 → `versão mudou`, exit 1. | Corrigido em `9534c36`. | 9534c36 |
| Achado anterior: C37 aceitava o aceite sem conferir cobertura dos gates dos perfis. O teste agora exige as linhas `PASS` na sequência e com os comandos derivados dos `profile.yaml`, e o registro contém essas linhas para todos os cenários. | `tests/test_acceptance_doc_f8.py:25-42, 91-107`; `docs/aceite/fase-8.md:26-81`. | Corrigido em `99b98a0`; a execução real permanece registrada no aceite e não é reproduzível por este teste documental. | 99b98a0 |

## Limits

- O aceite de R37 foi julgado pelo teste documental e pelo registro em `docs/aceite/fase-8.md`; não reexecutei operações externas/Context7 nem containers reais.
- Esta segunda passagem foi restrita a R27/C27, C10, C13, C15, C37, Biome e aos dois achados fechados; os demais checks mantêm o julgamento anterior.
- Biome: os dois templates usam agora `linter.rules.preset: "recommended"`; a mudança de sintaxe remove o aviso anterior, preservando o preset. Os gates reais constam aprovados no aceite e nos proofs; não rodei novamente a suíte.
- O probe de idade da primeira passagem ficou mascarado pela classificação então incorreta de `desconhecida`; nesta segunda passagem, 30 dias retorna exit 0 e 31 dias retorna exit 1 como `velha`.
