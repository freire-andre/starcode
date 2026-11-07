# brief-media-escopo verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at `27bdfd7`
**HEAD**: 0f8c0d9
**Verifier**: codex (padrão do CLI) · LaForge claude-sonnet-5-5

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_brief_media_escopo.py` `test_validate_spec_warns_medium_without_may_change` | yes |
| C2 | `tests/test_brief_media_escopo.py` `test_check_scope_medium_uses_spec_may_change` | yes |
| C3 | `tests/test_brief_media_escopo.py` `test_check_scope_medium_without_may_change_warns` | no - testa o aviso e erros de STATE/Handoff, mas não verifica que o intervalo vazio continua gerando erro |
| C4 | `tests/test_brief_media_escopo.py` `test_check_scope_medium_ticket_id` | yes |
| C5 | `tests/test_brief_media_escopo.py` `test_run_gates_ticket_medium_checks_commits` | yes |
| C6 | `tests/test_brief_media_escopo.py` `test_spec_brief_includes_boundaries` | yes |
| C7 | `tests/test_brief_media_escopo.py` `test_execute_medium_runs_ticket_gate` | yes |
| C8 | `tests/test_brief_media_escopo.py` `test_decisions_records_f7_11_medium_scope` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C3 não cobre a preservação do erro para intervalo sem commit exigida por R3. | `tests/test_brief_media_escopo.py:70-81` só avalia intervalos com commits; a verificação adicional de `check_scope` não cobre intervalo vazio. | Adicionar caso MEDIUM sem May change com intervalo sem commits e afirmar o erro de intervalo vazio. | |
| C5 não verifica o caso de vários commits, embora R5 exija `check_commit` em cada commit. | `tests/test_brief_media_escopo.py:92-100` usa um commit em cada intervalo; nenhum caso inclui dois commits com um deles sem `Refs`. | Testar intervalo de dois commits e confirmar rejeição quando qualquer commit não contém o ID esperado. | |

## Limits

Não executei a suíte completa; os proofs registram 385 testes aprovados no HEAD 27bdfd7, anterior ao HEAD analisado 0f8c0d9.
Não reproduzi os oito checks via execução individual; inspecionei seus testes e o diff do range.
Exemplos adicionais de R2: `check_scope.allowed('docs2/x.md', ['docs/']) -> False`; `check_scope.allowed('docs/x.md', ['docs/']) -> True`; `check_scope.allowed('a.py', ['a.py', 'a.py']) -> True`; `check_scope.allowed('a.py', ['*.py']) -> True`.
