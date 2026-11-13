# Ajustes do review do PR #39 verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 30f6d31
**HEAD**: 55d47f2
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_coverage_rule.py` `test_covers_pasta_igualdade_e_glob` | yes |
| C2 | `tests/test_coverage_rule.py` `test_gates_usam_a_mesma_regra` | no - só intercepta chamadas feitas por `check_scope`; não falha se o gate das tasks deixar de usar `covers`. |
| C3 | `tests/test_coverage_rule.py` `test_citacao_coberta_por_glob` | yes |
| C4 | `tests/test_coverage_rule.py` `test_travessia_nao_coberta_por_glob` | yes |
| C5 | `tests/test_coverage_rule.py` `test_nome_sem_pasta_continua_coberto` | yes |
| C6 | `tests/test_dispatch_start.py` `test_start_segunda_gravacao_falha_sai_3` | yes |
| C7 | `tests/test_dispatch_start.py` `test_start_exit_3_avisa_e_liga_worktree` | yes |
| C8 | `tests/test_skills_exec.py` `test_execute_descreve_exit_3` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C2 não verifica o uso compartilhado por `validate_tasks`: o teste passa sem exercitar esse gate. | `tests/test_coverage_rule.py:22` | Com `gates_common.covers` mockado, avaliar uma citação no gate das tasks e afirmar a chamada/resultado, além de verificar `check_scope`. |  22e7907 |
| A asserção C8 aceita qualquer texto que contenha fragmentos do contrato; não fixa o comando completo nem o comportamento descrito. | `tests/test_skills_exec.py:18` | Verificar o texto completo do comando e as instruções de recuperação necessárias no contexto da seção 2. |  2b4d7e1 |

## Limits

`python -m unittest discover -s tests -v`: 767 testes executados, OK (1 skipped), 343.899s.
Probe: `python -c "import sys; sys.path.insert(0, 'scripts/gates'); import gates_common as g; print('R1 normalized parent:', g.covers('a/../b.py', 'b.py')); print('R1 directory boundary:', g.covers('scripts-extra/x.py', 'scripts/')); print('R3 empty path:', g.covers('', '*')); print('R3 root path:', g.covers('/', '*'))"` imprimiu `R1 normalized parent: True`, `R1 directory boundary: False`, `R3 empty path: True`, `R3 root path: False`; os casos extras não revelaram falha nos requisitos verificados.
Regra sem check dedicado: recibo sem dispatch id deve mostrar `-` na linha de aviso de exit 3; `start` usa `rec['dispatch'] or '-'`, mas nenhum check cobre esse caso.
