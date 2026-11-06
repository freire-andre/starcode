# Fase 5: Hooks nos outros CLIs: Spec

**Approved**: 2026-11-06 - user: "Sim"

**Size**: LARGE
**Risk triggers**: Segurança
**Status**: Approved

## Context

Desde a Fase 1, só o Claude registra os hooks do StarCode (F1-7). No Codex, no Antigravity e no OpenCode os
scripts `git_guard.py`, `secret_scan.py` e `banner.py` vão no `dist/`, mas nenhum CLI os chama. Por isso, nesses
CLIs, nada barra Git perigoso nem segredo em commit ou comentário, e o banner só aparece quando o `engajar` o roda.
A matriz `src/capabilities.yaml` marca `hooks` e `banner_hook` como `unavailable: Fase 5` nos três.

Sucesso: numa sessão real de cada CLI, os comandos perigosos e os segredos são bloqueados, e os comandos normais
do fluxo passam. A matriz e a documentação de compatibilidade refletem o resultado.
Discovery: `.specs/features/fase-5-hooks/context.md`. Issue: SC-12.

## Scope

- Registro de `git_guard.py` e `secret_scan.py` no Codex (`hooks/hooks.json` do plugin), no Antigravity
  (`hooks.json` nativo) e no OpenCode (plugin JS na pasta global).
- Registro de `banner.py` por hook no Codex (SessionStart) e no Antigravity (SessionStart com `injectSteps`).
- `tools/build.py`: geração dos registros por CLI; `tools/install_local.py`: caminhos absolutos e cópia do plugin
  do OpenCode.
- Setup: passos por CLI (trust do Codex, cópia do plugin do OpenCode com confirmação, checagem do Python) e
  detecção do plugin legado `starcode-hello` no Codex.
- Banner: aviso de hooks do Codex sem trust; Picard: parada clara quando o worker do Codex trava por hooks
  pendentes.
- Matriz (`src/capabilities.yaml`), `docs/compatibilidade.md`, `DECISIONS.md` e roteiros de aceite por CLI com
  evidência em `docs/aceite/fase-5.md`.

## Non-Goals

- Banner por hook no OpenCode: não há evento de início de sessão confirmado; o banner continua vindo do `engajar`.
- Mudar o que `git_guard.py` e `secret_scan.py` bloqueiam (regras da Fase 1) além do necessário para ler o
  payload de cada CLI.
- Claude: os hooks dele já existem e não mudam.
- Remover plugins ou hooks de terceiros ou legados sem o usuário: o setup só aponta o comando (D31).
- Usar `--dangerously-bypass-hook-trust` ou qualquer forma de dar trust no lugar do usuário.
- Marketplace privado, instalação a partir do GitHub, CI e release (Fase 6).

## Requirements

Convenções: "comando perigoso" = os casos que o `git_guard.py` já bloqueia no Claude (`push --force`,
`reset --hard`, `branch -D`, `clean -fd`, `checkout -- .`, push fora dos modos 3/4, merge no ramo base sem
autorização); "segredo" = o que o `secret_scan.py` já detecta; "comandos normais do fluxo" = `git status`,
`git add`, `git commit` sem segredo, `git switch`, `git merge --no-ff` no ramo de integração, `orca ...`,
`python ... run_gates.py ...` e a suíte de testes do repo.

Geração (build):

- **R1** - WHEN `tools/build.py` roda THEN the system SHALL gravar `dist/codex/hooks/hooks.json` com `PreToolUse` matcher `Bash` chamando `git_guard.py` e `secret_scan.py`, e `SessionStart` chamando `banner.py --cli codex`, no formato de comando do `hooks.json` do Claude.
- **R2** - WHEN `tools/build.py` roda THEN the system SHALL gravar `dist/antigravity/hooks.json` na raiz, com hooks nomeados: `PreToolUse` matcher `run_command` chamando `git_guard.py --agy` e `secret_scan.py --agy`, e `SessionStart` chamando `banner.py --agy --cli antigravity`.
- **R3** - WHEN `tools/build.py` roda THEN the system SHALL gravar `dist/opencode/plugins/starcode.js`, um objeto puro `{ id, setup }` sem import de pacote, que registra `ctx.tool.hook("execute.before")`.
- **R4** - The system SHALL manter o `dist/` sem caminho absoluto de máquina: os caminhos dos scripts são resolvidos por variável de raiz do plugin ou gravados na cópia instalada (R8).

Comportamento em cada CLI:

- **R5** - WHEN o agente do Codex (com trust dado) ou do Antigravity tenta um comando perigoso ou um commit com segredo THEN the system SHALL bloquear o comando, com o motivo do `git_guard`/`secret_scan` visível na sessão, usando JSON deny com exit 0 (F0-5).
- **R6** - WHEN o plugin do OpenCode recebe `execute.before` da ferramenta `shell` THEN the system SHALL repassar `input.command` ao `git_guard.py` e ao `secret_scan.py` no formato de payload do Claude e, se algum responder deny, lançar um erro cuja mensagem contém o motivo.
- **R7** - WHEN um comando normal do fluxo roda em qualquer um dos três CLIs THEN the system SHALL deixá-lo passar sem bloqueio e sem aviso de hook falho.
- **R8** - WHEN `tools/install_local.py --cli antigravity` ou `--cli opencode` instala o plugin THEN the system SHALL gravar na cópia instalada os caminhos absolutos dos scripts (Antigravity: `hooks.json` em `~/.gemini/config/plugins/starcode`; OpenCode: `~/.config/opencode/plugins/starcode.js`).
- **R9** - IF o hook não consegue rodar o script (Python ausente, payload sem comando, JSON inválido, erro interno) THEN the system SHALL deixar o comando passar e escrever um aviso de uma linha que começa com `StarCode hook:` (fail-open, F1-2).
- **R10** - WHEN o banner roda por hook no Codex ou no Antigravity THEN the system SHALL entregar o mesmo texto do `banner.py --full --text --cli <cli>` como contexto da sessão (Codex: `additionalContext`; Antigravity: `injectSteps` com `ephemeralMessage`).

Setup e instalação:

- **R11** - WHEN o setup roda no Codex THEN the system SHALL mostrar o passo de trust (`/hooks`, aprovar os hooks do `starcode`) e SHALL nunca dar o trust por conta própria.
- **R12** - WHEN o setup roda no OpenCode THEN the system SHALL pedir confirmação antes de copiar o plugin para `~/.config/opencode/plugins/` e SHALL informar o caminho gravado.
- **R13** - IF o `python` não está no PATH do CLI THEN the system SHALL avisar no setup, com a linha `Python não encontrado: os hooks do StarCode não vão rodar neste CLI`.
- **R14** - IF `~/.codex/config.toml` tem o plugin `starcode-hello@starcode` habilitado THEN the system SHALL listar no relatório de concorrentes (`scripts/conflicts.py`) o item e o comando para removê-lo, sem removê-lo.
- **R15** - WHEN `tools/install_local.py` ou o setup roda de novo THEN the system SHALL deixar um único registro de cada hook (sem duplicar entradas em `hooks.json` nem arquivos na pasta de plugins).

Banner, Picard e matriz:

- **R16** - IF o banner roda com `--cli codex` e `~/.codex/config.toml` não tem `trusted_hash` para os hooks do `starcode` (ou eles estão com `enabled = false`) THEN the system SHALL imprimir `Hooks do Codex sem trust: aprove em /hooks`.
- **R17** - IF o `worker-start` de um worker Codex falha com `agent-hooks-review-prompt` THEN the system SHALL parar o despacho e mostrar ao usuário o passo de trust (`/hooks`), sem tentar de novo nem contornar.
- **R18** - WHEN a Fase 5 é aceita THEN the system SHALL marcar em `src/capabilities.yaml` `hooks: ok` no Codex, no Antigravity e no OpenCode, `banner_hook: ok` no Codex e no Antigravity, e manter `banner_hook: unavailable` no OpenCode com o fallback atual; um CLI que reprovar no aceite mantém `unavailable` com o motivo.
- **R19** - WHEN o aceite roda THEN the system SHALL registrar em `docs/aceite/fase-5.md`, por CLI e numa sessão real: versão do CLI, bloqueio de `git push --force`, bloqueio de commit com segredo, banner (Codex e Antigravity) e a lista de comandos normais do fluxo que passaram.

## Data & Contracts

- Codex e Claude: payload de entrada `{"tool_input": {"command": "..."}, "cwd": "..."}`; saída de bloqueio
  `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}`,
  exit 0 (F0-5, provado na Fase 0 com `hello_guard`).
- Antigravity: entrada `toolCall.args.CommandLine`; saída `{"decision":"deny","reason":"..."}` ou
  `{"decision":"allow"}`, exit 0 (F0-6). Banner: `{"injectSteps":[{"ephemeralMessage":"..."}]}`.
- OpenCode V2: `event.input.command` em `execute.before`; bloqueio por `throw new Error(<motivo>)` (ADR-0001). O
  plugin chama `python <script>` por processo filho, com o payload no formato do Claude na entrada padrão.
- Raiz do plugin no Codex: `${CLAUDE_PLUGIN_ROOT}` no comando do hook (usado por plugins de terceiros no Codex
  0.166; **não verificada** para o `starcode`). Se o aceite reprovar, o `install_local` grava o caminho absoluto na
  cópia instalada, como no Antigravity.
- Trust do Codex: chaves `[hooks.state."starcode@starcode:hooks/hooks.json:<evento>:<i>:<j>"]` com
  `trusted_hash` e `enabled` em `~/.codex/config.toml` (formato lido do config local; a conta do hash é do Codex e
  o banner não a confere).

## States

- Hook ativo: bloqueia perigoso, deixa passar normal.
- Hook sem trust (Codex): não roda; o banner avisa (R16) e o despacho de worker para (R17).
- Hook quebrado (sem Python, erro interno): comando passa com aviso `StarCode hook:` (R9).
- CLI reprovado no aceite: extra continua `unavailable` com o motivo (R18).

## Edge Cases

- Comando composto (`git status && git push --force`): o `git_guard` já trata a linha inteira; vale igual nos
  três CLIs.
- Worker da Orca em outro worktree: o hook lê o modo Git do worktree do comando (`cwd` do payload, F1-1).
- Hash do trust muda quando o `hooks.json` do Codex muda numa versão nova: o Codex pede trust de novo e o banner
  avisa (R16).
- OpenCode carregado por `OPENCODE_CONFIG_DIR`: o hook não dispara (F0-3); o setup só instala na pasta global.
- Payload sem comando ou de outra ferramenta (leitura de arquivo): passa sem bloqueio e sem aviso.
- Plugin legado `starcode-hello` instalado junto: os hooks dele seguem rodando até o usuário removê-lo (R14).

## Decisions

| Item | Options | Status |
|---|---|---|
| OpenCode na Fase 5 | bloqueio sem banner · bloqueio + tentar banner · fora da fase | approved - user: "Bloqueio sim, banner não" |
| Prova do aceite | sessão real por CLI (prova o registro, custa sessões) · só testes automatizados (barato, não prova o registro) | approved - user: "Sessão real por CLI" |
| Hooks legados no Codex | detectar e mostrar comando · remover com confirmação · fora da fase | approved - user: "Detecta e mostra o comando" |

Defaults técnicos da Troi (não perguntados; o usuário pode mudar nesta aprovação): banner avisa Codex sem trust
(R16); erro interno do hook não bloqueia (R9); caminho absoluto na cópia instalada do Antigravity e do OpenCode
(R8); testes unitários com payload de cada CLI além da sessão real.

## Open Questions
None.
