**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude-code · claude-opus-5-5

## TL;DR

COMMENT. Snapshot e raio de impacto entregam o que a spec pede e a escada passa (build --check, check_decisions e 715 testes). Quatro defeitos reais deixam a seleção de regressão parcial ou quebram o brief do Q: caminho com `{{module}}` derruba o q-brief (W1), renomeação esconde o arquivo apagado (W2), no modo 1 o q-brief ignora os arquivos rastreados modificados (W3) e `conftest.py` vira o único teste escolhido (W4). Um nit no restore (W5). Fora do review: `dist/` (gerado, conferido por `build.py --check`).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/dispatch.py:443 | O bloco `{{regression}}` entra antes da checagem de marcadores; caminho com `{{module}}` (profiles/*/template) faz o `q_brief` levantar `marcadores não preenchidos`, contra o R32. Correção: rodar o `re.findall` antes de inserir o bloco. | scripts/dispatch.py:443, scripts/dispatch.py:444, scripts/impact.py:371 | aberto |
| W2 | 🟠 should-fix | scripts/impact.py:69 | `git diff --name-only` detecta renomeação por padrão e lista só o caminho novo; o arquivo apagado some e o R20 não dispara (teste que importa o módulo antigo fica de fora). Correção: `--no-renames`. | scripts/impact.py:69, scripts/impact.py:347, https://git-scm.com/docs/git-diff | aberto |
| W3 | 🟠 should-fix | scripts/dispatch.py:425 | No modo 1 o q-brief usa `base..HEAD`, vazio sem commits; só os não rastreados entram e os rastreados modificados ficam fora, sem `rodar tudo`. Correção: no modo 1, `diff=base` (árvore de trabalho). | scripts/dispatch.py:428, scripts/impact.py:70, skills/engajar/references/execute.md:227 | aberto |
| W4 | 🟠 should-fix | scripts/impact.py:80 | `tests/conftest.py` conta como teste e é o único escolhido quando muda; o pytest carrega as fixtures sem import, então os testes que as usam ficam de fora. Correção: `conftest.py` mudado vira `rodar tudo`. | scripts/impact.py:80, scripts/impact.py:7, https://docs.pytest.org/en/stable/reference/fixtures.html | aberto |
| W5 | 🟡 nit | scripts/snapshot.py:216 | Arquivo do snapshot trocado por pasta de mesmo nome: `voltar` roda antes de `remover` e falha sempre, ao contrário do R12. Correção: aplicar os `remover` antes dos `voltar`. | scripts/snapshot.py:203, scripts/snapshot.py:216 | aberto |

## Escada determinística

- `python tools/build.py --check`: OK, dist/ em dia.
- `python scripts/check_decisions.py`: OK.
- `python -m unittest discover -s tests`: 715 testes, OK (1 skip).
- `gh pr checks 34`: checks ubuntu/windows pendentes no momento do review.
- Bypass scan (`scan_bypasses.py`): 25 candidatos, todos aceitos (noqa E402/F401 do padrão `sys.path` já usado no repo, BLE001 justificado no próprio comentário, `skipIf` de plataforma com motivo).

## Pesquisa

- https://git-scm.com/docs/git-diff
- https://docs.pytest.org/en/stable/reference/fixtures.html
