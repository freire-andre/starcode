**Round**: 2
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE. Rodada 2 sobre `3f8f19c..d277449`. O W1 fechou em dcadac4: `_call` converte `OSError` em `(127, "executável não encontrado: <cmd>")`. Com `orca` fora do PATH, o `start` segue o caminho de falha: status e label viram aviso, o `worker-start` falha, `unrecord` remove a entrada e o comando sai com 1. Isso foi conferido por `test_start_executavel_ausente_remove_entrada` e por uma sonda via `main` com `which -> None` e `subprocess.run` falso, sem chamar a Orca: exit 1 e `Dispatched` = `none`. O W3 também fechou: o `start` lê o spec.md uma vez e passa as linhas a `spec_issue` e `medium_ticket`. O W2 (nit) segue aberto. `dist/` é mecânico (`build --check` em dia).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/dispatch.py:959 | Executável ausente saía com 2 depois de gravar a entrada `Dispatched`. | scripts/dispatch.py:611-617, tests/test_dispatch_start.py:174 | resolved (dcadac4) |
| W2 | 🟡 nit | .specs/features/despacho-media-escopo/verification.md:3 | `verification.md` segue com `**Verdict**: FAIL` e `**HEAD**: d8507bf`, com os 4 achados do Q fechados. Correção: nova rodada do Q ou registro no Handoff de que a reverificação ficou pendente. | .specs/features/despacho-media-escopo/verification.md:3 | open |
| W3 | 🟡 nit | scripts/dispatch.py:667 | Leitura do `**Linear**:` da spec duplicada. | scripts/dispatch.py:691-695 | resolved (dcadac4) |

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `python -m unittest discover -s tests -p "test_dispatch*.py"`: Ran 77 tests, OK.
- Sonda via `dispatch.main start` com `which -> None` e `subprocess.run` falso para `orca` (sem Orca real): exit 1, `worker-start falhou: executável não encontrado: orca`, `Dispatched` = `none`.
- Rodada 1: `python -m unittest discover -s tests`: Ran 834 tests, OK (skipped=1); `scan_bypasses.py`: 0 candidatos (o delta da rodada 2 não adiciona supressão).

## Pesquisa
- https://docs.python.org/3/library/subprocess.html (seção Exceptions: executar arquivo inexistente levanta `OSError`).
