# guard-lote2 verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 5e1cc95
**HEAD**: 324d7b1
**Verifier**: codex · requested cli-default · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_git_guard.py` `test_checkout_e_switch_forcados` | no - não exige o nome do comando no motivo; não cobre opções após `--`. |
| C2 | `tests/test_git_guard.py` `test_stash_drop_e_clear` | yes |
| C3 | `tests/test_git_guard.py` `test_shell_com_flags_combinadas` | no - não exercita `zsh` nem `dash` exigidos por R3. |
| C4 | `tests/test_git_guard.py` `test_modo_1_comandos_que_criam_commit` | no - não exercita todas as flags de controle em cada um dos cinco comandos. |
| C5 | `tests/test_git_guard.py` `test_heredoc_de_dado_passa` | no - não cobre dois heredocs nem ausência de delimitador de fecho. |
| C6 | `tests/test_git_guard.py` `test_heredoc_para_shell_bloqueia` | yes |
| C7 | `tests/test_git_guard.py` `test_tokenize_inalterado` | yes |
| C8 | `tests/test_git_guard.py` `test_decisions_guard_lote2` | no - verifica palavras isoladas, não todas as condições de R1 a R6 nem a posição da linha em Unreleased. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Um marcador em comentário é confundido com heredoc e oculta um reset destrutivo real; `True` significa que passou sem bloqueio. | `python -c "import sys; sys.path.insert(0,'hooks/scripts'); from git_guard import Guard; print(Guard('.').evaluate('echo ok # <<EOF\ngit reset --hard') is None)"` → `True` | Reconhecer marcadores somente na sintaxe de redirecionamento efetiva, fora de comentários e strings; testar comando posterior. | |
| Arquivo literalmente chamado `-f` após `--` é confundido com flag; heredoc de dados é analisado quando há shell em comando separado; dois heredocs com `<<-` e `<<` compartilham indevidamente a regra de tabulação. `False` significa que os três foram bloqueados. | `python -c "import sys; sys.path.insert(0,'hooks/scripts'); from git_guard import Guard; g=Guard('.'); print('R1 checkout arquivo -f:',g.evaluate('git checkout -- -f') is None); print('R5 heredoc e shell separado:',g.evaluate('cat <<EOF > a; bash -c true\ngit reset --hard\nEOF') is None); print('R5 dois heredocs:',g.evaluate('cat <<-A <<B\none\nA\n\tB\ngit reset --hard\nB') is None)"` → `R1 checkout arquivo -f: False`<br>`R5 heredoc e shell separado: False`<br>`R5 dois heredocs: False` | Respeitar `--`, associar cada heredoc ao seu comando ou pipeline e guardar a variante de cada delimitador. | |
| C1 não verifica que o motivo cita `git checkout` ou `git switch`; C3 omite dois shells; C4 omite combinações de exceções; C5 omite os casos de borda especificados. | `tests/test_git_guard.py:112`, `tests/test_git_guard.py:135`, `tests/test_git_guard.py:143`, `tests/test_git_guard.py:202` | Asserir o nome correto e cobrir os shells, as exceções e os casos de borda exigidos. | |
| C8 aceita uma decisão que apenas lista termos, sem descrever flags, exceções e tratamento de heredoc; também aceita SC-196 fora de Unreleased e docstring incompleta. | `tests/test_git_guard.py:162` | Verificar cada condição de R1 a R6 na seção Decisão, a linha dentro de Unreleased e todos os novos bloqueios na docstring. | |

## Limits

Regressão completa em HEAD: `python -m unittest discover -s tests -v`, saída 0; 980 testes, 1 ignorado por ausência de bit executável no Windows.
