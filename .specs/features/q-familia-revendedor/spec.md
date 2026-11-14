# Família do Q por revendedor: Spec

**Approved**: 2026-11-14 - user: "SIM"

**Size**: MEDIUM
**Risk triggers**: Autorização (independência do verificador Q)
**Status**: Approved
**Linear**: SC-171
**May change**: scripts/model_info.py, DECISIONS.md, tests/test_model_info.py, tests/fixtures/models-dev.json, dist/

## Context
Item C.1 de `starcode-triagem-v2-2026-11-13.md` (fora do Git). `vendor()` em `scripts/model_info.py:122-134` usa o nome do provedor como família quando a entrada do catálogo não traz `canonical_model_id`. Um Claude servido por revendedor (`github-copilot`, `azure`, `amazon-bedrock`, `google-vertex-anthropic`, `opencode`) recebe a família do revendedor, e `dispatch.compare`/`q_cli` o aceitam como Q independente de um LaForge Claude. Não verificada: se o catálogo real do models.dev traz `canonical_model_id` nessas entradas (não há cache nesta máquina); a regra não depende disso. Sucesso: nenhum revendedor servindo um Claude passa como independente de um LaForge Claude.

## Scope
- `vendor()` distingue o provedor que é o próprio fornecedor do modelo do provedor revendedor.
- Para revendedor sem id canônico, a família sai do nome do modelo; o que não se reconhece vira `unknown`.

## Non-Goals
- Mudar a ordem de escolha do Q (`Q_CLI_ORDER`), o `families` do `crew.yaml` ou `PREFIX_FAMILIES` do `dispatch.py`.
- Baixar o catálogo durante o despacho (`cached_family` continua com `fetch=False`).
- Qualquer opção, comando ou perfil novo (congelamento D-i).

## Requirements
- **R1** - WHEN a entrada não tem `canonical_model_id`, o provedor não é `openrouter` nem fornecedor (lista de R4) e o último segmento do id do modelo começa com `claude` THEN `vendor()` SHALL devolver `anthropic` para `github-copilot/claude-sonnet-5-5`, `azure/claude-sonnet-5-5`, `google-vertex-anthropic/claude-sonnet-5-5` e `opencode/claude-sonnet-5-5`.
- **R2** - WHEN o último segmento do id tem um fornecedor conhecido antes do primeiro `.` (ex.: `amazon-bedrock/anthropic.claude-sonnet-5-5`) THEN `vendor()` SHALL devolver esse fornecedor (`anthropic`).
- **R3** - IF o provedor é revendedor, a entrada não tem `canonical_model_id` e o nome do modelo não começa com nenhum prefixo da tabela de R7 nem com fornecedor conhecido antes do `.` THEN `vendor()` SHALL devolver `unknown` (ex.: `github-copilot/acme-x`).
- **R4** - WHEN o provedor é fornecedor (`anthropic`, `openai`, `google`, `deepseek`, `zai`, `zhipuai`, `moonshotai`, `mistral`, `xai`, `meta`) THEN `vendor()` SHALL manter a família do provedor com os aliases de hoje (`zai/glm-notools`, sem id canônico, continua `zhipu`), e o `canonical_model_id`, quando existe, SHALL continuar com precedência sobre tudo (`opencode/muse-spark-1.2` continua `meta`).
- **R5** - WHEN o catálogo em cache tem a entrada de um dos cinco revendedores servindo `claude-sonnet-5-5` sem id canônico THEN `dispatch.compare("opencode:<revendedor>/<modelo>", "claude:claude-sonnet-5-5")` SHALL devolver `same` para cada um dos cinco.
- **R6** - WHEN o LaForge é `claude:claude-sonnet-5-5`, o Q configurado é `opencode:github-copilot/claude-sonnet-5-5` (catálogo sem id canônico) e codex e opencode estão disponíveis THEN `dispatch.q_cli` SHALL devolver `codex`, nunca o configurado.
- **R7** - WHEN um revendedor sem id canônico serve um modelo de outro fornecedor THEN `vendor()` SHALL usar a tabela de prefixos do nome: `claude` → `anthropic`; `gpt`, `o1`, `o3`, `o4`, `codex` → `openai`; `gemini` → `google`; `deepseek` → `deepseek`; `glm` → `zhipu`; `kimi` → `moonshotai`; `grok` → `xai`; `mistral`, `codestral`, `devstral` → `mistral`; `llama` → `meta`.
- **R8** - IF não há catálogo em cache THEN `dispatch.family("opencode:github-copilot/claude-sonnet-5-5")` SHALL continuar devolvendo `unknown`.
- **R9** - The system SHALL ter no `DECISIONS.md` a entrada da issue desta feature (`### SC-171:`), descrevendo R1 a R8, com **Problema**, **Decisão**, **Motivo** e **Por que não é bug** citando os testes.

## Edge Cases
- Bedrock com prefixo `anthropic.`: R2 (C2).
- Revendedor com modelo desconhecido: R3 (C3).
- Fornecedor sem id canônico (`zai/glm-notools`) e id canônico com precedência (`opencode/muse-spark-1.2`): R4 (C4).
- Sem catálogo em cache: R8 (C8).
- Revendedor servindo modelo não Claude (`azure/gpt-6-luna`): R7 (C7).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Com entrada `{}` (sem `canonical_model_id`), `assertEqual(vendor(p, {}, m), "anthropic")` para os quatro pares `github-copilot`, `azure`, `google-vertex-anthropic` e `opencode` com `claude-sonnet-5-5` (R1)
Proof: run unit | test_revendedor_claude_vira_anthropic ... ok

**C2** - `assertEqual(vendor("amazon-bedrock", {}, "anthropic.claude-sonnet-5-5"), "anthropic")` (R2)
Proof: run unit | test_bedrock_prefixo_do_fornecedor ... ok

**C3** - `assertEqual(vendor("github-copilot", {}, "acme-x"), "unknown")` e o mesmo com `azure` e `opencode` (R3)
Proof: run unit | test_revendedor_modelo_desconhecido_vira_unknown ... ok

**C4** - `info(catalog, "zai/glm-notools")["family"] == "zhipu"`, `info(catalog, "opencode/muse-spark-1.2")["family"] == "meta"` e `info(catalog, "anthropic/claude-opus-5-5")["family"] == "anthropic"`, cada um com `assertEqual` (R4)
Proof: run unit | test_fornecedor_e_id_canonico_mantem_familia ... ok

**C5** - Com um catálogo de teste em `STARCODE_MODELS_DEV_FILE` que traz `claude-sonnet-5-5` sem id canônico nos cinco revendedores (`amazon-bedrock` com `anthropic.claude-sonnet-5-5`), `assertEqual(dispatch.compare("opencode:<revendedor>/<modelo>", "claude:claude-sonnet-5-5"), "same")` para cada um (R5)
Proof: run unit | test_compare_revendedor_claude_e_same ... ok

**C6** - Com o mesmo catálogo e codex e opencode disponíveis, `assertEqual(dispatch.q_cli("claude:claude-sonnet-5-5", "opencode:github-copilot/claude-sonnet-5-5", caps), "codex")` (R6)
Proof: run unit | test_q_cli_recusa_revendedor_claude ... ok

**C7** - Tabela com um modelo por linha de R7 servido por `azure` sem id canônico (ex.: `gpt-6-luna`, `o3-mini`, `codex-mini`, `gemini-3`, `deepseek-v4`, `glm-5.3`, `kimi-k3`, `grok-5`, `mistral-large`, `codestral-2`, `devstral-2`, `llama-5`): `assertEqual` da família esperada em cada linha (R7)
Proof: run unit | test_prefixos_de_modelo_por_revendedor ... ok

**C8** - Com `STARCODE_MODELS_DEV_FILE` apontando para arquivo inexistente e sem cache, `assertEqual(dispatch.family("opencode:github-copilot/claude-sonnet-5-5"), "unknown")` (R8)
Proof: run unit | test_sem_catalogo_revendedor_unknown ... ok

**C9** - `DECISIONS.md` tem a entrada da issue com `github-copilot`, `amazon-bedrock`, `unknown` e `Por que não é bug` citando os testes de C1 a C8 (R9)
Proof: run unit | test_decisions_q_familia_revendedor ... ok

## Handoff

**Phase:** review
**Size:** none yet
**Git mode:** none yet
**Next:** Gates de provas e done após a correção
**Linear:** SC-171
**Integration branch:** feature/q-familia-revendedor
**Last integrated:** ac13e858e6897ceac4b20fcad079700e10cd811e
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
