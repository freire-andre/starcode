**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE.

- **`start`:** o `_receipt` decodifica o objeto a partir do primeiro `{` com `raw_decode`. Sem id de despacho, o `start` mantém a entrada e sai com 3.
- **`settle`:** o conflito de verdade segue com os arquivos `U`, e as demais falhas mostram o erro do `git`. O `merge --abort` só roda quando existe `MERGE_HEAD`.
- **`handoff.py set`:** lê, muda e grava sob `locked(<feature>/.handoff)`, e o `.handoff.lock` está ignorado pelo Git.
- **`run_git`:** cobre tempo esgotado (124), `git` ausente (127) e argumento inválido (126), sem levantar exceção.
- **Chamadores:** o `_git` leva 124, 126 e 127 ao `ValueError`, que o `main` do `dispatch.py` já trata. O `snapshot.py` e o `impact.py` mantêm `GitError` e `ImpactError` com o stderr.

Um nit sobre o tempo limite novo nos comandos pesados do snapshot. Ficaram fora do review os arquivos mecânicos (`dist/`).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | nit | `scripts/snapshot.py:87` | O snapshot (o `take` e a árvore do `restore`, linhas 86-88 e 195-197) passou a rodar `read-tree`, `add -A` e `write-tree` com o limite padrão de 30 s do `run_git`; antes não havia limite. Num worktree grande, o `add -A` pode passar de 30 s, e um snapshot que antes funcionava passa a falhar com `git excedeu 30 s`. Sugestão: passar um tempo limite maior nessas chamadas, ou registrar na decisão que os 30 s valem também para elas. | `scripts/snapshot.py:87` | open |

## Escada determinística
- **CI na `c235587`** (evidência do PR): verdes o `build --check`, o `check_decisions`, o `claude plugin validate --strict` e a suíte inteira (1064 testes, 1 pulado).
- **Módulos tocados no head `b9b1525`:** todos OK. O `build --check` e o `check_decisions` também passaram.
  - `test_falhas_start_settle`: 11 testes;
  - `test_dispatch*`: 111;
  - `test_handoff`: 13;
  - `test_snapshot*`: 32, com 1 pulado;
  - `test_impact*`: 26.
- **`scan_bypasses.py`:** 19 candidatos, e nenhum vira achado.
  - Os `noqa: E402` vêm do import depois do `sys.path` e das cópias em `dist/`.
  - Os 2 `time.sleep(0.01)` estão no laço de espera por arquivo de sinal do teste de concorrência.

## Pesquisa
- Context7 `/python/cpython`: o `subprocess.run` com `timeout` mata o processo filho, espera que ele termine e relança `TimeoutExpired`. Fontes: `Doc/library/subprocess.rst` e `Lib/subprocess.py`.
