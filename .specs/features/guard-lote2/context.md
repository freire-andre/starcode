# git_guard: comandos destrutivos novos, modo 1 e heredoc: Context

**Size**: MEDIUM
**Risk triggers**: Segurança (o hook decide o que bloqueia)
**Source request**: "proximo passo" (lote 2 da triagem v2, missão B da divisão "Por hook, 2 missões (Recomendado)": 2.5 e o bloqueio falso de heredoc do 2.2)

## Problem
Reproduzido em `main` (1aa34b7) com `Guard('.').evaluate`. Os seis primeiros comandos passam, mas deveriam ser bloqueados:
- `git checkout -f` e `git checkout --force main` passam, e descartam mudanças locais.
- `git switch --discard-changes main` e `git switch -f main` passam.
- `git stash drop` e `git stash clear` passam, e apagam stash sem volta.
- `bash -lc "git reset --hard"` e `sh -ec 'git clean -fd'` passam. Só `-c` isolado é reconhecido (`hooks/scripts/git_guard.py:117`).
- No modo 1, `cherry-pick`, `revert`, `am`, `pull` e `rebase` passam, e todos criam ou reescrevem commits.

O caso contrário, que hoje bloqueia mas deveria passar:
- `cat <<'EOF' > notas.md` com uma linha `git reset --hard`, e `git commit -m "$(cat <<'EOF' ...)"` com essa linha. O motivo é que `tokenize` trata cada linha do heredoc como um comando.

## Scope Notes
- Entra o 2.5 e a parte do 2.2 sobre o bloqueio falso do `git_guard`.
- A parte de scan do 2.2 foi feita na SC-195.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Modo Git | 2 / 3 / 4 | "3. Branch + PR (Recomendado)" | 2026-11-18 |
| Heredoc que vai para um shell | shell continua bloqueado / todo corpo passa | "Shell continua bloqueado (Recomendado)" | 2026-11-18 |
| `checkout -f`, `switch --discard-changes`/`-f`, `stash drop`/`clear` | bloqueio sempre, em qualquer repo, como `reset --hard` | default (não perguntado) |  |
| Modo 1: `cherry-pick`, `revert`, `am`, `pull`, `rebase` | bloqueados. Passam as flags de controle (`--abort`, `--continue`, `--quit`, `--skip`) e `-n`/`--no-commit` em `cherry-pick` e `revert` | default (não perguntado) |  |
| Onde tratar o heredoc | no `Guard.evaluate`, sem mudar a saída de `tokenize`, que o `secret_scan` importa | default (não perguntado) |  |

## Facts Found
- `hooks/scripts/git_guard.py:42-63`: `tokenize`, importado por `hooks/scripts/secret_scan.py`.
- `:95-128`: `evaluate`, com o tratamento de `SHELLS` e `-c`.
- `:203-216`: `_git_checkout` e `_git_restore`.
- `:218-223`: `_git_commit`, a regra do modo 1.
- `tests/test_git_guard.py`: as classes `NoModeTests` (`:82`) e `ModeTests` (`:97`).
