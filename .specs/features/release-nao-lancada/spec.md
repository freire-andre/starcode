# Release recusa seção não lançada: Spec

**Approved**: 2026-11-07 - user: "Sim para os dois"

**Size**: MEDIUM
**Risk triggers**: Irreversibilidade (tag e GitHub Release)
**Linear**: SC-81

## Context
Hoje o `tools/release.py` extrai as notas do release da seção `## [<VERSION>]` do `CHANGELOG.md` sem conferir a data. A Fase 7 deixou a seção `## [1.1.0] - não lançada`. Se o `VERSION` passar para `1.1.0` antes de datar essa seção, o script cria a tag e o Release com uma seção marcada como não lançada.

O script também confere só `docs/aceite/fase-6.md` (`ACEITE` fixo). O aceite da Fase 7 (`docs/aceite/fase-7.md`) não entra nas pré-condições.

Pendência da Fase 7 (SC-14, achado do T6). O usuário autorizou seguir em 2026-11-07 ("Com relação ao item 3 e 4 pode seguir").

## Scope
- `tools/release.py`:
  - recusar a seção da versão quando ela não tem data;
  - conferir todos os aceites a partir da Fase 6.
- Testes em `tests/test_release.py`.
- Decisão F7-10 em `DECISIONS.md`.

## Non-Goals
- Mudar o `VERSION`, datar o CHANGELOG, criar a tag v1.1.0 ou o Release. Isso fica para depois, com confirmação própria.
- Mudar o formato dos aceites das Fases 1–5, que usam outros textos em `**Resultado**`.
- Mudar a CI (`release-check`).

## Requirements
- **R1** - IF o cabeçalho `## [<VERSION>]` do `CHANGELOG.md` não tem uma data `AAAA-MM-DD` (por exemplo `## [1.1.0] - não lançada`) THEN `tools/release.py` SHALL sair com código 1 e a mensagem `CHANGELOG.md: a seção [<VERSION>] não tem data (não lançada); date a seção antes do release`, sem rodar `git tag`, `git push` nem `gh release`. Isso vale com e sem `--yes`.
- **R2** - WHEN a seção `## [<VERSION>] - <AAAA-MM-DD>` existe THEN the system SHALL extrair as notas como hoje (regressão do comportamento da 1.0.0).
- **R3** - The system SHALL conferir as pré-condições de aceite em todo `docs/aceite/fase-<N>.md` com N ≥ 6, em ordem numérica. IF algum deles tem um `**Resultado**:` diferente de `aprovado`, ou não tem nenhum `**Resultado**:`, THEN the system SHALL sair com código 1 e a mensagem `aceite não aprovado em docs/aceite/fase-<N>.md: <seção>`, citando o primeiro pendente.
- **R4** - The system SHALL registrar em `DECISIONS.md` a decisão F7-10 com R1 e R3: aceites a partir da Fase 6, porque as Fases 1–5 usam outro formato de resultado.

## Edge Cases
- **Seção com data em outro formato** (`2026/11/08`): é tratada como sem data (R1). O formato aceito é só `AAAA-MM-DD`, o mesmo da 1.0.0.
- **Sem nenhum `docs/aceite/fase-<N>.md` com N ≥ 6:** sai com 1 e a mensagem `aceite não aprovado em docs/aceite: nenhum aceite da Fase 6 em diante`.
- **`fase-10.md` existe:** a ordem é numérica (6, 7, …, 10), não alfabética.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Com `VERSION` 1.1.0 e `## [1.1.0] - não lançada`, o release sai com 1 e a mensagem de R1, sem chamar `git tag`, com e sem `--yes` (R1)
Proof: run unit | test_release_refuses_undated_changelog_section ... ok

**C2** - Com `## [1.1.0] - 2026-11-08`, as notas são extraídas e o fluxo segue até as pré-condições (R2)
Proof: run unit | test_release_notes_extracted_from_dated_section ... ok

**C3** - Com `fase-6.md` aprovado e `fase-7.md` pendente, o release sai com `aceite não aprovado em docs/aceite/fase-7.md: <seção>`; com `fase-10.md` pendente e `fase-7.md` aprovado, cita `fase-10.md` (R3)
Proof: run unit | test_release_checks_every_acceptance_from_phase_6 ... ok

**C4** - `DECISIONS.md` tem a decisão F7-10 (R4)
Proof: run unit | test_decisions_records_f7_10_release_guard ... ok

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** LaForge implementa SC-81
**Linear:** SC-81
**Integration branch:** not created
**Last integrated:** 697221c
**Dispatched:** Q-fix · cf8c324 · ctx_d8ac252dbebb · model claude-sonnet-5-5
**Settled:** 2026-11-07: spec aprovada e issue criada: "Sim para os dois"
**Attempts:** none
**Reports:** 2026-11-07: SC-81: R1–R4 em release.py/test_release.py/DECISIONS (F7-10), 376 testes rc 0; check_scope não se aplica (MÉDIA); commit 7e81d47; 2026-11-07: Q (antigravity gemini-3.8-flash-high): FAIL, 3 achados (mensagem sem aceites ≥6; data não estrita; testes C1/C3/C4 frouxos)
**Breaker:** closed
