# Gate D30 no CI e decisões da 1.8.0: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "vamos implementar as melhorias do arquivo @starcode-triagem-v2-2026-11-13.md" (fatiado pelo Picard: uma feature por passo do primeiro corte da seção 12; esta é o passo 1, itens 0.1 e 0.2)

## Problem
O gate D30 (`scripts/check_decisions.py`) nunca falha no CI. O `actions/checkout@v4` sem `fetch-depth` faz um clone de profundidade 1, então `git log -1 -- skills scripts hooks` e `git log -1 -- DECISIONS.md` devolvem o mesmo commit e o script responde "OK (atualizado no mesmo commit)". Por isso a 1.8.0 saiu sem nenhuma entrada no `DECISIONS.md` e com o CI verde, embora mude quem responde às paradas do fluxo e quem aprova as tasks. Num clone completo de `5daf74c` o gate já está vermelho (último commit em `skills/`/`scripts/`/`hooks/` é `a069e55`; último no `DECISIONS.md` é `2e781bb`, anterior).

## Users
O dono do repositório (único mantenedor) e os agentes do StarCode que leem o `DECISIONS.md` antes de revisar (protocolo do topo do arquivo).

## Success
- No CI, o job `checks` roda o gate sobre o histórico completo; uma mudança em `skills/`, `scripts/` ou `hooks/` sem entrada nova no `DECISIONS.md` deixa o PR vermelho.
- Em repositório raso, `check_decisions.py` não responde OK: falha com mensagem que diz que o clone é raso e como corrigir.
- O `DECISIONS.md` registra as decisões que a 1.8.0 tomou, e `check_decisions.py` fica verde num clone completo.

## Constraints
- A regra D30 não muda (decisão D-e da triagem anterior): só a execução do gate.
- Nunca editar `dist/`; regenerar com `python tools/build.py` se algum arquivo fonte gerado mudar.
- Ticket que mexe em `scripts/` lista `DECISIONS.md` no próprio May change (defeito R.7 da triagem: o `check_scope` não enxerga o acréscimo do brief).
- `dispatch.py start`/`settle` não funcionam em feature MÉDIA (R.6): despacho e integração manuais.
- Artefatos e gates pelo código do repositório, não pelo plugin instalado.
- 0.1 e 0.2 no mesmo PR: sem 0.2, o CI corrigido fica vermelho.

## Scope Notes
- Dentro (0.1): `fetch-depth: 0` no checkout do job `checks` de `.github/workflows/ci.yml`; `check_decisions.py` detecta repositório raso (`git rev-parse --is-shallow-repository`) e falha com mensagem clara; teste que cria um clone raso e espera a falha.
- Dentro (0.2): entradas no `DECISIONS.md` para: piloto automático (o que é delegável, citando a regra de paradas D29 e a aprovação das tasks); aceitação de `piloto:` só no `tasks.md`; skill `config` e `model_info.py` (confiança no catálogo do models.dev, cache de 7 dias, níveis de custo); config local por repositório e ordem de precedência; skill `menu`. Uma entrada também para a mudança de 0.1 no próprio `check_decisions.py` (é mudança em `scripts/`).
- Fora: corrigir os defeitos do piloto (0.4 a 0.7, decisões D-g e D-h) e o Q sobre o diff da 1.8.0 (0.3), que são passos posteriores do primeiro corte. As decisões D-g a D-k só viram entrada quando o item delas for implementado (seção 8 da triagem).
- Fora: os jobs `eval` e `release-check` do CI (não rodam o gate).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Código de saída em repositório raso | 1 (desatualizado) / 2 (ambiente inválido, como "não é repositório Git") | 2, porque o gate não consegue avaliar; mensagem cita `fetch-depth: 0` / `git fetch --unshallow` · default (não perguntado) | 2026-11-13 |
| IDs das entradas da 1.8.0 | prefixo de fase / ID da issue do Linear (como SC-167) / prefixo da versão | `V18-1` a `V18-5` para as decisões da 1.8.0, e o ID da issue da feature para a entrada do gate raso · default (não perguntado) | 2026-11-13 |
| Conteúdo das entradas da 1.8.0 | descrever o comportamento entregue / já incorporar as correções decididas (D-g, D-h) | descrever o comportamento entregue, com "Por que não é bug" citando os testes existentes (`test_piloto.py`, `test_model_info.py`, `test_config_skill.py`, `test_menu_skill.py`); defeitos conhecidos ficam para os itens 0.4 a 0.7 · default (não perguntado) | 2026-11-13 |
| Onde o teste do clone raso roda | Linux e Windows / só Linux | nos dois sistemas da matriz, com `git clone --depth 1 file://...` a partir de um repositório temporário · default (não perguntado) | 2026-11-13 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Failure and partial failure | Se `git rev-parse --is-shallow-repository` falhar (git antigo sem a opção), o script não declara OK em silêncio: trata como não-raso só quando a saída é exatamente `false`. |
| External dependency failure | O teste depende só do `git` local (clone `file://`), sem rede. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `.github/workflows/ci.yml:26`: `actions/checkout@v4` sem `with:`; o passo `check_decisions` roda em `ubuntu-latest` e `windows-latest`.
- `scripts/check_decisions.py`: exit 0 ok, 1 desatualizado, 2 sem repositório Git ou sem `DECISIONS.md`; compara commits (`git log -1`, `merge-base --is-ancestor`); nenhuma verificação de clone raso (`grep is-shallow` vazio em `scripts/` e `tests/`).
- `tests/test_check_decisions.py`: `CheckDecisionsTests(TempRepoCase)` com `test_flow`, `test_same_commit_ok`, `test_dirty_watched_without_decisions_fails`, `test_missing_file`.
- `DECISIONS.md`: entradas `### <ID>: <título> (<requisitos>)` com os itens **Problema**, **Decisão**, **Motivo** e **Por que não é bug**; última entrada `SC-167`. Nenhuma ocorrência de "piloto", "models.dev" ou "config.local".
- 1.8.0 (`CHANGELOG.md`): skills `menu`, `config`, `piloto-automatico`; `scripts/model_info.py` (cache de 7 dias, `MAX_AGE_S = 7 * 24 * 3600`); config local `.starcode/config.local.json` com prioridade sobre o config do usuário; gates aceitam `**Approved**: <data> - piloto: "D<n> ..."` no `tasks.md` só com piloto ativo e mandato confirmado (`scripts/gates/gates_common.py:183-203`); a spec continua exigindo aprovação do usuário.
- Precedência dos modelos (`context/STARCODE.md`, seção Models): sessão > config local do repositório > config do usuário > padrão do `crew.yaml`.
- `skills/piloto-automatico/SKILL.md`: seção 4 (regras após a aprovação da spec), seção 5 (o que nunca é decidido), seção 7 (encerrar ao fim).
- Testes existentes da 1.8.0: `tests/test_piloto.py`, `tests/test_model_info.py`, `tests/test_config_skill.py`, `tests/test_menu_skill.py`.
