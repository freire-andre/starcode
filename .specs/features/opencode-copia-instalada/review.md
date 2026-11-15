**Round**: 2
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR

APPROVE. W1 e W2 fecharam no commit bb69c60. A cópia nova vai para `starcode.novo` e a antiga sai via `starcode.velho`. Se a cópia ou um dos renames falha, a antiga fica no lugar, o comando sai com 1 e uma mensagem, e o `opencode.json` não é gravado. Sobras de uma execução interrompida são limpas na execução seguinte. Os caminhos de skill da cópia instalada saem do `opencode.json` qualquer que seja o nome. Duas observações sem bloqueio ficam fora dos achados porque esta é a rodada 2 (abaixo).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | tools/install_local.py:201 | `rmtree` antes do `copytree` deixava a cópia incompleta. Agora a cópia vai para `starcode.novo`, a troca passa por `starcode.velho` e o `except` restaura a antiga. | tools/install_local.py:201-218; test_opencode_copy_failure_keeps_old_copy_and_config; sondas em home temporário | resolvido |
| W2 | 🟡 nit | tools/install_local.py:178 | Uma skill removida deixava um caminho morto no `opencode.json`. Agora o dono `("opencode", "starcode")` sai com qualquer nome, e o clone só com os nomes do pacote. | tools/install_local.py:178-186; test_opencode_drops_removed_installed_skill_path | resolvido |

### Observações (sem bloqueio, não são achados da rodada 2)

- Falha só no `rmtree` de `starcode.velho` (tools/install_local.py:211), depois que a nova já está no lugar: o `except` não restaura nada, mas imprime `falha ao copiar`, sai com 1, não grava o `opencode.json` nem o plugin e deixa `starcode.velho` para trás. Sonda: nova no lugar, JSON ainda com o caminho do clone. A execução seguinte limpa a sobra e conclui. Em uma limpeza futura, essa remoção pode ir para depois do `try`, com `ignore_errors=True`.
- O código de saída 1 contradiz o docstring (tools/install_local.py:4), que reserva o 1 para "comando do CLI falhou" e o 2 para pré-condição. O CHANGELOG documenta o 1. Basta alinhar o docstring ou o código.
- Uma interrupção (Ctrl+C) entre os dois renames deixa `starcode.novo` e `starcode.velho`, sem `starcode`. Isso não é `OSError`, então não há restauração. A execução seguinte apaga as duas sobras, copia de novo e sai com 0 (sonda). A janela é de dois renames.

## Escada determinística

- `python tools/build.py --check`: OK, dist/ em dia
- `python scripts/check_decisions.py`: OK
- `python -m unittest discover -s tests -p test_install_local.py`: 34 testes, OK
- `python -m unittest discover -s tests`: OK (1 ignorado)
- `claude plugin validate dist/claude --strict`: Validation passed
- `scan_bypasses.py`: 0 candidatos
- Sondas só com `--home` temporário, via `main()` com `which` simulado, sem chamar a Orca. (a) Sobras `starcode.novo` e `starcode.velho` sem `starcode`: exit 0, sobras removidas, cópia completa. (b) `rmtree` de `starcode.velho` falhando: exit 1, nova no lugar, JSON não gravado, sobra `starcode.velho`. (c) Rename de `starcode` falhando: exit 1, antiga intacta, sem sobras. (d) Rename de `starcode.novo` falhando: exit 1, antiga restaurada com o conteúdo original. (e) `KeyboardInterrupt` entre os renames: ficam só as sobras, e a execução seguinte recupera com exit 0.

## Pesquisa

- Nenhuma superfície externa nova na correção (só `shutil` e `pathlib` da biblioteca padrão).
- Rodada 1: Context7 `/websites/opencode_ai`, https://opencode.ai/docs/skills.md, https://opencode.ai/docs/commands.md, https://opencode.ai/docs/cli/plugins.md
