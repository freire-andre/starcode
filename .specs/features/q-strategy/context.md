# q-strategy: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "vamos para a proxima etapa" (passo 11 do primeiro corte da triagem v2: item 3.6, `qStrategy`; decisão D-b: ligar ao `dispatch.py q-cli`)

## Problem
O campo `qStrategy` do config do usuário é validado, mas nenhum script o lê. A skill `config` oferece o campo ao usuário, então existe uma opção que aparece na tela e não tem efeito nenhum.

## Users
O dono do repositório e quem usa o StarCode com o config do usuário (`~/.starcode/config.json`). O Picard lê a saída do `dispatch.py q-cli` no passo 4 da verificação (execute.md).

## Success
Com `qStrategy` no config, o `q-cli` segue a ordem das estratégias e devolve a primeira disponível. Sem o campo, o comportamento atual (F3-6, F4-6) não muda. Um teste de tabela cobre as três estratégias (triagem v1, item 3.6).

## Constraints
- Congelamento D-i vigente até o fim do primeiro corte: nada de novo além do item.
- A regra de família (o Q nunca na família do LaForge) continua valendo em qualquer estratégia.

## Scope Notes
- Dentro: `q-cli` lê `qStrategy` do config do usuário e segue a ordem; `orca-worker` = o percurso atual (Q configurado, codex, antigravity, opencode, regra de família); `self-verified` = devolve `self-verified` com exit 1.
- Dentro: `opencode-subagent` continua aceito pelo validador, mas o `q-cli` trata como indisponível, avisa no stderr e passa para a próxima estratégia; a skill `config` deixa de oferecer esse valor até ele ser implementado.
- Fora: implementar o Q como subagente do OpenCode (fura o congelamento D-i; vira feature própria).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| `opencode-subagent` sem implementação | fica no enum e o q-cli pula / implementar agora / remover do enum | "Fica no enum, q-cli pula (Recomendado)" | 2026-11-16 |
| `self-verified` antes de `orca-worker` | a ordem do usuário manda / worker sempre primeiro | "Sim, a ordem do usuário manda (Recomendado)" | 2026-11-16 |
| Lista sem `self-verified` e nada disponível | devolve `self-verified` (exit 1, como hoje) / erro | default (não perguntado): devolve `self-verified`, igual à R19 atual | 2026-11-16 |
| Config ausente, inválido ou sem o campo | comportamento atual / erro | default (não perguntado): comportamento atual, sem aviso quando o campo falta | 2026-11-16 |
| Teste injetável | ler o config real / caminho injetável | default (não perguntado): o `q_cli` recebe a estratégia por parâmetro (ou caminho de config injetável) para o teste de tabela não depender de `~/.starcode` | 2026-11-16 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | O validador já exige lista ordenada, sem repetição, ≥1 item, valores do enum (`scripts/config/validate_config.py:33,57`). Config inválido ou ilegível: `q-cli` ignora o campo e segue o comportamento atual. |
| External dependency failure | Estratégia indisponível (nenhum CLI de outra família com `orca_worker` ok) passa para a próxima da lista. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `scripts/config/validate_config.py:33` define `Q_STRATEGIES = ("opencode-subagent", "orca-worker", "self-verified")`; linha 57 valida o campo.
- `schemas/config.md:17,30` documenta o campo; `skills/config/SKILL.md:69` o oferece como chave opcional (só escopo global).
- `scripts/dispatch.py:623` `q_cli(laforge, configured, caps_dir)`: percorre o Q configurado e depois `Q_CLI_ORDER = ("codex", "antigravity", "opencode")` (linha 77), devolve o primeiro de outra família com `orca_worker` ok; `None` vira `self-verified` com exit 1 (linhas 999-1004).
- `skills/engajar/references/execute.md:143-151`: saída `self-verified` → o Picard roda o `q` como subagente de contexto limpo e marca `**Verification:** self-verified`.
- Nenhum código no repo implementa `opencode-subagent`: a palavra só aparece no enum, no schema e na skill `config`.
- O config do usuário atual tem `qStrategy: ["orca-worker"]` e `crew.q.cli = codex`.
- Caminho do config do usuário: `scripts/starcode_common.py:69` (`user_config_path`).
