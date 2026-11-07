# cabecalho-robusto verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 1e061ea
**HEAD**: 1d4e026
**Verifier**: codex gpt-6-luna · LaForge claude-sonnet-5-5

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_crew_hook.py` `test_crew_hook_skill_marks_member_and_shows_header` | yes |
| C2 | `tests/test_crew_hook.py` `test_crew_hook_header_plain_text` | no - comprova comprimento de 80 caracteres, mas não que a missão seja o texto correto truncado, nem os valores completos de papel, CLI e modelo. |
| C3 | `tests/test_crew_hook.py` `test_crew_hook_post_tool_use_pulses` | yes |
| C4 | `tests/test_crew_hook.py` `test_crew_hook_stop_and_prompt_toggle` | yes |
| C5 | `tests/test_crew_hook.py` `test_crew_hook_session_end_clears` | yes |
| C6 | `tests/test_crew_hook.py` `test_crew_live_expiry_and_laforge_count` | yes |
| C7 | `tests/test_crew_hook.py` `test_crew_hook_never_breaks` | yes |
| C8 | `tests/test_crew_hook.py` `test_build_registers_crew_hook_only_in_claude` | yes |
| C9 | `tests/test_crew_hook.py` `test_build_header_rule_per_cli` | yes |
| C10 | `tests/test_crew_hook.py` `test_statusline_expiry_and_laforge_count` | yes |
| C11 | `tests/test_crew_hook.py` `test_banner_warns_outdated_plugin` | yes |
| C12 | `tests/test_crew_hook.py` `test_decisions_records_f7_12_crew_hook` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R6 aceita carimbos de data no futuro e fontes desconhecidas como sessões válidas; isso pode manter tripulantes ativos indevidamente. | `scripts/crew_live.py:119`; sondagem `crew_live.entry_active`: `future hook True`, `unknown source True` | Rejeitar `at` futuro e aceitar apenas `source` `hook` ou `cli`; acrescentar casos aos testes de validade. | |
| C2 não prova os valores fixos da missão nem os componentes completos de papel/CLI/modelo e bordão exigidos por R2. | `tests/test_crew_hook.py:77` | Comparar os valores de cada linha e o conteúdo exato da missão truncada, incluindo a fronteira de 80 caracteres. | |

## Limits

Não verifiquei a execução real dos hooks pelo Claude Code; a suíte prova geração e configuração, não o comportamento do host.
