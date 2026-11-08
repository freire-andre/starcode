# Cabeçalho e status da tripulação robustos: Spec

**Approved**: 2026-11-07 - user: "sim"
**Status**: Approved

**Size**: MEDIUM
**Risk triggers**: estado compartilhado (várias sessões gravam `.starcode/live/`)
**Linear**: SC-84
**May change**: hooks/scripts/crew_hook.py, scripts/crew_live.py, scripts/statusline.py, hooks/scripts/banner.py, tools/build.py, skills/engajar/SKILL.md, skills/troi/SKILL.md, skills/spock/SKILL.md, skills/data/SKILL.md, skills/laforge/SKILL.md, skills/mccoy/SKILL.md, skills/q/SKILL.md, skills/engajar/references/crew-voice.md, DECISIONS.md, CHANGELOG.md, tests/, dist/

## Context
O cabeçalho do tripulante (F6-6) e o `crew.json` (F6-7) dependem do modelo rodar `crew_live.py start/stop` e repetir o texto. Com o plugin instalado na 1.0.0 nada apareceu, e uma sessão encerrada sem `stop` deixou `picard: 1, spock: 1` presos. Decisões do usuário em 2026-11-07 (Troi): hook mostra sempre; validade de 15 min com pulso por ferramenta; 0 enquanto espera a resposta; só o Claude Code nesta feature. Detalhes e fatos verificados em `context.md`.

## Scope
- Novo `hooks/scripts/crew_hook.py` registrado no Claude Code pelo `tools/build.py`.
- `.starcode/live/sessions.json` ao lado do `crew.json`, que continua plano e passa a ser recalculado.
- Validade das entradas, `statusline.py` com a validade e a contagem do LaForge, aviso de versão no `banner.py`.
- Texto do cabeçalho nas skills da pasta `dist/claude`; decisão F7-12; CHANGELOG.

## Non-Goals
- Hooks equivalentes no Codex, Antigravity e OpenCode (feature seguinte, depois de verificar a API de cada um). Neles o cabeçalho segue pela instrução atual.
- Mudar o formato do `crew.json` ou do `progress.json`.
- Consultar a rede para saber a última versão publicada.

## Requirements
- **R1** - WHEN o Claude Code dispara `PreToolUse` com `tool_name` `Skill` e `tool_input.skill` igual a `starcode:<skill>` ou `<skill>` de um tripulante do `crew.json` do plugin, OR dispara `UserPromptExpansion` com `command_name` `starcode:<skill>` THEN `crew_hook.py` SHALL gravar em `sessions.json` a entrada `{"<session_id>": {"member": "<key>", "active": true, "source": "hook", "at": "<iso>"}}`, recalcular o `crew.json` e imprimir `{"systemMessage": "<cabeçalho>"}` sem nenhum campo de decisão de permissão.
- **R2** - The system SHALL montar o cabeçalho do hook em texto puro (sem markdown, cuja renderização no `systemMessage` não foi verificada): linha `━` ×36, `<emoji> <NOME> ASSUME A PONTE`, `<papel> · <cli> · <modelo>`, `Missão: <texto>` (de `tool_input.args`, cortado em 80 caracteres, omitida quando vazia) e o bordão entre aspas, fechando com a linha `━`.
- **R3** - WHEN o Claude Code dispara `PostToolUse` THEN `crew_hook.py` SHALL atualizar só o `at` da entrada da sessão, se existir, sem imprimir nada.
- **R4** - WHEN o Claude Code dispara `Stop` THEN `crew_hook.py` SHALL marcar a entrada da sessão com `"active": false`; WHEN dispara `UserPromptSubmit` e a sessão tem entrada THEN SHALL marcar `"active": true` e renovar `at`. Nenhum dos dois imprime algo.
- **R5** - WHEN o Claude Code dispara `SessionEnd` THEN `crew_hook.py` SHALL remover a entrada da sessão e recalcular o `crew.json`.
- **R6** - The system SHALL recalcular o `crew.json` a cada escrita em `sessions.json`: cada tripulante vale 1 se tiver uma entrada ativa e válida, senão 0; `laforge` vale o maior entre o número de entradas ativas e válidas do LaForge e o valor gravado por `crew_live.py set laforge <n>`. Uma entrada `source: hook` vale por 15 min desde `at`; uma entrada `source: cli` (gravada por `crew_live.py start` ou `set`) vale por 60 min. Entradas vencidas SHALL ser removidas na escrita seguinte.
- **R7** - IF `crew_hook.py` recebe JSON inválido, está fora de um repositório Git, ou falha ao ler ou gravar os arquivos THEN SHALL sair com código 0 sem imprimir nada.
- **R8** - The system SHALL registrar em `dist/claude/hooks/hooks.json` (gerado por `tools/build.py`) o `crew_hook.py` com timeout 10 s em `PreToolUse` matcher `Skill`, `UserPromptExpansion` matcher `starcode:.*`, `PostToolUse` matcher `*`, `Stop`, `UserPromptSubmit` e `SessionEnd`, mantendo os hooks atuais. Os `hooks.json` das outras pastas do `dist/` SHALL ficar sem o `crew_hook.py`.
- **R9** - The system SHALL trocar, só nas skills de `dist/claude`, a instrução "Header first (F6-6)" de cada tripulante pela frase `In Claude Code the StarCode hook already showed your header and marks you as working: do not run crew_live.py start/stop and do not repeat the header.`; as outras pastas do `dist/` mantêm a instrução atual.
- **R10** - The system SHALL fazer o `statusline.py` aplicar a validade de R6 lendo `sessions.json` sem gravar nada, e mostrar o LaForge com contagem maior que 1 como `🔧 LaForge ×<n>`.
- **R11** - WHEN o repositório aberto é o código-fonte do StarCode (tem `VERSION` e `dist/claude/.claude-plugin/plugin.json`) e a versão do plugin em execução é menor que o `VERSION` do repositório THEN `banner.py` SHALL incluir a linha `⚠️ plugin StarCode instalado <x>, repositório <y>: atualize o plugin e abra uma nova sessão`, em todos os CLIs.
- **R12** - The system SHALL registrar em `DECISIONS.md` a decisão F7-12 com R1–R11 e acrescentar a entrada em `## [Unreleased]` do `CHANGELOG.md`.

## Edge Cases
- **Skill que não é de tripulante** (`starcode:setup`, outra skill qualquer): nenhum registro e nenhuma saída.
- **Dois tripulantes na mesma sessão** (Picard chama Troi): a entrada da sessão passa para o último que assumiu.
- **`PostToolUse` sem entrada da sessão:** nada muda.
- **`crew_live.py reset`:** apaga também `sessions.json`.
- **Plugin mais novo que o repositório:** sem aviso.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `PreToolUse` de `Skill` `starcode:spock` grava a sessão ativa, põe `spock: 1` no `crew.json` e imprime só `systemMessage`; `UserPromptExpansion` de `starcode:engajar` faz o mesmo para o Picard; `starcode:setup` não grava nem imprime (R1)
Proof: run unit | test_crew_hook_skill_marks_member_and_shows_header ... ok

**C2** - O cabeçalho tem a linha `━`×36, `🖖 SPOCK ASSUME A PONTE`, papel, CLI e modelo, `Missão:` cortada em 80 caracteres, o bordão, e nenhum `>`, `#` ou `**` (R2)
Proof: run unit | test_crew_hook_header_plain_text ... ok

**C3** - `PostToolUse` renova só o `at` da sessão e não imprime nada; sem entrada, nada muda (R3)
Proof: run unit | test_crew_hook_post_tool_use_pulses ... ok

**C4** - `Stop` deixa o tripulante em 0 e `UserPromptSubmit` volta para 1, sem saída (R4)
Proof: run unit | test_crew_hook_stop_and_prompt_toggle ... ok

**C5** - `SessionEnd` remove a sessão e o tripulante volta a 0 (R5)
Proof: run unit | test_crew_hook_session_end_clears ... ok

**C6** - Entrada `hook` de 16 min e `cli` de 61 min valem 0 e somem na escrita seguinte; `cli` de 59 min vale 1; duas sessões LaForge e `set laforge 1` dão `laforge: 2` (R6)
Proof: run unit | test_crew_live_expiry_and_laforge_count ... ok

**C7** - JSON inválido, pasta sem Git e arquivo ilegível saem com 0 e saída vazia (R7)
Proof: run unit | test_crew_hook_never_breaks ... ok

**C8** - `dist/claude/hooks/hooks.json` tem os 6 eventos com o `crew_hook.py` e timeout 10, mantém `git_guard`, `secret_scan` e `banner`; `dist/codex`, `dist/antigravity` e `dist/opencode` não citam `crew_hook` (R8)
Proof: run unit | test_build_registers_crew_hook_only_in_claude ... ok

**C9** - As 7 skills de tripulante em `dist/claude` têm a frase de R9 e não mandam rodar `crew_live.py" start`; as de `dist/codex` mantêm o "Header first (F6-6)" (R9)
Proof: run unit | test_build_header_rule_per_cli ... ok

**C10** - A statusline trata como 0 uma sessão vencida sem gravar arquivo, e mostra `🔧 LaForge ×2` (R10)
Proof: run unit | test_statusline_expiry_and_laforge_count ... ok

**C11** - O banner avisa com a linha de R11 quando o plugin é 1.0.0 e o repositório 1.1.0, e não avisa com versões iguais, plugin mais novo ou repositório que não é o StarCode (R11)
Proof: run unit | test_banner_warns_outdated_plugin ... ok

**C12** - `DECISIONS.md` tem F7-12 e o `CHANGELOG.md` tem a entrada em `[Unreleased]` (R12)
Proof: run unit | test_decisions_records_f7_12_crew_hook ... ok

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** gate done, push e PR
**Linear:** SC-84
**Integration branch:** not created
**Last integrated:** c5b759e
**Dispatched:** none
**Settled:** 2026-11-07: 2026-11-07: Troi: hook mostra sempre; 15 min + pulso; 0 enquanto espera; Claude agora, outros depois; 2026-11-07: 2026-11-07: spec aprovada e issue criada: "sim"
**Attempts:** none
**Reports:** 2026-11-07: 2026-11-07: SC-84: R1–R12 (e57d4b0), gate ticket verde, 397 testes rc 0, hook de fumaça ok; 2026-11-07: 2026-11-07: Q (codex gpt-6-luna): FAIL, 2 achados (R6 aceita at futuro e source desconhecida; C2 frouxo); 2026-11-07: 2026-11-07: Q-fix: 2 achados fechados (fd18f19); 397 testes rc 0
**Breaker:** closed
