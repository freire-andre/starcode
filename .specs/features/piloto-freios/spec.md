# Freios do piloto automático: Spec

**Approved**: 2026-11-16 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: Autorização (o que o piloto pode decidir no lugar do usuário)
**Status**: Approved
**Linear**: SC-187
**May change**: scripts/piloto.py, scripts/gates/gates_common.py, skills/piloto-automatico/SKILL.md, tests/test_piloto.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Itens 0.5, 0.6 e 0.7 da triagem v2, com as decisões D-g e D-h do dono. Discovery: `.specs/features/piloto-freios/context.md`.
- Hoje o gate aceita a aprovação `piloto:` só com o piloto ativo (`scripts/gates/gates_common.py:203-210`), mas a skill manda encerrar o piloto no fim da feature, e o gate reprova se for rodado de novo depois disso.
- `piloto.py registrar` não tem limite para decisões `⚠️ revisar`.
- Dependência nova, esquema de banco e desvio de arquitetura são delegáveis sem mandato.

## Scope
- Gate: a aprovação `piloto:` vale com o piloto ativo ou encerrado, com mandato confirmado pelo usuário e a decisão citada registrada até o encerramento.
- `piloto.py registrar`: freio na 3ª decisão `⚠️ revisar` (exit 3), opção `--categoria`, e registro "devolvido ao usuário" fora do freio.
- Skill `piloto-automatico`: seções 4, 5 e 7 descrevem o freio, a categoria e o novo critério do gate.

## Non-Goals
- Aceite do piloto em sessão real (0.8, pendência do dono).
- Mudar o mandato, `confirmar`, `encerrar`, o banner ou o gate da spec (que continua recusando `piloto:`).
- Detectar sozinho que uma decisão é de dependência, esquema ou arquitetura: quem marca é o Picard, com `--categoria`.

## Decisions
| Item | Options | User answer |
|---|---|---|
| Aprovação `piloto:` depois de `encerrar` (D-g) | continua válida com mandato confirmado e decisão registrada antes do encerramento / deixa de valer | approved - user: decisão D-g da triagem v2 ("Continua válida") |
| 3ª decisão `⚠️ revisar` | recusa, exit 3, freio fica / recusa só a 3ª / grava e sai 3 | approved - user: "Recusa, exit 3, freio fica (Recomendado)" |
| Como reconhecer os três casos de arquitetura (D-h) | opção `--categoria` / só texto da skill | approved - user: "Opção --categoria (Recomendado)" |

## Requirements
- **R1** - WHEN o tasks.md tem `**Approved**: <data> - piloto: "D<n> ..."`, o `piloto.md` está `encerrado`, o mandato foi confirmado pelo usuário e `D<n>` tem carimbo igual ou anterior ao do `**Encerrado:**` THEN `run_gates.py tasks` e `run_gates.py done` SHALL aceitar a aprovação.
- **R2** - IF a decisão citada tem carimbo posterior ao do `**Encerrado:**` THEN os gates de tasks e de verificação SHALL reprovar a aprovação `piloto:`.
- **R3** - IF o mandato não foi confirmado pelo usuário (sem a citação `- user:`) THEN os gates SHALL reprovar a aprovação `piloto:`, com o piloto ativo ou encerrado.
- **R4** - WHEN a feature já tem 2 decisões `⚠️ revisar` e o `registrar` grava uma 3ª que também seria `⚠️ revisar` THEN o `registrar` SHALL recusar sem gravar, sair com 3 e escrever no stderr `freio: 3ª decisão ⚠️ revisar nesta feature; devolva a pergunta ao usuário`.
- **R5** - WHEN a feature tem 1 decisão `⚠️ revisar` e o `registrar` grava a 2ª THEN o `registrar` SHALL gravá-la e sair com 0.
- **R6** - WHILE o freio está acionado (2 ou mais decisões `⚠️ revisar` gravadas) the system SHALL recusar com exit 3 toda nova decisão que seria `⚠️ revisar`, e SHALL continuar gravando decisões de confiança `alta` ou `media` com base.
- **R7** - WHEN o `registrar` recebe `--decision "devolvido ao usuário"` THEN the system SHALL gravar a entrada sem `⚠️ revisar`, sem contá-la no freio e sem recusá-la pelo freio.
- **R8** - IF o `registrar` recebe `--categoria dependencia`, `esquema` ou `arquitetura` sem nenhum `M<n>` em `--basis` THEN the system SHALL recusar sem gravar, sair com 3 e escrever no stderr `categoria <valor> exige item de mandato (--basis M<n>); devolva a pergunta ao usuário`; com um `M<n>` existente SHALL gravar e citar a categoria no título da decisão.
- **R9** - IF `--categoria` recebe outro valor THEN o `registrar` SHALL sair com 2 (uso), sem gravar.
- **R10** - The system SHALL ter na skill `piloto-automatico`: na seção 4, o freio (exit 3 → devolver a pergunta e registrar "devolvido ao usuário") e o uso de `--categoria`; na seção 5, dependência nova, mudança de esquema de banco e desvio de decisão de arquitetura entre o que não é delegado sem item de mandato; e no passo 5 da seção 4, o novo critério do gate (ativo ou encerrado, decisão registrada até o encerramento).
- **R11** - The system SHALL ter no `DECISIONS.md` a entrada da issue desta feature (`### SC-187:`) com **Problema**, **Decisão** (R1 a R10), **Motivo** e **Por que não é bug** citando os testes, e uma linha em `CHANGELOG.md` `[Unreleased]`.

## Edge Cases
- Decisão com carimbo igual ao do `**Encerrado:**` (mesmo segundo): conta como anterior, R1 (C1).
- Decisão `baixa` com base é `⚠️ revisar` e conta no freio: R4 (C4).
- Registro "devolvido ao usuário" depois do freio acionado: R7 (C7).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Piloto encerrado, mandato confirmado e decisão com carimbo igual ou anterior: `tasks` e `done` aceitam (R1)
Proof: run unit | test_aprovacao_vale_depois_de_encerrar (test_piloto.PilotFreiosTests.test_aprovacao_vale_depois_de_encerrar) ... ok

**C2** - Decisão com carimbo posterior ao encerramento: os dois gates reprovam (R2)
Proof: run unit | test_decisao_depois_do_encerramento_reprova (test_piloto.PilotFreiosTests.test_decisao_depois_do_encerramento_reprova) ... ok

**C3** - Mandato sem o usuário reprova com o piloto ativo e encerrado (R3)
Proof: run unit | test_mandato_sem_user_reprova_ativo_e_encerrado (test_piloto.PilotFreiosTests.test_mandato_sem_user_reprova_ativo_e_encerrado) ... ok

**C4** - A 3ª `⚠️ revisar` (inclusive `baixa` com base) sai 3 com a mensagem exata e bytes do `piloto.md` iguais (R4)
Proof: run unit | test_freio_na_terceira_revisar (test_piloto.PilotFreiosTests.test_freio_na_terceira_revisar) ... ok

**C5** - A 2ª `⚠️ revisar` é gravada com exit 0 (R5)
Proof: run unit | test_segunda_revisar_segue (test_piloto.PilotFreiosTests.test_segunda_revisar_segue) ... ok

**C6** - Com o freio acionado, nova `⚠️ revisar` sai 3 e decisão `alta` com base é gravada (R6)
Proof: run unit | test_freio_fica_e_alta_segue (test_piloto.PilotFreiosTests.test_freio_fica_e_alta_segue) ... ok

**C7** - "devolvido ao usuário" é gravado sem `⚠️ revisar`, não conta e passa com o freio acionado (R7)
Proof: run unit | test_devolvido_ao_usuario_fora_do_freio (test_piloto.PilotFreiosTests.test_devolvido_ao_usuario_fora_do_freio) ... ok

**C8** - Cada `--categoria` sem `M<n>` sai 3 com a mensagem exata; com `M<n>` grava e cita a categoria (R8)
Proof: run unit | test_categoria_exige_mandato (test_piloto.PilotFreiosTests.test_categoria_exige_mandato) ... ok

**C9** - `--categoria` inválida sai 2 sem gravar (R9)
Proof: run unit | test_categoria_invalida_sai_2 (test_piloto.PilotFreiosTests.test_categoria_invalida_sai_2) ... ok

**C10** - Textos de R10 nas seções 4 e 5 da skill (R10)
Proof: run unit | test_skill_descreve_freio_e_categoria (test_piloto.PilotFreiosTests.test_skill_descreve_freio_e_categoria) ... ok

**C11** - Entrada do `DECISIONS.md` com os quatro campos, R1 a R10 na Decisão, testes citados e linha no CHANGELOG (R11)
Proof: run unit | test_decisions_piloto_freios (test_piloto.PilotFreiosTests.test_decisions_piloto_freios) ... ok

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** LaForge implementa T1 (SC-187)
**Linear:** SC-187
**Integration branch:** feature/piloto-freios
**Last integrated:** b6cc2083d0a67faf4570989be362799d5e941163
**Dispatched:** none
**Settled:** 2026-11-16: spec + issue: "sim"
**Attempts:** none
**Reports:** 2026-11-16: T1: gate ativo/encerrado, freio exit 3, devolvido fora do freio, --categoria, skill, DECISIONS, CHANGELOG, dist; 949 OK; ticket gate verde em 0ba1ba9; 2026-11-16: provas verdes; 2026-11-16: Q: codex · effective unconfirmed · FAIL, 4 achados (devolvido + --categoria sem M<n> gravado, contra R8; C6, C7 sem conferir o arquivo; C11 sem os termos de R10); 949 OK; q-check 0. Decisão do Picard: segue a spec aprovada (R8 recusa também o devolvido; o devolvido é gravado sem --categoria)
**Breaker:** closed
