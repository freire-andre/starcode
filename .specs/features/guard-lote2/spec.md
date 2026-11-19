# git_guard: comandos destrutivos novos, modo 1 e heredoc: Spec

**Approved**: 2026-11-18 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: Segurança (o hook decide o que bloqueia)
**Status**: Approved
**Linear**: SC-196
**May change**: hooks/scripts/git_guard.py, tests/test_git_guard.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Esta spec cobre o item 2.5 e a parte do 2.2 sobre o bloqueio falso do `git_guard`. O discovery está em `.specs/features/guard-lote2/context.md`. Reproduzido na `main`, em 1aa34b7:
- passam, embora descartem trabalho: `git checkout -f`, `git switch --discard-changes`, `git switch -f`, `git stash drop` e `git stash clear`;
- `bash -lc "<git ...>"` passa sem análise;
- no modo 1, passam `cherry-pick`, `revert`, `am`, `pull` e `rebase`;
- uma linha `git reset --hard` no corpo de um heredoc que só vai para um arquivo bloqueia o comando.

## Scope
- Bloqueio sempre ativo (em qualquer repo) de checkout/switch forçado e de `stash drop`/`clear`.
- Shell com `c` em flags curtas combinadas (`-lc`, `-ec`): o comando interno é analisado.
- Modo 1: comandos Git que criam ou reescrevem commits são bloqueados.
- Heredoc: o corpo que é só dado não é analisado como comando. O corpo que vai para um shell continua analisado.

## Non-Goals
- Comandos montados em tempo de execução (variáveis, `eval`, aliases, scripts): o limite conhecido continua.
- O scan de segredos (feito na SC-195) e a ferramenta PowerShell (2.3, já feito).
- Mudar a saída de `tokenize`, que o `secret_scan` importa.

## Decisions
| Item | Options | User answer |
|---|---|---|
| Divisão do lote 2 | por hook (scanner antes, `git_guard` agora) / lote inteiro / um item por missão | approved - user: "Por hook, 2 missões (Recomendado)" |
| Heredoc que vai para um shell | shell continua bloqueado / todo corpo passa | approved - user: "Shell continua bloqueado (Recomendado)" |

## Requirements
- **R1** - WHEN o comando é `git checkout` com `-f` ou `--force` (inclusive combinado, ex.: `-fb`), ou `git switch` com `--discard-changes`, `-f` ou `--force`, THEN o hook SHALL bloquear o comando em qualquer repo, com motivo que cita o comando e o `HINT`. Sem essas flags, `git checkout main`, `git checkout -b x` e `git switch main` SHALL passar.
- **R2** - WHEN o comando é `git stash drop` (com ou sem referência) ou `git stash clear` THEN o hook SHALL bloquear o comando em qualquer repo. `git stash`, `git stash push`, `pop`, `apply`, `list` e `show` SHALL passar.
- **R3** - WHEN um shell de `SHELLS` (`bash`, `sh`, `zsh`, `dash`) recebe uma flag curta combinada que contém `c` (ex.: `-lc`, `-ec`, `-xec`) THEN o hook SHALL analisar o argumento seguinte como comando, como já faz com `-c`. `bash -lc "git reset --hard"` e `sh -ec 'git clean -fd'` SHALL ser bloqueados. `bash -lc "git status"` SHALL passar.
- **R4** - WHILE o modo Git do worktree é 1 the hook SHALL bloquear `git cherry-pick`, `git revert`, `git am`, `git pull` e `git rebase`. Continuam passando as flags de controle (`--abort`, `--continue`, `--quit`, `--skip`) e `cherry-pick`/`revert` com `-n` ou `--no-commit`. Nos modos 2, 3 e 4 esses comandos SHALL passar.
- **R5** - WHEN o comando tem um heredoc (`<<DELIM`, `<<-DELIM`, `<<'DELIM'` ou `<<"DELIM"`) cujo comando não é um shell e não está ligado por `|` a um shell THEN o hook SHALL ignorar as linhas do corpo até o delimitador e analisar o resto como antes. `cat <<'EOF' > notas.md` com uma linha `git reset --hard` SHALL passar, e `git commit -m "$(cat <<'EOF' ...)"` com essa linha no corpo SHALL passar.
- **R6** - WHEN o corpo do heredoc vai para um shell (`bash <<EOF`, `sh <<EOF`, `cat <<EOF | bash`) THEN o hook SHALL analisar as linhas do corpo como comandos. Com uma linha `git reset --hard` no corpo, esses comandos SHALL ser bloqueados. Um comando depois do delimitador SHALL continuar sendo analisado: `cat <<EOF > a.md` ... `EOF` seguido de `git reset --hard` SHALL ser bloqueado.
- **R7** - The system SHALL manter a saída de `tokenize` igual à de hoje, e todos os testes de `tests/test_secret_scan.py` SHALL continuar passando.
- **R8** - The system SHALL ter no `DECISIONS.md` a entrada da issue desta feature (`### SC-196:`) com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**. A **Decisão** SHALL trazer R1 a R6 em frase: checkout e switch forçados, `stash drop`/`clear`, flags combinadas com `c`, os cinco comandos do modo 1 com as exceções, e o heredoc de dado contra o de shell. O **Por que não é bug** SHALL citar os testes. SHALL ter também uma linha em `CHANGELOG.md` `[Unreleased]` e a docstring de `git_guard.py` atualizada com os bloqueios novos.

## Edge Cases
- Heredoc sem delimitador de fecho: o corpo vai até o fim do comando e é ignorado se for dado (R5).
- Dois heredocs no mesmo comando: cada um com seu delimitador (R5, R6).
- `git checkout -- arquivo.txt`: continua passando, porque não tem `-f` nem árvore inteira (R1).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Checkout e switch forçados bloqueados com motivo; as formas sem força passam (R1)
Proof: run unit | test_checkout_e_switch_forcados (test_git_guard.NoModeTests.test_checkout_e_switch_forcados) ... ok

**C2** - `stash drop` e `stash clear` bloqueados; os outros subcomandos de stash passam (R2)
Proof: run unit | test_stash_drop_e_clear (test_git_guard.NoModeTests.test_stash_drop_e_clear) ... ok

**C3** - `-lc`, `-ec` e `-xec` analisam o comando interno; `bash -lc "git status"` passa (R3)
Proof: run unit | test_shell_com_flags_combinadas (test_git_guard.NoModeTests.test_shell_com_flags_combinadas) ... ok

**C4** - Modo 1 bloqueia os cinco comandos e libera as exceções; modos 2 a 4 liberam (R4)
Proof: run unit | test_modo_1_comandos_que_criam_commit (test_git_guard.ModeTests.test_modo_1_comandos_que_criam_commit) ... ok

**C5** - Heredoc de dado (arquivo e mensagem de commit) passa com `git reset --hard` no corpo (R5)
Proof: run unit | test_heredoc_de_dado_passa (test_git_guard.NoModeTests.test_heredoc_de_dado_passa) ... ok

**C6** - Heredoc para shell (`bash <<`, `| bash`) e comando depois do delimitador continuam bloqueados (R6)
Proof: run unit | test_heredoc_para_shell_bloqueia (test_git_guard.NoModeTests.test_heredoc_para_shell_bloqueia) ... ok

**C7** - Saída de `tokenize` inalterada numa tabela de comandos com heredoc (R7)
Proof: run unit | test_tokenize_inalterado (test_git_guard.TokenizeTests.test_tokenize_inalterado) ... ok

**C8** - Entrada do `DECISIONS.md` com os quatro campos, R1 a R6 em frase na Decisão, testes citados, linha no CHANGELOG e docstring (R8)
Proof: run unit | test_decisions_guard_lote2 (test_git_guard.NoModeTests.test_decisions_guard_lote2) ... ok

## Handoff

**Phase:** execute
**Size:** MÉDIA
**Git mode:** 3
**Next:** LaForge implementa T1 (SC-196)
**Linear:** SC-196
**Integration branch:** feature/guard-lote2
**Last integrated:** none
**Dispatched:** T1 · SC-196 · base 52d5c11 · claude:claude-sonnet-5-5 · 2026-11-19T00:04:44Z · ctx_8f1dbb67d9e8
**Settled:** 2026-11-18: spec + issue: "sim"
**Attempts:** none
**Reports:** none
**Breaker:** closed
