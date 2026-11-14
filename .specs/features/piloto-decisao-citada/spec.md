# Aprovação do piloto confere a decisão citada: Spec

**Approved**: 2026-11-14 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: Autenticação e autorização (gate de aprovação das tasks)
**Status**: Approved
**Linear**: SC-170
**May change**: scripts/piloto.py, scripts/gates/gates_common.py, scripts/gates/validate_tasks.py, scripts/gates/validate_verification.py, DECISIONS.md, tests/test_piloto.py, dist/

## Context
Item 0.4 de `starcode-triagem-v2-2026-11-13.md` (fora do Git). O gate aceita `**Approved**: <data> - piloto: "D<n> ..."` no `tasks.md` só pelo formato `D<n>` (`scripts/gates/gates_common.py:183-184`), então uma aprovação pode citar uma decisão que nunca foi registrada; o teste atual aprova `piloto: "D4 ..."` sem decisão no `piloto.md`. E o `piloto.md` tem dois leitores com regras diferentes: o gate exige `**Mandato confirmado:** <data> - user:`, o `piloto.py` aceita só a data. Sucesso: a aprovação do piloto só vale com a decisão citada registrada, e o `piloto.md` passa a ter um leitor só.

## Scope
- `scripts/piloto.py` passa a ser o único leitor do `piloto.md` (status, mandato confirmado, decisões registradas).
- Os gates de tasks e de verificação conferem que a decisão citada existe.
- Mensagem própria quando a aprovação cita decisão não registrada.

## Non-Goals
- Aprovação depois do `encerrar` (item 0.5, decisão D-g): continua exigindo `**Status:** ativo`.
- Freio na 3ª decisão `⚠️ revisar` e decisões de arquitetura não delegáveis (itens 0.6 e 0.7, decisão D-h).
- Mudar o formato que o `piloto.py` grava.

## Requirements
- **R1** - The system SHALL ler o `piloto.md` só por funções de `scripts/piloto.py` (piloto ativo, mandato confirmado pelo usuário e IDs das decisões registradas); `scripts/gates/gates_common.py` SHALL NOT ter regex de `Mandato confirmado`, de `**Status:**` nem de `### D`.
- **R2** - WHEN o `tasks.md` tem `**Approved**: <data> - piloto: "D7 ..."`, o piloto está ativo, o mandato foi confirmado pelo usuário e o `piloto.md` tem `### D7 · ` THEN o gate de tasks (`validate_tasks.py`) e o gate de verificação (`validate_verification.py`) SHALL aceitar a aprovação do `tasks.md`.
- **R3** - IF a aprovação `piloto:` cita `D<n>` e o `piloto.md` não tem `### D<n> · ` THEN cada um dos dois gates SHALL reprovar com o erro `tasks.md: a aprovação do piloto cita D<n>, que não está registrada no piloto.md`.
- **R4** - The system SHALL continuar recusando a aprovação `piloto:` no `spec.md`, mesmo com a decisão registrada.
- **R5** - IF o `piloto.md` tem `**Mandato confirmado:** <data>` sem `- user:` THEN `piloto.py ativo <slug>` SHALL sair com 1 e os gates SHALL recusar a aprovação `piloto:`.
- **R6** - IF o `tasks.md` tem a aprovação `piloto:` e o `piloto.md` não existe THEN os dois gates SHALL recusar a aprovação, sem exceção, com a mensagem de hoje (`tasks.md sem `**Approved**: ...``).
- **R7** - WHEN a aprovação cita `D07` e o `piloto.md` tem `### D7 · ` THEN os gates SHALL aceitar, porque a comparação é pelo número da decisão.
- **R8** - WHEN o `tasks.md` tem duas linhas `piloto:`, uma citando decisão inexistente e outra citando decisão registrada THEN os gates SHALL aceitar a aprovação.
- **R9** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-170` descrevendo R1 a R8, com **Problema**, **Decisão**, **Motivo** e **Por que não é bug** citando os testes.

## Edge Cases
- Decisão citada marcada `⚠️ revisar`: aceita (item 0.6 cuida do freio) - coberto por C2, que usa uma decisão sem `--basis`.
- `piloto.md` ausente: R6 (C6).
- `D07` × `D7`: R7 (C7).
- Duas linhas `piloto:`: R8 (C8).
- Mandato sem `- user:`: R5 (C5).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `gates_common.py` não contém `Mandato confirmado`, `\*\*Status:` nem `### D`, e `approved()` usa as funções do `piloto.py` (R1)
Proof: run unit | test_gates_leem_piloto_pelo_piloto_py ... ok

**C2** - Com piloto ativo, mandato confirmado e `### D7 · ` registrada por `piloto.py registrar` sem `--basis` (marcada `⚠️ revisar`), `piloto: "D7 tasks cobrem a spec"` no `tasks.md` passa em `validate_tasks` e em `validate_verification`, sem erro sobre o `tasks.md` (R2)
Proof: run unit | test_aprovacao_com_decisao_registrada_passa_nos_dois_gates ... ok

**C3** - Com `piloto: "D4 ..."` e só a `D1` registrada, `validate_tasks` e `validate_verification` trazem, cada um, o erro exato `tasks.md: a aprovação do piloto cita D4, que não está registrada no piloto.md` (R3)
Proof: run unit | test_decisao_inexistente_reprova_nos_dois_gates ... ok

**C4** - Com a decisão registrada, a linha `piloto:` no `spec.md` continua reprovando com o erro de `spec.md sem` (R4)
Proof: run unit | test_spec_recusa_piloto_com_decisao_registrada ... ok

**C5** - Com `**Mandato confirmado:** 2026-11-14` sem `- user:`, `piloto.py ativo` sai com 1 e `approved()` devolve falso para a linha `piloto:` (R5)
Proof: run unit | test_mandato_sem_user_nao_vale ... ok

**C6** - Sem `piloto.md`, os dois gates reprovam o `tasks.md` com a mensagem de `tasks.md sem` e sem exceção (R6)
Proof: run unit | test_sem_piloto_md_reprova_sem_excecao ... ok

**C7** - `piloto: "D07 ..."` com `### D7 · ` registrada é aceita (R7)
Proof: run unit | test_d07_cita_d7 ... ok

**C8** - Duas linhas `piloto:` no `tasks.md`, `D9` (inexistente) e `D1` (registrada), são aceitas (R8)
Proof: run unit | test_uma_linha_valida_basta ... ok

**C9** - `DECISIONS.md` tem a entrada da issue com o texto exato da mensagem de R3, `- user:`, `D07` e `Por que não é bug` citando os testes de C1 a C8 (R9)
Proof: run unit | test_decisions_piloto_decisao_citada ... ok

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** Gates proofs e done
**Linear:** SC-170
**Integration branch:** feature/piloto-decisao-citada
**Last integrated:** 5b87da5d7f70d9cb7c8cea28542fe52137c29d72
**Dispatched:** LaForge pós-Q · 3d2cee7
**Settled:** none
**Attempts:** none
**Reports:** 2026-11-14: T1: piloto.py único leitor (active_confirmed_in, registered_decisions_in), gates conferem a decisão citada, 8 testes, SC-170; suíte 844 ok; 2026-11-14: Q (codex · effective gpt-6-luna): FAIL, 3 achados (ID longo dá ValueError; C3 assertIn em lista; C6 startswith); suíte 844 ok; 2026-11-14: LaForge pós-Q: achado 1 em db632d9, testes dos 3 em 5120f73; 23 testes ok
**Breaker:** closed
