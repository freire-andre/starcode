# Versao-e-retro: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "próximo passo", com a divisão "Duas MÉDIAs" (missão 7a do passo 4 da seção 12 da triagem v2: itens N.4 e N.2; a 7b leva N.3, N.7 e N.8)

## Problem
- **N.4**: um brief gerado pelo plugin 1.6.1 instalado não trazia uma regra que já estava no repositório (retro de manutenção, item 2).
  - Hoje o brief e o Handoff não dizem que versão do plugin os gerou.
  - O banner só avisa quando o plugin instalado é mais velho que o `VERSION` do repositório (`hooks/scripts/banner.py:153-168`, F7-12). O `dispatch.py` não avisa nada.
- **N.2**: as ações propostas nas retros não têm estado. Não dá para saber, no repositório, quais foram feitas, recusadas ou seguem abertas.
  - São 35 arquivos `retro.md` em `.specs/features/`.

## Users
- O Picard, que despacha workers com o plugin instalado e decide o que fazer com as sugestões das retros.
- O usuário, que quer ver as ações abertas.

## Success
- Todo brief e todo Handoff com despacho dizem a versão do plugin.
- O `dispatch.py` avisa quando a versão instalada difere do `VERSION` do repositório do StarCode.
- Cada linha nova de retro tem `Estado`, e um comando lista as abertas de todas as retros e muda o estado de uma linha.

## Constraints
- D30: entrada no `DECISIONS.md`.
- N.7 (missão 7b): estado novo é escrito por script.
- O `execute.md` não é tocado nesta parte: a divisão dele é o N.8, na 7b.

## Scope Notes
- Dentro: N.4 e N.2.
- Fora: preencher o `Estado` das 35 retros antigas e as ações concretas citadas no N.2.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Missão 7 | duas MÉDIAs / uma GRANDE / uma MÉDIA | Duas MÉDIAs (Recomendado) | 2026-11-21 |
| N.4: aviso em que sentido | só instalado mais velho / qualquer diferença | qualquer diferença, no `dispatch.py`; o banner fica como está (F7-12) — default (não perguntado) | 2026-11-21 |
| N.4: onde grava no Handoff | campo novo `Plugin` / dentro de `Dispatched` | campo novo `**Plugin:**`, gravado pelo `dispatch.py start` — default (não perguntado) | 2026-11-21 |
| N.2: retros sem coluna `Estado` | listar como abertas / contar à parte | contar à parte numa linha final; `--todas` lista as linhas delas como `sem estado` — default (não perguntado) | 2026-11-21 |
| N.2: valor inicial | `aberto` / `aberto: <issue>` | a Guinan escreve `aberto`; `aberto: <issue>` quando houver issue — default (não perguntado) | 2026-11-21 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | `retros.py estado` recusa linha inexistente, retro sem a coluna e valor fora dos três formatos. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `hooks/scripts/banner.py:128-137`: `plugin_version()` lê `.claude-plugin/plugin.json`, `crew.json` ou `VERSION` na raiz do plugin. `outdated_plugin_line` (153-168) reconhece o repositório do StarCode por `VERSION` e `dist/claude/.claude-plugin/plugin.json`.
- `scripts/handoff.py:33-46`: `FIELDS`, com opção, marcador e padrão.
- `scripts/dispatch.py`: `spec_brief` (375), `_worker_brief` (466), `q_brief` (510), `screens_brief` (557) e `fix_brief` (989).
- `skills/guinan/references/retro.md`: tabela `| # | Severidade | Categoria | Evidência | Ação proposta |`.
- `VERSION` do repositório: 1.8.0.
