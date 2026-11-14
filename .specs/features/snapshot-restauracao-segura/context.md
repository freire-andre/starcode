# Snapshot e restauração seguros: Context

**Size**: MEDIUM
**Risk triggers**: Irreversibilidade (a restauração sobrescreve e apaga arquivos não commitados)
**Source request**: "PROXIMO PASSO do primeiro corte da triagem" → passo 6: R.3 e R.4 de `starcode-triagem-v2-2026-11-13.md`

## Problem
- **R.3:** `snapshot.py take` troca o ref a cada chamada (`scripts/snapshot.py:77-93`), e `execute.md` manda rodar `take` antes de todo despacho no modo 1. Depois de três tentativas, a saída (b) do disjuntor restaura o estado anterior à 3ª tentativa, não o anterior ao ticket.
- **R.4:** `_diff` usa `--no-renames` e a restauração só toca o May change (`scripts/snapshot.py:195-206`, `:265-266`). Num arquivo movido de fora para dentro do May change, a cópia nova é removida e o original, listado como "fora do ticket", não volta. Depois do `drop`, o conteúdo some. Não há cópia da árvore anterior à restauração, e o `--yes` recalcula o plano em vez de executar o que o usuário viu.

## Users
O Picard no modo 1 (saída (b) do disjuntor) e o usuário que confirma a restauração.

## Success
A saída (b) sempre volta ao estado anterior ao ticket. Nenhuma restauração deixa um arquivo do snapshot sem cópia. A árvore anterior à restauração fica recuperável. O `--yes` só executa o plano que o usuário viu.

## Constraints
- Congelamento D-i: nenhum comando, opção ou perfil novo.
- Mantém F12-1/F12-2: índice temporário, `.git/index` real intocado, nenhum comando de descarte em massa.
- Reabre a decisão F12 R3 ("substitui o ref"), tomada por padrão sem perguntar (`.specs/features/fase-12-robustez/context.md:42`), com evidência nova: ela quebra a saída (b) do disjuntor.

## Scope Notes
- Dentro: R.3 e R.4 da triagem, no `scripts/snapshot.py`, nos testes e no texto das seções 6 e 7 do `execute.md`, se ele citar a substituição.
- Fora: R.5 (May change lido do `tasks.md` gravado no snapshot), qualquer item que não seja R.3/R.4, qualquer opção nova.

## Gray Areas

| Item | Options | User answer | Date |
|---|---|---|---|
| `take` com snapshot já existente | mantém o primeiro / numera as tentativas | Mantém o primeiro: não grava nada e imprime `mantido <hash>` ("Mantém o primeiro") | 2026-11-14 |
| Amarrar o `--yes` ao plano visto | plano gravado no dry-run / flag `--plan <hash>` | Plano gravado no dry-run, em `<git-dir>/starcode/`; o `--yes` recusa se o plano recalculado diferir ("Plano gravado no dry-run") | 2026-11-14 |
| Linha "voltar" fora do May change | recusa tudo / restaura e avisa | Recusa tudo: exit 1, lista os caminhos, nada é tocado ("Recusa tudo") | 2026-11-14 |
| Quais linhas "voltar" fora do ticket causam a recusa | só arquivo do snapshot ausente na árvore atual / qualquer linha fora | Só arquivo ausente (movido ou apagado); edição do usuário fora do ticket segue "não tocada", como no F12-2 ("Só arquivo ausente") | 2026-11-14 |
| Onde fica o ref da árvore pré-restauração | `refs/starcode/pre-restore/<slug>/<ticket>` / dentro de `refs/starcode/snapshots/` | `refs/starcode/pre-restore/<slug>/<ticket>`, fora do prefixo que o `list` lê. Default (não perguntado) | 2026-11-14 |
| `drop` e o ref pré-restauração | apaga junto / mantém | apaga junto com os snapshots da feature, que é a mesma retenção (feature em `done`). Default (não perguntado) | 2026-11-14 |
| Retomada de uma restauração parcial (`--yes` de novo) | recusa porque o plano mudou / aceita o que falta | aceita quando o plano recalculado é subconjunto do plano gravado (as linhas já feitas saem); o ref pré-restauração da primeira execução não é sobrescrito. Default (não perguntado) | 2026-11-14 |
| `--yes` sem dry-run anterior | recusa / executa | recusa com exit 1 e manda rodar sem `--yes` primeiro. Default (não perguntado) | 2026-11-14 |
| Plano gravado depois do sucesso | apaga / mantém | apaga ao terminar sem falha. Default (não perguntado) | 2026-11-14 |

## Implicit Requirements

| Dimension | Requirement or N/A because ... |
|---|---|
| Failure and partial failure | Falha ao gravar o ref pré-restauração: nada é restaurado (exit 1). Falha no meio da restauração: a retomada segue a linha "Retomada" acima |
| Retries, idempotency and duplicates | Um `take` repetido não muda o ref (R.3). Um `restore --yes` repetido depois do sucesso recusa por falta de plano gravado |
| Data lifecycle | O ref pré-restauração e o plano gravado seguem a retenção dos snapshots (`drop` em `done`); o plano some no sucesso |
| Observability | `take` imprime `mantido <hash>`; o `restore --yes` imprime o hash do ref pré-restauração |

Demais dimensões: N/A para este escopo.

## Facts Found
- `scripts/starcode_common.py:51` `git_dir()` usa `git rev-parse --absolute-git-dir`, que funciona em worktree ligado, onde `.git` é um arquivo. `<git-dir>/starcode/` já guarda o `session.json` (`scripts/git_mode.py:3`).
- Testes que mudam de sentido: `tests/test_snapshot.py:68` `test_take_substitui_snapshot_existente`; e `tests/test_snapshot_restore.py:205` `test_restore_falha_parcial_e_retomada` e `:234` `test_cenario_aceite_disjuntor_modo_1` precisam continuar passando com o plano gravado.
- Decisões a atualizar no `DECISIONS.md`: F12-1 (substituição no `take`) e F12-2 (o `--yes` recalcula o plano).
- `execute.md` seção 7 manda rodar `take` antes de cada despacho; a seção 6 descreve a saída (b) com o `restore`.
