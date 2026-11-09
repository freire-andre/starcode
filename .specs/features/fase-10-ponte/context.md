# Fase 10 — Painel Orca "Ponte": Context

**Size**: LARGE
**Risk triggers**: none
**Source request**: "vamos para proxima fase, lembre de atualizar o linear" (Fase 10 do PLANO_STARCODE.md: "Plugin da Orca (`orca-plugin-authoring`): tripulação, modo Git, issue do worktree, fase SDD, workers da Frota e atalhos. Aceite: o painel reflete o estado real do worktree ativo e é atualizado quando um evento de agente acontece.")

## Problem
O estado do StarCode (quem da tripulação está trabalhando, modo Git, fase da feature, progresso, workers da Frota) fica espalhado em arquivos (`.starcode/live/*.json`, `<git-dir>/starcode/session.json`, `tasks.md ## Handoff`) e só aparece no banner, quando uma sessão começa. Dentro da Orca não há uma visão contínua desse estado para o worktree em foco.

## Users
O dono do repositório (único usuário do StarCode), trabalhando na Orca IDE com vários worktrees e workers.

## Success
- Um painel lateral da Orca, "Ponte", mostra para o worktree em foco: tripulação ativa, modo Git, issue do Linear (ID, título, estado), fase SDD e progresso da feature, workers da Frota e atalhos.
- O painel muda quando o worktree em foco muda (`workspace.changed`) e quando um agente muda de estado (`agent.status.changed`), sem o usuário recarregar.
- Um item na barra de status resume o estado (ex.: "🖖 fase-10-ponte · execute · modo 3").

## Constraints
- Orca 1.4.255; API de plugins 1.4 (`"pluginApi": 1`). Componentes e entradas sem build pedem `engines.orca >=1.4.246`.
- Ler arquivos do worktree exige um worker Node (`execution: trusted-worker`): o painel não tem acesso a arquivos nem à rede.
- Painel não digita em terminal; só o worker age (`agent.launch`, `editor.open`).
- Toda capability nova pede aprovação do usuário na Orca (`approval_required`, exit 3); o agente nunca aprova por ele.
- O plugin só lê o estado do StarCode; nunca escreve em `.specs/`, `.starcode/live/` nem no Handoff (D28).
- Sem publicação no catálogo público da Orca (repo privado).

## Scope Notes
- Entra (usuário, 2026-11-09): plugin **neste repo, com instalação local** (gerado em `dist/` e instalado pelo `install_local.py`).
- Entra: atalhos **abrir spec/tasks/Handoff no editor**, **abrir a issue no Linear**, **iniciar o Picard** (agente com o prompt de engajar) e **atualizar agora**.
- Entra: **item na barra de status**.
- Entra: issue com **ID, título e estado**, obtidos pelo worker via `orca linear issue --current`, com cache.
- Fora: publicação no catálogo da Orca; verificação de telas (Fase 11); qualquer escrita de estado pelo plugin.

- Entra (usuário, 2026-11-09, depois da primeira aprovação da spec): "tem dois projetos que colocam vida pra demonstrar os agentes trabalhando [...] verifique se da pra colocar algo. Monte a analise ajuste o plano caso necessario" (Pixel Agents, Habblaud, Habblaude). Análise: `analise-referencias.md`.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Distribuição | neste repo com instalação local / repo próprio publicado | neste repo, instalação local | 2026-11-09 |
| Atalhos | abrir arquivos / abrir issue / iniciar Picard / atualizar | os quatro | 2026-11-09 |
| Barra de status | sim / não | sim | 2026-11-09 |
| Issue do worktree | ID+título+estado via `orca linear` / só ID | ID, título e estado | 2026-11-09 |
| Feature exibida quando há várias no worktree | a de `**Phase:**` não `done` mais recente / todas | a mais recente não `done`; se todas `done`, a última atualizada, marcada como concluída — default (não perguntado) |
| Worktree sem StarCode (sem `.starcode/` nem `.specs/`) | painel vazio com aviso / esconder | estado vazio com a frase "StarCode não configurado neste worktree" — default (não perguntado) |
| Workers da Frota | da Orca (`agents.list`) / do Handoff (`--dispatched`) | os dois: tickets despachados do Handoff, com o estado do agente da Orca quando o terminal casar — default (não perguntado) |
| Prompt do atalho "Iniciar o Picard" | agente fixo / agente do `crew.yaml` do Picard | agente e modelo do Picard pela precedência D17 (config do usuário > `crew.yaml`) — default (não perguntado) |
| Idioma do painel | PT-BR / segue `outputLanguage` | PT-BR (D16) — default (não perguntado) |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | JSON inválido, ausente ou com chave desconhecida em qualquer fonte vira "indisponível" naquela seção, sem derrubar o painel; arquivos maiores que 1 MiB são ignorados. |
| Failure and partial failure | Cada seção falha sozinha (ex.: `orca linear` fora do ar mostra só o ID do ramo/Handoff com "Linear indisponível"); o erro aparece em uma linha, nunca um stack trace. |
| Retries, idempotency and duplicates | Leitura é idempotente; eventos repetidos só redesenham. A chamada ao Linear não é repetida em laço: no máximo uma por evento, com cache de 60 s por issue. Atalho "Iniciar o Picard" com clique duplo não abre dois agentes (trava enquanto o lançamento não volta). |
| Authorization boundaries and rate limits | Só as capabilities dos atalhos escolhidos (`workspace:read`, `agent:read`, `workspace:write`, `agent:launch`, `storage:own`); o worker roda só `orca linear issue` como processo externo; rate limit do Linear coberto pelo cache acima. |
| Concurrency and ordering | Eventos em rajada (vários workers) são agrupados (debounce curto) e o último estado vence; uma leitura em andamento descartada se o worktree em foco mudar no meio. |
| Data lifecycle | N/A because o plugin não guarda dados próprios além do cache em memória/`storage` da Orca, descartável. |
| Observability | O painel mostra a hora da última atualização (`RelativeTime`) e a fonte de cada seção; erros do worker vão para o log do plugin (`dev watch`). |
| External dependency failure | Orca sem `orca` no PATH, Linear desconectado ou `session.json` ausente: seção marcada como indisponível com o motivo. |
| State-transition rules | N/A because o painel só exibe; transições de fase e de issue são do Picard. Sessões vencidas seguem a validade de `sessions.json` (F7-12: 15 min hook / 60 min cli). |

## Facts Found
- Skill da Orca `orca-plugin-authoring` (Orca 1.4.255): painel de componentes `.tsx` (`sandboxed-ui`) + worker `trusted-worker` com `main`; eventos `workspace.changed` (desde 1.4.246) e `agent.status.changed`; host do painel tem `plugin.request` para pedir dados ao worker (`orca.panels.handle`); `statusBar.update` só no worker; `editor.open`/`agent.launch` pedem `workspace:write`/`agent:launch`; ciclo `orca plugin create/dev watch/test/check/validate/inspect`.
- `workspace.readContext` devolve branch, nome e terminais, mas **não o caminho**; `workspace.list` (worker) devolve `path` e `branch` de cada workspace — o caminho do worktree em foco sai do cruzamento dos dois.
- Estado ao vivo: `.starcode/live/crew.json` (plano, contagem por tripulante, F6-7/R18), `sessions.json` (F7-12, validade 15/60 min), `progress.json` (F6-8, por feature: done/total/percent/phase/updatedAt) — `.starcode/live/` fica no worktree principal (F6-7).
- Modo Git: `<git-dir>/starcode/session.json` por worktree (F1-1), gravado por `scripts/git_mode.py`.
- Fase SDD e workers despachados: `tasks.md ## Handoff` (`**Phase:**`, `--dispatched`, `--integration-branch`), escrito só pelo `scripts/handoff.py` (D28).
- Build e instalação: `tools/build.py` gera `dist/<cli>`; `tools/install_local.py` instala Codex/Antigravity/OpenCode a partir de `dist/` (o plugin da Orca entra como mais um alvo).
- Linear: `orca linear issue [--current] --json` existe no Orca 1.4.255.
- Exemplos oficiais em `examples/plugins/` de github.com/stablyai/orca (`hello-orca`, `hello-tsx`, `worker-panel`).
