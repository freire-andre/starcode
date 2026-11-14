# Snapshot e restauração seguros verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at `a2d9d3e`
**HEAD**: 5ddf9a4
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_snapshot.py` `test_take_mantem_snapshot_existente` | yes |
| C2 | `tests/test_snapshot_restore.py` `test_restore_dry_run_grava_plano` | yes |
| C3 | `tests/test_snapshot_restore.py` `test_restore_recusa_snapshot_ausente_fora_do_ticket` | yes |
| C4 | `tests/test_snapshot_restore.py` `test_restore_edicao_fora_do_ticket_nao_recusa` | yes |
| C5 | `tests/test_snapshot_restore.py` `test_restore_yes_sem_plano_recusa` | yes |
| C6 | `tests/test_snapshot_restore.py` `test_restore_yes_plano_mudou_recusa` | yes |
| C7 | `tests/test_snapshot_restore.py` `test_restore_grava_pre_restore_e_apaga_plano` | yes |
| C8 | `tests/test_snapshot_restore.py` `test_restore_pre_restore_falha_nao_toca_arquivos` | yes |
| C9 | `tests/test_snapshot_restore.py` `test_restore_falha_parcial_e_retomada` | yes |
| C10 | `tests/test_snapshot_restore.py` `test_cenario_aceite_disjuntor_modo_1` | yes |
| C11 | `tests/test_snapshot_restore.py` `test_drop_remove_pre_restore_e_planos_da_feature` | yes |
| C12 | `tests/test_snapshot_restore.py` `test_decisions_snapshot_restauracao_segura` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| `drop feat` deixa para trás um plano da feature quando o JSON está inválido; `drop` termina com sucesso. | Comando: `python "$env:TEMP\q_snapshot_r11.py"`<br>Saída literal:<br>`removidos 0 snapshots de feat`<br>`EXIT=0; PLAN_EXISTS=True` | Remova o arquivo de plano correspondente mesmo quando seu conteúdo não puder ser lido, sem apagar planos de slugs vizinhos. | |
| O tratamento de erro ignora falha ao apagar o plano após restauração; o comando pode anunciar sucesso e deixar um plano iniciado gravado, contrariando R10. | `scripts/snapshot.py:378` | Não ignore a falha de limpeza; informe que a restauração terminou, mas a remoção do plano falhou, e mantenha um estado retomável ou permita nova limpeza. | |
| A asserção de C4 aceita qualquer saída que contenha o fragmento `  notas.md`, inclusive um caminho maior ou texto adicional; não fixa a linha do caminho como critério. | `tests/test_snapshot_restore.py:288` | Compare a linha completa ou valide a lista de caminhos parseada. | |

## Limits

- A regressão completa em HEAD passou: `python -m unittest discover -s tests -v` — 872 testes, 0 falhas, 1 ignorado; saída final `OK (skipped=1)`.
- C8 simula a falha por mock em `_write_pre_restore`; não provoca uma falha real do `git update-ref`.
