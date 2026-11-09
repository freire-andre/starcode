# LESSONS - mantido por scripts/lessons.py

> Gerado. Não edite à mão: o próximo `lessons.py` sobrescreve. O estado fica em `.specs/lessons.json`.
> promote_threshold=2 features distintas

## Confirmed

Vistas em features distintas. Entram nos briefs.

_nenhuma_

## Candidates

Vistas uma vez. Em observação, não entram nos briefs.

### L1 - Valide campos obrigatórios exigindo string não vazia após strip, não só None ou "", porque o gate aceitou attacker: [] e o teste só cobria campo ausente.
- signal: `weak_test` · features: 1 · scope: `scripts/review`
- features: fase-9-worf-guinan-diagnostico
- sources: scripts/review/review_gate.py:72
- updated: 2026-11-09T18:54:53Z

### L2 - Compare a linha exata e o valor esperado no teste, não só assertIn de um trecho ou um padrão genérico, porque C11 e C39 passariam com texto ou nível errados.
- signal: `weak_test` · features: 1
- features: fase-9-worf-guinan-diagnostico
- sources: tests/test_review_post.py:test_post_own_pr_falls_back_to_comment; tests/test_acceptance_doc_f9.py
- updated: 2026-11-09T18:54:53Z

### L3 - Registre a decisão no DECISIONS.md no mesmo ciclo de qualquer correção em scripts/, skills/ ou hooks/, porque o check_decisions deixa as provas vermelhas.
- signal: `gate_fail` · features: 1
- features: fase-9-worf-guinan-diagnostico
- sources: proofs.md: check_decisions após 9e7679a
- updated: 2026-11-09T18:54:53Z

## Quarantined

Confirmadas que falharam ao serem aplicadas. Ignorar.

_nenhuma_
