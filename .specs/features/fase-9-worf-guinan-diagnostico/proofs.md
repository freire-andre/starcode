# fase-9-worf-guinan-diagnostico proofs

**HEAD**: 8ad073e
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 42 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_scan_reports_each_category_with_new_line_number ... ok` | pass |
| C2 | `run unit / test_scan_ignores_removed_context_and_always_exits_zero ... ok` | pass |
| C3 | `run unit / test_gate_rejects_severity_nits_and_missing_evidence ... ok` | pass |
| C4 | `run unit / test_gate_requires_tldr_with_verdict ... ok` | pass |
| C5 | `run unit / test_compute_verdict_mapping ... ok` | pass |
| C6 | `run unit / test_gate_rejects_banned_terms_accent_insensitive ... ok` | pass |
| C7 | `run unit / test_gate_round_convergence_rules ... ok` | pass |
| C8 | `run unit / test_gate_security_fields_required ... ok` | pass |
| C9 | `run unit / test_gate_security_states_and_hardening ... ok` | pass |
| C10 | `run unit / test_post_refuses_without_gate_or_when_already_posted ... ok` | pass |
| C11 | `run unit / test_post_own_pr_falls_back_to_comment ... ok` | pass |
| C12 | `run unit / test_post_gh_failure_and_success_marks_posted ... ok` | pass |
| C13 | `run unit / test_worf_skill_review_flow_order ... ok` | pass |
| C14 | `run unit / test_worf_skill_evidence_or_silence ... ok` | pass |
| C15 | `run unit / test_worf_skill_review_md_contract ... ok` | pass |
| C16 | `run unit / test_worf_review_standards_bypass_rule ... ok` | pass |
| C17 | `run unit / test_worf_skill_never_merges ... ok` | pass |
| C18 | `run unit / test_lessons_add_rejects_invalid_input ... ok` | pass |
| C19 | `run unit / test_lessons_dedupe_and_promote_on_two_features ... ok` | pass |
| C20 | `run unit / test_lessons_penalize_render_and_corrupt_store ... ok` | pass |
| C21 | `run unit / test_guinan_skill_signals_and_no_finding_no_lesson ... ok` | pass |
| C22 | `run unit / test_guinan_skill_retro_contract ... ok` | pass |
| C23 | `run unit / test_briefs_include_up_to_ten_confirmed_lessons ... ok` | pass |
| C24 | `run unit / test_briefs_unchanged_without_confirmed_lessons ... ok` | pass |
| C25 | `run unit / test_diagnostico_runs_harness_score_and_track_a ... ok` | pass |
| C26 | `run unit / test_diagnostico_report_contract ... ok` | pass |
| C27 | `run unit / test_diagnostico_failures ... ok` | pass |
| C28 | `run unit / test_diagnostico_gitignore_warning ... ok` | pass |
| C29 | `run unit / test_diagnostico_skill_cost_approval ... ok` | pass |
| C30 | `run unit / test_diagnostico_judge_protocol ... ok` | pass |
| C31 | `run unit / test_crew_declares_diagnostico_skill ... ok` | pass |
| C32 | `run unit / test_crew_worf_guinan_invocation_both ... ok` | pass |
| C33 | `run unit / test_execute_review_worf_after_pr ... ok` | pass |
| C34 | `run unit / test_execute_guinan_after_done ... ok` | pass |
| C35 | `run unit / test_build_fase9_skills_and_scripts_in_all_clis ... ok` | pass |
| C36 | `run unit / test_evals_f9_routing_cases ... ok` | pass |
| C37 | `run unit / test_credits_f9_sources_and_headers ... ok` | pass |
| C38 | `run unit / test_release_docs_f9 ... ok` | pass |
| C39 | `run unit / test_fase9_acceptance_sections ... ok` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `claude plugin validate dist/claude --strict` | pass |
| Build | `python scripts/check_decisions.py` | pass |

## Output

`Run unit` - exit 0

```
test_verification_fails_on_open_finding_or_missing_approval (test_validate_verification.ValidateVerificationTests.test_verification_fails_on_open_finding_or_missing_approval) ... ok
test_worf_review_standards_bypass_rule (test_worf_skill.WorfSkillTests.test_worf_review_standards_bypass_rule) ... ok
test_worf_skill_evidence_or_silence (test_worf_skill.WorfSkillTests.test_worf_skill_evidence_or_silence) ... ok
test_worf_skill_never_merges (test_worf_skill.WorfSkillTests.test_worf_skill_never_merges) ... ok
test_worf_skill_review_flow_order (test_worf_skill.WorfSkillTests.test_worf_skill_review_flow_order) ... ok
test_worf_skill_review_md_contract (test_worf_skill.WorfSkillTests.test_worf_skill_review_md_contract) ... ok
test_execute_stops_on_codex_hooks_review (test_worker_skills.WorkerSkillTests.test_execute_stops_on_codex_hooks_review) ... ok
test_laforge_calls_mccoy_on_second_failure (test_worker_skills.WorkerSkillTests.test_laforge_calls_mccoy_on_second_failure) ... ok
test_laforge_skill_scope_tdd_commit (test_worker_skills.WorkerSkillTests.test_laforge_skill_scope_tdd_commit) ... ok
test_mccoy_skill_regression_and_report (test_worker_skills.WorkerSkillTests.test_mccoy_skill_regression_and_report) ... ok

----------------------------------------------------------------------
Ran 572 tests in 255.922s

OK
```
