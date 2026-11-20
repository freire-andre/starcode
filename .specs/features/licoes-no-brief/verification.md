# licoes-no-brief verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 8abe449
**HEAD**: ab310f9
**Verifier**: codex · requested cli-default · effective GPT-6.1 Terra medium (terminal)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_licoes_no_brief.py` `test_ordem_por_recorrencia` | yes |
| C2 | `tests/test_licoes_no_brief.py` `test_licoes_antes_das_regras` | yes |
| C3 | `tests/test_licoes_no_brief.py` `test_fix_brief` | no - não associa todos os campos a cada achado nem prova a união dos tickets. |
| C4 | `tests/test_licoes_no_brief.py` `test_execute_e_decisions` | no - a seção Decisão pode omitir requisitos da correção e ainda passar. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| O brief gerado ignora os `differs` de telas, embora devam acompanhar os achados do Q; se só houver divergências de tela, o gerador recusa o brief por não haver achados abertos. | `scripts/dispatch.py:984` e `scripts/dispatch.py:990`; `skills/engajar/references/execute.md:174` e `skills/engajar/references/execute.md:179` | Incluir as divergências de tela no brief único e tratar o caso em que só existem divergências de tela; cobrir ambos os cenários. | |
| C3 usa fragmentos soltos para os campos de dois achados: pode associar Finding, Evidence ou Fix ao achado errado, omitir campos, título ou alterar regras e ainda passar. Também não cita o teste separado da união de May change dos tickets. | `tests/test_licoes_no_brief.py:95` e `tests/test_licoes_no_brief.py:111`; `tests/test_licoes_no_brief.py:122`; `.specs/features/licoes-no-brief/spec.md:52` | Comparar o brief integral esperado, incluindo cada campo em sua seção e todas as regras, e citar também o teste de união dos tickets. | |
| C4 não exige na seção Decisão os termos de todos os requisitos: podem desaparecer a proibição de escrever em `.specs/`, os gates e o relatório de cada achado. | `tests/test_licoes_no_brief.py:137` | Exigir na seção Decisão os termos de cada requisito, inclusive todas as regras fixas e saídas do brief. | |

## Limits

Regressão em HEAD: `python -m unittest discover -s tests -v` passou, com 1.039 testes e 1 ignorado (`test_restore_yes_devolve_bit_executavel`: bit executável não existe no Windows).
