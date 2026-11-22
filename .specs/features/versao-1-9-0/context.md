# Versão 1.9.0: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "para que eu possa fazer o teste, primeiro preciso saber se o plugin instalado em todos os agentes esta atualizado com as correções que implementamos." Depois, à proposta de fechar a 1.9.0 e atualizar os agentes: "sim".

## Problem
Os cinco agentes (Claude Code, Codex, Antigravity, OpenCode e a Ponte da Orca) têm cópias da 1.8.0 de 2026-11-13 ou anteriores (OpenCode em 1.6.1). Desde então entraram 89 merges e o `CHANGELOG.md` acumula 24 itens em `[Unreleased]`. O Claude Code puxa do GitHub e guarda o plugin pela versão, então sem trocar a versão ele não atualiza.

## Users
O dono do repositório, que vai usar o StarCode num projeto real no passo 5 (a pausa).

## Success
- `VERSION` em 1.9.0, propagado pelo `tools/build.py` aos manifestos e ao `dist/`.
- `CHANGELOG.md` com `## [1.9.0] - 2026-11-22` acima dos itens que estavam em `[Unreleased]`, e o `[Unreleased]` vazio.
- Depois do merge: os cinco agentes reinstalados a partir da 1.9.0, conferidos arquivo a arquivo (passo do Picard, fora do código).

## Constraints
- `dist/` só pelo `python tools/build.py`.
- Sem tag nem release no GitHub agora: o push da tag dispara o CI, e o Actions está sem minutos até 01/12.

## Scope Notes
- Dentro: troca de versão (VERSION, `src/orca/orca-plugin.json`, teste de versão em `tests/test_build.py`, linha de estado do `README.md`), `CHANGELOG.md`, `dist/` e manifestos gerados.
- Fora: tag e release no GitHub; mudança de comportamento do plugin.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Número da versão | 1.9.0 (minor: comportamento novo, sem quebra) · 1.8.1 | "sim" à proposta da 1.9.0 | 2026-11-22 |
| Tag/release no GitHub | agora · depois de 01/12 | "sim" à proposta (depois de 01/12) | 2026-11-22 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Demais dimensões | N/A para este escopo: só troca de versão. |

## Facts Found
- A versão fixa aparece em `VERSION`, `src/orca/orca-plugin.json:5`, `tests/test_build.py:447-453` (`test_version_is_1_2_0_in_all_manifests`) e `README.md:6`.
- `tools/build.py` regenera o `dist/`, o `.claude-plugin/marketplace.json` e o `.agents/plugins/marketplace.json` (linhas 449-460).
- Troca anterior: commit e6461c5 (`chore(release): versão 1.8.0`).
- Marketplace do Claude Code: GitHub `freire-andre/starcode`; Codex: marketplace local apontando para `dist/codex`.
