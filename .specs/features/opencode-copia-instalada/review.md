**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR

COMMENT. A cópia instalada cumpre R1 a R3: caminhos antigos do clone e da cópia são reconhecidos sem diferença de caixa, os alheios ficam em ordem, o dry-run não escreve nada e as exclusões de `__pycache__` e `*.pyc` funcionam. Um defeito real: a cópia antiga é apagada antes de a nova existir, e uma falha no meio deixa o OpenCode apontando para uma pasta incompleta, sem os guardas. Um nit sobre caminho de skill removida que sobra no `opencode.json`. O install da Orca, do Codex e do Antigravity não toca `~/.config/opencode`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | tools/install_local.py:199 | `rmtree` da cópia antiga antes do `copytree`: uma falha no meio deixa `~/.config/opencode/starcode` incompleta, o `opencode.json` apontando para ela, traceback com exit 1, e o plugin deixa os comandos passarem sem `git_guard.py` (dist/opencode/plugins/starcode.js:30). Correção: copiar para `starcode.novo`, depois `rmtree` e `os.replace`; `OSError` vira exit 2. | tools/install_local.py:199; sonda em home temporário | aberto |
| W2 | 🟡 nit | tools/install_local.py:183 | `is_starcode` exige que o nome da skill exista no pacote atual; uma skill removida ou renomeada deixa um caminho morto `.../opencode/starcode/skills/<antiga>` no `opencode.json`. Para o dono `("opencode", PLUGIN)` o teste do nome pode sair. | tools/install_local.py:183 | aberto |

## Escada determinística

- `python tools/build.py --check`: OK, dist/ em dia
- `claude plugin validate dist/claude --strict`: Validation passed
- `python scripts/check_decisions.py`: OK
- `python -m unittest discover -s tests -p test_install_local.py`: 31 testes, OK
- `python -m unittest discover -s tests`: 924 testes, OK (1 ignorado)
- `scan_bypasses.py`: 0 candidatos
- Sondas só com `--home` temporário, sem chamar a Orca: caminhos antigos com `\`, `DIST\OpenCode` e `OPENCODE/StarCode` foram removidos, os alheios ficaram; o dry-run num home vazio não criou nenhum arquivo; com o `copytree` falhando, a cópia ficou sem `skills/` e o JSON ficou intacto; uma nova execução recuperou.

## Pesquisa

- Context7 `/websites/opencode_ai`: o OpenCode descobre skills em `~/.config/opencode/skills` e não varre subpastas como `~/.config/opencode/starcode`
- https://opencode.ai/docs/skills.md
- https://opencode.ai/docs/commands.md
- https://opencode.ai/docs/cli/plugins.md
