# Fase 5: Hooks nos outros CLIs: Context

**Size**: LARGE
**Risk triggers**: Segurança
**Source request**: "vamos para proxima etapa, lembre de atualizar o Linear" (próxima etapa = Fase 5 do PLANO_STARCODE.md, issue SC-12: "Registrar `git_guard.py`, `secret_scan.py` e `banner.py` no Codex (config do usuário + confiança, feito pelo setup), no Antigravity e no OpenCode (V2). Aceite: os testes de bloqueio passam em todo CLI marcado como suportado, sem falso positivo nos comandos normais do fluxo.")

## Problem
Hoje só o Claude tem os hooks do StarCode registrados (F1-7). No Codex, no Antigravity e no OpenCode os scripts vão no `dist/`, mas nada os chama: o `git_guard` não barra Git perigoso, o `secret_scan` não barra segredo em commit/comentário e o banner só aparece quando o engajar o roda. A matriz (`src/capabilities.yaml`) marca `hooks` e `banner_hook` como `unavailable: Fase 5` nesses três CLIs.

## Users
O usuário do StarCode (hoje o dono do repo) rodando a tripulação no Codex, no Antigravity ou no OpenCode, inclusive como worker da Orca.

## Success
- Em cada CLI marcado como suportado, numa sessão real: `git push --force`, um segredo num commit/comentário e o marcador de teste são bloqueados.
- Os comandos normais do fluxo (git add/commit/switch/merge --no-ff no ramo de integração, `orca ...`, `python ... run_gates.py`, testes) passam sem bloqueio.
- `src/capabilities.yaml` e `docs/compatibilidade.md` passam `hooks` (e `banner_hook` onde couber) para `ok`, com o banner deixando de mostrar esses extras como indisponíveis.

## Constraints
- Bloqueio por JSON deny com exit 0, nunca exit 2 (F0-5). Antigravity: `{"decision":"deny"}` via `--agy` (F0-6).
- Codex: hooks vêm do `hooks/hooks.json` do plugin e exigem trust do usuário em `/hooks`; nunca `--dangerously-bypass-hook-trust` (F0-1).
- Antigravity: `hooks.json` nativo na raiz do plugin, matcher `run_command`, comando em `toolCall.args.CommandLine`; banner por `SessionStart` com `injectSteps`/`ephemeralMessage`; caminho absoluto para a cópia instalada (F0-6).
- OpenCode: plugin JS como objeto puro `{ id, setup }`, sem importar `@opencode/plugin`, copiado para `~/.config/opencode/plugins/` (F0-3); ferramenta `shell`, campo `input.command`.
- Escrita em pasta global do usuário só com confirmação no setup.
- Nunca contornar um hook (STARCODE.md, Git).

## Scope Notes
- Dentro: registro de `git_guard.py` e `secret_scan.py` nos três CLIs; `banner.py` no Codex e no Antigravity; passo de trust do Codex no setup; atualização da matriz e da documentação de compatibilidade.
- Dentro: o setup detecta hooks/plugins legados (`starcode-hello` no Codex) e mostra o comando para removê-los, sem remover sozinho.
- Fora: banner por hook no OpenCode (não há evento de início de sessão; segue vindo do engajar).
- Fora: Claude (já tem os hooks desde a Fase 1); Frota, CI e empacotamento (Fase 6+).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| OpenCode na Fase 5 | bloqueio sem banner / bloqueio + tentar banner / fora da fase | bloqueio sim, banner não | 2026-11-06 |
| Prova do aceite | sessão real por CLI / só testes automatizados | sessão real por CLI (como na Fase 4) | 2026-11-06 |
| Hooks legados no Codex (`starcode-hello`) | detectar e mostrar comando / remover com confirmação / fora | detecta e mostra o comando (padrão D31) | 2026-11-06 |
| Codex sem trust dado | banner avisa "hooks não confiáveis" e o Picard checa antes de despachar worker / silêncio | avisar no banner + checagem antes do despacho (`docs/compatibilidade.md`, linha Codex) | default (não perguntado) |
| Hook falha por erro interno (python ausente, JSON inválido) | fail-open com aviso / fail-closed | fail-open com aviso, igual ao Claude hoje (o hook é rede contra acidente, F1-2) | default (não perguntado) |
| Caminho dos scripts no Antigravity | absoluto gerado pelo install_local / variável de raiz | absoluto para a cópia instalada até haver variável confirmada (F0-6) | default (não perguntado) |
| Testes automatizados além da sessão real | só sessão real / sessão real + payloads gravados por CLI | sessão real + testes unitários com payload de cada CLI (regressão barata) | default (não perguntado) |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | Cada adaptador lê o comando do campo do seu CLI (`tool_input.command`, `toolCall.args.CommandLine`, `input.command`); payload sem comando = não bloqueia e não quebra. |
| Failure and partial failure | Erro interno do hook não trava a sessão (fail-open com aviso); bloqueio só por decisão explícita. Instalação parcial (um CLI falha) é reportada por CLI. |
| Retries, idempotency and duplicates | Rodar o setup/install_local de novo não duplica hooks no `hooks.json`, no `config.toml` nem na pasta de plugins do OpenCode. |
| Authorization boundaries and rate limits | Trust do Codex é decisão do usuário; o StarCode só orienta. Rate limits: N/A because os hooks são locais. |
| Concurrency and ordering | Workers da Orca em paralelo leem o modo Git do próprio worktree (F1-1); nada novo além disso. |
| Data lifecycle | N/A because os hooks não guardam dados; só leem `session.json` do worktree. |
| Observability | Bloqueio mostra o motivo no CLI (texto do deny); banner indica hooks ativos/não confiáveis/indisponíveis por CLI. |
| External dependency failure | Python ausente no PATH do CLI: o setup checa e avisa; mudança de formato de hook numa versão nova do CLI aparece no aceite real. |
| State-transition rules | N/A because não há estados novos; o modo Git continua sendo o do `git_mode.py`. |

## Facts Found
- Scripts já com formato Antigravity: `hooks/scripts/git_guard.py`, `secret_scan.py`, `banner.py` (`--agy`).
- Registro do Claude: `dist/claude/hooks/hooks.json` (PreToolUse Bash → git_guard + secret_scan; SessionStart → banner).
- Matriz de extras: `src/capabilities.yaml` (codex/antigravity/opencode com `hooks: unavailable`).
- Evidência da Fase 0 e aceite da Fase 4: `docs/compatibilidade.md` (notas 1, 2, 5, 6, 12, 13).
- Decisões: `DECISIONS.md` F0-1, F0-3, F0-5, F0-6, F1-2, F1-7.
- Instalador local: `tools/install_local.py` (codex, antigravity, opencode); setup sem passos específicos de CLI (`skills/setup/SKILL.md`, seção 6).
- Roteiros de aceite por CLI da fase anterior: `docs/aceite/roteiros-fase-4/`.
- Codex local ainda tem `[plugins."starcode-hello@starcode"]` em `~/.codex/config.toml`.
