# Ponte: missão ativa em outro worktree: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "e quanto as issues no linear 142, 143 e 144? qual sua sugestão?" → "sim, começa pelo patch v1.5.1" (SC-142: o painel da Ponte mostra a missão ativa de outro worktree)

## Problem
O painel da Ponte (Orca) e a barra de status leem só as features do worktree em foco. Quando o foco está
no checkout principal, com a última feature já done, e a missão em andamento vive num worktree filho
(ou noutro worktree do mesmo repositório), o painel mostra a feature concluída e esconde a missão ativa.

## Users
Quem acompanha a tripulação pelo painel da Ponte na Orca enquanto o trabalho roda em worktrees filhos.

## Success
Com o foco num worktree cuja feature está done (ou sem feature), o painel e a barra de status mostram a
missão ativa de outro worktree do mesmo repositório, marcada como "Missão ativa em outro worktree", com
fase e progresso, e um atalho que foca aquele worktree. Se o worktree em foco tem missão ativa, nada muda.

## Constraints
- O ponte.py continua só leitura (F10-R10, D28): nada é escrito em nenhum worktree.
- Os outros worktrees vêm do próprio git (`git worktree list --porcelain`), sem estado novo.
- O atalho usa só capacidades já aprovadas na Orca (`workspace:read`, `workspace:write`); acessos novos
  forçariam nova aprovação do painel.
- `schemaVersion` do snapshot: mudança compatível (campo novo opcional), sem quebrar o painel antigo.

## Scope Notes
- Dentro: procurar missão não done nos outros worktrees quando a local está done ou não existe; mostrar a
  ativa no lugar da local; contagem das demais; atalho para focar o worktree; barra de status.
- Fora: escrever estado; listar todas as missões; mudar o critério de escolha dentro de um worktree.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| O que o painel mostra quando a local está done e há missão ativa em outro worktree | a ativa no lugar, com aviso / a local mais uma linha de aviso | A missão ativa (no lugar, com o aviso e o atalho) | 2026-11-12 |
| Várias missões ativas em outros worktrees | a mais recente + "e mais N" / todas em lista | A mais recente + contagem | 2026-11-12 |
| Atalho para focar o worktree | incluir / não | incluir, com `workspace:write` já aprovado — default (não perguntado) | 2026-11-12 |
| Worktree em foco com missão ativa | nada muda / também mostrar as outras | nada muda — default (não perguntado) | 2026-11-12 |
| Critério de "mais recente" entre worktrees | mtime do Handoff / data do commit | mtime do arquivo do Handoff, igual ao `choose_feature` — default (não perguntado) | 2026-11-12 |
| Worktree ilegível ou removido no meio da leitura | erro no painel / ignorar | ignorar aquele worktree e registrar em `errors` sem derrubar o snapshot — default (não perguntado) | 2026-11-12 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Failure and partial failure | `git worktree list` falhando ou worktree sumido (prunable): o snapshot segue com a feature local e uma entrada em `errors` |
| External dependency failure | Orca sem o workspace correspondente ao caminho: o atalho não aparece (ou avisa), o resto do painel funciona |
| Concurrency and ordering | leitura enquanto o Picard grava o Handoff: arquivo parcial vira erro daquele worktree, não do snapshot |
| demais dimensões | N/A para este escopo (sem entrada de usuário, sem autorização nova, sem dados retidos) |

## Facts Found
- `scripts/ponte.py`: `choose_feature` olha só `snap.root/.specs/features`; prefere não done pelo mtime do Handoff e cai na done mais recente; `build_feature` monta `slug`, `phase`, `size`, `done`, `linear`, `integrationBranch`, `progress`, `breaker`, `files`; `snapshot()` publica `schemaVersion 1`.
- `scripts/crew_live.py`: `main_worktree(cwd)` via `git rev-parse --git-common-dir`; progresso em `.starcode/live/progress.json` do checkout principal.
- `src/orca/src/worker.ts`: `focus()` usa `workspace.readContext` e `workspace.list` (`pickFocus` casa pela branch); `statusText(snap)` monta a barra; `editor.open` e `agent.launch` já usam `workspaceId`.
- `src/orca/orca-plugin.json`: capacidades `workspace:read` e `workspace:write` já aprovadas; evento `workspace.changed`.
