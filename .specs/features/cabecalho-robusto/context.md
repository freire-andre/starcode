# Cabeçalho e status da tripulação robustos: Context

**Size**: MEDIUM
**Risk triggers**: estado compartilhado (várias sessões gravam o mesmo `.starcode/live/crew.json`)
**Source request**: "pode abrir a feature de robustez do cabeçalho" (sobre: "Aparentemente ele sempre mostra apenas o Picard direto trabalhando e o Spock as vezes. [...] ele não esta mostrando o cabeçalho apresentando o agente que vai iniciar o trabalho.")

## Problem
O cabeçalho do tripulante (F6-6) e o status em `crew.json` (F6-7) dependem do modelo rodar `crew_live.py start/stop` e repetir o texto. Com o plugin instalado desatualizado (1.0.0) ou com a instrução perdida, nada aparece; uma sessão que termina sem `stop` deixa o tripulante em 1 para sempre (`picard: 1, spock: 1` presos desde 19:33 de 2026-11-07).

## Users
O usuário do StarCode, que quer ver quem assumiu a tarefa e alimentar um painel (statusline, Ponte da Fase 10).

## Success
No Claude Code o cabeçalho aparece sempre que um tripulante assume, sem depender do modelo; o `crew.json` nunca fica preso em 1 depois que a sessão some; o banner avisa quando o plugin instalado está atrás do repo do StarCode.

## Constraints
- `crew.json` continua plano `{"picard": 0|1, ..., "laforge": <n>}` (pedido original: simples, barato).
- Hooks nunca quebram a sessão: saem com 0 e JSON válido (F0-5); Python stdlib.
- Fatos do Claude Code verificados no Context7 (code.claude.com/docs/en/hooks): `PreToolUse` com matcher `Skill` só dispara quando o modelo chama a skill; `/skill` digitado dispara `UserPromptExpansion` (casa por `command_name`); `systemMessage` é mostrado ao usuário; `SessionEnd` recebe `session_id` e `reason`; a entrada comum dos hooks traz `session_id`.

## Scope Notes
Dentro: hooks do Claude, validade do status, aviso de versão. Fora (o usuário escolheu "Claude agora, outros depois"): hooks equivalentes no Codex, Antigravity e OpenCode.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Quem mostra o cabeçalho no Claude | hook sempre / agente repete + hook reserva | Hook mostra sempre | 2026-11-07 |
| Validade do status | 15 min + pulso por ferramenta / 60 min sem pulso | 15 min + pulso por ferramenta | 2026-11-07 |
| Status enquanto espera a resposta | 0 enquanto espera / 1 até o fim da etapa | 0 enquanto espera | 2026-11-07 |
| CLIs | Claude agora, outros depois / os quatro | Claude agora, outros depois | 2026-11-07 |
| Onde guardar sessão e hora | dentro do `crew.json` / arquivo ao lado | arquivo ao lado `sessions.json`, `crew.json` segue plano (default (não perguntado)) | 2026-11-07 |
| Aviso de versão | comparar com o registro remoto / com o repo local do StarCode | só quando o repo aberto é o próprio StarCode (sem rede) (default (não perguntado)) | 2026-11-07 |
| Missão no cabeçalho do hook | sem missão / argumentos da skill | os argumentos da skill, cortados em 80 caracteres (default (não perguntado)) | 2026-11-07 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| failure and partial failure | hook com erro (JSON inválido, sem repo, arquivo travado) sai com 0 e não mostra nada |
| concurrency and ordering | gravação atômica (temp + `os.replace`, como hoje); a última escrita vence; `crew.json` é recalculado das sessões a cada escrita |
| data lifecycle | sessão sem pulso há mais de 15 min é descartada na próxima escrita |
| observability | `crew_live.py show` mostra também as sessões |
| demais dimensões | N/A para este escopo |

## Facts Found
- `scripts/crew_live.py` (start/stop/set/reset/progress/show; `header()`; laforge 0..10).
- `scripts/statusline.py` `segment()` lê `crew.json` e mostra quem tem `v == 1` (LaForge com 2+ some).
- `tools/build.py` `claude_hooks()` gera `dist/claude/hooks/hooks.json` (hoje PreToolUse Bash + SessionStart).
- `hooks/scripts/banner.py` monta o banner do SessionStart.
- Skills com a instrução "Header first (F6-6)": engajar, troi, spock, data, laforge, mccoy, q.
