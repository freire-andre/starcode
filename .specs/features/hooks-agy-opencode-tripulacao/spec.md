# Hooks da tripulação no Antigravity e no OpenCode: Spec

**Approved**: 2026-11-08 - user: "sim"
**Status**: Approved

**Size**: MEDIUM
**Risk triggers**: estado compartilhado (`.starcode/live/` gravado por sessões de CLIs diferentes)
**Linear**: SC-86
**May change**: hooks/scripts/crew_hook.py, hooks/opencode/starcode.js, tools/build.py, DECISIONS.md, CHANGELOG.md, docs/compatibilidade.md, tests/, dist/

## Context
A F7-12 (SC-84) pôs o `crew_hook.py` no Claude Code e a F7-14/F7-15 (SC-85) no Codex. No Antigravity e no OpenCode o cabeçalho ainda depende do modelo rodar `crew_live.py start`. Escolhas do usuário em 2026-11-08: Antigravity "Hook injeta e o modelo repete"; OpenCode "Mensagem sintética + modelo repete".

Fatos da sondagem de 2026-11-08 (`~/.starcode/notas/sonda-hooks-agy-opencode-2026-11-08.md`):
- **agy 1.5.2**:
  - Eventos válidos: `SessionStart`, `PreInvocation`, `PostInvocation`, `Stop`, `PreToolUse` e `PostToolUse`. Não há `SessionEnd` nem `UserPromptSubmit`.
  - A entrada traz `conversationId`, `lastUserInput`, `modelName`, `workspacePaths` e `invocationNum`, sem `cwd`.
  - A leitura da skill aparece como `read_file`/`view_file` (`toolCall.args.Path`) ou `run_command` (`toolCall.args.CommandLine`).
  - O `Stop` traz `fullyIdle: true`.
  - A saída aceita só `injectSteps: [{"ephemeralMessage": ...}]` (testado em `SessionStart` e `PostInvocation`), que só o modelo vê.
  - `systemMessage`, `statusMessage` e `displayMessage` são recusados, e no `PreToolUse` um campo recusado bloqueia a ferramenta.
  - `{"decision": "allow"}` libera a ferramenta sem perguntar ao usuário. O efeito de `{}` na liberação da ferramenta não foi verificado.
- **OpenCode 2.2.3** (plugin V2 `{id, setup(ctx)}`):
  - `ctx.tool.hook("execute.before"/"execute.after")` traz `tool` e `input`. Na skill, `tool === "skill"` e o nome vem em `input.id`.
  - `ctx.session.hook("prompt")` traz `{sessionID, prompt: {text}}`, e `ctx.session.hook("experimental.idle")` marca o fim do turno.
  - `ctx.session.synthetic({sessionID, text, resume: false})` insere uma mensagem.
  - A pasta vem de `ctx.location.directory`. Não há evento de fim de processo.
  - Um `await` no registro de hooks travou uma execução da sondagem.

## Scope
- Modo `--cli antigravity` e `--cli opencode` no `crew_hook.py`.
- Grupo de hooks da tripulação no `hooks.json` do `dist/antigravity`, gerado pelo `tools/build.py`.
- Hooks da tripulação no plugin `hooks/opencode/starcode.js`.
- Regra do cabeçalho nas skills do `dist/antigravity` e do `dist/opencode`.
- Decisão F7-16, CHANGELOG e `docs/compatibilidade.md`.

## Non-Goals
- Mostrar o cabeçalho na tela sem passar pelo modelo (nenhum dos dois CLIs aceita mensagem de hook para o usuário).
- Mudar o formato de `crew.json` ou `sessions.json`.
- Mudar os hooks do Claude e do Codex.

## Requirements
- **R1** - WHEN o agy dispara `PreToolUse` com `toolCall.name` `read_file`, `view_file` ou `run_command` e `toolCall.args.Path` ou `toolCall.args.CommandLine` casa com o `SKILL.md` de um tripulante (mesma regra de caminho do Codex, R1 da F7-14) THEN `crew_hook.py --cli antigravity` SHALL gravar a sessão `conversationId` como no Claude (`source: hook`), usando `workspacePaths[0]` como pasta. Também SHALL recalcular o `crew.json` e guardar o cabeçalho pendente em `.starcode/live/pending.json` (`{"<conversationId>": "<cabeçalho>"}`).
- **R2** - The system SHALL fazer `crew_hook.py --cli antigravity` nunca imprimir campo de decisão (`decision`, `allow`, `ask`, `deny`) nem `systemMessage`, `statusMessage` ou `displayMessage`, em qualquer evento. No `PreToolUse` a saída SHALL ser vazia.
- **R3** - WHEN o agy dispara `PostInvocation` e `pending.json` tem cabeçalho para o `conversationId` THEN `crew_hook.py --cli antigravity` SHALL imprimir `{"injectSteps": [{"ephemeralMessage": "Comece sua próxima resposta ao usuário com este cabeçalho, sem mudar nada:\n<cabeçalho>"}]}` e remover a pendência.
- **R4** - The system SHALL montar o cabeçalho do agy e do OpenCode como o do Codex (`plain_header`), com `antigravity · <modelName>` ou `opencode · <modelo do tripulante na config, ou "padrão do CLI">` na linha do papel.
- **R5** - The system SHALL fazer, no modo antigravity, `PostToolUse` renovar `at`, `PreInvocation` com `invocationNum` 0 marcar `"active": true` e `Stop` marcar `"active": false`. Nenhum desses eventos imprime algo, e a sessão sem `SessionEnd` vence pela validade de 15 min (F7-12, R6).
- **R6** - WHEN `crew_hook.py --cli opencode` recebe `{"event": "skill", "session_id", "skill", "cwd", "mission"}` de um tripulante THEN SHALL gravar a sessão e imprimir `{"header": "<cabeçalho>"}`. Os eventos `pulse`, `prompt` e `idle` SHALL renovar `at`, marcar ativo e marcar inativo, sem saída.
- **R7** - The system SHALL fazer `hooks/opencode/starcode.js` registrar, sem `await` no registro, os hooks `execute.before` (`tool === "skill"` → evento `skill` com `input.id`), `execute.after` (`pulse`), `session.hook("prompt")` (`prompt`) e `session.hook("experimental.idle")` (`idle`). Quando vier `header`, o plugin SHALL chamar `ctx.session.synthetic({sessionID, text: "Comece sua próxima resposta ao usuário com este cabeçalho, sem mudar nada:\n" + header, resume: false})`. Qualquer erro SHALL ser engolido, sem bloquear a ferramenta nem o turno, e os guardas atuais do `execute.before` SHALL ser mantidos.
- **R8** - The system SHALL registrar no `hooks.json` do `dist/antigravity` o grupo `starcode-crew` com `crew_hook.py --cli antigravity`, timeout 10 s, em `PreToolUse` com matcher `read_file|view_file|run_command`, `PostToolUse`, `PreInvocation`, `PostInvocation` e `Stop`. Os grupos `starcode-guard` e `starcode-banner` SHALL ser mantidos.
- **R9** - The system SHALL trocar, nas skills de tripulante do `dist/antigravity` e do `dist/opencode`, a instrução "Header first (F6-6)" pela frase `In <Antigravity|OpenCode> the StarCode hook marks you as working and sends you your header: start your next reply with it exactly as sent, and do not run crew_live.py start/stop.`
- **R10** - IF a entrada é inválida, está fora de um repositório Git, ou a leitura ou gravação falha THEN `crew_hook.py` nos modos antigravity e opencode SHALL sair com código 0 sem imprimir nada.
- **R11** - The system SHALL registrar a decisão F7-16 em `DECISIONS.md` e a entrada em `## [Unreleased]` do `CHANGELOG.md`. Na linha "Cabeçalho por hook" do `docs/compatibilidade.md`, SHALL pôr Antigravity e OpenCode como "✅ (o modelo repete)".

## Edge Cases
- **Mesmo tripulante na mesma sessão:** nova leitura do `SKILL.md` só renova `at` e não gera pendência nova (como R4 da F7-14).
- **`PostInvocation` sem pendência:** saída vazia.
- **Modelo que não repete o cabeçalho:** o status em `crew.json` fica certo mesmo assim; o cabeçalho na tela depende do modelo (limite aceito pelo usuário).
- **Skill que não é de tripulante no OpenCode** (`input.id` desconhecido): sem gravação e sem mensagem sintética.
- **Python ausente no OpenCode:** `spawnSync` falha, o plugin engole o erro e segue.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `PreToolUse` agy `read_file` com `Path` `C:\x\starcode\skills\troi\SKILL.md` grava a sessão, põe `troi: 1`, cria a pendência e não imprime nada; `run_command` com `Get-Content ...\starcode\skills\spock\SKILL.md` faz o mesmo; `view_file` de outro plugin não faz nada (R1, R2)
Proof: run unit | test_crew_hook_agy_skill_read_marks_pending ... ok

**C2** - Em nenhum evento do modo antigravity a saída tem `decision`, `systemMessage`, `statusMessage` ou `displayMessage` (R2)
Proof: run unit | test_crew_hook_agy_never_decides ... ok

**C3** - `PostInvocation` com pendência imprime só `injectSteps` com a ordem e o cabeçalho (`antigravity · <modelName>`) e limpa a pendência; um segundo `PostInvocation` não imprime nada (R3, R4)
Proof: run unit | test_crew_hook_agy_post_invocation_injects_header ... ok

**C4** - No modo antigravity, `PostToolUse` renova `at`, `PreInvocation` 0 ativa, `PreInvocation` 1 não muda nada e `Stop` desativa, sem saída (R5)
Proof: run unit | test_crew_hook_agy_lifecycle ... ok

**C5** - O modo opencode com `skill` `starcode:laforge` grava e imprime `header` com `opencode ·`; `pulse`, `prompt` e `idle` mudam a sessão sem saída; skill desconhecida não faz nada (R4, R6)
Proof: run unit | test_crew_hook_opencode_events ... ok

**C6** - `dist/opencode/plugins/starcode.js` registra os 4 hooks sem `await` no registro, chama `ctx.session.synthetic` com `resume: false`, tem `try/catch` em cada hook e mantém os guardas (R7)
Proof: run unit | test_opencode_plugin_registers_crew_hooks ... ok

**C7** - O `hooks.json` do `dist/antigravity` tem `starcode-crew` com os 5 eventos, timeout 10 e o matcher de R8, e mantém guard e banner (R8)
Proof: run unit | test_build_registers_crew_hook_in_antigravity ... ok

**C8** - As 7 skills de tripulante do `dist/antigravity` e do `dist/opencode` têm a frase de R9 com o nome do CLI e não mandam rodar `crew_live.py" start` (R9)
Proof: run unit | test_build_header_rule_agy_opencode ... ok

**C9** - Entrada inválida, pasta sem Git e falha de gravação saem com 0 e saída vazia nos modos antigravity e opencode (R10)
Proof: run unit | test_crew_hook_agy_opencode_never_break ... ok

**C10** - `DECISIONS.md` tem F7-16, o CHANGELOG tem a entrada e `docs/compatibilidade.md` mostra Antigravity e OpenCode com "✅ (o modelo repete)" (R11)
Proof: run unit | test_decisions_records_f7_16_agy_opencode_hooks ... ok

## Handoff

**Phase:** execute
**Size:** MÉDIA
**Git mode:** 3
**Next:** esperar worker_done da correção
**Linear:** SC-86
**Integration branch:** not created
**Last integrated:** bd5cc2a
**Dispatched:** SC-86 fix --event → claude claude-sonnet-5-5 (ctx_4f0dca32b584)
**Settled:** 2026-11-08: 2026-11-08: Antigravity: hook injeta e o modelo repete; OpenCode: mensagem sintética + modelo repete; 2026-11-08: 2026-11-08: spec aprovada e issue criada: "sim"
**Attempts:** none
**Reports:** 2026-11-08: 2026-11-08: SC-86: R1–R11 (bd5cc2a), gate ticket verde, 420 testes rc 0; Picard: agy não manda nome do evento na entrada, falta --event no comando
**Breaker:** closed
