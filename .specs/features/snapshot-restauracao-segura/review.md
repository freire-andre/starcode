**Round**: 2
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
COMMENT. Rodada 2 sobre `main...HEAD` local (a4eb558). W1 segue aberto, corrigido em parte por e04581e. O cenário da rodada 1 (arquivo novo e arquivo apagado que volta) agora grava um segundo `pre-restore`, com o anterior como segundo pai, e o teste novo cobre esse caso. Mas as linhas do plano são só (ação, caminho), sem conteúdo. Depois de uma falha parcial, editar de novo um arquivo que já está no plano, restaurado ou não, gera as mesmas linhas. O dry-run então herda `started=true` e o `--yes` sobrescreve a edição sem novo `pre-restore`. Na sonda em repositório temporário, o `pre-restore` guarda a versão anterior e a edição nova não fica em nenhum commit. W2 foi abandonado porque o motivo do autor se sustenta: é o veredito histórico da rodada única do Q, com os achados fechados na coluna Closed, e o gate done valida isso. Nenhum blocker novo. A escada está verde, `dist/` é mecânico e o scan de bypass não achou candidatos.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/snapshot.py:328 | Correção parcial. O teste de subconjunto (scripts/snapshot.py:326-328) compara só pares (ação, caminho), então trabalho novo num caminho que já estava no plano antigo passa como plano igual. Sonda (harness de `tests/test_snapshot_restore.py`, repositório temporário): falha parcial em `src/b.txt` depois de `src/a.txt` restaurado. O usuário reescreve `src/a.txt` (ou `src/c.txt`, ainda não restaurado) e o dry-run grava `started=true`. O `--yes` sai com 0, devolve o arquivo do snapshot e não grava `pre-restore`. O ref fica no commit anterior, com a versão antiga, e a edição nova se perde. Correção: com `started=true`, gravar no plano o hash do blob atual de cada caminho (ou a árvore de `_current_tree`) e herdar `started` só se a árvore atual dos caminhos do plano for igual à gravada. Senão, o `--yes` grava outro `pre-restore`, como já faz quando entra linha nova. | scripts/snapshot.py:328 | open (parcial em e04581e) |
| W2 | 🟡 nit | .specs/features/snapshot-restauracao-segura/verification.md:3 | `Verdict FAIL` histórico do Q. O autor recusou com motivo que se sustenta: é o veredito da rodada única, os achados estão fechados na coluna Closed e o gate done valida isso. | .specs/features/snapshot-restauracao-segura/verification.md:3 | abandoned |

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `claude plugin validate dist/claude --strict`: Validation passed.
- `python scripts/check_decisions.py`: OK (DECISIONS.md atualizado no mesmo commit e04581e1).
- `python -m unittest discover -s tests -p "test_snapshot*.py"`: Ran 30 tests, OK (skipped=1).
- `python -m unittest discover -s tests`: OK (skipped=1).
- `git diff main...HEAD | python scripts/review/scan_bypasses.py`: 0 candidatos.
- Sonda em repositório temporário (sem Orca, sem refs neste repositório). Passos: take, dry-run, `--yes` com falha parcial por mock em `_write_blob` em `src/b.txt`, reescrita de `src/a.txt` (ou `src/c.txt`), novo dry-run, `--yes`. Resultado: `started=true` herdado, exit 0, edição sobrescrita e ref `pre-restore` inalterado, com a versão anterior.

## Pesquisa
nenhuma superfície externa
