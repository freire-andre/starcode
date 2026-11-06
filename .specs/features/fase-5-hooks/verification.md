# fase-5-hooks verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at a89e298
**HEAD**: 30e6c4a
**Verifier**: codex · requested padrão do CLI (sem --model) · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_build.py` `test_codex_hooks_json_registers_guards_and_banner` | yes |
| C2 | `tests/test_build.py` `test_antigravity_hooks_json_native_format` | yes |
| C3 | `tests/test_build.py` `test_dist_has_no_machine_absolute_paths` | yes |
| C4 | `tests/test_build.py` `test_session_start_banner_runs_in_hook_mode` | yes |
| C5 | `tests/test_opencode_plugin.py` `test_opencode_plugin_in_dist_is_pure_object` | yes |
| C6 | `tests/test_opencode_plugin.py` `test_opencode_plugin_throws_on_guard_deny` | no - confirma apenas erro não vazio; não comprova que a mensagem contém o motivo do guard como R6 exige |
| C7 | `tests/test_opencode_plugin.py` `test_opencode_plugin_allows_normal_command` | yes |
| C8 | `tests/test_opencode_plugin.py` `test_opencode_plugin_fails_open_with_warning` | yes |
| C9 | `tests/test_git_guard.py` `test_force_push_denied_codex_and_antigravity_payloads` | yes |
| C10 | `tests/test_secret_scan.py` `test_secret_commit_denied_codex_and_antigravity_payloads` | yes |
| C11 | `tests/test_git_guard.py` `test_normal_flow_commands_pass_all_payloads` | yes |
| C12 | `tests/test_git_guard.py` `test_invalid_payload_fails_open_with_warning` | yes |
| C13 | `tests/test_install_local.py` `test_install_writes_absolute_paths_in_installed_copy` | yes |
| C14 | `tests/test_install_local.py` `test_install_twice_keeps_single_registration` | yes |
| C15 | `tests/test_banner.py` `test_codex_banner_warns_hooks_without_trust` | yes |
| C16 | `tests/test_build.py` `test_banner_hook_mode_matches_text_per_cli` | no - compara com `--text` sem `--full`, embora R10 fixe a saída de `--full --text` |
| C17 | `tests/test_skills_cli.py` `test_setup_codex_shows_trust_step` | yes |
| C18 | `tests/test_skills_cli.py` `test_setup_opencode_confirms_plugin_copy` | yes |
| C19 | `tests/test_skills_cli.py` `test_setup_checks_python_per_cli` | yes |
| C20 | `tests/test_support.py` `test_conflicts_lists_starcode_hello` | yes |
| C21 | `tests/test_worker_skills.py` `test_execute_stops_on_codex_hooks_review` | yes |
| C22 | `tests/test_acceptance_scripts_f5.py` `test_acceptance_scripts_f5_have_sections` | yes |
| C23 | `tests/test_acceptance_doc_f5.py` `test_acceptance_doc_f5_codex_filled` | yes |
| C24 | `tests/test_acceptance_doc_f5.py` `test_acceptance_doc_f5_antigravity_filled` | yes |
| C25 | `tests/test_acceptance_doc_f5.py` `test_acceptance_doc_f5_opencode_filled` | yes |
| C26 | `tests/test_acceptance_doc_f5.py` `test_capabilities_match_f5_acceptance` | yes |
| C27 | `tests/test_build.py` `test_antigravity_hook_commands_without_quotes` | yes |
| C28 | `tests/test_install_local.py` `test_antigravity_install_refuses_path_with_space` | yes |
| C29 | `tests/test_secret_scan.py` `test_agy_real_commit_payload_denies_staged_secret` | yes |
| C30 | `tests/test_opencode_plugin.py` `test_opencode_plugin_uses_event_workdir` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| O scanner ignora segredos adicionados depois dos primeiros 2.000.000 bytes do diff staged; quebra a exigência de bloquear commit com segredo. | `hooks/scripts/secret_scan.py:146`; probe: diff staged com 2.100.000 `x` antes de `API_KEY=Ab3dEf6hIj9kLm2nOp5qRs8tUv1wXy4z`; `secret_scan.evaluate('git commit -m safe', repo)` retornou `[]` (`secret line beyond truncation detected: False`). | Não truncar o diff antes de examinar todas as linhas adicionadas; se houver limite, encerrar com aviso ou bloquear, nunca deixar de verificar silenciosamente. | 0633da8 |
| A saída do SessionStart não corresponde ao banner de `--full --text` definido em R10: o hook chama `build_banner(..., full=False, ...)` e omite checagens que aparecem em modo full. | `hooks/scripts/banner.py:274`; `dist/codex/hooks/hooks.json` e `dist/antigravity/hooks.json` chamam `banner.py` sem `--full`; `tests/test_build.py:test_banner_hook_mode_matches_text_per_cli` também compara somente `--text` sem `--full`. | Fazer o hook entregar o mesmo texto de `--full --text --cli <cli>` e comparar explicitamente esses modos no teste. | 411cd80 |
| C6 não prova que o erro contém o motivo específico da negação. | `tests/test_opencode_plugin.py:55-60` só exige `out["error"]` não vazio para `git push --force`. | Verificar que a mensagem contém o motivo concreto retornado pelo guard. | cbfb50f |

## Limits

Não executei a suíte completa; usei as provas em `proofs.md` conforme instruído e rodei apenas o probe de diff grande.
Não repeti aceites interativos dos CLIs; considerei a evidência registrada em `docs/aceite/fase-5.md`.
