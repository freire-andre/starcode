# fase-3-execucao verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 5d85ab1
**HEAD**: 62ad45b
**Verifier**: codex · requested padrão do CLI · effective unconfirmed (config.toml do Codex: gpt-6-luna)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_check_proofs.py` `test_check_proofs_writes_proofs_md` | no - não verifica execução de cada Run; Run sem Proof é ignorado (ver Finding 1) |
| C2 | `tests/test_check_proofs.py` `test_run_proof_needs_words_in_order_on_one_line` | yes |
| C3 | `tests/test_check_proofs.py` `test_dirty_tree_marks_mode1_and_fails` | yes |
| C4 | `tests/test_validate_verification.py` `test_verification_fails_on_missing_or_stale_proofs` | yes |
| C5 | `tests/test_validate_verification.py` `test_verification_fails_on_open_finding_or_missing_approval` | yes |
| C6 | `tests/test_validate_verification.py` `test_degraded_warns_and_strict_fails` | yes |
| C7 | `tests/test_check_scope.py` `test_check_scope_flags_outside_may_change` | no - testa glob `docs/*.md`, não padrão de pasta com `/` declarado no check |
| C8 | `tests/test_check_scope.py` `test_check_scope_flags_state_and_handoff` | yes |
| C9 | `tests/test_run_gates_exec.py` `test_run_gates_execution_stages` | yes |
| C10 | `tests/test_handoff.py` `test_handoff_execution_fields` | yes |
| C11 | `tests/test_handoff.py` `test_attempts_count_and_reset` | yes |
| C12 | `tests/test_handoff.py` `test_third_failure_opens_breaker` | yes |
| C13 | `tests/test_banner.py` `test_banner_shows_open_breaker` | yes |
| C14 | `tests/test_banner.py` `test_banner_shows_degraded_verification` | no - cobre `self-verified`, não o marcador `degraded` citado pelo check |
| C15 | `tests/test_q_skill.py` `test_q_brief_contract` | yes |
| C16 | `tests/test_q_skill.py` `test_q_skill_records_model_and_head` | yes |
| C17 | `tests/test_worker_skills.py` `test_laforge_skill_scope_tdd_commit` | yes |
| C18 | `tests/test_worker_skills.py` `test_laforge_calls_mccoy_on_second_failure` | yes |
| C19 | `tests/test_worker_skills.py` `test_mccoy_skill_regression_and_report` | yes |
| C20 | `tests/test_dispatch.py` `test_next_ticket_respects_dependencies` | yes |
| C21 | `tests/test_dispatch.py` `test_ticket_brief_has_block_and_worker_rules` | yes |
| C22 | `tests/test_dispatch.py` `test_q_brief_fills_placeholders` | yes |
| C23 | `tests/test_dispatch.py` `test_family_compare` | yes |
| C24 | `tests/test_skills_exec.py` `test_execute_ref_dispatch_steps` | yes |
| C25 | `tests/test_skills_exec.py` `test_execute_ref_integration_and_resume` | yes |
| C26 | `tests/test_skills_exec.py` `test_execute_ref_q_dispatch` | yes |
| C27 | `tests/test_skills_exec.py` `test_execute_ref_post_q_cycle` | yes |
| C28 | `tests/test_skills_exec.py` `test_execute_ref_linear_states` | yes |
| C29 | `tests/test_skills_exec.py` `test_execute_ref_mode1_and_no_stop` | yes |
| C30 | `tests/test_build.py` `test_build_emits_execution_skills` | yes |
| C31 | `tests/test_build.py` `test_routing_and_decisions_cover_phase3` | yes |
| C32 | `tests/test_acceptance_doc.py` `test_acceptance_doc_has_all_scripts` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C1/R1: `check_proofs.py` ignora uma linha `Run` sem `Proof` associado, contrariando a execução de cada Run. | `scripts/gates/check_proofs.py:108`; probe: Run declarado sem referência produziu `PROBE1 ok= True declared_run_output_present= False result= 1 pass, 0 fail` | Executar cada comando `Run` declarado uma vez e incluir sua saída no `proofs.md`, mesmo sem referência em Proof. | |
| C7/R6: a prova não testa o caso de padrão de pasta com `/` apesar de fazer parte do claim. | `tests/test_check_scope.py:39` cobre `docs/*.md`, sem padrão `app/` | Adicionar caso com `May change: app/` e arquivo `app/child.py`. | |
| C14/R30: a prova não testa o valor `degraded` do marcador; só testa `self-verified`. | `tests/test_banner.py:38` | Cobrir ambos os valores (`degraded` e `self-verified`) e confirmar a linha completa do banner. | |
| Assertions mais frouxas: C13 verifica substrings (`assertIn`) em vez da linha completa `Disjuntor aberto: <slug> (<id>)`; C14 também verifica só substrings; C32 aceita qualquer hash hexadecimal de 7 caracteres como evidência, sem verificar que é commit do roteiro. | `tests/test_banner.py:27,40`; `tests/test_acceptance_doc.py:26` | Comparar o valor completo do banner e validar a evidência citada contra o resultado do roteiro. | |

## Limits

O segundo probe (`May change: app/`, arquivo `app/child.py`) passou, sem defeito nesse valor de borda.

Não foi executado o fluxo Orca/Linear de ponta a ponta; os checks correspondentes verificam texto de instrução, não chamadas reais.
As provas documentadas são de 5d85ab1; o HEAD atual 62ad45b só acrescenta artefatos `.specs/`, permitido pela regra de validade de provas do gate.

