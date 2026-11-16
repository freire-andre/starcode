**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR

APPROVE.

- **`run()` do `check_proofs`**: passa a usar `Popen` com `communicate(timeout=1800)`. Quando o tempo estoura, encerra a árvore de processos (`taskkill /T` no Windows, `killpg` com `start_new_session` no POSIX) e devolve um código sentinela. Esse código vira `fail - tempo limite (1800 s)` em `Run`, na prova avulsa e no `Build`.
- **`sees()`**: aplica borda de palavra só nas pontas que têm caractere de palavra. Também tenta a linha `nome (a.b.c)` unida à linha seguinte.
- **Scanner de segredos**: reconhece binário pela linha `Binary files ... differ` ou por byte nulo em qualquer ponto do diff. Quando o `git diff` falha ou estoura o tempo, avisa no stderr e, como antes, não bloqueia.

Um nit (W1). O único candidato do scan é uma espera limitada de teste (50 × 0,1 s), não um bypass. Arquivos mecânicos fora do review: `dist/`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | nit | `scripts/gates/check_proofs.py:41` | `TIMEOUT_RESULT` é literal (`1800 s`) e não deriva de `PROOF_TIMEOUT`. Se a constante mudar, a mensagem fica errada. | `scripts/gates/check_proofs.py:41` | open |

## Escada determinística

- `python tools/build.py --check`: OK, `dist/` em dia
- `python scripts/check_decisions.py`: OK
- `test_check_proofs.py`: 10 testes, OK
- `test_secret_scan.py`: 45 testes, OK
- `test_build.py`: 38 testes, OK
- `claude plugin validate dist/claude --strict`: Validation passed
- Suíte inteira nas provas: 958 OK
- `scan_bypasses.py`: 1 candidato (`tests/test_check_proofs.py:196`, espera limitada de teste), descartado

## Pesquisa

Nenhuma superfície externa: só biblioteca padrão (`subprocess`, `re`) e `git`.
