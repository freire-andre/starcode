# Ponte: missão ativa em outro worktree: Spec

**Approved**: 2026-11-12 - user: "sim"

**Size**: MEDIUM
**Status**: Approved
**Risk triggers**: none
**Linear**: SC-142
**May change**: scripts/ponte.py, src/orca/src/protocol.ts, src/orca/src/worker.ts, src/orca/src/worker.test.ts, src/orca/src/scene-model.ts, src/orca/src/scene-model.test.ts, src/orca/src/panel.tsx, src/orca/src/panel.test.tsx, src/orca/src/panel.check.ts, tests/test_ponte.py, DECISIONS.md, dist/

## Context
O `scripts/ponte.py` lê só as features do worktree em foco (`choose_feature`). Com o foco no checkout
principal e a última feature done, o painel da Ponte e a barra de status escondem a missão que roda num
worktree filho. Descoberta: `context.md` desta pasta.

## Scope
- O snapshot ganha o campo opcional `elsewhere` com a missão ativa de outro worktree do mesmo repositório.
- O painel e a barra de status mostram essa missão no lugar da feature local done, com aviso, contagem e
  atalho que foca o worktree (`workspace.open`, capacidade `workspace:write` já aprovada).

## Non-Goals
- Escrever qualquer estado (F10-R10, D28).
- Listar todas as missões ativas.
- Mudar o critério de escolha dentro de um mesmo worktree.
- Novas capacidades no manifesto do plugin da Orca.

## Decisions
| Item | Options | User answer |
|---|---|---|
| Local done + missão ativa em outro worktree | a ativa no lugar, com aviso / a local mais uma linha | approved - user: "A missão ativa (Recommended)" |
| R7 sem a capacidade `notifications:show` (achado do Q) | mensagem no painel / pedir a capacidade | approved - user: "Mensagem no painel (Recommended)" (2026-11-12) |
| Várias ativas em outros worktrees | a mais recente + "e mais N" / todas em lista | approved - user: "A mais recente + contagem (Recommended)" |

## Requirements
- R1 - WHEN a feature escolhida no worktree em foco tem `Phase` done ou não há feature THEN the system SHALL procurar, nos outros worktrees de `git worktree list --porcelain` do mesmo repositório, features com `Phase` diferente de done, pelo mesmo critério do `choose_feature` (mtime do arquivo do Handoff; empate decidido pelo maior slug em ordem lexicográfica), e publicar a mais recente em `elsewhere` com `worktree` (caminho posix), `branch`, `others` (quantas outras ativas existem) e os mesmos campos de `feature` (`slug`, `phase`, `size`, `progress`, ...).
- R2 - WHEN a feature do worktree em foco não está done THEN the system SHALL publicar `elsewhere: null` sem ler os outros worktrees.
- R3 - IF `git worktree list` falha, ou um worktree listado está ausente ou ilegível THEN the system SHALL ignorar aquele worktree, acrescentar um item em `errors` com fonte `worktrees` e manter o resto do snapshot (sair com 0).
- R4 - The system SHALL manter `schemaVersion` 1, e `elsewhere` SHALL ser opcional (painel sem o campo funciona como hoje); o ponte.py SHALL continuar sem escrever nada.
- R5 - WHEN o snapshot tem `elsewhere` THEN o painel SHALL mostrar essa missão no lugar da feature local, com o aviso "Missão ativa em outro worktree" acompanhado de `<branch>`, `<fase>` e `<done>/<total>` quando houver progresso, e "e mais N" quando `others` > 0.
- R6 - WHEN o snapshot tem `elsewhere` THEN a barra de status SHALL mostrar `🖖 <slug> · <fase> · outro worktree` (mais ` · modo N` como hoje).
- R7 - WHEN o usuário aciona o atalho do aviso THEN the system SHALL chamar `workspace.open` com o id do workspace da Orca cujo `path` casa com `elsewhere.worktree`; IF nenhum workspace casa THEN o painel SHALL mostrar, junto do atalho, a mensagem "worktree não aberto na Orca: <caminho>", sem chamar `notifications.show` e sem lançar erro.
- R8 - The system SHALL registrar em `DECISIONS.md` a decisão P151-2 com o campo `elsewhere` e o critério.

## Edge Cases
- Comparação de caminhos sem diferenciar maiúsculas/minúsculas e barras no Windows (`F:\x` = `f:/x`).
- Worktree `prunable` ou `bare` na listagem: ignorado (R3, sem erro para `bare`).
- O próprio worktree em foco aparece na listagem: excluído da busca.

## Open Questions
None.

## Checks

**Build**: `orca plugin validate src/orca --json`; `orca plugin check src/orca --json`; `python tools/build.py --check`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`
**Run plugin**: `orca plugin test src/orca`

**C1** - Local done e outro worktree com feature em `execute`: `elsewhere.slug`, `elsewhere.worktree`, `elsewhere.branch` e `others` 0 corretos; com duas ativas, sai a de Handoff mais novo e `others` 1; com mtime igual, sai o maior slug (R1)
Proof: run unit | test_elsewhere_picks_newest_active_worktree ... ok

**C2** - Feature local ativa: `elsewhere` null e o git não é chamado para listar worktrees (R2)
Proof: run unit | test_elsewhere_null_when_local_active ... ok

**C3** - `git worktree list` falhando e worktree listado inexistente: rc 0, item em `errors` com fonte `worktrees`, `feature` local preservada (R3)
Proof: run unit | test_elsewhere_worktree_errors_do_not_break_snapshot ... ok

**C4** - Snapshot continua `schemaVersion` 1 e nenhum arquivo é criado, removido ou tem o conteúdo alterado nos worktrees (comparação por conteúdo) (R4)
Proof: run unit | test_elsewhere_snapshot_is_read_only ... ok

**C5** - Painel com `elsewhere` mostra "Missão ativa em outro worktree", a fase, `2/3` e "e mais 1"; sem `elsewhere` mostra a feature local como antes (R5)
Proof: run plugin | ✔ painel mostra a missão ativa de outro worktree

**C6** - Barra de status com `elsewhere`: `🖖 <slug> · execute · outro worktree · modo 3` (R6)
Proof: run plugin | ✔ barra de status indica missão em outro worktree

**C7** - Atalho chama `workspace.open` com o id do workspace de mesmo caminho (comparação sem caixa e barras); sem workspace casando, o painel mostra "worktree não aberto na Orca: <caminho>" e `notifications.show` não é chamado (R7)
Proof: run plugin | ✔ atalho foca o worktree da missão ativa

**C8** - `DECISIONS.md` tem P151-2 (R8)
Proof: run unit | test_decisions_records_p151_2_elsewhere ... ok

## Handoff

**Phase:** done
**Size:** MÉDIA
**Git mode:** 3
**Next:** provas, done, Worf r2
**Linear:** SC-142
**Integration branch:** not created
**Last integrated:** Worf-fix · 8eaaf36
**Dispatched:** none
**Settled:** 2026-11-12: Corrigir os dois (Recommended); 2026-11-12: vou na sua recomendação
**Attempts:** none
**Reports:** 2026-11-12: Q (codex): FAIL, 3 achados (R7 notificação sem capacidade; C4 só mtime/tamanho; desempate do R1 não especificado); 2026-11-12: Q2 (codex): 3 achados fechados; 2 novos abertos (same_path C:/ = c:; C5 por substring); 2026-11-12: done verde; Q2 com 5 achados fechados; 2026-11-12: PR #31 aberto; 2026-11-12: Worf r1: COMMENT (W1 should-fix, W2 nit), publicado no PR #31; CI verde 670/670
**Breaker:** closed
