# hooks-agy-opencode-tripulacao verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at a34dbf3
**HEAD**: a28cfe0
**Verifier**: codex · gpt-6-luna (família OpenAI; implementação em claude-sonnet-5-5)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_crew_hook_agy_opencode.py` `test_crew_hook_agy_skill_read_marks_pending` | yes |
| C2 | `tests/test_crew_hook_agy_opencode.py` `test_crew_hook_agy_never_decides` | yes |
| C3 | `tests/test_crew_hook_agy_opencode.py` `test_crew_hook_agy_post_invocation_injects_header` | yes |
| C4 | `tests/test_crew_hook_agy_opencode.py` `test_crew_hook_agy_lifecycle` | yes |
| C5 | `tests/test_crew_hook_agy_opencode.py` `test_crew_hook_opencode_events` | yes |
| C6 | `tests/test_crew_hook_agy_opencode.py` `test_opencode_plugin_registers_crew_hooks` | no - testa o caminho feliz, mas não injeta falha de registro, hook, spawn ou `synthetic`; não prova que todos os erros são engolidos |
| C7 | `tests/test_crew_hook_agy_opencode.py` `test_build_registers_crew_hook_in_antigravity` | yes |
| C8 | `tests/test_crew_hook_agy_opencode.py` `test_build_header_rule_agy_opencode` | yes |
| C9 | `tests/test_crew_hook_agy_opencode.py` `test_crew_hook_agy_opencode_never_break` | yes |
| C10 | `tests/test_crew_hook_agy_opencode.py` `test_decisions_records_f7_16_agy_opencode_hooks` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Nova leitura da mesma skill na mesma sessão cria uma nova pendência, contrariando o edge case aprovado de apenas renovar `at`. | `hooks/scripts/crew_hook.py:188-212`; sondagem: após ler `troi/SKILL.md`, consumir a pendência com `PostInvocation` e ler a mesma skill de novo, `pending.json` voltou a conter `c1` (saídas de ambas as leituras: vazias). | Detectar sessão ativa válida do mesmo membro; renovar `at` sem recriar a pendência. | |
| C6 não verifica a tolerância a erros exigida por R7; verificações de texto por contagem de `catch` não demonstram o comportamento sob rejeição ou exceção. | `tests/test_crew_hook_agy_opencode.py:202-229` | Exercitar rejeições/exceções em registro, execução do hook e `ctx.session.synthetic`, confirmando que não escapam nem bloqueiam o turno. | |
| As asserções de cabeçalho são mais fracas que o texto integral fixado por R3/R4/R6. | `tests/test_crew_hook_agy_opencode.py:50-60, 91-98, 142-146`; usam `assertIn`/`startswith` em vez de comparar o cabeçalho completo, incluindo linha de papel, modelo e demais linhas. | Comparar a string integral esperada para os casos especificados. | |

## Limits

- As provas registram execução em `a34dbf3`; `a28cfe0` altera apenas `proofs.md`, então o código testado é idêntico, mas não há execução registrada no HEAD exato.
- O comportamento contra a versão real do Antigravity/OpenCode não foi verificado; a suíte usa payloads e API simulados.
