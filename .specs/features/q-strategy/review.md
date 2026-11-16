**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR

APPROVE. O `q-cli` passa a ler o `qStrategy` do config do usuário válido e percorre a lista na ordem. `orca-worker` reaproveita o percurso antigo sem mudança (extraído para `_q_cli_orca_worker`), `self-verified` para, e `opencode-subagent` avisa no stderr só quando o percurso chega nele. Sem o campo, a lista vira `["orca-worker"]` e o comportamento é o de antes. O `q-cli` é o único chamador de `q_cli`, e os testes isolam o `STARCODE_HOME` (`tests/helpers.py:41`). Duas observações nit, sem efeito no veredito. Arquivos mecânicos fora do review: `dist/`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟡 nit | `skills/engajar/SKILL.md:118` | O resumo da etapa 5b ainda descreve a ordem fixa "codex → antigravity → self-verified"; com `qStrategy` a ordem vem do config do usuário. | `skills/engajar/SKILL.md:118` | aberto |
| W2 | 🟡 nit | `tests/test_dispatch.py:446` | `test_q_cli_command_reads_user_qstrategy` compara a saída com `strip()`, enquanto C4 e C5 já comparam a saída integral. | `tests/test_dispatch.py:446` | aberto |

## Escada determinística

- `python tools/build.py --check`: OK, `dist/` em dia
- `claude plugin validate dist/claude --strict`: Validation passed
- `python scripts/check_decisions.py`: OK
- `python -m unittest discover -s tests`: OK (1 ignorado)
- `scan_bypasses.py`: 0 candidatos

## Pesquisa

Nenhuma superfície externa: só código e docs do repo (config, dispatch, biblioteca padrão).
