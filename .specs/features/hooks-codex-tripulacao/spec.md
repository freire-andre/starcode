# Hooks da tripulação no Codex: Spec

**Approved**: 2026-11-07 - user: "Sim"
**Status**: Approved

**Size**: MEDIUM
**Risk triggers**: estado compartilhado (`.starcode/live/` gravado por sessões de CLIs diferentes)
**Linear**: SC-85
**May change**: hooks/scripts/crew_hook.py, tools/build.py, hooks/scripts/banner.py, DECISIONS.md, CHANGELOG.md, docs/compatibilidade.md, tests/, dist/

## Context
A F7-12 (SC-84) pôs no Claude Code o hook `crew_hook.py`, que mostra o cabeçalho do tripulante e mantém `.starcode/live/sessions.json`. Nos outros CLIs o cabeçalho ainda depende do modelo seguir a instrução da skill. O usuário escolheu em 2026-11-07: "Codex agora, sondagem dos outros" e "Leitura do SKILL.md + $skill".

Fatos do Codex 0.167 verificados no código-fonte (Context7, `openai/codex`, `codex-rs/hooks`):
- eventos `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop` e `SessionEnd`, todos com `session_id` e `cwd` na entrada;
- `PreToolUse` e `PostToolUse` trazem `tool_name` e `tool_input`; o shell é `Bash` com `tool_input.command` (o `git_guard` do Codex já usa esse matcher, aceito na Fase 5);
- a saída tem o campo universal `system_message`. Não verificado: a grafia exata no JSON (`systemMessage`, como no Claude) e como o Codex mostra o texto na tela. Isso fica para o aceite.
- O Codex não tem ferramenta "Skill": ele lê o `SKILL.md` pelo shell (docs/compatibilidade.md, nota 4), e o usuário chama a skill digitando `$<nome>`.
- Hooks novos de plugin no Codex pedem confiança do usuário (F0-1, `hooks.state` com `trusted_hash`). Sem a confiança, o hook não roda.

## Scope
- `crew_hook.py` com o modo Codex (`--cli codex`).
- Registro no `dist/codex/hooks/hooks.json` pelo `tools/build.py`.
- Frase do cabeçalho nas skills de `dist/codex`.
- Aviso no banner do Codex quando os hooks da tripulação ainda não têm confiança.
- Decisão F7-14, CHANGELOG e a linha do Codex em `docs/compatibilidade.md`.

## Non-Goals
- Antigravity e OpenCode: um worker separado sonda os eventos deles; a feature vem depois, com os fatos.
- Dar a confiança aos hooks no lugar do usuário (só o usuário confia hooks no Codex).
- Mudar o formato de `crew.json` ou `sessions.json`.

## Requirements
- **R1** - WHEN o Codex dispara `PreToolUse` com `tool_name` `Bash` e `tool_input.command` contém um caminho que casa com `starcode…[\/]skills[\/]<skill>[\/]SKILL.md` (sem diferenciar maiúsculas), sendo `<skill>` a skill de um tripulante do `crew.json` do plugin, THEN `crew_hook.py --cli codex` SHALL gravar a sessão como no Claude (R1 da F7-12, `source: hook`), recalcular o `crew.json` e imprimir `{"systemMessage": "<cabeçalho>"}` sem campo de decisão.
- **R2** - WHEN o Codex dispara `UserPromptSubmit` e o campo `prompt` contém, no início ou depois de um espaço, `$starcode:<skill>` ou `$<skill>` de um tripulante THEN `crew_hook.py --cli codex` SHALL fazer o mesmo que em R1, com a missão vinda do resto da linha depois do token, cortada em 80 caracteres. WHEN o `prompt` não tem esse token e a sessão tem entrada THEN SHALL só marcar `"active": true` e renovar `at` (R4 da F7-12).
- **R3** - The system SHALL repetir no Codex o comportamento da F7-12 para `PostToolUse` (renova `at`), `Stop` (`"active": false`) e `SessionEnd` (remove a sessão), sem imprimir nada.
- **R4** - WHEN a mesma sessão já tem o mesmo tripulante ativo THEN uma nova leitura do mesmo `SKILL.md` SHALL só renovar `at`, sem imprimir o cabeçalho de novo.
- **R5** - IF a entrada é inválida, está fora de um repositório Git, ou a leitura ou gravação falha THEN `crew_hook.py --cli codex` SHALL sair com código 0 sem imprimir nada.
- **R6** - The system SHALL registrar em `dist/codex/hooks/hooks.json` o `crew_hook.py --cli codex` com timeout 10 s em `PreToolUse` matcher `Bash`, `UserPromptSubmit`, `PostToolUse`, `Stop` e `SessionEnd` (os quatro últimos sem matcher), mantendo `git_guard`, `secret_scan` e `banner`. `dist/antigravity` e `dist/opencode` SHALL continuar sem `crew_hook`.
- **R7** - The system SHALL trocar, nas skills de `dist/codex`, a instrução "Header first (F6-6)" pela frase `In Codex the StarCode hook shows your header and marks you as working once its hooks are trusted: do not run crew_live.py start/stop and do not repeat the header.`
- **R8** - WHEN o banner roda no Codex e algum hook da tripulação do plugin `starcode` não tem entrada confiável em `hooks.state` do `~/.codex/config.toml` THEN o banner SHALL incluir a linha `⚠️ Codex: confie nos hooks da tripulação do StarCode (abra o Codex e aceite o aviso de hooks) para o cabeçalho aparecer`.
- **R9** - The system SHALL registrar a decisão F7-14 em `DECISIONS.md`, a entrada em `## [Unreleased]` do `CHANGELOG.md` e, em `docs/compatibilidade.md`, a linha "Cabeçalho por hook" com Claude ✅, Codex ✅ (após confiança), Antigravity e OpenCode "em sondagem".

## Edge Cases
- **Comando que só cita o caminho sem ler** (`ls skills/troi`): sem `SKILL.md` no fim do caminho, nada acontece.
- **`SKILL.md` de outro plugin** (caminho sem `starcode`): nada acontece.
- **`$data` no meio de uma palavra** (`US$data`): não casa (exige início ou espaço antes).
- **Hooks sem confiança:** nada roda; o banner avisa (R8) e a skill não repete o cabeçalho, por isso o usuário vê o aviso do banner.
- **Claude e Codex no mesmo repositório:** as sessões têm `session_id` diferentes e somam no `crew.json`.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `PreToolUse` `Bash` com `Get-Content C:\x\starcode\1.1.0\skills\troi\SKILL.md` grava a sessão, põe `troi: 1` e imprime só `systemMessage`; com `cat .../other-plugin/skills/troi/SKILL.md` e com `ls .../starcode/skills/troi` nada acontece (R1)
Proof: run unit | test_crew_hook_codex_skill_read_marks_member ... ok

**C2** - `UserPromptSubmit` com `$starcode:spock revisar a spec` e com `$troi` grava e mostra o cabeçalho com a missão; `US$data` não casa; um prompt comum numa sessão existente só reativa (R2)
Proof: run unit | test_crew_hook_codex_prompt_token ... ok

**C3** - No modo Codex, `PostToolUse` renova `at`, `Stop` põe 0 e `SessionEnd` remove, sem saída (R3)
Proof: run unit | test_crew_hook_codex_lifecycle ... ok

**C4** - Uma segunda leitura do mesmo `SKILL.md` na mesma sessão não imprime nada e renova `at` (R4)
Proof: run unit | test_crew_hook_codex_no_repeat_header ... ok

**C5** - Entrada inválida, pasta sem Git e falha de gravação saem com 0 e saída vazia no modo Codex (R5)
Proof: run unit | test_crew_hook_codex_never_breaks ... ok

**C6** - `dist/codex/hooks/hooks.json` tem os 5 eventos com `crew_hook.py --cli codex` e timeout 10, mantém os hooks atuais; antigravity e opencode não citam `crew_hook` (R6)
Proof: run unit | test_build_registers_crew_hook_in_codex ... ok

**C7** - As 7 skills de tripulante em `dist/codex` têm a frase de R7 e não mandam rodar `crew_live.py" start`; as de `dist/antigravity` mantêm o "Header first (F6-6)" (R7)
Proof: run unit | test_build_header_rule_codex ... ok

**C8** - O banner do Codex avisa com a linha de R8 quando falta a confiança de um hook da tripulação e não avisa quando todos estão em `hooks.state` (R8)
Proof: run unit | test_banner_warns_codex_crew_hooks_untrusted ... ok

**C9** - `DECISIONS.md` tem F7-14, o CHANGELOG tem a entrada em `[Unreleased]` e `docs/compatibilidade.md` tem a linha "Cabeçalho por hook" (R9)
Proof: run unit | test_decisions_records_f7_14_codex_hooks ... ok

## Handoff

**Phase:** done
**Size:** MÉDIA
**Git mode:** 3
**Next:** merge do PR em main; o usuário confia os hooks novos no Codex
**Linear:** SC-85
**Integration branch:** not created
**Last integrated:** c90fb7d
**Dispatched:** none
**Settled:** 2026-11-07: 2026-11-07: Codex agora, sondagem dos outros; gatilho: leitura do SKILL.md + $skill; 2026-11-07: 2026-11-07: spec aprovada, issue e sondagem: "Sim"
**Attempts:** none
**Reports:** 2026-11-07: 2026-11-07: SC-85: R1–R9 (f7caf92), gate ticket verde, 409 testes rc 0, fumaça do hook Codex ok; observação do Picard: cabeçalho no Codex mostra CLI/modelo da config, não o real; 2026-11-07: 2026-11-07: Q (antigravity gemini-3.8-flash-high): FAIL, 3 achados (maiúsculas em R1/R2 via member_for; C1/C2 sem caixa nem cabeçalho sem missão); 2026-11-07: 2026-11-07: Q-fix: 3 achados fechados + cabeçalho com CLI real no Codex (0ccee4c, F7-15); 410 testes rc 0
**Breaker:** closed
