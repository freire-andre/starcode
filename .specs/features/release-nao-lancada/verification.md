# release-nao-lancada verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 697221c
**HEAD**: c413777
**Verifier**: antigravity · requested gemini-3.8-flash-high · effective gemini-3.8-flash-high

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_release.py` `test_release_refuses_undated_changelog_section` | yes |
| C2 | `tests/test_release.py` `test_release_notes_extracted_from_dated_section` | yes |
| C3 | `tests/test_release.py` `test_release_checks_every_acceptance_from_phase_6` | yes |
| C4 | `tests/test_release.py` `test_decisions_records_f7_10_release_guard` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Quando não há nenhum arquivo de aceite com fase N ≥ 6 em `docs/aceite/` (diretório vazio ou contendo apenas aceites das Fases 1 a 5), `tools/release.py` sai com `aceite não aprovado em docs/aceite/fase-6.md: arquivo ausente`, divergindo da mensagem exigida pelo caso de borda da spec: `aceite não aprovado em docs/aceite: nenhum aceite da Fase 6 em diante`. | `tools/release.py:76`; confirmado em execução isolada sem aceites da fase 6 em diante, onde `python tools/release.py create` retornou código 1 e a mensagem `aceite não aprovado em docs/aceite/fase-6.md: arquivo ausente` contra `spec.md:36`. | Em `tools/release.py:76`, emitir `aceite não aprovado em docs/aceite: nenhum aceite da Fase 6 em diante` e cobrir com teste unitário em `tests/test_release.py`. | b29e340 |
| `_undated` aceita como datada qualquer seção cujo cabeçalho contenha `\d{4}-\d{2}-\d{2}` em qualquer ponto da linha, em vez de exigir o formato estrito fixado por R2 (`## [<VERSION>] - <AAAA-MM-DD>`). Cabeçalhos como `## [1.1.0] - não lançada (2026-11-08)` ou `## [1.1.0] - adiada para 2026-12-01` são tratados como datados e avançam para o release. | `tools/release.py:70`; confirmado em teste onde `CHANGELOG.md` com `## [1.1.0] - não lançada (2026-11-08)` passou por `_undated` e seguiu para pré-condições sem recusar com a mensagem de R1. | Em `tools/release.py:70`, validar que o sufixo da linha de versão segue estritamente o formato ` - \d{4}-\d{2}-\d{2}$` (ex.: `not re.fullmatch(r" - \d{4}-\d{2}-\d{2}", m.group(1).rstrip())`). | 42cebfc |
| Asserções da suíte mais fracas que os critérios: C4 (`test_decisions_records_f7_10_release_guard`) verifica apenas `"### F7-10:"` e `"Fase 6"` sem checar os requisitos R1 e R3 ou o motivo de compatibilidade com Fases 1–5; C3 (`test_release_checks_every_acceptance_from_phase_6`) testa `fase-10.md` com `fase-7.md` já aprovado, sem provar a ordenação numérica contra alfabética caso ambos estivessem pendentes; C1 (`test_release_refuses_undated_changelog_section`) não cobre o caso de borda de data em outro formato (`2026/11/08`) nem cabeçalho nu (`## [1.1.0]`). | `tests/test_release.py:177-219` (`test_release_refuses_undated_changelog_section`, `test_release_checks_every_acceptance_from_phase_6`, `test_decisions_records_f7_10_release_guard`). | Endurecer as asserções em `tests/test_release.py` para cobrir o caso de borda de formato de data e cabeçalho sem sufixo em C1, ordenação com múltiplos pendentes simultâneos em C3, e a presença de R1/R3/motivo em C4. | b3504d8 |

## Limits

- Execução real dos comandos remotos de mutating (`git tag`, `git push`, `gh release create`) contra o repositório remoto do GitHub, que são simulados via `runner` fake nos testes unitários para não alterar o repositório real.
