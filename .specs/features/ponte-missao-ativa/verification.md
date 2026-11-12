# ponte-missao-ativa verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 61fec64
**HEAD**: 61fec64
**Verifier**: codex · requested padrão do CLI · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_ponte.py` `test_elsewhere_picks_newest_active_worktree` | yes |
| C2 | `tests/test_ponte.py` `test_elsewhere_null_when_local_active` | yes |
| C3 | `tests/test_ponte.py` `test_elsewhere_worktree_errors_do_not_break_snapshot` | yes |
| C4 | `tests/test_ponte.py` `test_elsewhere_snapshot_is_read_only` | no - a comparação de tamanho e mtime não detecta toda alteração nos arquivos |
| C5 | `src/orca/src/panel.test.tsx` `painel mostra a missão ativa de outro worktree` | yes |
| C6 | `src/orca/src/worker.test.ts` `barra de status indica missão em outro worktree` | yes |
| C7 | `src/orca/src/worker.test.ts` `atalho foca o worktree da missão ativa` | no - a chamada de notificação não está autorizada pelo manifesto |
| C8 | `tests/test_ponte.py` `test_decisions_records_p151_2_elsewhere` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R7 não entrega a notificação exigida quando não há workspace correspondente: `notifications:show` não consta nas capacidades, e a tentativa é capturada, de modo que o usuário só recebe o texto de erro na interface do painel. O teste passa porque o mock aceita `notifications.show`; isso não comprova a entrega na Orca. | `src/orca/src/worker.ts:542`; `src/orca/orca-plugin.json:55-61`; `src/orca/src/worker.test.ts:936-957` | Tornar a notificação possível sob as restrições da spec, ou alterar o critério aprovado e testar o comportamento suportado. | |
| C4 não demonstra ausência de escrita: `tree()` guarda somente mtime e tamanho; uma escrita que preserve ambos passa despercebida. | `tests/test_ponte.py:365-381` | Comparar conteúdo e metadados relevantes antes e depois, ou observar operações de escrita durante a execução. | |
| R1 escolhe lexicograficamente pelo slug quando Hand-offs têm mtime igual, embora o critério só determine o mais recente; não há check de empate que fixe esse resultado. | `scripts/ponte.py:297`; `tests/test_ponte.py:292-310` | Definir o desempate na spec ou evitar depender de ordem não especificada. | |

## Limits

Os testes e exemplos da prova foram aceitos como executados em HEAD conforme `proofs.md`; não repeti a suíte completa.
O comando de probing `ponte.same_path('C:/x/../y', 'c:/y')` retornou `False`; a spec exige equivalência de caixa e barras, não normalização de segmentos `..`.
Não validei a entrega real de `notifications.show` na Orca; manifesto e captura do erro indicam que a capacidade está ausente.