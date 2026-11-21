# Catálogo conferido e adaptador da Orca: Spec

**Approved**: 2026-11-21 - user: "sim["

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-211
**May change**: scripts/model_info.py, scripts/orca_cli.py, scripts/screens.py, scripts/dispatch.py, hooks/scripts/banner.py, .specs/stack/orca.md, tests/test_catalogo_e_orca.py, tests/test_model_info.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Itens C.6 e N.5 da triagem v2, missão 6 do passo 4. Discovery em `.specs/features/catalogo-e-orca/context.md`. Hoje:
- o cache do models.dev aceita qualquer objeto JSON;
- o texto do catálogo chega cru ao agente, e o catálogo é relido a cada consulta;
- três scripts chamam a Orca cada um do seu jeito.

## Scope
- `model_info.py`: forma conferida antes de gravar, texto limpo e cortado, catálogo lido uma vez por processo.
- `scripts/orca_cli.py`: resolução do executável, env, tempo limite e leitura do JSON. É usado pelo `screens.py`, pelo banner e pelo `dispatch.py`.
- `.specs/stack/orca.md` com o comportamento verificado, gravado pelo `stack_cache.py write`.

## Non-Goals
- O worker TS da Ponte.
- Mudar mensagens ou códigos de saída do `screens.py`, do banner ou do `dispatch.py`.

## Decisions
| Item | Options | Status |
|---|---|---|
| Forma mínima do catálogo | objeto não vazio · ao menos um provedor com `models` objeto | approved - user: "você decide" (ao menos um provedor com `models` objeto; default registrado no context.md) |
| Env do CLI | herdar · herdar sem as variáveis da F10-14 | approved - user: "você decide" (sem as variáveis da F10-14; default registrado no context.md) |
| Quem escreve `orca.md` | Picard · LaForge pelo `stack_cache.py` | approved - user: "você decide" (LaForge pelo `stack_cache.py`; default registrado no context.md) |

## Requirements
- **R1** - WHEN `model_info.download` recebe JSON sem ao menos um provedor cujo valor é objeto com `models` objeto THEN the system SHALL devolver `None` e SHALL NOT tocar o cache: o arquivo existente fica idêntico em bytes e em `mtime`.
- **R2** - The `model_info.info` SHALL limpar o `name` e a `description` (tirar os caracteres de controle da categoria Unicode `C*`, inclusive ESC e quebras de linha; juntar espaços em branco seguidos num só; cortar o `name` em 80 caracteres e a `description` em 200), e a mesma limpeza vale para a saída `--json` e para o `render`.
- **R3** - The `model_info.load_catalog` SHALL interpretar o arquivo de catálogo no máximo uma vez por processo para a mesma origem (arquivo de `STARCODE_MODELS_DEV_FILE` ou cache). Chamadas seguintes de `load_catalog`, `cached_family` e `cached_tier` SHALL reutilizar o resultado. Um `download` bem-sucedido SHALL atualizar o resultado guardado.
- **R4** - The `scripts/orca_cli.py` SHALL oferecer `resolve()` (o caminho do `orca` pelo PATH com `shutil.which`, que acha o `orca.cmd` no Windows, ou `None`), `env()` (cópia do ambiente sem as chaves `NODE_*`, `ELECTRON_RUN_AS_NODE`, `ORCA_NODE_OPTIONS` e `ORCA_CLI_COMMAND`; no Windows, completa `USERPROFILE`, `APPDATA` e `LOCALAPPDATA` a partir da pasta do usuário quando faltam) e `run(args, timeout, cwd=None)`, que devolve `code`, `stdout`, `stderr`, `data` (o JSON do stdout quando é objeto, senão `None`) e `error`: `None` em sucesso; em falha (código diferente de 0 ou `data.ok` falso), a primeira mensagem não vazia entre `error.message`, `error` texto, stderr, stdout e `saiu com <código>`. O `run` SHALL NOT levantar exceção: devolve 127 sem executável, 124 com tempo esgotado e 126 com `OSError`.
- **R5** - The `screens.py` e o `hooks/scripts/banner.py` SHALL chamar a Orca pelo `orca_cli.run`, e o `dispatch.default_runner` pelo `orca_cli.resolve` e `orca_cli.env`. Nenhum arquivo `.py` em `scripts/` ou `hooks/` fora do `orca_cli.py` SHALL chamar `shutil.which("orca")`, e as mensagens e os códigos de saída dos três não mudam.
- **R6** - The `.specs/stack/orca.md` SHALL existir, gravado por `python scripts/stack_cache.py write . orca ...` com a versão 1.4.268, com um resumo que cita a resolução do CLI (Electron e `ELECTRON_RUN_AS_NODE`, F10-14), o env, o `--current` que olha o terminal que chama (F10-8), a resposta `ok:false` com `error.message` e o `orca plugin test` que só roda no mesmo drive da instalação; o `python scripts/stack_cache.py check .` SHALL dar `ok` para a entrada `orca`.
- **R7** - The `DECISIONS.md` SHALL ter a entrada `### SC-<n>:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug** (com os testes), e o `CHANGELOG.md` uma linha em `[Unreleased]`.

## Edge Cases
- Resposta 200 com `{"error": "rate limited"}`: o cache bom fica (R1).
- `description` com `\x1b[31m` e quebras de linha: sai sem ESC e numa linha só (R2).
- Orca ausente no PATH: o banner segue com "comando `orca` não encontrado no PATH" (R5).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Resposta com forma errada (lista de casos: objeto vazio, provedor sem `models`, `models` não objeto) devolve `None` e deixa o cache idêntico em bytes e `mtime`; uma forma válida grava (R1)
Proof: run unit | test_download_confere_forma (test_catalogo_e_orca.CatalogoEOrcaTests.test_download_confere_forma) ... ok

**C2** - `name` e `description` com ESC, quebras e texto longo saem limpos e cortados em 80 e 200, no `info` e no `render` (R2)
Proof: run unit | test_texto_do_catalogo_limpo (test_catalogo_e_orca.CatalogoEOrcaTests.test_texto_do_catalogo_limpo) ... ok

**C3** - Três chamadas (`load_catalog`, `cached_family`, `cached_tier`) interpretam o arquivo uma vez só; depois de um `download` o resultado novo é o devolvido (R3)
Proof: run unit | test_catalogo_lido_uma_vez (test_catalogo_e_orca.CatalogoEOrcaTests.test_catalogo_lido_uma_vez) ... ok

**C4** - `orca_cli`: `env` tira as chaves proibidas e completa as pastas do Windows; `run` com executável falso dá sucesso com `data`, `ok:false` com `error.message`, 127, 124 e 126, sem exceção (R4)
Proof: run unit | test_orca_cli_run_e_env (test_catalogo_e_orca.CatalogoEOrcaTests.test_orca_cli_run_e_env) ... ok
Proof: run unit | test_saida_127_124_126_do_orca (test_catalogo_e_orca.CatalogoEOrcaTests.test_saida_127_124_126_do_orca) ... ok

**C5** - Nenhum `shutil.which("orca")` fora do `orca_cli.py` em `scripts/` e `hooks/`, e `screens`, banner e `dispatch` importam o `orca_cli` (R5)
Proof: run unit | test_um_adaptador_da_orca (test_catalogo_e_orca.CatalogoEOrcaTests.test_um_adaptador_da_orca) ... ok

**C6** - `.specs/stack/orca.md` existe com a versão 1.4.268 e os cinco temas, e o `stack_cache.py check` dá `ok` para `orca` (R6)
Proof: run unit | test_stack_orca_documentada (test_catalogo_e_orca.CatalogoEOrcaTests.test_stack_orca_documentada) ... ok

**C7** - Entrada do SC no `DECISIONS.md` com as quatro partes e os termos de cada requisito, e linha no `CHANGELOG.md` (R7)
Proof: run unit | test_decisions_e_changelog (test_catalogo_e_orca.CatalogoEOrcaTests.test_decisions_e_changelog) ... ok

## Handoff

**Phase:** pr-review
**Size:** MEDIUM
**Git mode:** 3
**Next:** push e PR (com confirmação), depois Worf
**Linear:** SC-211
**Integration branch:** feature/catalogo-e-orca
**Last integrated:** T1
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
