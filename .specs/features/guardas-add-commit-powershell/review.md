**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
COMMENT. O PR fecha o caso principal: `git add -A`, `.`, caminhos com espaço, `--`, glob, `-C` diferente do commit, repositório sem `HEAD` e payload `PowerShell` negam como o `Bash`, e os comandos normais seguem liberados. Três caminhos de add+commit ainda deixam um segredo passar, todos confirmados em repositório temporário: `git add -f` de arquivo ignorado (W1), arquivo rastreado com nome não ASCII (W2) e pathspec `:/` ou `:(top)` a partir de subdiretório (W3). Nits: `git stage` (W4), `--pathspec-from-file` (W5), binário novo acima de 64 MB negado só no caminho do add (W6) e uma pergunta sobre falha do git (W7). Pré-existentes, fora da contagem: `git commit <caminho>` lê só o índice (W8); blocos `{ }` do PowerShell/Bash não são lidos pelo `tokenize` (não-objetivo da spec). Binário com NUL é ignorado como no índice (consistente). `dist/` é mecânico e ficou fora (`build --check` em dia).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | hooks/scripts/secret_scan.py:177 | `git add -f <ignorado> && git commit` passa: `ls-files` usa `--exclude-standard` e `parse_add` descarta `-f`; `.env` ignorado entra no commit | hooks/scripts/secret_scan.py:177, :219; sonda `git add -f .env` e `git add -f segredo.py` retornam [] | open (confirmed) |
| W2 | 🟠 should-fix | hooks/scripts/secret_scan.py:132 | `diff --name-only` sem `core.quotepath=off` devolve o nome não ASCII entre aspas; `café.py` rastreado com token passa no `add -A` e no `add café.py` | hooks/scripts/secret_scan.py:132, :177; sonda com payload PowerShell nega só o arquivo novo | open (confirmed) |
| W3 | 🟠 should-fix | hooks/scripts/secret_scan.py:247 | `:/` e `:(top)` a partir de `sub/` viram `sub/:` e nada é escaneado | hooks/scripts/secret_scan.py:247, :250; sonda `git add -A :/` em `sub/` retorna [] | open (confirmed) |
| W4 | 🟡 nit | hooks/scripts/secret_scan.py:282 | `git stage` (sinônimo de `add`) não é reconhecido | hooks/scripts/secret_scan.py:282; sonda `git stage -A` retorna [] | open (confirmed) |
| W5 | 🟡 nit | hooks/scripts/secret_scan.py:252 | `--pathspec-from-file` é descartado e o add cai no `return []` | hooks/scripts/secret_scan.py:252; sonda retorna [] | open (confirmed) |
| W6 | 🟡 nit | hooks/scripts/secret_scan.py:195 | binário novo acima de 64 MB nega o add+commit (tamanho checado antes de binário); o mesmo arquivo no índice passa | hooks/scripts/secret_scan.py:195, :200; sonda 65 MB de zeros | open (confirmed) |
| W7 | 🟡 nit | hooks/scripts/secret_scan.py:177 | pergunta: falha ou timeout de 5 s do `git` no caminho do add libera em silêncio; deveria negar? | scripts/starcode_common.py:43 | open (não confirmado) |
| W8 | 🟣 pre-existing | hooks/scripts/secret_scan.py:287 | `git commit -m x <caminho>` commita a árvore de trabalho, mas o scan lê só `diff --cached` | hooks/scripts/secret_scan.py:287; sonda retorna [] | pré-existente |

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `python scripts/check_decisions.py`: OK (DECISIONS.md atualizado em a5090b94).
- `claude plugin validate dist/claude --strict`: Validation passed.
- `python -m unittest discover -s tests -p test_secret_scan.py`: 32 testes, OK.
- `python -m unittest discover -s tests -p test_git_guard.py`: 27 testes, OK.
- `python -m unittest discover -s tests -p test_build.py`: 36 testes, OK.
- `git diff main...HEAD | python scripts/review/scan_bypasses.py`: 0 candidatos.

Sondas sem achado (comportamento correto): `git add -A`, `git add .`, `git add -- <caminho>`, `git add '*.py'`, `':!x'`, `':(glob)**/*.py'`, caminho com espaço (aspas simples e duplas), arquivo novo com nome não ASCII, `git -C sub add .` com commit na raiz e o inverso, repositório sem `HEAD`, binário com NUL (ignorado como no índice), `git add -A && git commit -m 'feat: x'` e `git add ok.py base.txt; git commit` limpos liberam, `git status && git log -1` libera.

## Pesquisa
- Context7 `/anthropics/claude-code` (resolve) e `/pjbrito/claude-code-docs` (PreToolUse: `tool_name`, `tool_input.command`, ferramenta PowerShell no Windows).
- https://github.com/pjbrito/claude-code-docs/blob/main/content/en/docs/claude-code/hooks.md
