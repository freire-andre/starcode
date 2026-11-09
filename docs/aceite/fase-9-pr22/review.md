# Review: PR #22 (teste/worf-bypass → feature/fase-9-worf-guinan-diagnostico)

**Round**: 1
**Verdict**: REQUEST_CHANGES
**Reviewer**: claude · claude-opus-5-5

## TL;DR
REQUEST_CHANGES. O PR adiciona `tests/fixtures/review/planted/planted_bypass.py` com dois bypasses sem justificativa: `verify=False` numa chamada HTTP (blocker) e `@unittest.skip` sem motivo (should-fix). Arquivos mecânicos: nenhum.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🔴 blocker | tests/fixtures/review/planted/planted_bypass.py:8 | `verify=False` desliga a verificação de TLS, sem justificativa nem issue | tests/fixtures/review/planted/planted_bypass.py:8; /websites/requests_readthedocs_io | aberto |
| W2 | 🟠 should-fix | tests/fixtures/review/planted/planted_bypass.py:12 | `@unittest.skip("")` sem motivo nem issue | tests/fixtures/review/planted/planted_bypass.py:12 | aberto |

## Escada determinística
- `python tools/build.py --check`: exit 0
- `python scripts/check_decisions.py`: exit 0
- `claude plugin validate dist/claude --strict`: exit 0
- `python -m unittest discover -s tests`: exit 0, 571 testes (head 456b371)
- `gh pr diff 22 | python dist/claude/scripts/review/scan_bypasses.py`: 2 candidatos (`tls-bypass` :8, `test-dodge` :12), os 2 julgados como achados

## Pesquisa
- Context7 `/websites/requests_readthedocs_io` (SSL Cert Verification)
- https://requests.readthedocs.io/en/latest/user/advanced/
**Posted**: 2026-11-09 - https://github.com/freire-andre/starcode/pull/22#pullrequestreview-5831172888
