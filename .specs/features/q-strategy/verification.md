# q-strategy verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 169e619
**HEAD**: e6174aa
**Verifier**: codex · requested cli-default · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_dispatch.py` `test_q_strategy_none_keeps_current_order` | yes |
| C2 | `tests/test_dispatch.py` `test_q_strategy_orca_worker_walks_cli_order` | yes |
| C3 | `tests/test_dispatch.py` `test_q_strategy_self_verified_first_wins` | yes |
| C4 | `tests/test_dispatch.py` `test_q_strategy_opencode_subagent_skipped_with_warning` | no - a saída do comando é normalizada com `strip()`, aceitando espaços ou linhas extras. |
| C5 | `tests/test_dispatch.py` `test_q_strategy_nothing_available_is_self_verified` | no - falta verificar a saída e o código do comando quando nenhum worker está disponível. |
| C6 | `tests/test_dispatch.py` `test_q_cli_command_reads_user_qstrategy` | yes |
| C7 | `tests/test_dispatch.py` `test_q_strategy_docs_match_implementation` | yes |
| C8 | `scripts/check_decisions.py` `check` | no - verifica a data relativa dos commits, mas não o conteúdo exigido por R8. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C4 aceita espaços e linhas extras no stderr apesar do aviso exato exigido. | `tests/test_dispatch.py:408` | Comparar stderr integral com o aviso e sua quebra de linha esperada. | |
| C5 não prova que o comando imprime `self-verified` e sai com 1 quando `orca-worker` não encontra CLI de outra família. | `tests/test_dispatch.py:413` | Invocar o comando nesse cenário e conferir saída e código exatos. | |
| A prova de C8 passa sem entrada SC-185, seus quatro campos, referências aos testes ou linha no changelog; o teste adicional de decisão também procura fragmentos sem verificar cada requisito na seção Decisão nem o changelog. | `scripts/check_decisions.py:55`, `tests/test_dispatch.py:455` | Testar a entrada SC-185 por seção e requisitos, as referências aos testes e a linha sob Unreleased. | |
| A parada ao obter um worker antes de `opencode-subagent` não tem teste que garanta ausência de aviso; uma avaliação antecipada poderia avisar silenciosamente fora da ordem. | `scripts/dispatch.py:654`, `tests/test_dispatch.py:397` | Testar `['orca-worker', 'opencode-subagent']` com worker disponível e conferir resultado e stderr vazio. | |

## Limits

Regressão completa em HEAD: `python -m unittest discover -s tests -v`, 935 testes em 456,901 s, OK, 1 ignorado.
Sondas independentes: R2 com Q configurado devolveu `codex`; R4 com `opencode-subagent`, `self-verified`, `orca-worker` devolveu `None` e um aviso.
