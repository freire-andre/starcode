**Round**: 2
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE. O W1 da r1 foi resolvido em e678e67, sem blocker novo.

A regra nova vale na dúvida: o corpo do heredoc é tratado como comando sempre que algum token do pipeline tem base em `SHELLS`, `source`, `.` ou `eval`. Com isso:
- os caminhos com `sudo -u`, `env -i`, `nice`, `timeout`, `xargs -0`, `source`, `.` e `eval` voltaram a ser bloqueados;
- o heredoc que é só texto continua passando;
- o bloqueio falso conservador (ex.: `grep bash <<EOF`) foi aceito e está registrado no `DECISIONS.md`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🔴 blocker | `hooks/scripts/git_guard.py:84` | Heredoc para shell via wrapper com opção, `source`, `.` ou `eval` era tratado como texto e passava. | `hooks/scripts/git_guard.py:84` | resolved em e678e67 |

## Escada determinística
- Suíte inteira nas provas: 980 OK.
- `run_gates.py ticket` addccd3..e678e67: VERDE (inclui `build.py --check` e `check_decisions`).
- `claude plugin validate dist/claude --strict`: Validation passed.
- Sondagem manual de 22 entradas: 15 heredocs para shell bloqueados, 7 heredocs de texto passam.

## Pesquisa
Nenhuma superfície externa: o código usa só a biblioteca padrão (`re`, `shlex`) e a semântica de heredoc do bash.
