# piloto-freios: Context

**Size**: MEDIUM
**Risk triggers**: Autorização (o que o piloto pode decidir no lugar do usuário)
**Source request**: "Próximo passo" (resto do lote 0 da triagem v2: itens 0.5, 0.6 e 0.7, com as decisões D-g e D-h do dono)

## Problem
- 0.5: o gate só aceita a aprovação `piloto:` com o piloto ativo, e a skill manda encerrar o piloto no fim de toda feature; rodar `run_gates.py tasks` ou `done` de novo numa feature concluída com piloto reprova (correção do Worf depois do PR, "assumo daqui").
- 0.6: decisão sem base vira `baixa` e `⚠️ revisar`, mas não há limite; o piloto pode ir até o fim só com decisões sem base.
- 0.7: dependência nova, mudança de esquema de banco e desvio de decisão de arquitetura ficam delegáveis sem mandato.

## Users
O dono do repositório usando `/starcode:piloto-automatico`; o Picard em piloto automático; os gates de tasks e de verificação.

## Success
- D-g: feature com piloto encerrado passa em `run_gates.py tasks` e `done`; aprovação que cita decisão registrada depois do encerramento reprova.
- D-h (0.6): a 2ª decisão `⚠️ revisar` segue; a 3ª para e devolve a pergunta ao usuário (mesmo desenho do disjuntor D27).
- D-h (0.7): os três casos só são decididos pelo piloto com item de mandato que os cubra (`--basis M<n>`); sem ele, devolvidos ao usuário.

## Constraints
- `piloto.py` é o único leitor e escritor de `piloto.md`; os gates leem pelo `piloto.py`.
- Códigos de saída atuais do `piloto.py`: 0 ok, 1 regra recusada/ausente, 2 uso.

## Scope Notes
- Dentro (0.5, D-g): a aprovação `piloto:` vale com piloto ativo **ou encerrado**, desde que o mandato tenha sido confirmado pelo usuário e a decisão citada tenha sido registrada antes do `**Encerrado:**`.
- Dentro (0.6, D-h): a 3ª decisão sem base da feature é recusada pelo `registrar` com exit 3 e mensagem de freio; daí em diante toda decisão sem base é recusada (o freio fica). O Picard devolve a pergunta ao usuário.
- Dentro (0.7, D-h): `registrar --categoria dependencia|esquema|arquitetura` exige um `M<n>` em `--basis`; sem ele, recusa com exit 3 ("devolva ao usuário"). A skill manda usar a opção nesses três casos e lista os três na seção 5.
- Fora: o aceite em sessão real (0.8, pendência do dono).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| 3ª decisão sem base | recusa, exit 3, freio fica / recusa só a 3ª / grava e sai 3 | "Recusa, exit 3, freio fica (Recomendado)" | 2026-11-16 |
| Como reconhecer os três casos de arquitetura | opção `--categoria` / só texto da skill | "Opção --categoria (Recomendado)" | 2026-11-16 |
| Registro "devolvido ao usuário" | conta no freio / não conta | default (não perguntado): `--decision "devolvido ao usuário"` é gravado sem `⚠️ revisar`, não conta no freio e nunca é recusado por ele (é o próprio caminho de volta ao usuário) | 2026-11-16 |
| "Registrada antes do encerramento" | carimbo da decisão vs. do `**Encerrado:**` / posição no arquivo | default (não perguntado): compara o carimbo da decisão com o do `**Encerrado:**`; decisão com carimbo posterior não vale (o carimbo tem precisão de segundo e o `registrar` já recusa depois do encerramento, então carimbo igual conta como anterior) | 2026-11-16 |
| Código do freio | 3 / outro | default (não perguntado): exit 3 para o freio e para `--categoria` sem `M<n>`, distinto de 1 (regra recusada) e 2 (uso) | 2026-11-16 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| State-transition rules | Aprovação `piloto:` vale em piloto ativo ou encerrado, nunca com mandato sem o usuário; decisão registrada depois do `**Encerrado:**` não vale. |
| Input validation and limits | O freio conta só decisões `⚠️ revisar` da própria feature; registros "devolvido ao usuário" não contam. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `scripts/gates/gates_common.py:203-210` `pilot_approved` exige `active_confirmed_in` (status `ativo` + mandato com `- user:`).
- `scripts/piloto.py` `record` recusa com piloto encerrado ou mandato não confirmado; sem `--basis` força `baixa` e grava ` · ⚠️ revisar` no título da decisão.
- `scripts/piloto.py` `finish` troca o status para `encerrado` e grava `**Encerrado:** <carimbo>` antes de `## Mandato`.
- `skills/piloto-automatico/SKILL.md` seção 4 (regras), 5 (o que nunca é delegado: Git, spec, push, PR, review, merge, deploy, credencial, destrutiva, custo, disjuntor), 7 (encerrar no fim).
- `tests/test_piloto.py:112-113` fixa que o gate só aceita com `Status: ativo`.
