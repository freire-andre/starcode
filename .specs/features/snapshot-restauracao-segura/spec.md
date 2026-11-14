# Snapshot e restauração seguros: Spec

**Approved**: 2026-11-14 - user: "Sim"

**Size**: MEDIUM
**Risk triggers**: Irreversibilidade (a restauração sobrescreve e apaga arquivos não commitados)
**Status**: Approved
**Linear**: SC-174
**May change**: scripts/snapshot.py, tests/test_snapshot.py, tests/test_snapshot_restore.py, DECISIONS.md, dist/

## Context
Itens R.3 e R.4 de `starcode-triagem-v2-2026-11-13.md` (fora do Git). Discovery em `context.md`. No modo 1, `take` substitui o ref a cada tentativa (`scripts/snapshot.py:77-93`), e a saída (b) do disjuntor volta ao estado anterior à 3ª tentativa, não ao anterior ao ticket. A restauração (`cmd_restore`, `:232-305`) não guarda a árvore que vai sobrescrever. Ela recalcula o plano no `--yes` e, com `--no-renames`, perde o original de um arquivo movido de fora para dentro do May change. Sucesso: a saída (b) volta ao estado anterior ao ticket, a árvore pré-restauração fica num ref, o `--yes` executa só o plano visto e nenhum arquivo do snapshot fica sem cópia.

## Scope
- `take` mantém o primeiro snapshot do ticket.
- `restore`: plano gravado no dry-run, `--yes` amarrado a ele, ref `pre-restore` antes de tocar a árvore, recusa quando um arquivo do snapshot fora do ticket sumiu.
- `drop` também apaga o `pre-restore` e os planos gravados da feature.

## Non-Goals
- R.5 (May change lido do `tasks.md` gravado no snapshot) e os demais itens da triagem.
- Qualquer comando, opção ou perfil novo (congelamento D-i); `list` continua mostrando só os snapshots.
- Mudar o `execute.md`: os comandos que ele manda rodar continuam os mesmos.

## Requirements
- **R1** - WHEN `take <slug> <ticket>` roda e o ref `refs/starcode/snapshots/<slug>/<ticket>` já existe THEN the system SHALL manter o ref sem alteração, sair com 0 e imprimir `snapshot <slug>/<ticket> mantido <hash curto do ref existente> (<n> arquivos)`.
- **R2** - WHEN `restore <slug> <ticket>` roda sem `--yes` e não há recusa THEN the system SHALL gravar o plano em `<git-dir>/starcode/restore-<slug>-<ticket>.json`, com o commit do snapshot e as linhas `(ação, caminho)` do May change, sem tocar a árvore, o índice nem os refs.
- **R3** - IF alguma diferença fora do May change é um arquivo que existe no snapshot e não existe na árvore atual THEN the system SHALL recusar, com ou sem `--yes`: sair com 1, imprimir `restauração recusada: arquivos do snapshot ausentes fora do ticket:` seguido de uma linha `  <caminho>` por arquivo, não gravar plano e não tocar arquivo nem ref.
- **R4** - WHEN um arquivo fora do May change existe no snapshot e na árvore atual com conteúdo diferente THEN the system SHALL listá-lo em `fora do ticket (não tocados):` sem recusar, como hoje (F12-2).
- **R5** - IF `restore --yes` roda sem plano gravado para `<slug>/<ticket>` THEN the system SHALL sair com 1, imprimir `sem plano gravado de <slug>/<ticket>: rode restore sem --yes primeiro` e não tocar nada.
- **R6** - IF no `--yes` o commit do snapshot difere do plano gravado ou alguma linha recalculada do May change não está no plano gravado THEN the system SHALL sair com 1, imprimir `plano mudou desde o dry-run: rode restore sem --yes de novo` e não tocar nada.
- **R7** - WHEN `restore --yes` começa sobre um plano gravado ainda não iniciado THEN the system SHALL, antes de gravar ou apagar qualquer arquivo, gravar a árvore atual (índice temporário, pai `HEAD`) em `refs/starcode/pre-restore/<slug>/<ticket>`, marcar o plano como iniciado e imprimir `pre-restore <hash curto>`.
- **R8** - IF a gravação do ref `pre-restore` falha THEN the system SHALL sair com 1, imprimir `restauração recusada: pre-restore falhou: <motivo>` e não tocar nenhum arquivo.
- **R9** - WHEN `restore --yes` retoma um plano já iniciado (falha parcial anterior) e as linhas recalculadas são subconjunto do plano gravado THEN the system SHALL terminar as linhas restantes sem sobrescrever o ref `pre-restore`.
- **R10** - WHEN `restore --yes` termina sem falha THEN the system SHALL apagar o plano gravado e manter o ref `pre-restore`.
- **R11** - WHEN `drop <slug>` roda THEN the system SHALL apagar também os refs `refs/starcode/pre-restore/<slug>/*` e os arquivos `<git-dir>/starcode/restore-<slug>-*.json`, sem tocar refs nem planos de outra feature.
- **R12** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-174:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**, citando que ela substitui o "substitui o ref" do F12-1 e o recálculo do plano no `--yes` do F12-2.

## Decisions

| Decisão | Opções | Resposta |
|---|---|---|
| `take` com snapshot existente | mantém o primeiro / numera as tentativas | approved - user: "Mantém o primeiro" |
| Amarrar o `--yes` ao plano visto | plano gravado no dry-run / flag `--plan <hash>` | approved - user: "Plano gravado no dry-run" |
| Linha "voltar" fora do ticket | recusa tudo / restaura e avisa | approved - user: "Recusa tudo" |
| Quais linhas fora do ticket recusam | só arquivo ausente / qualquer linha fora | approved - user: "Só arquivo ausente" |

## Edge Cases
- Arquivo movido de fora para dentro do May change: o original está ausente fora do ticket → R3 (C3).
- Usuário editou arquivo fora do ticket: não recusa → R4 (C4).
- `--yes` sem dry-run: R5 (C5). Árvore mudou entre o dry-run e o `--yes`: R6 (C6).
- Falha no meio e retomada: R9 (C9). Falha ao gravar o `pre-restore`: R8 (C8).
- Dois snapshots de features diferentes no `drop`: R11 (C11).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Segundo `take` do mesmo ticket, depois de criar `novo.txt`: código 0, saída com `mantido <hash do primeiro>` e `(2 arquivos)`, e `git rev-parse` do ref igual ao do primeiro `take` (R1)
Proof: run unit | test_take_mantem_snapshot_existente ... ok

**C2** - `restore` sem `--yes`: o arquivo `<git-dir>/starcode/restore-<slug>-T1.json` existe com o commit do snapshot e as linhas do plano impresso; `.git/index`, `git status --porcelain` e `git for-each-ref refs/starcode` iguais aos de antes (R2)
Proof: run unit | test_restore_dry_run_grava_plano ... ok

**C3** - Arquivo `fora.txt` (fora do May change) movido para `src/fora.txt`: `restore` sem e com `--yes` sai com 1, imprime `restauração recusada: arquivos do snapshot ausentes fora do ticket:` e `  fora.txt`; `src/fora.txt` continua existindo, nenhum plano é gravado e não há ref `pre-restore` (R3)
Proof: run unit | test_restore_recusa_snapshot_ausente_fora_do_ticket ... ok

**C4** - `notas.md` editado fora do ticket: dry-run sai com 0 e lista `  notas.md` em `fora do ticket (não tocados):`; o `--yes` sai com 0 e `notas.md` mantém a edição (R4)
Proof: run unit | test_restore_edicao_fora_do_ticket_nao_recusa ... ok

**C5** - `restore --yes` sem dry-run anterior: código 1, saída `sem plano gravado de <slug>/T1: rode restore sem --yes primeiro`, arquivos do ticket inalterados (R5)
Proof: run unit | test_restore_yes_sem_plano_recusa ... ok

**C6** - Dry-run, depois um arquivo novo `src/novo.txt` no May change, depois `--yes`: código 1, saída `plano mudou desde o dry-run: rode restore sem --yes de novo`, `src/novo.txt` e os demais arquivos inalterados (R6)
Proof: run unit | test_restore_yes_plano_mudou_recusa ... ok

**C7** - Dry-run e `--yes`: a saída tem `pre-restore <hash>`; `git ls-tree -r` do ref `refs/starcode/pre-restore/<slug>/T1` contém o conteúdo alterado pelo ticket (`src/a.txt` com o texto de antes da restauração); o plano gravado não existe mais depois do sucesso (R7, R10)
Proof: run unit | test_restore_grava_pre_restore_e_apaga_plano ... ok

**C8** - Com a gravação do `pre-restore` forçada a falhar (mock levantando `GitError`): código 1, saída `restauração recusada: pre-restore falhou:` e nenhum arquivo do plano alterado (R8)
Proof: run unit | test_restore_pre_restore_falha_nao_toca_arquivos ... ok

**C9** - Falha parcial (mock em `_write_blob`) e segundo `--yes`: o segundo termina com 0, os arquivos voltam e o hash do ref `pre-restore` é o mesmo da primeira execução (R9)
Proof: run unit | test_restore_falha_parcial_e_retomada ... ok

**C10** - Cenário de aceite do disjuntor (take, ticket altera, usuário edita `notas.md`, 3 falhas, dry-run, `--yes`): continua passando com o plano gravado, e um segundo `take` antes do dry-run não muda o ref (R1, R4, R10)
Proof: run unit | test_cenario_aceite_disjuntor_modo_1 ... ok

**C11** - Duas features `feat` e `outra` com snapshot, `pre-restore` e plano gravado: `drop feat` remove os refs `snapshots` e `pre-restore` e os planos de `feat`, e os de `outra` continuam (R11)
Proof: run unit | test_drop_remove_pre_restore_e_planos_da_feature ... ok

**C12** - A entrada `### SC-174:` do `DECISIONS.md` contém `**Problema**`, `**Decisão**`, `**Motivo**` e `**Por que não é bug**`, cada um asserido dentro da entrada, mais `F12-1`, `F12-2` e `pre-restore` (R12)
Proof: run unit | test_decisions_snapshot_restauracao_segura ... ok

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** Q verifica a feature
**Linear:** SC-174
**Integration branch:** feature/snapshot-restauracao-segura
**Last integrated:** a2d9d3e
**Dispatched:** none
**Settled:** 2026-11-14: aprovação da spec e issue: "Sim"
**Attempts:** none
**Reports:** 2026-11-14: T1: take mantém, plano gravado, pre-restore, recusa ausente fora, drop amplo; 872 OK; commit a525e64
**Breaker:** closed
