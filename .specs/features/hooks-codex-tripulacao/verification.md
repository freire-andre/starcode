# hooks-codex-tripulacao verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 869ebad
**HEAD**: a84a8a0
**Verifier**: antigravity gemini-3.8-flash-high · LaForge claude-sonnet-5-5

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_crew_hook.py` `test_crew_hook_codex_skill_read_marks_member` | no - não testa caminho com nome da skill em maiúsculas; `member_for` compara sensível a maiúsculas e falha em R1 |
| C2 | `tests/test_crew_hook.py` `test_crew_hook_codex_prompt_token` | no - não testa token de prompt com maiúsculas (ex.: `$Spock`, `$TROI`) que falha silenciosamente, nem `$troi` isolado sem missão |
| C3 | `tests/test_crew_hook.py` `test_crew_hook_codex_lifecycle` | yes |
| C4 | `tests/test_crew_hook.py` `test_crew_hook_codex_no_repeat_header` | yes |
| C5 | `tests/test_crew_hook.py` `test_crew_hook_codex_never_breaks` | yes |
| C6 | `tests/test_crew_hook.py` `test_build_registers_crew_hook_in_codex` | yes |
| C7 | `tests/test_crew_hook.py` `test_build_header_rule_codex` | yes |
| C8 | `tests/test_banner.py` `test_banner_warns_codex_crew_hooks_untrusted` | yes |
| C9 | `tests/test_crew_hook.py` `test_decisions_records_f7_14_codex_hooks` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R1 exige casamento de caminho sem diferenciar maiúsculas, mas `member_for` compara `m.get("skill") == name` de forma sensível a caixa; comandos como `cat .../skills/Troi/SKILL.md` ou `Get-Content ...\SPOCK\SKILL.md` falham silenciosamente. | `hooks/scripts/crew_hook.py:50`; execução com `cat /starcode/skills/Troi/SKILL.md` resulta em código 0 e saída vazia `''` | Em `hooks/scripts/crew_hook.py:46`, normalizar `name = name.lower()` antes de comparar com `m.get("skill")`. | yes - 0ccee4c (`member_for` sem distinguir maiúsculas; `skills/Troi/SKILL.md` e `\SPOCK\SKILL.md` casam) |
| R2 exige casamento de `$starcode:<skill>` ou `$<skill>`, mas tokens com letras maiúsculas (ex.: `$Spock`, `$TROI`) falham silenciosamente pelo mesmo motivo de `member_for`. | `hooks/scripts/crew_hook.py:50`; prompt `"$Spock revisar spec"` resulta em saída vazia `''` | A mesma normalização `name = name.lower()` em `member_for` resolve este caso; adicionar testes com maiúsculas para R1 e R2. | yes - 0ccee4c (`$Spock` e `$TROI` casam; testes de R2 com maiúsculas) |
| C1 e C2 não testam a insensibilidade a maiúsculas no nome da skill nem validam o formato completo do cabeçalho emitido quando não há missão. | `tests/test_crew_hook.py:332,348` | Adicionar casos de teste para `<skill>` em maiúsculas/misto e validar a ausência da linha `Missão:` no `$troi` sem argumentos. | yes - 0ccee4c (casos de maiúsculas em C1/C2 e cabeçalho completo de `$troi` sem `Missão:`) |

## Limits

A execução real dos hooks dentro do runtime do Codex 0.167 e a renderização do markdown na tela do host não foram verificadas (conforme nota 17 da spec, ficam para o aceite).
