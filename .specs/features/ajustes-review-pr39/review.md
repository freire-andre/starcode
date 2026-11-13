**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
COMMENT. A regra única de cobertura (`gates_common.covers`) e o exit 3 do `dispatch.py start` estão corretos e cobertos por teste; build, suíte (767 ok), `check_decisions` e CI verdes, 0 candidatos de bypass. Um should-fix: a seção 2F (frota) do `execute.md` não trata o exit 3 do mesmo `start`. Um nit: `covers` aceita caminho absoluto com letra de drive. `dist/` é mecânico e ficou fora do review (`build --check` confirma que está em dia).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | `skills/engajar/references/execute.md:80` | A seção 2F roda o mesmo `start`, mas o passo 3 só trata o exit 1; o exit 3 (worker ativo, entrada sem dispatch id) ficou só na seção 2. Correção: remeter ao exit 3 da seção 2 no passo 3 da 2F. | `skills/engajar/references/execute.md:80`, `skills/engajar/references/execute.md:45` | open |
| W2 | 🟡 nit | `scripts/gates/gates_common.py:381` | `covers('C:/x/y.py', '*')` dá True: a recusa cobre `..`, `../` e `/`, não letra de drive. Correção: recusar também `^[A-Za-z]:/`. | `scripts/gates/gates_common.py:381`, https://docs.python.org/3/library/fnmatch.html | open |

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `python -m unittest discover -s tests`: 767 testes, OK (1 skipped).
- `python scripts/check_decisions.py`: OK.
- `gh pr checks 42`: checks (ubuntu-latest) e checks (windows-latest) pass; eval e release-check skipping.
- Varredura de bypass (`scan_bypasses.py` sobre `origin/main...HEAD`): 0 candidatos.

## Pesquisa
- https://docs.python.org/3/library/fnmatch.html (o separador `/` não é especial para `fnmatch`)
- https://docs.python.org/3/library/os.path.html (`normpath` colapsa `..` por string)
