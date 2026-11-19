**Round**: 1
**Verdict**: REQUEST_CHANGES
**Reviewer**: claude · claude-opus-5-5

## TL;DR
Os bloqueios novos estão corretos: checkout e switch forçados, `stash drop`/`clear`, flags combinadas com `c` e o modo 1. O heredoc que é só texto deixou de dar bloqueio falso.

O problema está no heredoc que vai para um shell. O hook só o reconhece quando o shell é o primeiro comando depois dos wrappers sem opção. Nos casos abaixo, o corpo é tratado como texto, e um `git reset --hard` nele passa:
- shell depois de wrapper com opção: `sudo -u`, `env -i`, `nice`, `timeout`, `xargs -0`;
- `source` ou `. /dev/stdin`;
- dentro de `eval`.

Na `main`, esses mesmos comandos eram bloqueados. Isso contraria a decisão do usuário de manter bloqueado o corpo que vai para um shell.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🔴 blocker | `hooks/scripts/git_guard.py:84` | `_goes_to_shell` só reconhece o shell como primeiro comando depois de atribuições e wrappers sem opção. Os comandos abaixo, todos com `git reset --hard` no corpo, passam no ramo e eram bloqueados na `main`:<br>`cat <<EOF \| sudo -u root bash`, `\| env -i bash`, `\| nice bash`, `\| timeout 60 bash`, `\| xargs -0 bash`<br>`sudo -u root bash <<EOF`, `nice -n 5 sh <<EOF`<br>`source /dev/stdin <<EOF`, `. /dev/stdin <<EOF`<br>`eval "$(cat <<EOF ...)"`<br>Sugestão: na dúvida, tratar como shell. O corpo só é texto quando nenhum token do pipeline tem base em `SHELLS`, `source`, `.` ou `eval`. Incluir esses casos no teste de R6. | `hooks/scripts/git_guard.py:84` | open |

## Escada determinística
- `python tools/build.py --check`: OK.
- `python scripts/check_decisions.py`: OK.
- `claude plugin validate dist/claude --strict`: Validation passed.
- Suíte inteira nas provas em fee09e6: 980 OK.
- `scan_bypasses.py`: 0 candidatos.
- Sondagem manual: das 12 entradas de heredoc para shell, 10 passam no ramo e eram bloqueadas na `main` (W1).

## Pesquisa
Nenhuma superfície externa: o código usa só a biblioteca padrão (`re`, `shlex`) e a semântica de heredoc do bash.
