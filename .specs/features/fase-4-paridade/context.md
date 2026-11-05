# Fase 4: paridade com Codex, Antigravity e OpenCode: Context

**Size**: LARGE
**Risk triggers**: múltiplos CLIs (contrato de instalação de cada um), integração externa (Orca, Linear, provedores de modelo)
**Source request**: "siga para proxima etapa" (Fase 4 do `PLANO_STARCODE.md` §10, issue SC-11)

## Problem
O StarCode só foi aceito no Claude Code. O `dist/` já gera pastas para Codex, Antigravity e OpenCode, mas
nenhum roteiro das Fases 1–3 rodou nesses CLIs. A instalação, as skills, os scripts e o despacho por Orca
podem quebrar em cada um sem que ninguém perceba.

## Users
O dono do repositório, que quer usar a tripulação a partir de qualquer um dos 4 CLIs dentro da Orca.

## Success
- O núcleo comum passa em cada CLI: instalar, configurar (`setup`), engajar, planejar (Troi, Spock, Data
  com aprovações e publicação no Linear) e executar uma feature no modo 2 (LaForge por ticket, Q de outra
  família, gates verdes).
- Cada extra (hooks, banner por hook, subagente com outro modelo, MCP do Linear) está ✅ ou marcado como
  indisponível na matriz, com o fallback funcionando e informado pelo banner.
- Evidência em `docs/aceite/fase-4.md`, uma seção por CLI.

## Constraints
- Decisões fechadas: sub-issues da SC-11 no projeto StarCode; Git modo 3; aceite **completo por CLI**
  (setup/engajar, planejamento e 1 feature modo 2 com Q de outra família) no sandbox
  `F:\Projetos\starcode-sandbox`, time PROJ; nunca criar projeto de teste no time SC.
- Gemini CLI fora (D32); Antigravity é `agy` 1.4.12. OpenCode v2.2.3. Codex 0.166.0.
- Hooks nos outros CLIs (`git_guard`, `secret_scan`, `banner` por hook) são a Fase 5; aqui, o banner vem
  do `engajar` rodando `banner.py --full --text`.
- Itens herdados da Fase 3: falso positivo do banner (verificação degradada por citação de
  `self-verified`), `dispatch.py brief` para MÉDIA a partir do `## Checks` da spec, Picard no worktree de
  integração (avaliar).

## Scope Notes
- Dentro:
  - ajustes do gerador e dos adaptadores para Codex, Antigravity e OpenCode;
  - instalação e `setup` em cada CLI;
  - aceite completo por CLI;
  - os três itens herdados da Fase 3.
- Aceite conduzido por **worker automático com roteiro** (resposta do usuário): eu despacho um worker
  Orca do CLI testado, com as respostas e as aprovações do usuário escritas de antemão no briefing.
- No CLI testado rodam Picard, Troi, Spock, Data e LaForge; **o Q fica num CLI de outra família**
  (resposta do usuário).
- OpenCode no aceite usa `openrouter/deepseek/deepseek-v4-pro` (resposta do usuário).
- Uma feature **nova e pequena por CLI** (2–3 tickets), do zero (resposta do usuário).
- Fora: os hooks `git_guard`, `secret_scan` e banner por hook nos outros CLIs (Fase 5), empacotamento e
  marketplace (Fase 6), modo Frota (Fase 7).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Quem conduz a sessão de aceite em cada CLI | usuário interativo · worker automático com roteiro | worker automático com roteiro | 2026-11-05 |
| Modelo do OpenCode no aceite | deepseek-v4-pro (OpenRouter) · claude-sonnet-5.5 (OpenRouter) · gratuito/Nvidia | deepseek-v4-pro | 2026-11-05 |
| Papéis no CLI testado | tripulação toda com o Q fora · só o Picard | tripulação toda, Q fora | 2026-11-05 |
| Feature por CLI | nova e pequena por CLI · reusar csv-import-export | nova e pequena por CLI | 2026-11-05 |
| Missões do aceite | Codex: data de vencimento (`add --vence`, `list` mostra vencidas); Antigravity: busca por texto (`buscar TERMO`); OpenCode: exportar para Markdown (`exportar-md`) | default (não perguntado) | 2026-11-05 |
| Aprovações no roteiro | gravadas como `user (roteiro pré-aprovado em 2026-11-05): "sim"` · pedir na hora | default (não perguntado): pré-aprovadas no briefing, com essa marca, e as respostas da Troi também escritas de antemão | 2026-11-05 |
| Q por CLI testado | Codex → Antigravity (gemini-3.8-flash-high); Antigravity → Codex; OpenCode/DeepSeek → Codex | default (não perguntado) | 2026-11-05 |
| Modelo do Antigravity para a tripulação | gemini-3.8-flash-high · claude-sonnet-4-6 | default (não perguntado): gemini-3.8-flash-high (família Google, diferente do Q Codex) | 2026-11-05 |
| Picard no worktree de integração | sim (Handoff, provas e verificação no mesmo ramo) · manter como na Fase 3 | default (não perguntado): avaliar na spec; adotar se o aceite por worker já roda no worktree de integração | 2026-11-05 |
| Hooks do Codex na Fase 4 | registrar já (o Codex lê do plugin) · deixar para a Fase 5 | default (não perguntado): Fase 5, como no plano; aqui só o aviso de trust pendente | 2026-11-05 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | O `setup` de cada CLI valida o caminho de instalação e recusa com mensagem quando a pasta do plugin ou o binário do CLI não existe. |
| Failure and partial failure | Um extra que falha num CLI vira linha "indisponível" na matriz com o fallback; o núcleo que falha reprova o CLI no aceite (sem marcar como indisponível). |
| Retries, idempotency and duplicates | Reinstalar ou rodar o `setup` de novo não duplica entradas (`opencode.json`, a pasta global de plugins, o marketplace do Codex). |
| Authorization boundaries and rate limits | Workers do aceite não usam `--dangerously-skip-permissions` nem `--dangerously-bypass-hook-trust`; as permissões são estreitas (F0-1). Limite de uso de provedor (OpenRouter) é tratado como falha de dependência externa. |
| Concurrency and ordering | Um CLI por vez no aceite; dentro dele, os tickets em sequência (Fase 3). |
| Data lifecycle | N/A, porque não há dados novos persistidos além dos artefatos `.specs/` e do Linear, que seguem as regras das Fases 2–3. |
| Observability | O banner (`engajar` → `banner.py --full --text`) mostra o CLI, os extras indisponíveis e o fallback ativo; o relatório final de cada worker cita o modelo efetivo. |
| External dependency failure | Sem login no CLI ou no provedor, sem trust de hooks no Codex ou com a Orca fora: o worker para com a linha exata do erro, e o aceite registra o que bloqueou. |
| State-transition rules | As mesmas das Fases 2–3 (Handoff só pelo `handoff.py`, Done só com confirmação e nunca no modo 1). |

## Facts Found
- `tools/build.py`: `build_codex` (`.codex-plugin/plugin.json`, `AGENTS.md`), `build_antigravity`
  (`plugin.json` na raiz, `rules/starcode.md`), `build_opencode` (`commands/sc-<skill>.md`); nenhum dos
  três registra hooks (teste `test_layout_per_cli`).
- `docs/compatibilidade.md` (Fase 0):
  - Codex lê os hooks do plugin, mas exige trust (sem trust, o `worker-start` falha) e precisa de JSON
    deny com exit 0 (F0-5).
  - Antigravity precisa de adaptador nativo; seu subagente só aceita `inherit`/`flash`/`pro`, e o
    `invoke_subagent` ficou inconclusivo.
  - OpenCode carrega skills por caminho absoluto no `opencode.json` e o plugin só na pasta global ou do
    projeto; não tem evento de banner. O `worker-start` com `--model` só vale em worktree existente
    (não testado).
- Despacho aninhado: um worker Orca (o Picard no CLI testado) despachando os próprios workers (LaForge e Q) é **não verificado**; a Fase 3 só despachou a partir da sessão principal.
- CLIs presentes: `codex-cli 0.166.0`, `agy 1.4.12`, `opencode v2.2.3`.
- Modelos:
  - OpenCode tem credenciais OpenRouter (354 modelos, incluindo `anthropic/*`, `deepseek/*`,
    `google/gemini-3*`) e Nvidia.
  - `agy models` lista `gemini-3.8-flash-*`, `claude-sonnet-4-6`, `claude-opus-4-6-thinking` e
    `gpt-oss-120b-medium`.
- `skills/setup/SKILL.md` já oferece Q em codex/opencode/antigravity e `qStrategy`
  (opencode-subagent, orca-worker, self-verified).
- MCP do Linear: só ativo no Claude; o StarCode usa o `orca linear` para quase tudo (D2), mas o Projeto e o
  Documento do Data usam o MCP.
