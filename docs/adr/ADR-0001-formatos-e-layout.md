# ADR-0001: Formatos de plugin e layout de `dist/`

- Status: aceito (Fase 0, 2026-11-03; revisado no mesmo dia: Gemini CLI substituído pelo Antigravity CLI, D32)
- Evidência: `docs/compatibilidade.md`, `docs/cli-baseline/`

## Contexto

O StarCode tem uma fonte única e precisa gerar um adaptador por CLI (D8). A Fase 0 testou um plugin mínimo no layout real para confirmar os formatos antes de escrever o `tools/build.py`.

## Decisão

Uma pasta por CLI em `dist/`, gerada pelo build. Nenhum arquivo é compartilhado entre pastas.

| CLI | Manifesto | Skills | Hooks | Agentes | Distribuição |
|---|---|---|---|---|---|
| Claude | `dist/claude/.claude-plugin/plugin.json` (+ `icon.png`, `author`) | `skills/<nome>/SKILL.md` | `hooks/hooks.json`, `${CLAUDE_PLUGIN_ROOT}` | `agents/*.md` com `model:` | `.claude-plugin/marketplace.json` na raiz, `source: ./dist/claude` |
| Codex | `dist/codex/.codex-plugin/plugin.json` (`interface`) | `skills/` | `hooks/hooks.json` do plugin (exige trust) | — | `.agents/plugins/marketplace.json`, `source: {source: local, path: ./dist/codex}` (tem prioridade sobre o do Claude) |
| Antigravity | `dist/antigravity/plugin.json` na raiz (`author` é string) | `skills/` | `hooks.json` na raiz, hooks nomeados: `PreToolUse` matcher `run_command` (comando em `toolCall.args.CommandLine`, bloqueio `{"decision":"deny"}`), `SessionStart` com `injectSteps: [{ephemeralMessage}]` | `agents/*.md` (`model: flash\|pro`) | `agy plugin install <pasta>` (também converte plugins do Claude, mas mantém o hook do Claude, que não dispara) |
| OpenCode | — | `skills/`, registradas no `opencode.json` com caminho absoluto | `plugins/starcode.ts`, objeto puro `{id, setup}` sem import, copiado para `~/.config/opencode/plugins/` | `agents/*.md` com `mode: subagent` | setup copia os arquivos |

Regras de formato:

- Bloqueio por JSON com exit 0: `hookSpecificOutput.permissionDecision: "deny"` (Claude e Codex; F0-5) e `{"decision":"deny"}` (Antigravity). No OpenCode, o bloqueio é um `throw` em `execute.before`. Nunca exit 2 (o PowerShell o reduz a 1 no Codex).
- O banner usa `hookSpecificOutput.additionalContext` no `SessionStart` (Claude; Codex quando houver trust). No Antigravity, `injectSteps` com `ephemeralMessage` (`systemMessage` não chegou ao modelo no teste).
- Uma skill nunca proíbe o shell, porque o Codex lê skills pelo shell.
- `claude plugin validate dist/claude --strict` faz parte da CI.

## Consequências

- O plano dizia que o Codex 0.166 removeu os hooks de plugin. Isso não se confirmou: os hooks vêm do plugin, mas exigem trust do usuário. O setup orienta a aprovação e o despacho de workers do Codex verifica antes se há hooks pendentes.
- O caminho dos scripts de hook no Codex ainda não tem variável de raiz confirmada. O teste usou caminho absoluto. Fica para a Fase 4.
- O modelo efetivo não vem no recibo da Orca. Ver a atualização da D17 em `DECISIONS.md`.
