**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
COMMENT. O caminho da PEQUENA funciona de ponta a ponta: a spec SMALL passa no gate, o dispatch trata a feature como T1, o `q-waive` grava o marcador e o `done` aceita `waived` só como palavra inteira e só em spec SMALL. Um should-fix: o gate da spec SMALL não exige a linha `Proof:` em cada check. Dois nits: o `STARCODE.md` ainda diz que a Guinan sempre roda, e o `q-waive` sobrescreve um `verification.md` que já existe. Arquivos mecânicos fora do review: `dist/`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | `scripts/gates/validate_spec.py:105` | O `_check_small` não exige `Proof:` em cada check. Uma spec SMALL com check sem prova dá `ok` e só falha no `run_gates.py proofs`, depois do worker. A spec mínima não tem aprovação humana, então o gate é a única conferência. Na MÉDIA, o `validate_checks` recusa isso já na spec | `scripts/gates/validate_spec.py:105` | open |
| W2 | 🟡 nit | `src/context/STARCODE.md:58` | As regras centrais dizem que a Guinan sempre roda a retro, sem a exceção da PEQUENA | `src/context/STARCODE.md:58` | open |
| W3 | 🟡 nit | `scripts/dispatch.py:923` | O `q_waive` sobrescreve um `verification.md` existente sem aviso (perde o relatório de um Q que tenha rodado) | `scripts/dispatch.py:923` | open |

## Escada determinística
- Suíte inteira em `8bb50f9`: 989 testes OK (1 skip).
- `python tools/build.py --check`, `python scripts/check_decisions.py`, `claude plugin validate dist/claude --strict`: verdes.
- `run_gates.py proofs` (8/8) e `done --strict`: verdes.
- `scan_bypasses.py`: 0 candidatos.
- Sondas: a spec com o alias `PEQUENA` passa; o `q-waive` sem feature sai com 2; um check sem `Proof:` passa na spec e falha no proofs.

## Pesquisa
Nenhuma superfície externa: biblioteca padrão (`re`, `pathlib`) e scripts internos.
