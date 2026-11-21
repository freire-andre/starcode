# Restauração pelo snapshot e telas restritas: Spec

**Approved**: 2026-11-21 - user: "Sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-210
**May change**: scripts/snapshot.py, scripts/gates/check_scope.py, scripts/screens.py, scripts/gates/validate_verification.py, scripts/gates/images.py, tests/test_restauracao_e_telas.py, tests/test_snapshot.py, tests/test_screens.py, tests/test_images.py, tests/test_validate_verification.py, tests/test_validate_verification_screens.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Itens R.5 e R.10 da triagem v2 (seção 10), missão 5 do passo 4. Discovery em `.specs/features/restauracao-e-telas/context.md`. Hoje:
- o `restore` lê o escopo da árvore de trabalho, e não do snapshot;
- a captura de telas aceita qualquer host e qualquer `--out`;
- o veredito casa por trecho de nome;
- um PNG só com cabeçalho passa.

## Scope
- `snapshot.py restore` com o `May change` lido do snapshot.
- `screens.py capture` restrito a host local e a `captures/<nome>.running.png`.
- Veredito do `screens.md` pelo nome inteiro; PNG sem `IDAT` recusado.

## Non-Goals
- JPEG e WebP sem dados.
- Mudar o formato do `screens.md` ou do snapshot.

## Decisions
| Item | Options | Status |
|---|---|---|
| Hosts fora de localhost | recusar sempre · recusar por padrão com `--allow-host` | approved - user: "você decide" (recusar por padrão com `--allow-host`; default registrado no context.md) |
| PNG sem dados | exigir `IDAT` · exigir `IDAT` e `IEND` | approved - user: "você decide" (exigir `IDAT`; default registrado no context.md) |
| Snapshot sem o artefato | cair para a árvore · recusar | approved - user: "você decide" (recusar; default registrado no context.md) |

## Requirements
- **R1** - WHEN `snapshot.py restore <slug> <ticket>` roda THEN the system SHALL ler o `May change` do `tasks.md` (ou, sem ele, do `spec.md`) da feature como está gravado no commit do snapshot (`git show <snapshot>:<caminho>`), e não da árvore de trabalho. IF o snapshot não tem nem `tasks.md` nem `spec.md` da feature THEN SHALL sair com 2 e `snapshot sem tasks.md nem spec.md de <slug>: restauração recusada`, sem mudar nenhum arquivo.
- **R2** - The `screens.py capture` SHALL aceitar a URL só quando o host, em minúsculas, é `localhost`, `127.0.0.1`, `[::1]` ou termina em `.localhost`, ou quando é igual a um `--allow-host <host>` (repetível). Nos demais casos SHALL sair com 2 e `host fora do padrão local: <host> (use --allow-host <host> para liberar)`, antes de abrir a aba.
- **R3** - The `screens.py capture` SHALL aceitar `--out` só quando o arquivo termina em `.running.png` e a pasta-mãe se chama `captures`. Nos demais casos SHALL sair com 2 e `--out precisa ser captures/<nome>.running.png: <valor>`, antes de abrir a aba.
- **R4** - The `validate_verification.py` SHALL casar o veredito do `screens.md` com a captura pelo nome inteiro: a célula da tela, sem crases, SHALL ter como último segmento do caminho exatamente `<nome>.running.png` ou `<nome>.png`. `admin-login.running.png` SHALL NOT satisfazer `login.png`.
- **R5** - The `images.image_size` SHALL recusar um PNG sem nenhum chunk `IDAT`, com a mensagem `<caminho>: PNG sem dados de imagem (nenhum IDAT)`.
- **R6** - The `DECISIONS.md` SHALL ter a entrada `### SC-<n>:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug** (com os testes), e o `CHANGELOG.md` uma linha em `[Unreleased]`.

## Edge Cases
- Escopo ampliado na árvore depois do snapshot: o arquivo fora do escopo gravado não é restaurado (R1).
- `http://LOCALHOST:3000`: o host é comparado em minúsculas (R2).
- Célula `captures/login.running.png`: casa com `login.png` (R4).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Escopo ampliado na árvore depois do snapshot não entra na restauração; snapshot sem artefato dá código 2, a linha exata e nenhum arquivo mudado (R1)
Proof: run unit | test_restore_le_escopo_do_snapshot (test_restauracao_e_telas.RestauracaoETelasTests.test_restore_le_escopo_do_snapshot) ... ok

**C2** - Tabela de URLs: os quatro hosts locais, o host em maiúsculas e um host liberado passam; outro host dá código 2 e a linha exata, sem chamar a Orca (R2)
Proof: run unit | test_capture_so_host_local (test_restauracao_e_telas.RestauracaoETelasTests.test_capture_so_host_local) ... ok

**C3** - Tabela de `--out`: `captures/x.running.png` passa; `captures/x.png`, `outro/x.running.png` e `x.running.png` dão código 2 e a linha exata, sem chamar a Orca (R3)
Proof: run unit | test_capture_out_restrito (test_restauracao_e_telas.RestauracaoETelasTests.test_capture_out_restrito) ... ok

**C4** - `admin-login.running.png` não satisfaz `login.png` e o erro `screens.md sem veredito para` aparece; `login.running.png` e `captures/login.png` satisfazem (R4)
Proof: run unit | test_veredito_nome_inteiro (test_restauracao_e_telas.RestauracaoETelasTests.test_veredito_nome_inteiro) ... ok

**C5** - PNG só com cabeçalho recusado com a mensagem exata; PNG válido com `IDAT` lido (R5)
Proof: run unit | test_png_sem_idat (test_restauracao_e_telas.RestauracaoETelasTests.test_png_sem_idat) ... ok

**C6** - Entrada do SC no `DECISIONS.md` com as quatro partes e os termos de cada requisito, e linha no `CHANGELOG.md` (R6)
Proof: run unit | test_decisions_e_changelog (test_restauracao_e_telas.RestauracaoETelasTests.test_decisions_e_changelog) ... ok

## Handoff

**Phase:** review
**Size:** MEDIUM
**Git mode:** 3
**Next:** Q verifica
**Linear:** SC-210
**Integration branch:** feature/restauracao-e-telas
**Last integrated:** T1 (82be556)
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
