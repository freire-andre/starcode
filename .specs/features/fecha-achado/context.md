# Fechamento de achado do Q com commit e cobertura: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "Prossigamos" (lote 3 da triagem v2, item 3.7: "Achado do Q só fecha com commit e check (D-c). [...] Implementar como subcomando que preenche a célula `Closed` (retro `ponte-missao-ativa`, item 4: a edição manual da tabela quebrou o gate). Resolve os dois")

## Problem
Hoje o gate `done` só confere que a célula `Closed` cita um commit do repositório (`scripts/gates/validate_verification.py:276-289`). Não confere o que cobre o achado. Quem preenche a célula é o Picard, editando a tabela à mão ou por script improvisado. Nesta sessão isso deixou o `done` vermelho duas vezes: um `||` que criou uma célula a mais (pequena-minima) e pipes sem escape na evidência do Q, que deslocaram a coluna (pr-review). Nos dois casos o erro dizia "sem commit em `Closed`", sem apontar a causa.

## Users
O Picard (fluxo) e o dono do repositório.

## Success
Um subcomando preenche a célula `Closed` com `<sha> · <cobertura>`, conferindo o commit e a cobertura antes de gravar. O gate `done` recusa um fechamento sem os dois e acusa linha de tabela com número de células diferente do cabeçalho, com o número da linha. O brief do Q pede `&#124;` para pipe dentro de célula.

## Constraints
- Decisão do dono D-c (triagem v1, linhas 77 e 88): o fechamento exige o commit e o check que cobre o achado, sem segundo Q.
- Modo 1 (`degradada (modo 1)`) continua valendo como hoje.
- Entrada no `DECISIONS.md` (D30). O `dist/` é regenerado.

## Scope Notes
- Dentro: o item 3.7, mais as duas sugestões de retro desta sessão (pr-review, item 1: célula a mais acusada com o número da linha e `&#124;` no brief do Q; pequena-minima, item 1: subcomando no lugar da edição manual).
- Fora: os itens 3.2, 3.4, 3.3 e 3.8 da triagem.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| O que vale como cobertura | `C<n>` ou teste existente / só `C<n>` / teste que passou no proofs.md | `C<n>` de um check da feature ou `test_<nome>` que existe como `def test_<nome>` em `tests/` no HEAD | 2026-11-19 |
| Onde fica o subcomando | `dispatch.py` / script novo | `dispatch.py close-finding`, junto de `q-check` e `q-waive`: default (não perguntado) | 2026-11-19 |
| Como escolher o achado | número da linha / trecho do texto | Número de ordem do achado na tabela `## Findings` (1, 2, ...): default (não perguntado) | 2026-11-19 |
| Formato da célula | `<sha> · <cobertura>` / outro | `<sha curto> · C<n>` ou `<sha curto> · test_<nome>`. Vários commits ou coberturas separados por vírgula: default (não perguntado) | 2026-11-19 |
| Features antigas | recusar / tolerar | A regra vale para o gate `done` de agora em diante. Os `verification.md` já fechados não são revalidados no CI, e as fixtures dos testes são atualizadas: default (não perguntado) | 2026-11-19 |
| Linha com células a mais ou a menos | erro / aviso | Erro com o número da linha no `verification.md`, nas tabelas `## Checks` e `## Findings`: default (não perguntado) | 2026-11-19 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | O subcomando recusa (saída 2, sem gravar) um commit que não existe no repo, uma cobertura que não é `C<n>` da feature nem teste existente, um achado fora da faixa e uma tabela malformada |
| Failure and partial failure | A gravação reescreve só a célula `Closed` da linha escolhida, com as células escapadas, e mantém o resto do arquivo em bytes |
| demais dimensões | N/A para este escopo |

## Facts Found
- `scripts/gates/validate_verification.py:76-101` (`_tables`, `_col`, `_cell`; a divisão por `|` não trata o escape) e `:276-289` (regra do `Closed`).
- `skills/engajar/references/execute.md:171`: "Then write the commit in each `Closed` cell".
- `scripts/dispatch.py`: `q-brief`, `q-check` e `q-waive`.
- `tests/test_validate_verification.py` e `tests/test_q_skill.py` usam `Closed`.
