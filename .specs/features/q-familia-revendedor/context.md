# Família do Q por revendedor: Context

**Size**: MEDIUM
**Risk triggers**: Autorização (independência do verificador Q)
**Source request**: "vamos implementar as melhorias do arquivo @starcode-triagem-v2-2026-11-13.md" (passo 4 do primeiro corte: item C.1, "Q da mesma família aceito como independente quando o modelo vem por revendedor")

## Problem
O Q só vale como verificação independente se for de outra família de modelo que o LaForge. `vendor()` em `scripts/model_info.py:122-134` usa o nome do provedor como família quando a entrada do catálogo não traz `canonical_model_id`. Um Claude servido por revendedor (`github-copilot`, `azure`, `amazon-bedrock`, `google-vertex-anthropic`, `opencode`) recebe a família do revendedor e passa como independente de um LaForge Claude.

## Users
O dono do repositório que configura o Q pelo OpenCode com um provedor revendedor; o fluxo do Picard, que escolhe o CLI do Q por `dispatch.py q-cli`/`compare`.

## Success
Nenhum dos cinco revendedores servindo um Claude dá família diferente de `anthropic` (ou dá `unknown`), então nunca passa como independente de um LaForge Claude. Teste de tabela com os revendedores.

## Constraints
- Congelamento D-i: nenhuma opção, comando ou perfil novo.
- O catálogo (cache do models.dev) pode não existir; nunca baixar no despacho (`cached_family` usa `fetch=False`).
- Não foi possível conferir se o catálogo real traz `canonical_model_id` nessas entradas (sem cache nesta máquina): a regra não pode depender dele.

## Scope Notes
- Dentro: a família de `provider/model` quando o provedor não é o fornecedor do modelo (revendedor), pela família do próprio modelo.
- Fora: mudar a ordem de escolha do Q, o `crew.yaml` `families` (já tem precedência) e qualquer opção nova.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Família de um revendedor sem id canônico | (a) prefixo do nome do modelo (`claude` → anthropic, `gpt` → openai...), senão `unknown`; (b) sempre `unknown` | default (não perguntado): (a), como propõe a triagem; o que não se reconhece vira `unknown`, que nunca conta como independente | 2026-11-14 |
| Quem é "fornecedor" e não revendedor | lista fixa de provedores que são o próprio fornecedor (anthropic, openai, google, deepseek, zai/zhipuai, moonshotai, mistral, xai...) | default (não perguntado): lista fixa no código; provedor fora dela sem id canônico e sem prefixo conhecido vira `unknown` | 2026-11-14 |
| Prefixo no último segmento com ponto (`anthropic.claude-...` do Bedrock) | ignorar o prefixo do fornecedor antes do ponto ou não | default (não perguntado): reconhecer tanto `anthropic.` quanto `claude` no último segmento | 2026-11-14 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| External dependency failure | Sem catálogo, `family()` continua em `unknown` para `provider/model` desconhecido (já é assim, `dispatch.py:532-539`). |
| Authorization boundaries | `unknown` nunca conta como independente (`dispatch.py:598`); a mudança só pode tornar a regra mais restrita, nunca aceitar um par que hoje é recusado por ser da mesma família. |

Demais dimensões: N/A para este escopo.

## Facts Found
- `scripts/model_info.py:122-134` `vendor()`: id canônico → segmento do openrouter → provedor; aliases em `VENDOR_ALIASES` (`model_info.py:36`).
- `scripts/model_info.py:189-195` `cached_family` → `lookup` + `vendor`, usado por `dispatch._catalog_family`.
- `scripts/dispatch.py:509-545` `family()`: `crew.yaml families` → `PREFIX_FAMILIES` (`dispatch.py:71`, só no id inteiro) → `_catalog_family` para `provider/model`. `compare` dá `unknown` se um dos lados é `unknown`.
- Reprodução (entrada sem `canonical_model_id`): `vendor("github-copilot", {}, "claude-sonnet-5-5")` → `github-copilot`; o mesmo com `azure`, `amazon-bedrock` (`anthropic.claude-sonnet-5-5`) e `google-vertex-anthropic`; `vendor("opencode", {}, "muse-spark-1.2")` → `opencode`.
- Testes atuais: `tests/test_model_info.py:51` (família por id canônico e openrouter), `tests/test_dispatch.py:309` (`family` com openrouter e deepseek). O fixture tem `opencode/muse-spark-1.2` com id canônico → `meta`, e isso deve continuar.
