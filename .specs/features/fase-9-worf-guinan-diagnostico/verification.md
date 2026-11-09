# fase-9-worf-guinan-diagnostico verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 153071a
**HEAD**: 74b376f
**Verifier**: codex · requested padrão do CLI · effective GPT-6-Luna medium

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_review_scan.py` `test_scan_reports_each_category_with_new_line_number` | yes |
| C2 | `tests/test_review_scan.py` `test_scan_ignores_removed_context_and_always_exits_zero` | yes |
| C3 | `tests/test_review_gate.py` `test_gate_rejects_severity_nits_and_missing_evidence` | yes |
| C4 | `tests/test_review_gate.py` `test_gate_requires_tldr_with_verdict` | yes |
| C5 | `tests/test_review_gate.py` `test_compute_verdict_mapping` | yes |
| C6 | `tests/test_review_gate.py` `test_gate_rejects_banned_terms_accent_insensitive` | yes |
| C7 | `tests/test_review_gate.py` `test_gate_round_convergence_rules` | yes |
| C8 | `tests/test_review_gate.py` `test_gate_security_fields_required` | no - valores não textuais vazios passam como evidência/campos de segurança presentes |
| C9 | `tests/test_review_gate.py` `test_gate_security_states_and_hardening` | yes |
| C10 | `tests/test_review_post.py` `test_post_refuses_without_gate_or_when_already_posted` | yes |
| C11 | `tests/test_review_post.py` `test_post_own_pr_falls_back_to_comment` | yes |
| C12 | `tests/test_review_post.py` `test_post_gh_failure_and_success_marks_posted` | yes |
| C13 | `tests/test_worf_skill.py` `test_worf_skill_review_flow_order` | yes |
| C14 | `tests/test_worf_skill.py` `test_worf_skill_evidence_or_silence` | yes |
| C15 | `tests/test_worf_skill.py` `test_worf_skill_review_md_contract` | yes |
| C16 | `tests/test_worf_skill.py` `test_worf_review_standards_bypass_rule` | yes |
| C17 | `tests/test_worf_skill.py` `test_worf_skill_never_merges` | yes |
| C18 | `tests/test_lessons.py` `test_lessons_add_rejects_invalid_input` | yes |
| C19 | `tests/test_lessons.py` `test_lessons_dedupe_and_promote_on_two_features` | yes |
| C20 | `tests/test_lessons.py` `test_lessons_penalize_render_and_corrupt_store` | yes |
| C21 | `tests/test_guinan_skill.py` `test_guinan_skill_signals_and_no_finding_no_lesson` | yes |
| C22 | `tests/test_guinan_skill.py` `test_guinan_skill_retro_contract` | yes |
| C23 | `tests/test_dispatch_lessons.py` `test_briefs_include_up_to_ten_confirmed_lessons` | yes |
| C24 | `tests/test_dispatch_lessons.py` `test_briefs_unchanged_without_confirmed_lessons` | yes |
| C25 | `tests/test_diagnostico.py` `test_diagnostico_runs_harness_score_and_track_a` | yes |
| C26 | `tests/test_diagnostico.py` `test_diagnostico_report_contract` | yes |
| C27 | `tests/test_diagnostico.py` `test_diagnostico_failures` | yes |
| C28 | `tests/test_diagnostico.py` `test_diagnostico_gitignore_warning` | yes |
| C29 | `tests/test_diagnostico_skill.py` `test_diagnostico_skill_cost_approval` | yes |
| C30 | `tests/test_diagnostico_skill.py` `test_diagnostico_judge_protocol` | yes |
| C31 | `tests/test_diagnostico_skill.py` `test_crew_declares_diagnostico_skill` | yes |
| C32 | `tests/test_diagnostico_skill.py` `test_crew_worf_guinan_invocation_both` | yes |
| C33 | `tests/test_flow_worf_guinan.py` `test_execute_review_worf_after_pr` | yes |
| C34 | `tests/test_flow_worf_guinan.py` `test_execute_guinan_after_done` | yes |
| C35 | `tests/test_build.py` `test_build_fase9_skills_and_scripts_in_all_clis` | yes |
| C36 | `tests/test_evals_f9.py` `test_evals_f9_routing_cases` | yes |
| C37 | `tests/test_credits_f9.py` `test_credits_f9_sources_and_headers` | yes |
| C38 | `tests/test_release_docs_f9.py` `test_release_docs_f9` | yes |
| C39 | `tests/test_acceptance_doc_f9.py` `test_fase9_acceptance_sections` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R8 aceita campos de segurança não textuais e vazios; um achado com `attacker: []` passa pelo gate. | `scripts/review/review_gate.py:72` (`blank` só considera `None` e string vazia); sondagem: `review_gate.check({... attacker: [], ...})` imprimiu `[]` (nenhuma violação). | Exigir string não vazia para cada campo textual de segurança e testar `[]`, `{}` e whitespace. | |
| Asserção mais fraca que o critério: C11 testa apenas `assertIn` para a linha de fallback do comentário, sem verificar o texto completo e o veredito exato exigidos por R15. C39 aceita qualquer nível `L0`–`L4` e qualquer fração numérica, sem comparar com o nível/score citados no aceite. | `tests/test_review_post.py:test_post_own_pr_falls_back_to_comment`; `tests/test_acceptance_doc_f9.py:test_fase9_acceptance_sections` | Comparar a linha completa do comentário com valor esperado; validar o nível e score do aceite contra a saída produzida. | |

## Limits

- A prova de testes declara execução em 153071a; analisei o código em 74b376f, cujo commit posterior adiciona provas, sem rerodar a suíte.
- Testei entradas extras: `attacker: []` foi aceito pelo gate; linha adicionada com 500 caracteres e `# noqa` foi limitada a 160 caracteres e detectada (`exit 0`, `scan: 1 candidate(s)`).
- Não verifiquei chamadas reais a `gh`, `npx` ou juízes externos; os testes usam doubles e B/C exigem execução com custo.
