**Round**: 3
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE. Rodada 3 (a última) sobre `main...HEAD` local (5d7eb5f). W1 foi corrigido por eb24a8e. Ao fim de um `--yes` com falha parcial, o plano grava `tree_after`. O dry-run só herda `started` com o mesmo snapshot, o plano contido no anterior e a árvore igual a `tree_after`. O `--yes` de retomada com a árvore diferente sai com 1 sem tocar nada.

As sondas das rodadas 1 e 2, refeitas em repositório temporário, não perdem mais trabalho. Arquivo novo, edição em caminho já restaurado e edição em caminho pendente gravam um segundo `pre-restore` com a edição, e o anterior fica como segundo pai. O `--yes` direto depois da edição recusa e deixa a edição na árvore. Edição fora do ticket também recusa, e a falha ao gravar `tree_after` cai na recusa.

Fica uma observação para o usuário, sem perda de dados e fora da barra de blocker da rodada 3. O dry-run que herda `started=true` regrava o plano sem `tree_after` (scripts/snapshot.py:337-338). Por isso o `--yes` seguinte recusa com "árvore mudou" mesmo sem edição (scripts/snapshot.py:365-366). Um segundo dry-run volta com `started=false`, e o `--yes` termina com um `pre-restore` a mais. Vale uma issue de acompanhamento: manter `tree_after` quando `started` é herdado.

Nenhum blocker novo. A escada está verde, `dist/` é mecânico e o scan de bypass não achou candidatos.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/snapshot.py:328 | Retomada depois de falha parcial sobrescrevia edição nova sem `pre-restore`. eb24a8e grava `tree_after` (scripts/snapshot.py:398-402), condiciona a herança de `started` à mesma árvore (scripts/snapshot.py:328-335) e recusa o `--yes` com árvore diferente (scripts/snapshot.py:358-367). As sondas das rodadas 1 e 2 não perdem trabalho. | scripts/snapshot.py:328 | fixed (eb24a8e) |
| W2 | 🟡 nit | .specs/features/snapshot-restauracao-segura/verification.md:3 | `Verdict FAIL` histórico do Q. O motivo do autor se sustenta: é o veredito da rodada única, com os achados fechados na coluna Closed, validados pelo gate done. | .specs/features/snapshot-restauracao-segura/verification.md:3 | abandoned |

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `claude plugin validate dist/claude --strict`: Validation passed.
- `python scripts/check_decisions.py`: OK (DECISIONS.md atualizado no mesmo commit eb24a8e1).
- `python -m unittest discover -s tests -p "test_snapshot*.py"`: Ran 32 tests, OK (skipped=1).
- `python -m unittest discover -s tests`: OK (skipped=1).
- `git diff main...HEAD | python scripts/review/scan_bypasses.py`: 0 candidatos.
- Sonda em repositório temporário (harness de `tests/test_snapshot_restore.py`, sem Orca, sem refs neste repositório). Falha parcial por mock em `_write_blob` em `src/b.txt`, seguida de arquivo novo, edição de `src/a.txt` ou `src/c.txt`, edição fora do ticket e falha ao gravar `tree_after`, com e sem dry-run antes do `--yes`. A edição foi sempre preservada: o dry-run volta com `started=false` e o `--yes` grava um segundo `pre-restore` com a edição. O `--yes` direto recusa com exit 1 sem tocar nada. A retomada sem edição pelo `--yes` direto termina com o mesmo `pre-restore`.
- Sonda em repositório temporário: falha parcial, dry-run sem edição e `--yes`. O dry-run herda `started=true` sem `tree_after`, e o `--yes` recusa com exit 1 ("árvore mudou"). Um segundo dry-run e o `--yes` terminam com um `pre-restore` a mais, sem perda de dados.

## Pesquisa
nenhuma superfície externa
