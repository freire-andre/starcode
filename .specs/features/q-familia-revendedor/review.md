**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
O Claude revendido sem `canonical_model_id` deixa de passar por Q independente de um LaForge Claude; R1 a R9 têm teste e os 24 testes de `test_model_info` passam. Conferida contra o catálogo real do models.dev (9135 entradas), a tabela de prefixos só diverge do id canônico em Llama-Nemotron (`meta` em vez de `nvidia`, direção conservadora), e `o1`/`o3`/`o4`/`codex` não casam nome de outro fornecedor.

Um should-fix: fornecedor fora de `VENDOR_PROVIDERS` (ex.: `alibaba`, Qwen) vira `unknown`, e o Q `opencode:alibaba/qwen3-coder-plus`, aceito no main, passa a ser recusado; o `suggest` cai em self-verified. Um nit: id regional do Bedrock sem canônico vira `unknown`.

Pré-existente: `dispatch.family` faz `lower()` no modelo antes do lookup, que diferencia maiúsculas, então `opencode:minimax/MiniMax-M3` já era `unknown` no main.

Fora do review: `dist/` (gerado, `build --check` OK) e os arquivos de `.specs/`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/model_info.py:50 | Fornecedor fora de `VENDOR_PROVIDERS` (`alibaba`) vira `unknown`: o Q `opencode:alibaba/qwen3-coder-plus` (sem canônico no catálogo real), aceito no main, é recusado pelo `q_cli`, e o `setup_helpers.suggest` com claude+opencode passa a self-verified. Correção: `alibaba` em `VENDOR_PROVIDERS` e `("qwen", "alibaba")` em `NAME_PREFIX_FAMILIES`, com caso no teste. | scripts/model_info.py:50 | aberto |
| W2 | 🟡 nit | scripts/model_info.py:151 | Só o segmento antes do primeiro `.` é olhado; ids regionais do Bedrock (`global.anthropic.claude-...`, `eu.anthropic.claude-...`) sem canônico dariam `unknown`. Hoje todos trazem o canônico, e `unknown` é o lado seguro. | scripts/model_info.py:151 | aberto |

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `python scripts/check_decisions.py`: OK (DECISIONS.md atualizado no commit 5e6d0ad9).
- `python -m unittest test_model_info` (em `tests/`): 24 testes OK.
- `python -m unittest discover -s tests -v` (informado pelo Picard): 856 OK, 1 skip.
- `git diff main...HEAD | python scripts/review/scan_bypasses.py`: 0 candidatos.

## Pesquisa
- https://models.dev/api.json, baixado em 2026-11-14 para um arquivo temporário fora do cache do usuário: 236 provedores, 9135 entradas, 7759 com `canonical_model_id`. Os cinco revendedores servindo Claude e as entradas `opencode/muse-*` trazem `canonical_model_id`. As exceções são `azure/claude-opus-4-6`, `claude-opus-4-5` e `claude-sonnet-4-5`, que agora viram `anthropic` pelo prefixo.
