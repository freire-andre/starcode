# Versão do plugin no despacho e estado das ações de retro: Spec

**Approved**: 2026-11-21 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-212
**May change**: scripts/dispatch.py, scripts/handoff.py, scripts/starcode_common.py, scripts/retros.py, hooks/scripts/banner.py, skills/guinan/SKILL.md, skills/guinan/references/retro.md, skills/engajar/references/state-format.md, tests/test_versao_e_retro.py, tests/test_handoff.py, tests/test_banner.py, tests/test_dispatch.py, tests/test_dispatch_start.py, tests/test_support.py, tests/test_licoes_no_brief.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Itens N.4 e N.2 da triagem v2, missão 7a do passo 4 (o usuário escolheu "Duas MÉDIAs"; a 7b leva N.3, N.7 e N.8). Discovery em `.specs/features/versao-e-retro/context.md`. Hoje:
- o brief e o Handoff não dizem que versão do plugin os gerou, e o `dispatch.py` não avisa quando o plugin instalado difere do repositório;
- as ações das retros não têm estado.

## Scope
- Versão do plugin em todo brief gerado pelo `dispatch.py` e no campo `**Plugin:**` do Handoff.
- Aviso do `dispatch.py` quando a versão difere do `VERSION` do repositório do StarCode.
- Coluna `Estado` na tabela da retro e `scripts/retros.py` para listar as abertas e mudar o estado.

## Non-Goals
- Preencher o `Estado` das retros antigas.
- Mudar o aviso do banner (F7-12).
- Tocar o `execute.md` (N.8, missão 7b).

## Decisions
| Item | Options | Status |
|---|---|---|
| Divisão da missão 7 | duas MÉDIAs · uma GRANDE · uma MÉDIA | approved - user: "Duas MÉDIAs (Recomendado)" |
| Sentido do aviso | só instalado mais velho · qualquer diferença | approved - user: "você decide" (qualquer diferença, no `dispatch.py`; default registrado no context.md) |
| Retros sem `Estado` | listar como abertas · contar à parte | approved - user: "você decide" (contar à parte, `--todas` lista; default registrado no context.md) |

## Requirements
- **R1** - The `dispatch.py` SHALL pôr a linha `**Plugin:** StarCode <versão>` logo abaixo do título de todo brief que gera (`brief`, `q-brief`, `screens-brief` e `fix-brief`). A `<versão>` é a do plugin que roda o script, lida como no banner (`.claude-plugin/plugin.json`, depois `crew.json`, depois `VERSION` da raiz do plugin), ou `desconhecida`.
- **R2** - WHEN `dispatch.py start` registra o despacho THEN the system SHALL gravar a mesma versão no campo `**Plugin:**` do Handoff (campo novo do `handoff.py`, opção `--plugin`, padrão `none yet`).
- **R3** - WHEN o `dispatch.py` gera um brief ou roda o `start` num repositório que tem `VERSION` e `dist/claude/.claude-plugin/plugin.json`, e a versão do plugin difere do `VERSION` THEN the system SHALL imprimir no stderr `aviso: plugin StarCode <versão> difere do VERSION <repo> do repositório: o brief segue as regras do plugin instalado`, sem mudar o código de saída. Fora desse repositório, ou com versões iguais, SHALL NOT imprimir o aviso.
- **R4** - The `skills/guinan/references/retro.md` SHALL ter a tabela com a última coluna `Estado` e a regra de que a Guinan escreve `aberto` em cada linha nova. Os valores válidos SHALL ser `aberto`, `aberto: <issue>`, `feito em <commit>` e `recusado: <motivo>`.
- **R5** - The `python scripts/retros.py abertas [--root DIR] [--json] [--todas]` SHALL listar, de todos os `.specs/features/*/retro.md`, as linhas cujo `Estado` começa com `aberto`, uma por linha (`<slug> #<n> <estado>: <ação proposta>`), e terminar com `<N> retro(s) sem coluna Estado`. Com `--todas`, SHALL listar também as linhas das retros sem a coluna, com o estado `sem estado`. A coluna é achada pelo nome do cabeçalho (`Estado`, `Ação proposta`), não pela posição. Exit 0.
- **R6** - The `python scripts/retros.py estado <slug> <n> (--feito <commit> | --recusado <motivo> | --aberto [<issue>])` SHALL reescrever só a célula `Estado` da linha `<n>` e manter o resto do arquivo idêntico em bytes. IF a retro não existe, não tem a coluna `Estado` ou não tem a linha `<n>` THEN SHALL sair com 2 e uma linha com o motivo, sem mudar o arquivo. Um `|` no texto vira `&#124;`.
- **R7** - The `DECISIONS.md` SHALL ter a entrada `### SC-<n>:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug** (com os testes), e o `CHANGELOG.md` uma linha em `[Unreleased]`.

## Edge Cases
- Plugin rodando da própria árvore do repositório (`scripts/` da fonte): a versão vem do `VERSION` e é igual, então não há aviso (R3).
- Retro com `|` escapado como `&#124;` numa célula: a contagem de colunas não quebra (R5, R6).
- `retros.py estado` numa linha que já está `feito em`: sobrescreve (R6).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Os quatro briefs começam com o título e, logo abaixo, `**Plugin:** StarCode <versão>`, com a versão de um plugin falso (manifesto, `crew.json`, `VERSION`, e `desconhecida` sem nenhum dos três) (R1)
Proof: run unit | test_brief_traz_versao_do_plugin (test_versao_e_retro.VersaoERetroTests.test_brief_traz_versao_do_plugin) ... ok

**C2** - `dispatch.py start` com runner falso grava `**Plugin:** <versão>` no Handoff, e o `handoff.py set --plugin` funciona sozinho (R2)
Proof: run unit | test_start_grava_plugin_no_handoff (test_versao_e_retro.VersaoERetroTests.test_start_grava_plugin_no_handoff) ... ok

**C3** - Tabela: repositório do StarCode com versão diferente imprime a linha exata no stderr e sai com o mesmo código; com versão igual ou fora do repositório do StarCode, nada no stderr (R3)
Proof: run unit | test_aviso_de_versao_diferente (test_versao_e_retro.VersaoERetroTests.test_aviso_de_versao_diferente) ... ok

**C4** - `retro.md` da Guinan tem o cabeçalho com `Estado` por último, a regra do `aberto` e os quatro formatos (R4)
Proof: run unit | test_retro_da_guinan_tem_estado (test_versao_e_retro.VersaoERetroTests.test_retro_da_guinan_tem_estado) ... ok

**C5** - `retros.py abertas` numa árvore falsa (retro com `Estado` em colunas fora de ordem e com `&#124;`, retro sem a coluna): saída exata, contagem final, `--todas` e `--json` (R5)
Proof: run unit | test_retros_abertas (test_versao_e_retro.VersaoERetroTests.test_retros_abertas) ... ok

**C6** - `retros.py estado`: os três formatos mudam só a célula (resto idêntico em bytes); retro inexistente, sem coluna e linha inexistente saem com 2, a linha exata e o arquivo intacto (R6)
Proof: run unit | test_retros_estado (test_versao_e_retro.VersaoERetroTests.test_retros_estado) ... ok

**C7** - Entrada do SC no `DECISIONS.md` com as quatro partes e a afirmação completa de cada requisito na seção Decisão, e linha no `CHANGELOG.md` (R7)
Proof: run unit | test_decisions_e_changelog (test_versao_e_retro.VersaoERetroTests.test_decisions_e_changelog) ... ok

## Handoff

**Phase:** review
**Size:** MEDIUM
**Git mode:** 3
**Plugin:** none yet
**Next:** Q verifica
**Linear:** SC-212
**Integration branch:** feature/versao-e-retro
**Last integrated:** T1
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
