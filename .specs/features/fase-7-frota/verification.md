# fase-7-frota verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 972c59c
**HEAD**: d2b715f
**Verifier**: antigravity · requested gemini-3.8-flash-high · effective gemini-3.8-flash-high (terminal: "Gemini 3.8 Flash · high")

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_dispatch.py` `test_batch_skips_integrated_active_and_waiting_tickets` | yes |
| C2 | `tests/test_dispatch.py` `test_batch_excludes_ticket_sharing_path_with_active` | yes |
| C3 | `tests/test_dispatch.py` `test_batch_sensitive_ticket_runs_alone_only_when_idle` | no - mascara o caso real: se o ticket com lockfile tiver `**Runs alone**: yes` (obrigatório pelo `validate_tasks`), `_sensitive_reason` devolve `Runs alone` em vez do padrão sensível |
| C4 | `tests/test_dispatch.py` `test_batch_limit_counts_active_workers` | yes |
| C5 | `tests/test_dispatch.py` `test_batch_json_contract` | yes |
| C6 | `tests/test_dispatch.py` `test_batch_exit_codes` | yes |
| C7 | `tests/test_dispatch.py` `test_batch_excludes_ticket_without_may_change` | yes |
| C8 | `tests/test_validate_config.py` `test_fleet_workers_accepts_valid_pairs_and_rejects_invalid` | yes |
| C9 | `tests/test_dispatch.py` `test_batch_round_robin_from_fleet_workers` | yes |
| C10 | `tests/test_dispatch.py` `test_batch_assign_overrides_pair` | yes |
| C11 | `tests/test_build.py` `test_cost_tier_from_map_free_suffix_and_unknown` | yes |
| C12 | `tests/test_dispatch.py` `test_batch_cost_total_counts_tiers` | yes |
| C13 | `tests/test_skills_exec.py` `test_execute_fleet_batch_confirmation` | yes |
| C14 | `tests/test_handoff.py` `test_dispatch_add_appends_and_replaces_same_ticket` | yes |
| C15 | `tests/test_handoff.py` `test_dispatch_remove_keeps_other_entries` | yes |
| C16 | `tests/test_skills_exec.py` `test_execute_fleet_worker_start_flags` | no - asserção mais frouxa que o critério: não verifica se o primeiro `--dispatch-add` inclui os 5 campos (par e horário) de R14 |
| C17 | `tests/test_skills_exec.py` `test_execute_fleet_start_failure_isolated` | yes |
| C18 | `tests/test_crew_live.py` `test_set_laforge_count_up_to_ten` | yes |
| C19 | `tests/test_dispatch.py` `test_next_open_dispatch_with_multiple_entries` | yes |
| C20 | `tests/test_skills_exec.py` `test_execute_fleet_wait_uses_nearest_deadline` | yes |
| C21 | `tests/test_skills_exec.py` `test_execute_fleet_integrates_on_arrival` | no - asserção mais frouxa que o critério: testa apenas a substring `run_gates.py ticket` sem validar o range `<base sha>..<ticket branch>` nem a base do despacho |
| C22 | `tests/test_dispatch.py` `test_overdue_lists_tickets_past_deadline` | yes |
| C23 | `tests/test_skills_exec.py` `test_execute_fleet_timeout_blocks_without_relaunch` | yes |
| C24 | `tests/test_skills_exec.py` `test_execute_fleet_cancel_preserves_worktree` | yes |
| C25 | `tests/test_skills_exec.py` `test_execute_fleet_failure_returns_ticket_to_queue` | yes |
| C26 | `tests/test_skills_exec.py` `test_execute_fleet_merge_conflict_continues` | yes |
| C27 | `tests/test_skills_exec.py` `test_execute_fleet_next_batch_then_proofs` | yes |
| C28 | `tests/test_skills_exec.py` `test_execute_fleet_unavailable_in_mode_1` | yes |
| C29 | `tests/test_dispatch.py` `test_q_cli_differs_from_all_laforge_families` | yes |
| C30 | `tests/test_acceptance_doc_f7.py` `test_fase7_acceptance_all_scenarios_approved` | yes |
| C31 | `tests/test_release_docs.py` `test_decisions_and_changelog_record_fase_7` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| `_sensitive_reason` prioriza `task.runs_alone` antes de `gc.is_sensitive`: tickets com arquivos sensíveis (que obrigatoriamente têm `**Runs alone**: yes` por `validate_tasks`) saem com `roda sozinho: Runs alone` em vez do padrão sensível exigido por R3 e R5. | `scripts/dispatch.py:165` (`if task.runs_alone: return "Runs alone"`); confirmado em execução em `docs/aceite/fase-7.md:36,67`. | Em `_sensitive_reason`, avaliar primeiro `gc.is_sensitive` nos caminhos de `task.may_change`; se houver padrão sensível, devolver o padrão; se não houver padrão e `task.runs_alone` for verdadeiro, devolver `"Runs alone"`. | |
| `execute.md:72` (seção 2F, passo 2.1) instrui o Picard a registrar `--dispatch-add` com apenas 3 campos antes do `worker-start`, omitindo o modelo e o horário UTC exigidos por R14, o que causa crash com erro 2 em `dispatch.py overdue`. | `skills/engajar/references/execute.md:72` (`--dispatch-add "<T> · <ID> · base <sha of I>"`) versus `spec.md:83` (R14) e `tests/test_dispatch.py:160` (`test_overdue_unreadable_time_exits_2`). | Em `skills/engajar/references/execute.md:72`, alinhar o comando com R14: `python "P/scripts/handoff.py" set <slug> --dispatch-add "<T> · <ID> · base <sha of I> · <cli:model> · <UTC time>"`. | |
| `execute.md:88` (seção 2F, passo 5) não explicita a invocação completa de `run_gates.py ticket` com o intervalo `<base sha>..<ticket branch>`, nem que `<base sha>` deve ser o hash registrado no despacho daquele ticket (e não o HEAD atual de `I`, que se move a cada merge concluído). | `skills/engajar/references/execute.md:88` (`A worker_done with success: run_gates.py ticket and, if green...`). | Em `skills/engajar/references/execute.md:88`, explicitar: `run_gates.py ticket <slug> <T> <base sha gravado no despacho do ticket>..<ticket branch>`. | |
| `dispatch.py overdue` não filtra entradas que já possuem o sufixo `· blocked`, continuando a listá-las como atrasadas a cada checagem e gerando reavisos e comentários repetidos no Linear a cada ciclo de espera. | `scripts/dispatch.py:280-293` (filtra apenas `tid in done`, sem checar `blocked`); verificado em execução onde entrada com `· blocked` retorna código 0 com a mesma linha de atraso. | Em `scripts/dispatch.py:280`, ignorar entradas cujo texto contenha `blocked` ou cujo último campo seja `blocked`. | |

## Limits

- Testes reais de concorrência com múltiplos CLIs simultâneos da Orca dependem de infraestrutura externa e credenciais com cota (como a cota do OpenCode observada no aceite real).
- A sincronização entre processos e concorrência na escrita em worktrees irmãos durante a Frota foi avaliada no aceite em T8, mas não é reprodutível isoladamente na verificação estática.
