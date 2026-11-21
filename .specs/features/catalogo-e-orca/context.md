# Catalogo-e-orca: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "próximo passo" (missão 6 do passo 4 da seção 12 da triagem v2: itens C.6 e N.5)

## Problem
- **C.6**: `scripts/model_info.py:78-94` (`download`) substitui o cache conferindo só se o JSON é um objeto. Uma resposta 200 com outro objeto troca um cache bom por 7 dias.
  - `name` e `description` do catálogo vão para o contexto do agente como vieram (`info`, linhas 212 e 217, e `render`, linha 255).
  - `load_catalog` relê e reinterpreta o arquivo a cada `cached_family` ou `cached_tier` (`dispatch.py:604` e `setup_helpers.py:144`).
- **N.5**: cada script chama o CLI `orca` com o seu próprio tratamento:
  - `scripts/screens.py:42-67` (`_orca`);
  - `hooks/scripts/banner.py:37-48` (`_run`);
  - `scripts/dispatch.py:697-701` (`default_runner`).
  
  Três incidentes da fase 10 vieram de comportamento da Orca que não estava escrito (F10-8, F10-9 e F10-14 no `DECISIONS.md`).

## Users
- O Picard e a skill `config`, que leem o catálogo.
- Todos os scripts que chamam a Orca.

## Success
- Um cache bom nunca é trocado por uma resposta com outra forma.
- O texto do catálogo chega limpo e cortado.
- O catálogo é lido uma vez por execução.
- Um único módulo Python chama a Orca.
- O comportamento verificado da Orca fica escrito em `.specs/stack/orca.md`.

## Constraints
- D30: entrada no `DECISIONS.md`.
- Mensagens e códigos de saída atuais do `screens.py`, do banner e do `dispatch.py` não mudam: os testes existentes seguem verdes sem edição.
- O worker TS da Ponte fica fora: a triagem pede o módulo "usado pelos scripts Python".
- `.specs/stack/` só é escrito pelo `scripts/stack_cache.py write`.

## Scope Notes
- Dentro: C.6 e N.5, como na triagem v2 (linhas 140 e 86).
- Fora: o worker TS da Ponte e a mudança de mensagens dos scripts migrados.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| C.6: forma mínima do catálogo | objeto não vazio / ao menos um provedor com `models` objeto | ao menos um provedor (valor objeto) com `models` objeto — default (não perguntado) | 2026-11-21 |
| C.6: limpeza do texto | só cortar / tirar caracteres de controle, juntar espaços e cortar | tirar controle (inclusive ESC e quebras), juntar espaços; `name` até 80 e `description` até 200 caracteres — default (não perguntado) | 2026-11-21 |
| N.5: env do CLI | herdar / herdar sem as variáveis que quebraram o worker (F10-14) | herdar sem `NODE_*`, `ELECTRON_RUN_AS_NODE`, `ORCA_NODE_OPTIONS` e `ORCA_CLI_COMMAND`; no Windows, completar `USERPROFILE`, `APPDATA` e `LOCALAPPDATA` quando faltam — default (não perguntado) | 2026-11-21 |
| N.5: quem escreve `orca.md` | o Picard / o LaForge pelo `stack_cache.py write` | o LaForge, pelo `stack_cache.py write`, com o arquivo no May change — default (não perguntado) | 2026-11-21 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | A forma do catálogo é conferida antes de gravar; o texto é cortado. |
| External dependency failure | O `orca_cli.run` nunca levanta exceção: 127 sem executável, 124 com tempo esgotado e 126 em erro do sistema. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `scripts/model_info.py:70-114`: `_read`, `download` e `load_catalog`.
- `scripts/screens.py:42-67`: `_orca` resolve com `shutil.which`, usa `TIMEOUT = 60` e lê `ok:false` e `error.message`.
- `hooks/scripts/banner.py:37-48`: `_run` devolve 127, 124 e 126. O banner importa de `ROOT/scripts` (linha 28).
- `scripts/dispatch.py:697-701`: `default_runner` resolve o `orca` pelo PATH (`orca.cmd` no Windows), e os testes injetam um `runner` falso.
- `scripts/stack_cache.py`: `write <repo> <lib> --id --project-version --doc-version --summary-file [--verified]`, com resumo de até 30 linhas.
- Orca instalada: 1.4.268.
