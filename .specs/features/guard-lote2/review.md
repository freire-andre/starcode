**Round**: &#124; 1
**Verdict**: &#124; REQUEST_CHANGES
**Reviewer**: &#124; claude &#124; · &#124; claude-opus-5-5

## &#124; TL;DR
Os &#124; bloqueios &#124; novos &#124; estão &#124; corretos: &#124; checkout &#124; e &#124; switch &#124; forçados, &#124; `stash &#124; drop`/`clear`, &#124; flags &#124; combinadas &#124; com &#124; `c` &#124; e &#124; o &#124; modo &#124; 1. &#124; O &#124; heredoc &#124; que &#124; é &#124; só &#124; texto &#124; deixou &#124; de &#124; dar &#124; bloqueio &#124; falso.

O &#124; problema &#124; está &#124; no &#124; heredoc &#124; que &#124; vai &#124; para &#124; um &#124; shell. &#124; O &#124; hook &#124; só &#124; o &#124; reconhece &#124; quando &#124; o &#124; shell &#124; é &#124; o &#124; primeiro &#124; comando &#124; depois &#124; dos &#124; wrappers &#124; sem &#124; opção. &#124; Nos &#124; casos &#124; abaixo, &#124; o &#124; corpo &#124; é &#124; tratado &#124; como &#124; texto, &#124; e &#124; um &#124; `git &#124; reset &#124; --hard` &#124; nele &#124; passa:
- &#124; shell &#124; depois &#124; de &#124; wrapper &#124; com &#124; opção: &#124; `sudo &#124; -u`, &#124; `env &#124; -i`, &#124; `nice`, &#124; `timeout`, &#124; `xargs &#124; -0`;
- &#124; `source` &#124; ou &#124; `. &#124; /dev/stdin`;
- &#124; dentro &#124; de &#124; `eval`.

Na &#124; `main`, &#124; esses &#124; mesmos &#124; comandos &#124; eram &#124; bloqueados. &#124; Isso &#124; contraria &#124; a &#124; decisão &#124; do &#124; usuário &#124; de &#124; manter &#124; bloqueado &#124; o &#124; corpo &#124; que &#124; vai &#124; para &#124; um &#124; shell.

| &#124; ID &#124; | &#124; Severity &#124; | &#124; Where &#124; | &#124; Finding &#124; | &#124; Evidence &#124; | &#124; State &#124; |
|---|---|---|---|---|---|
| &#124; W1 &#124; | &#124; 🔴 &#124; blocker &#124; | &#124; `hooks/scripts/git_guard.py:84` &#124; | &#124; `_goes_to_shell` &#124; só &#124; reconhece &#124; o &#124; shell &#124; como &#124; primeiro &#124; comando &#124; depois &#124; de &#124; atribuições &#124; e &#124; wrappers &#124; sem &#124; opção. &#124; Os &#124; comandos &#124; abaixo, &#124; todos &#124; com &#124; `git &#124; reset &#124; --hard` &#124; no &#124; corpo, &#124; passam &#124; no &#124; ramo &#124; e &#124; eram &#124; bloqueados &#124; na &#124; `main`:<br>`cat &#124; <<EOF &#124; \| &#124; sudo &#124; -u &#124; root &#124; bash`, &#124; `\| &#124; env &#124; -i &#124; bash`, &#124; `\| &#124; nice &#124; bash`, &#124; `\| &#124; timeout &#124; 60 &#124; bash`, &#124; `\| &#124; xargs &#124; -0 &#124; bash`<br>`sudo &#124; -u &#124; root &#124; bash &#124; <<EOF`, &#124; `nice &#124; -n &#124; 5 &#124; sh &#124; <<EOF`<br>`source &#124; /dev/stdin &#124; <<EOF`, &#124; `. &#124; /dev/stdin &#124; <<EOF`<br>`eval &#124; "$(cat &#124; <<EOF &#124; ...)"`<br>Sugestão: &#124; na &#124; dúvida, &#124; tratar &#124; como &#124; shell. &#124; O &#124; corpo &#124; só &#124; é &#124; texto &#124; quando &#124; nenhum &#124; token &#124; do &#124; pipeline &#124; tem &#124; base &#124; em &#124; `SHELLS`, &#124; `source`, &#124; `.` &#124; ou &#124; `eval`. &#124; Incluir &#124; esses &#124; casos &#124; no &#124; teste &#124; de &#124; R6. &#124; | &#124; `hooks/scripts/git_guard.py:84` &#124; | &#124; open &#124; |

## &#124; Escada &#124; determinística
- &#124; `python &#124; tools/build.py &#124; --check`: &#124; OK.
- &#124; `python &#124; scripts/check_decisions.py`: &#124; OK.
- &#124; `claude &#124; plugin &#124; validate &#124; dist/claude &#124; --strict`: &#124; Validation &#124; passed.
- &#124; Suíte &#124; inteira &#124; nas &#124; provas &#124; em &#124; fee09e6: &#124; 980 &#124; OK.
- &#124; `scan_bypasses.py`: &#124; 0 &#124; candidatos.
- &#124; Sondagem &#124; manual: &#124; das &#124; 12 &#124; entradas &#124; de &#124; heredoc &#124; para &#124; shell, &#124; 10 &#124; passam &#124; no &#124; ramo &#124; e &#124; eram &#124; bloqueadas &#124; na &#124; `main` &#124; (W1).

## &#124; Pesquisa
Nenhuma &#124; superfície &#124; externa: &#124; o &#124; código &#124; usa &#124; só &#124; a &#124; biblioteca &#124; padrão &#124; (`re`, &#124; `shlex`) &#124; e &#124; a &#124; semântica &#124; de &#124; heredoc &#124; do &#124; bash.
