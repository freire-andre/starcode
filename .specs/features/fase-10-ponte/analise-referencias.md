# Fase 10 — Análise das referências visuais (Pixel Agents, Habblaud, Habblaude)

Data: 2026-11-09. Pedido do usuário: "tem dois projetos que colocam vida pra demonstrar os agentes trabalhando [...] verifique se da pra colocar algo. Monte a analise ajuste o plano caso necessario".

## O que cada um é

| | Pixel Agents (`pixel-agents-hq/pixel-agents`) | Habblaud (`marmottajr/habblaud`) | Habblaude (habblaude.com) |
|---|---|---|---|
| Ideia | escritório em pixel art; cada agente é um personagem que senta na mesa e reage ao que faz | escritório virtual; cada projeto é uma sala, cada sessão/subagente um personagem | serviço pago (R$ 75–225/mês) de máquina na nuvem com o escritório do Habblaud |
| Agentes | só Claude Code (Codex, Gemini etc. no roteiro) | Claude Code e Codex | Claude Code |
| Detecção | hooks do Claude (`SessionStart`, `PreToolUse`, `PermissionRequest`, `Stop`) + leitura dos `.jsonl`; modo heurístico só com transcripts | lê `sessions/<pid>.json`, cauda dos `.jsonl`, `subagents/`; hooks opcionais (`PermissionRequest`); Codex por `~/.codex/sessions` | idem Habblaud |
| Desenho | React 19 + Canvas 2D, pathfinding, máquina de estados por personagem, sprites com manifesto | Canvas, arte de pixel **gerada por código** (personagens e móveis), SSE | idem |
| Estados | digitando (edita), lendo (busca), executando, balão de espera/permissão, som opcional | trabalhando, "precisa de você" (mão levantada), esperando shell, ocioso (passeia), subagente entrega e sai, sessão acaba e apaga a luz | idem + painel de atividade |
| Hospedagem | extensão VS Code (webview) ou servidor local `npx pixel-agents` | servidor Node local (porta 4747) + navegador, Docker | nuvem |
| Licença | MIT; personagens baseados no pacote Metro City de JIK-A-4 (licença dos assets **não declarada**) | MIT; arte gerada por código; logo e ilustrações geradas por IA | produto comercial |

## Confronto com o que o StarCode já tem

| Necessidade de uma "cena viva" | Eles | StarCode hoje |
|---|---|---|
| Quem está ativo | sessões/transcripts por agente | `.starcode/live/sessions.json` por **tripulante** (crew_hook nos 4 CLIs, F7-12..F7-20) |
| Estado do agente (trabalhando / esperando você / terminou) | hooks + transcripts | evento `agent.status.changed` da Orca (`working`/`blocked`/`waiting`/`done`) — já no plano (R13) |
| Subagentes / workers | subagentes do Claude | workers da Frota no Handoff (`**Dispatched:**`) + agentes da Orca — já no plano (R6, R25) |
| Tipo de atividade (lendo, editando, rodando) | `PreToolUse`/transcript | **não temos**: o crew_hook não grava a ferramenta |
| Onde desenhar | webview/navegador próprio, servidor local | painel da Orca: componentes (sem canvas) ou **painel HTML** (`ui: html`, canvas permitido, sem rede, eventos por `orca.on`) |
| Vários CLIs | 1–2 | 4 (Claude, Codex, Antigravity, OpenCode), porque a fonte é a Orca + `sessions.json` |

Conclusão: o StarCode já tem as **fontes de estado** que esses projetos precisam montar (e em mais CLIs). Falta só a **camada visual**. Ela cabe na Fase 10 como um segundo painel, HTML com canvas, sem servidor, sem porta e sem leitura de transcript.

## O que vale trazer (e o que não)

Entra na Fase 10 (proposta):
1. **Cena da Ponte**: painel HTML `ponte-cena` com a ponte de uma nave em pixel art **gerada por código** (como o Habblaud, sem arquivo de imagem de terceiros). Uma estação fixa por tripulante: o Picard na cadeira do capitão, Data e Troi ao lado, LaForge e os workers na engenharia, Q "aparece" com um clarão quando verifica.
2. **Estados animados**: tripulante ativo senta na estação e "digita"; agente `blocked`/`waiting` → balão "!" (o "precisa de você" do Habblaud); `done` → ✓ e o personagem levanta; tripulante inativo fica de pé na área do turbolift.
3. **Workers da Frota como personagens**: um LaForge por worker despachado, com o rótulo do ticket (até 6, depois "+N").
4. **Barra de status em alerta** quando algum agente do worktree está `blocked`/`waiting` (pequena extensão do R19).
5. **Diário de bordo**: as últimas 20 mudanças (estado de agente, foco, fase) em memória do worker, mostradas no painel de componentes (o "painel de atividade" do Habblaude).

Fica fora (e por quê):
- Copiar código ou sprites: os assets do Pixel Agents têm licença não declarada; o código dos dois é MIT, mas a cena é escrita do zero. Ambos entram no `CREDITS.md` como inspiração.
- Ler transcripts `.jsonl` / tipo de ferramenta (lendo, editando): exige mudar o crew_hook nos 4 CLIs e ler arquivos privados do agente. Fica como sugestão para uma fase futura.
- Servidor local, porta, Docker, acesso remoto, som, eventos do GitHub, editor de layout, "My day"/timelapse: fora do escopo do painel; a Orca já é o host.
- Semelhança com atores ou arte oficial de Star Trek: personagens genéricos de pixel com a cor da divisão e o emoji do tripulante.

## Impacto no plano

- Spec: +R38..R44 (cena, estados, workers, alerta, diário), R2 ganha `lastAt` por tripulante, R19 ganha o tom de alerta; volta para aprovação.
- Tasks: +2 tickets (modelo da cena, desenho da cena), que podem correr em paralelo com o painel e os atalhos; o diário de bordo entra no ticket dos atalhos. Total: 9 tickets.
