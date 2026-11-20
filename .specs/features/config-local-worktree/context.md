# Config local nos worktrees: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "Sigo com essa divisão e começo pela missão 1 (C.3, C.5 e C.7)?" "sim" (passo 4 da seção 12 da triagem v2; itens C.3, C.5 e C.7 da seção 10.1)

## Problem
A config local do repositório (`.starcode/config.local.json`) não é versionada e é lida de `<raiz do worktree atual>/.starcode/` (`scripts/starcode_common.py:80-91`). Nos worktrees ligados, que é onde a Orca abre as sessões e onde os workers rodam, o arquivo não existe, e a config volta em silêncio para a do usuário. A mescla com a config do usuário é campo a campo (`starcode_common.py:275`), o que pode produzir uma combinação de CLI e modelo que não existe. O valor de `model` aceita qualquer texto (C.5), e o `suggest` ignora a config atual (C.7).

Reprodução (repositório temporário, Q do usuário `antigravity · gemini-x`, Q local `{model: zai/glm-5.3}`), com `crew_at(repo_root(...))`:
- worktree principal: `antigravity · zai/glm-5.3`, fonte `local` (combinação inexistente);
- worktree ligado: `antigravity · gemini-x`, fonte `user`, e `load_local_config` devolve `None`.

## Users
O dono do repositório, que escolhe modelos por projeto, e o Picard e o banner, que leem a tripulação efetiva em qualquer worktree.

## Success
Num worktree ligado, a tripulação efetiva é a mesma do worktree principal. Uma entrada local nunca mistura o CLI de uma fonte com o modelo de outra. Um modelo malformado é recusado na validação. O `suggest` não desfaz escolhas já feitas.

## Constraints
- Sem mudar o formato dos arquivos de config, a não ser pela regra nova de que a entrada local precisa de `cli` e `model`.
- A config do usuário mantém a semântica atual (entrada parcial herda do padrão).

## Scope Notes
- C.3: a leitura cai para o worktree principal (`git rev-parse --git-common-dir`) quando o arquivo não existe no worktree atual; a entrada local substitui a do usuário inteira.
- C.5: conjunto de caracteres restrito para `model` (sem `-` inicial nem espaço), leitura do `@` corrigida no `parse_model_arg` e aviso no banner quando o arquivo local está versionado ou fora do `.gitignore`.
- C.7: o `suggest` parte do que já está configurado.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Entrada local parcial | exigir `cli` e `model` (o validador recusa a parcial) · herdar o CLI do padrão | Exigir CLI e modelo (Recomendado) | 2026-11-20 |
| `suggest` com config existente | manter o membro já configurado com CLI disponível · propor tudo e marcar as diferenças | Manter o configurado (Recomendado) | 2026-11-20 |
| Arquivo local no worktree ligado e no principal ao mesmo tempo | o do worktree atual vence · o do principal vence | o do worktree atual vence: default (não perguntado) | 2026-11-20 |
| Caracteres aceitos em `model` | `[A-Za-z0-9._:/+@-]`, sem `-` inicial · lista livre com só o `-` inicial proibido | conjunto fechado, sem `-` inicial nem espaço: default (não perguntado) | 2026-11-20 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| input validation and limits | `model` com conjunto de caracteres fechado; entrada local exige `cli` e `model` (C.5, C.3) |
| failure and partial failure | `git rev-parse` falhando ou fora de um repositório: fica a leitura atual, sem erro |
| observability | o banner avisa quando o arquivo local está versionado ou não está no `.gitignore` |
| demais dimensões | N/A para este escopo |

## Facts Found
- Leitura: `scripts/starcode_common.py:80-91` (`local_config_path`, `load_local_config`); chamadores: `crew_at` (`:285-289`), `scripts/dispatch.py:246`, `scripts/setup_helpers.py:89`, `hooks/scripts/banner.py:281`.
- Mescla: `effective_crew`, `starcode_common.py:270-281`.
- Validador: `scripts/config/validate_config.py` (`LOCAL_SCHEMA`, `:85-88`; `CREW_ENTRY` com `model` livre, `:50`; `ensure_ignored`, `:95-102`).
- `parse_model_arg`: `scripts/setup_helpers.py:121-128`, que corta no último `@` mesmo quando o sufixo não é um nível de custo.
- `suggest`: `scripts/setup_helpers.py:190-215`, que parte só do padrão do `crew.yaml`.
