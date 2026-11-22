# Suíte rápida, regra de estado e execute.md dividido: Spec

**Approved**: 2026-11-22 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-213
**May change**: scripts/dispatch.py, skills/engajar/SKILL.md, skills/engajar/references/execute.md, skills/engajar/references/execute-despacho.md, skills/engajar/references/execute-provas-e-q.md, skills/engajar/references/execute-pos-q-e-review.md, skills/engajar/references/execute-retomada.md, skills/engajar/references/execute-modo-1.md, skills/engajar/references/execute-media-pequena.md, skills/engajar/references/state-format.md, skills/piloto-automatico/SKILL.md, skills/laforge/SKILL.md, skills/mccoy/SKILL.md, src/context/STARCODE.md, AGENTS.md, tests/test_suite_e_execute.py, tests/test_support.py, tests/test_brief_media_escopo.py, tests/test_crew_live.py, tests/test_dispatch.py, tests/test_dispatch_qcheck.py, tests/test_dispatch_decisions.py, tests/test_dispatch_start.py, tests/test_execute_doc_start_settle.py, tests/test_fecha_achado.py, tests/test_flow_f12.py, tests/test_flow_worf_guinan.py, tests/test_licoes_no_brief.py, tests/test_pequena_minima.py, tests/test_skills_exec.py, tests/test_pr_review.py, tests/test_screens_flow.py, tests/test_uhura_skill.py, tests/test_worker_skills.py, tests/test_roteamento_worf_mccoy.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Itens N.3, N.7 e N.8 da triagem v2, missão 7b do passo 4. Discovery em `.specs/features/suite-e-execute/context.md`. Hoje:
- a suíte leva cerca de 25 min no F: (1.083 testes em 1.519 s, 2026-11-21), e a correção pós-Q exige "a suíte inteira verde" (`scripts/dispatch.py`, `FIX_RULES`);
- o estado novo não segue um padrão único (`lessons.py` guarda JSON; `piloto.py` guarda markdown lido por regex);
- o `execute.md` tem 3.977 palavras, e o Picard o carrega inteiro em toda feature.

## Scope
- Worker (ticket e correção pós-Q) roda a seleção do `impact.py`; a suíte inteira fica no gate de done (`Run unit`) e no CI.
- Medição única da suíte com `--durations 20`, anotada no `DECISIONS.md` com a linha de base.
- Regra de estado novo no `AGENTS.md`.
- `execute.md` vira índice; cada etapa ganha um arquivo em `skills/engajar/references/`.

## Non-Goals
- Acelerar, isolar ou reescrever testes lentos (decisão do usuário: fica para depois da pausa).
- Mudar o formato do Handoff (continua markdown).
- Mudar o texto das regras do fluxo ao dividir o `execute.md`: só move, com ajustes de referência cruzada.
- Mudar o `impact.py`, o gate de done ou o CI.
- Atualizar `docs/aceite/` (registro histórico).

## Decisions
| Item | Options | Status |
|---|---|---|
| Alcance do N.3 | só medir e trocar · também acelerar os testes lentos | approved - user: "Só medir e trocar (Recommended)" |
| Ampliar o May change durante o T1 (6 testes que leem o `execute.md` ou exigem o `piloto-automatico/SKILL.md` igual ao da main) | ampliar os 6 · só os 5 do `execute.md` · parar | approved - user: "Ampliar e seguir (Recommended)" (2026-11-22) |

## Requirements
- **R1** - The `FIX_RULES` do `scripts/dispatch.py` SHALL trocar "a suíte inteira verde" por: os testes escolhidos por `python "{plugin}/scripts/impact.py" select --diff <base>` verdes, e a suíte inteira só quando o veredito for `rodar tudo` ou a seleção falhar; mais o gate `ticket` verde, como hoje.
- **R2** - The `WORKER_RULES` do `scripts/dispatch.py` SHALL ter a mesma regra de testes do R1 antes da linha do gate `ticket`, e a regra do relatório final SHALL pedir a linha de veredito do `impact.py`.
- **R3** - The `skills/laforge/SKILL.md` e o `skills/mccoy/SKILL.md` SHALL dizer que o worker roda a seleção do `impact.py` (a suíte inteira só com `rodar tudo` ou seleção falha) e que a suíte inteira roda no gate de done (`Run unit` da spec) e no CI. A frase "The gates still run the whole suite" SHALL sair do McCoy.
- **R4** - The `DECISIONS.md` SHALL registrar uma medição de `python -m unittest discover -s tests --durations 20` feita nesta feature: número de testes, tempo total em segundos, os 5 testes mais lentos com o tempo de cada um, a máquina/drive, e a linha de base `1.083 testes em 1.519 s (2026-11-21, F:)`.
- **R5** - The `AGENTS.md` SHALL ter, em `## Regras`, a regra: arquivo de estado novo é JSON escrito por script, e o markdown que alguém lê é gerado a partir dele; o Handoff (`## Handoff`) continua markdown escrito pelo `handoff.py`.
- **R6** - The `skills/engajar/references/execute.md` SHALL manter o título, a introdução, as seções 0 e 1 e um índice que liga cada seção a seu arquivo: 2, 2F e 3 → `execute-despacho.md`; 4 → `execute-provas-e-q.md`; 5, Review (Worf) e Text for the PR → `execute-pos-q-e-review.md`; 6 → `execute-retomada.md`; 7 → `execute-modo-1.md`; 8 → `execute-media-pequena.md`; com a regra de carregar só o arquivo da etapa em curso. O `execute.md` SHALL ter no máximo 700 palavras.
- **R7** - The cada novo arquivo `execute-*.md` SHALL começar com um título `# Execute: <etapa>`, uma linha que remete ao `execute.md` para variáveis e pré-condições, e as suas seções com os mesmos cabeçalhos `## ` de hoje; cada cabeçalho `## ` do `execute.md` atual SHALL aparecer exatamente uma vez no conjunto dos sete arquivos.
- **R8** - The texto das seções movidas SHALL ser preservado: cada frase que os testes atuais exigem do `execute.md` SHALL continuar no conjunto, e os testes passam a ler o conjunto por um helper `execute_text()` em `tests/test_support.py` (o `execute.md` seguido dos `execute-*.md` em ordem alfabética).
- **R9** - The referências por seção ao `execute.md` em `skills/engajar/SKILL.md`, `skills/engajar/references/state-format.md`, `skills/piloto-automatico/SKILL.md`, `src/context/STARCODE.md` e no aviso do modo 1 do `scripts/dispatch.py` (`siga a seção 7 do execute.md, sem start`) SHALL apontar o arquivo novo da seção (ex.: `execute-media-pequena.md`, seção 8; `siga o execute-modo-1.md, sem start`).
- **R10** - The `DECISIONS.md` SHALL ter a entrada `### SC-<n>:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug** (com os testes), e o `CHANGELOG.md` uma linha em `[Unreleased]`.

## Edge Cases
- `impact.py` com veredito `rodar tudo` ou falhando (git ausente, tempo esgotado): a regra manda rodar a suíte inteira, nunca um conjunto vazio (R1, R2).
- Seção que cita outra seção pelo número ("section 7", "passo 3"): a referência continua válida porque os números e os cabeçalhos não mudam e o índice diz onde cada número mora (R6, R7).
- `dist/`: o build copia os arquivos novos de `references/` para todas as CLIs (`tools/build.py`, `rglob`); `python tools/build.py --check` confere.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - O `fix-brief` gerado traz a regra da seleção do `impact.py` com o fallback para a suíte inteira e não traz mais "a suíte inteira verde" (R1)
Proof: run unit | test_fix_brief_usa_selecao_do_impact (test_suite_e_execute.SuiteEExecuteTests.test_fix_brief_usa_selecao_do_impact) ... ok

**C2** - O brief de ticket traz a mesma regra antes da linha do gate `ticket` e pede a linha de veredito do `impact.py` no relatório (R2)
Proof: run unit | test_brief_do_ticket_usa_selecao_do_impact (test_suite_e_execute.SuiteEExecuteTests.test_brief_do_ticket_usa_selecao_do_impact) ... ok

**C3** - LaForge e McCoy citam a seleção do `impact.py`, o fallback e a suíte inteira no done e no CI; o McCoy não tem "The gates still run the whole suite" (R3)
Proof: run unit | test_laforge_e_mccoy_rodam_a_selecao (test_suite_e_execute.SuiteEExecuteTests.test_laforge_e_mccoy_rodam_a_selecao) ... ok

**C4** - A entrada da SC no `DECISIONS.md` tem `--durations 20`, a linha de base `1.083 testes em 1.519 s`, a contagem e o tempo novos e cinco testes com tempo (R4)
Proof: run unit | test_decisions_registra_a_medicao (test_suite_e_execute.SuiteEExecuteTests.test_decisions_registra_a_medicao) ... ok

**C5** - `AGENTS.md`, em `## Regras`, tem a regra do estado novo em JSON com markdown gerado e a exceção do Handoff (R5)
Proof: run unit | test_agents_tem_regra_de_estado (test_suite_e_execute.SuiteEExecuteTests.test_agents_tem_regra_de_estado) ... ok

**C6** - O `execute.md` tem as seções 0 e 1, o índice com os seis arquivos e suas seções, a regra de carregar só a etapa, e no máximo 700 palavras; cada arquivo novo existe e começa com `# Execute:` (R6, R7)
Proof: run unit | test_execute_md_vira_indice (test_suite_e_execute.SuiteEExecuteTests.test_execute_md_vira_indice) ... ok

**C7** - Os 12 cabeçalhos `## ` atuais aparecem exatamente uma vez no conjunto e cada um no arquivo que o índice diz; o helper `execute_text()` lê os sete arquivos (R7, R8)
Proof: run unit | test_cabecalhos_no_arquivo_certo (test_suite_e_execute.SuiteEExecuteTests.test_cabecalhos_no_arquivo_certo) ... ok

**C8** - Os testes de documentação que liam o `execute.md` passam lendo `execute_text()` (R8)
Proof: run unit | test_execute_md_snapshot_antes_do_ticket (test_flow_f12.FlowF12Tests.test_execute_md_snapshot_antes_do_ticket) ... ok
Proof: run unit | test_testes_leem_o_execute_por_execute_text (test_suite_e_execute.SuiteEExecuteTests.test_testes_leem_o_execute_por_execute_text) ... ok

**C9** - Nenhuma referência "`execute.md` section 6/7/8" ou "seção 7 do execute.md" sobra em `skills/`, `src/` e `scripts/`; cada uma aponta o arquivo novo; o aviso do modo 1 diz `siga o execute-modo-1.md, sem start` (R9)
Proof: run unit | test_referencias_apontam_o_arquivo_novo (test_suite_e_execute.SuiteEExecuteTests.test_referencias_apontam_o_arquivo_novo) ... ok

**C10** - Entrada da SC no `DECISIONS.md` com as quatro partes e linha no `CHANGELOG.md` (R10)
Proof: run unit | test_decisions_e_changelog (test_suite_e_execute.SuiteEExecuteTests.test_decisions_e_changelog) ... ok

## Handoff

**Phase:** pr-review
**Size:** MEDIUM
**Git mode:** 3
**Plugin:** 1.8.0
**Next:** Worf revisa o PR #82
**Linear:** SC-213
**Integration branch:** feature/suite-e-execute
**Last integrated:** 61344181c5488f06da3cc3d69c5a626741c7588c
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** 2026-11-22: T1: R1-R10 em 844421b; gate ticket verde; suíte 1.100 OK (667,5 s no C:); disjuntor none; 2026-11-22: Q: FAIL, 7 achados (C1-C4, C6, C8-C10); q-check ok; verifier codex effective unconfirmed; 2026-11-22: pós-Q: 7 achados fechados (0350d2f..45a37bd), merge 9e6f58c; gate ticket verde; 2026-11-22: done verde em 035cdde; proofs verdes; 2026-11-22: Guinan: L91-L93 novas; L2, L10, L20, L32 reforçadas; retro com 1 ação aberta
**Breaker:** closed
