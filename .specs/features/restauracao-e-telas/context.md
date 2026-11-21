# Restauracao-e-telas: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "Próximo passo" (missão 5 do passo 4 da seção 12 da triagem v2: itens R.5 e R.10)

## Problem
- **R.5**: `snapshot.py restore` lê o `May change` do `tasks.md` (ou do `spec.md`) da árvore de trabalho atual (`scripts/snapshot.py:162-176`, `_ticket_may_change`). Se o escopo mudou depois do snapshot, a restauração usa o escopo novo, e o modo 1 não tem o `check_scope` para segurar.
- **R.10**: as telas não têm restrição.
  - `screens.py capture` aceita qualquer URL http(s) (`scripts/screens.py:183`). Uma página logada de outro host pode ser fotografada e commitada.
  - `--out` grava em qualquer caminho (`scripts/screens.py:104-116`) e pode sobrescrever a captura vinculante.
  - `validate_verification.py` casa o veredito por trecho (`run_name in screen`, linha 328), então `admin-login.running.png` satisfaz `login.png`.
  - `images.image_size` aceita um PNG só com cabeçalho (`scripts/gates/images.py:56-65`).

## Users
- O Picard e o LaForge, que restauram um snapshot quando um ticket dá errado.
- O juiz de telas, que fotografa a aplicação rodando.

## Success
- O `restore` usa o escopo gravado no snapshot.
- A captura só fotografa `localhost` por padrão.
- O `--out` só grava `captures/<nome>.running.png`.
- O veredito casa pelo nome inteiro.
- Um PNG sem dados é recusado.

## Constraints
- D30: entrada no `DECISIONS.md`.
- O `run_git` (SC-208) já existe para ler o snapshot.

## Scope Notes
- Dentro: R.5 e R.10, como descritos na triagem v2 (linhas 157 e 162).
- Fora: JPEG e WebP sem dados (a triagem fala só de PNG).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| R.10: hosts fora de localhost | recusar sempre / recusar por padrão com `--allow-host <host>` | recusar por padrão; `--allow-host <host>` (repetível, igualdade exata do host) libera um host — default (não perguntado) | 2026-11-21 |
| R.10: o que é localhost | só `localhost` / `localhost`, `127.0.0.1`, `[::1]` e `*.localhost` | os quatro — default (não perguntado) | 2026-11-21 |
| R.10: PNG "sem dados" | exigir chunk `IDAT` / exigir `IDAT` e `IEND` | exigir ao menos um `IDAT` — default (não perguntado) | 2026-11-21 |
| R.5: snapshot sem o artefato | cair para a árvore de trabalho / recusar | recusar com mensagem, sem restaurar — default (não perguntado) | 2026-11-21 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | Host, `--out` e PNG são validados antes de qualquer efeito; a validação do `--out` acontece antes de abrir a aba. |
| Authorization boundaries | Captura só de host local, a menos que o host seja liberado de forma explícita. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `scripts/snapshot.py:162-176`: `_ticket_may_change` lê `tasks.md` ou `spec.md` com `check_scope.find_task` e `spec_may_change`, que leem o disco.
- `scripts/gates/check_scope.py:51-63`: `find_task` usa `vt.parse_tasks(gc.read_lines(...))`, e `spec_may_change` usa `gc.field_value(gc.read_lines(...), "May change")`.
- `scripts/screens.py:83-117`: `capture(url, width, height, out)` copia o screenshot para `out`. `scripts/screens.py:183` só confere `https?://\S+`.
- `scripts/gates/validate_verification.py:326-329`: `run_name in screen or cap.name in screen`.
- `scripts/gates/images.py:56-65`: `_png` lê só o IHDR.
