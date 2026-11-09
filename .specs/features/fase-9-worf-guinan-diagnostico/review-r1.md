# Review: PR #21 (feature/fase-9-worf-guinan-diagnostico → main)

**Round**: 1
**Verdict**: REQUEST_CHANGES
**Reviewer**: claude · claude-opus-5-5

## TL;DR
REQUEST_CHANGES. O CI do Ubuntu está vermelho: o npx falso de `tests/test_diagnostico.py` não roda no Linux e 4 testes do diagnóstico falham (o Windows passa). Há também um nit no `post_review.py`. Fora do review: `dist/` (gerado) e `scripts/harness/` (vendorizado do harness-eval 1.8.3, CC-BY-4.0).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🔴 blocker | tests/test_diagnostico.py:50 | o shim do npx falso chama `dirname` com o PATH restrito; falha no Linux | tests/test_diagnostico.py:50; tests/test_diagnostico.py:59; CI job 129366862666 | aberto |
| W2 | 🟡 nit | scripts/review/post_review.py:56 | emoji repetido no comentário inline | scripts/review/post_review.py:56; PR #22 review 5831172888 | aberto |

## Escada determinística
- `python tools/build.py --check`: exit 0
- `python scripts/check_decisions.py`: exit 0
- `python -m unittest discover -s tests` (Windows, local): exit 0, 572 testes
- CI `checks (windows-latest)`: pass; `checks (ubuntu-latest)`: fail (4 falhas e 1 erro em `test_diagnostico`)
- `git diff origin/main...HEAD | python scripts/review/scan_bypasses.py`: 76 candidatos, todos aceitos (padrões do próprio scan, fixtures, docs do aceite, `noqa: E402` de import após `sys.path`, `time.sleep` do modo lento do npx falso)

## Pesquisa
- https://github.com/freire-andre/starcode/actions/runs/42678656552/job/129366862666 (log do CI)
- nenhuma superfície externa nova além do `requests`, já pesquisado no PR #22, e do `harness-score@1.8.4`, coberto pela spec (R26)
**Posted**: 2026-11-09 - https://github.com/freire-andre/starcode/pull/21#pullrequestreview-5831297053
