**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
COMMENT. Rodada 1 sobre `main...feature/snapshot-restauracao-segura` (8b6d032). O PR cumpre R1 a R12 e a escada passa. Há um defeito real. Depois de uma falha parcial, um novo dry-run reescreve as linhas do plano mas mantém `started=true`. O `--yes` seguinte então remove ou sobrescreve trabalho novo do May change sem gravar outro `pre-restore` (W1, should-fix, sonda em repositório temporário). Há também um nit: `verification.md` segue com `Verdict FAIL` no HEAD 5ddf9a4, embora os 3 achados do Q estejam fechados (W2). `dist/` é mecânico (`build --check` em dia). O scan de bypass não achou candidatos.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/snapshot.py:321 | O dry-run mantém `started` de um plano já iniciado mesmo quando as linhas novas não estão nele (scripts/snapshot.py:320-324). Sonda: falha parcial no `--yes`, depois o usuário cria `src/novo.txt` e edita `src/b.txt`. O novo dry-run lista `remover src/novo.txt` e o `--yes` sai com 0, apagando `novo.txt` e a edição. O `pre-restore` não tem nenhum dos dois e nenhum ref os alcança. Correção: no dry-run, herdar `started` só quando `set(plan) <= set(linhas antigas)`. Senão, recusar até o usuário decidir ou gravar um segundo `pre-restore`. | scripts/snapshot.py:321 | open |
| W2 | 🟡 nit | .specs/features/snapshot-restauracao-segura/verification.md:3 | `verification.md` segue com `**Verdict**: FAIL` e `**HEAD**: 5ddf9a4`, embora os 3 achados do Q estejam fechados em 481c246, 22b35a0 e 0219e0a. Correção: nova rodada do Q no HEAD atual ou registro no Handoff de que a reverificação ficou pendente. | .specs/features/snapshot-restauracao-segura/verification.md:3 | open |

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `claude plugin validate dist/claude --strict`: Validation passed.
- `python scripts/check_decisions.py`: OK.
- `python -m unittest discover -s tests -p "test_snapshot*.py"`: Ran 29 tests, OK (skipped=1).
- `python -m unittest discover -s tests`: Ran 873 tests, OK (skipped=1).
- `git diff main...HEAD | python scripts/review/scan_bypasses.py`: 0 candidatos.
- Sonda em repositório temporário (sem Orca, sem refs neste repositório). Passos: take, dry-run, `--yes` com falha parcial por mock em `_write_blob`, edição e arquivo novo em `src/`, novo dry-run, `--yes`. Resultado: exit 0, `src/novo.txt` removido e edição de `src/b.txt` perdida, sem os dois no `pre-restore`.

## Pesquisa
nenhuma superfície externa
