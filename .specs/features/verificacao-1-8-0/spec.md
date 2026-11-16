# Verificação retroativa da 1.8.0: Spec

**Approved**: 2026-11-16 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-186
**May change**: scripts/piloto.py, scripts/model_info.py, scripts/gates/gates_common.py, scripts/gates/validate_tasks.py, scripts/gates/validate_verification.py, scripts/starcode_common.py, scripts/setup_helpers.py, tests/test_piloto.py, tests/test_model_info.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Item 0.3 da triagem v2 (`starcode-triagem-v2-2026-11-13.md`, fora do Git) e decisão D-j: a 1.8.0 saiu sem `.specs/features/`, sem `verification.md` e sem aceite. A regularização é uma lista curta de requisitos tirada do `CHANGELOG.md` `[1.8.0]`, das docstrings de `scripts/piloto.py` e `scripts/model_info.py` e do texto das skills. Em seguida, o Q é despachado sobre `piloto.py`, `model_info.py` e a mudança nos gates, e os achados são fechados. O Q julga o estado atual na `main` (514734a), porque os itens 0.4, C.1 e C.2 do primeiro corte já mudaram esses arquivos. Sucesso: cada promessa da 1.8.0 abaixo tem um teste que falharia se ela fosse falsa, ou um achado fechado.

## Scope
- `scripts/piloto.py`: mandato, decisões, confiança, `ativo`, códigos de saída.
- Gates: aprovação `piloto: "D<n> ..."` aceita só no tasks/verificação, com piloto ativo, mandato confirmado e decisão registrada.
- `scripts/model_info.py`: faixa de custo, veredito por papel, cache, códigos de saída, família.
- Config local por repositório: precedência e esquema.
- Texto das skills `piloto-automatico` e `troi` (seção 2G), na parte que os testes já cobrem.

## Non-Goals
- Skill `menu` (só texto, D-j).
- Tasks, Worf e retro retroativos (D-j).
- Comportamento novo além do que a 1.8.0 promete (congelamento D-i); um achado só corrige teste, código ou texto para cumprir o prometido.
- A troca de faixa do `gpt-6-luna` (dado do catálogo, não comportamento).

## Requirements
- **R1** - WHEN `piloto.py start <slug>` roda numa feature existente THEN the system SHALL criar `piloto.md` com `**Status:** ativo` e mandato pendente, e uma segunda chamada SHALL deixar o arquivo igual.
- **R2** - WHEN `piloto.py mandato` acrescenta itens antes de `confirmar` THEN the system SHALL numerá-los `M1`, `M2`... na ordem; IF `mandato` roda depois de `confirmar` THEN the system SHALL recusar com exit 1 sem mudar o arquivo.
- **R3** - IF `piloto.py registrar` roda sem mandato confirmado pelo usuário, ou com o piloto encerrado THEN the system SHALL recusar com exit 1 sem registrar a decisão.
- **R4** - WHEN uma decisão é registrada sem `--basis` THEN the system SHALL gravá-la com confiança `baixa`, e toda decisão `baixa` SHALL sair marcada `⚠️ revisar` no `piloto.md` e no `status`.
- **R5** - The system SHALL fazer `piloto.py` sair com 0 em sucesso, 1 para feature/piloto ausente ou regra recusada, e 2 para erro de uso.
- **R6** - WHEN o piloto está ativo com mandato confirmado THEN `piloto.py ativo <slug>` SHALL sair com 0 e o banner SHALL mostrar o piloto ativo; caso contrário `ativo` SHALL sair com 1.
- **R7** - WHEN o tasks.md tem `**Approved**: <data> - piloto: "D<n> ..."`, o piloto está ativo, o mandato foi confirmado pelo usuário e `D<n>` está registrada no `piloto.md` THEN os gates de tasks e de verificação SHALL aceitar a linha.
- **R8** - IF falta qualquer condição de R7 (sem `piloto.md`, piloto inativo, mandato sem o usuário, `D<n>` não registrada) THEN os gates de tasks e de verificação SHALL reprovar, e o gate da spec SHALL reprovar a linha `piloto:` em qualquer caso.
- **R9** - The system SHALL dar a faixa de custo pelo preço de saída por 1M tokens: `grátis` quando 0 ou id terminado em `:free`/`-free`, `$` abaixo de 2, `$$` abaixo de 12, `$$$` de 12 para cima, e `?` sem preço.
- **R10** - The system SHALL vetar todo papel para modelo sem chamada de ferramentas, avisar contexto abaixo de 200k em `pesado` e `execucao`, avisar falta de raciocínio em `pesado` e `q`, avisar modelo `$`/`grátis` em `pesado` e modelo `$$$` em `repetitivo`.
- **R11** - The system SHALL usar o catálogo em cache por até 7 dias, ler `STARCODE_MODELS_DEV_FILE` quando definido, e sair com 3 sem rede e sem cache, sem inventar dados; `model_info.py` SHALL sair com 0 (todos achados), 1 (algum id ausente), 2 (uso) ou 3 (catálogo indisponível).
- **R12** - WHEN o catálogo em cache tem um modelo `provedor/modelo` do OpenCode THEN o despacho SHALL dar a família do fabricante, e o `q_cli` SHALL aceitar esse modelo como Q quando a família difere da do LaForge; sem catálogo a família SHALL continuar `unknown`.
- **R13** - The system SHALL aplicar a precedência config local (`.starcode/config.local.json`) > config do usuário > `crew.yaml`, aceitar no config local só a chave `crew`, e o banner e a tabela da tripulação SHALL mostrar a origem local.
- **R14** - The system SHALL ter, na skill `piloto-automatico`, push, PR, merge e deploy reservados ao usuário e as decisões sem base marcadas `⚠️ revisar`; e, na skill `troi`, a seção 2G com perguntas numeradas `Q<n>` e sem teto de rodadas.

## Edge Cases
- Id `D07` cita a decisão 7: R7 (C7).
- Duas linhas `piloto:`, uma válida: R7 (C7).
- Catálogo velho (mais de 7 dias) sem rede: R11 (C11).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `start` cria `piloto.md` ativo com mandato pendente e é idempotente (R1)
Proof: run unit | test_start_is_idempotent_and_fixed_format (test_piloto.PilotoScriptTests.test_start_is_idempotent_and_fixed_format) ... ok

**C2** - Mandato numerado na ordem e recusado com exit 1 depois de `confirmar` (R2)
Proof: run unit | test_mandate_numbered_and_locked_after_confirm (test_piloto.PilotoScriptTests.test_mandate_numbered_and_locked_after_confirm) ... ok

**C3** - `registrar` recusado sem mandato confirmado pelo usuário e depois de `encerrar` (R3)
Proof: run unit | test_no_decision_before_confirmed_mandate (test_piloto.PilotoScriptTests.test_no_decision_before_confirmed_mandate) ... ok
Proof: run unit | test_finish_stops_decisions (test_piloto.PilotoScriptTests.test_finish_stops_decisions) ... ok
Proof: run unit | test_registrar_exige_mandato_com_user (test_piloto.PilotDecisaoCitadaTests.test_registrar_exige_mandato_com_user) ... ok

**C4** - Decisão sem `--basis` vira `baixa` e toda `baixa` sai `⚠️ revisar` (R4)
Proof: run unit | test_record_decisions_confidence_and_review (test_piloto.PilotoScriptTests.test_record_decisions_confidence_and_review) ... ok

**C5** - Códigos de saída 0, 1 e 2 do `piloto.py` (R5)
Proof: run unit | test_cli_exit_codes (test_piloto.PilotoScriptTests.test_cli_exit_codes) ... ok

**C6** - `ativo` sai 0 só com piloto ativo e mandato confirmado; banner mostra o piloto (R6)
Proof: run unit | test_banner_shows_active_autopilot (test_piloto.PilotBannerTests.test_banner_shows_active_autopilot) ... ok

**C7** - Gates de tasks e verificação aceitam `piloto: "D<n>"` com as quatro condições, `D07` cita D7 e uma linha válida basta (R7)
Proof: run unit | test_aprovacao_com_decisao_registrada_passa_nos_dois_gates (test_piloto.PilotDecisaoCitadaTests.test_aprovacao_com_decisao_registrada_passa_nos_dois_gates) ... ok
Proof: run unit | test_d07_cita_d7 (test_piloto.PilotDecisaoCitadaTests.test_d07_cita_d7) ... ok
Proof: run unit | test_uma_linha_valida_basta (test_piloto.PilotDecisaoCitadaTests.test_uma_linha_valida_basta) ... ok

**C8** - Sem uma das condições os gates reprovam; o gate da spec sempre reprova `piloto:` (R8)
Proof: run unit | test_decisao_inexistente_reprova_nos_dois_gates (test_piloto.PilotDecisaoCitadaTests.test_decisao_inexistente_reprova_nos_dois_gates) ... ok
Proof: run unit | test_sem_piloto_md_reprova_sem_excecao (test_piloto.PilotDecisaoCitadaTests.test_sem_piloto_md_reprova_sem_excecao) ... ok
Proof: run unit | test_mandato_sem_user_nao_vale (test_piloto.PilotDecisaoCitadaTests.test_mandato_sem_user_nao_vale) ... ok
Proof: run unit | test_spec_recusa_piloto_com_decisao_registrada (test_piloto.PilotDecisaoCitadaTests.test_spec_recusa_piloto_com_decisao_registrada) ... ok

**C9** - Faixas de custo nos limites 0, 2 e 12, `:free` e sem preço (R9)
Proof: run unit | test_tier_by_output_price (test_model_info.ModelInfoTests.test_tier_by_output_price) ... ok

**C10** - Veto sem ferramentas e os quatro avisos por papel (R10)
Proof: run unit | test_fit_vetoes_and_warnings (test_model_info.ModelInfoTests.test_fit_vetoes_and_warnings) ... ok

**C11** - Cache de 7 dias, arquivo local por variável, exit 3 sem rede e sem cache, e os códigos 0 a 3 (R11)
Proof: run unit | test_cache_fresh_stale_and_no_fetch (test_model_info.ModelInfoTests.test_cache_fresh_stale_and_no_fetch) ... ok
Proof: run unit | test_cli_exit_codes (test_model_info.ModelInfoTests.test_cli_exit_codes) ... ok

**C12** - Família de modelo do OpenCode pelo cache, aceito como Q de outra família, `unknown` sem catálogo (R12)
Proof: run unit | test_opencode_provider_models_get_a_family (test_model_info.DispatchFamilyTests.test_opencode_provider_models_get_a_family) ... ok
Proof: run unit | test_q_cli_accepts_opencode_model_of_other_family (test_model_info.DispatchFamilyTests.test_q_cli_accepts_opencode_model_of_other_family) ... ok
Proof: run unit | test_without_catalog_stays_unknown (test_model_info.DispatchFamilyTests.test_without_catalog_stays_unknown) ... ok

**C13** - Precedência local > usuário > padrão, esquema local só `crew`, banner e tabela com a origem local (R13)
Proof: run unit | test_precedence_local_over_user_over_default (test_model_info.LocalConfigTests.test_precedence_local_over_user_over_default) ... ok
Proof: run unit | test_local_schema_only_crew (test_model_info.LocalConfigTests.test_local_schema_only_crew) ... ok
Proof: run unit | test_banner_and_crew_table_show_local (test_model_info.LocalConfigTests.test_banner_and_crew_table_show_local) ... ok

**C14** - Regras da skill `piloto-automatico` e a seção 2G da `troi` (R14)
Proof: run unit | test_piloto_skill_rules (test_piloto.PilotSkillTests.test_piloto_skill_rules) ... ok
Proof: run unit | test_troi_grill_mode (test_piloto.PilotSkillTests.test_troi_grill_mode) ... ok

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** provas, depois Q (D-j: sem T1 de código)
**Linear:** SC-186
**Integration branch:** feature/verificacao-1-8-0
**Last integrated:** none
**Dispatched:** none
**Settled:** 2026-11-16: spec + issue: "sim"
**Attempts:** none
**Reports:** 2026-11-16: provas verdes nos testes existentes (14 checks); 2026-11-16: Q: codex · effective unconfirmed · FAIL, 13 achados (3 de comportamento: status sem ⚠️ revisar, contexto 0 sem aviso, ativos lista piloto pendente; 10 de testes fracos em C1-C6, C8-C11, C13, C14); 936 OK; q-check 0
**Breaker:** closed
