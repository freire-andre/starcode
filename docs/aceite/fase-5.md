# Aceite da Fase 5 (SC-52): hooks no Codex, Antigravity e OpenCode

Roteiros: `docs/aceite/roteiros-fase-5/<cli>.md`. Cada CLI tem a sua seção abaixo, preenchida numa sessão real.

## Codex

**Resultado**: aprovado

- **Versão**: codex-cli 0.166.0 (sessões reais via `codex exec` em clone de teste do sandbox, ramo `freire-andre/f5-codex-aceite`, `origin` apontando para um bare local descartável; `starcode` instalado pelo `install_local` a partir do worktree `f5-integ`). `${CLAUDE_PLUGIN_ROOT}` foi expandido: os hooks do `starcode` rodaram.
- **Trust (`/hooks`)**: feito pelo usuário antes da sessão: `~/.codex/config.toml` tem `trusted_hash` para `starcode@starcode:hooks/hooks.json:pre_tool_use:0:0`, `:pre_tool_use:0:1` e `:session_start:0:0`. O agente não deu o trust e nenhuma flag de bypass foi usada. O plugin legado `starcode-hello` já tinha sido removido pelo usuário e não apareceu.
- **Bloqueio de push forçado**: `git push --force origin main` bloqueado antes de executar: `Command blocked by PreToolUse hook: StarCode bloqueou `git push` forçado (--force, -f, --force-with-lease, +refspec ou --mirror). Reescrever o histórico remoto é proibido no fluxo. Se o usuário pediu isso de forma explícita, peça que ele mesmo rode o comando no terminal.` O bare de teste continuou em `9d1d904`.
- **Bloqueio de segredo**: com `segredo.txt` (valor de teste, montado em tempo de execução) já staged, `git commit -m "chore: teste"` bloqueado: `Command blocked by PreToolUse hook: StarCode bloqueou o comando: possível segredo encontrado.` Nenhum commit foi criado. O `git add` foi feito fora do Codex, porque o sandbox `workspace-write` do Codex nega escrita em `.git` (`index.lock: Permission denied`); o `git add` sozinho não dispara o `secret_scan`, que só age no commit.
- **Comandos normais**: passaram sem bloqueio e sem aviso `StarCode hook:`: `git status`, `git add .`, `git commit -m "feat: x"` (commit `5786718`), `git switch -c feature/x`, `git merge --no-ff feature/x` (`Already up to date`), `orca linear issue SC-1 --json`, `python scripts/gates/run_gates.py ticket x`, `python -m unittest discover -s tests -v` (3 testes ok). Sessão com `-s danger-full-access` só para o Codex poder gravar no `.git`; os hooks rodam antes do sandbox.
- **Banner**: sessão nova, o contexto inicial trouxe o banner via `additionalContext`, terminando em `CLI: codex` (sem o aviso `Hooks do Codex sem trust`, pois o trust estava dado). Texto: `StarCode · Diário do Capitão` / `Repositório: f5-codex-aceite · ramo freire-andre/f5-codex-aceite · modo Git: não definido (o Picard pergunta ao engajar)` / `Config do usuário: ✅ válido` / `Config do repositório: ausente (rode /starcode:setup)`.
- **Observações**: a 1ª tentativa foi recusada pelo próprio modelo, sem passar pelo hook, por não ter contexto de teste; o prompt passou a declarar o teste autorizado. Avisos alheios vistos e não corrigidos: `hooks.json` do plugin `fala` com campo `modules` desconhecido; `features.experimental_use_rmcp_client` ignorado; MCP `linear`/`linear-server` sem login.

## Antigravity

**Resultado**: pendente

- **Versão**: pendente
- **Contagem de hooks**: pendente
- **Bloqueio de push forçado**: pendente
- **Bloqueio de segredo**: pendente
- **Comandos normais**: pendente
- **Banner**: pendente

## OpenCode

**Resultado**: pendente

- **Versão**: pendente
- **Plugin na pasta global**: pendente
- **Bloqueio de push forçado**: pendente
- **Bloqueio de segredo**: pendente
- **Comandos normais**: pendente
- **Banner**: n/a (sem banner por hook, F5-3)
