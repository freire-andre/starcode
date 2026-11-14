**Round**: 2
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE. Rodada 2 sobre `1576f8c..91ac2c7`, com releitura de `main...HEAD`. O W1 fechou em 103b26b. A referência textual agora casa o basename com fronteira: antes do nome só pode vir início do texto ou caractere fora de `[A-Za-z0-9_.-]`, e depois dele só fim do texto ou caractere fora dessa classe (scripts/impact.py:374). `test_referencia_textual_exige_fronteira` (tests/test_impact.py:255) cobre a sonda da rodada 1, e a entrada SC-176 do `DECISIONS.md` registra a correção.

Sondas com `impact.select` em repositórios temporários, fora do repositório, usando `scripts/impact.py` do ramo:

- não casam, com `run-all: nenhum teste alcança a.py` (R6): `a.py` dentro de `"fixtures/data.py"`, `a.pyc`, `a.py_old`, `x.a.py`, `my-a.py` e `a.py.bak`;
- casam, com `selected` e a cadeia `a.py <- tests/test_x.py`: `"scripts/a.py"`, `'a.py'`, `a.py,`, `a.py` no fim do texto sem quebra de linha, `(a.py)`, `r"scripts\a.py"` e `"C:\\r\\a.py"`;
- `re.escape` segura caracteres especiais: `a+b.py` casa consigo e não casa em `aab.py`, `x(1).py` casa consigo, e `x[1].py` não casa em `x1.py`.

Nenhum blocker novo. `dist/` é mecânico: `build --check` em dia, e as 5 cópias são iguais a `scripts/impact.py`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/impact.py:374 | A referência textual casava o basename como substring solta (`a.py` dentro de `fixtures/data.py`), e assim um mudado sem teste não forçava `run-all` (R6). | scripts/impact.py:374, tests/test_impact.py:255, DECISIONS.md:1045 | resolved (103b26b, dist em 91ac2c7) |

### Observações residuais (não são achados)
A rodada 2 só aceita blocker novo, e nenhuma das duas chega a isso. Ficam registradas para uma issue de acompanhamento.

- **Fronteira só ASCII** (scripts/impact.py:374). Sonda: `o.py` mudado sem teste e `tests/test_x.py` com `"ação.py"` dão `selected` com `o.py <- tests/test_x.py`, quando o esperado era `run-all`. É um falso alcance da mesma classe do W1, mas só acontece quando uma letra não ASCII vem logo antes do nome. Trocar `A-Za-z0-9_` por `\w`, que é Unicode no `re` do Python, fecha o caso.
- **Ponto na fronteira direita** (scripts/impact.py:374). `a.py` no fim de uma frase (`"""Ver a.py."""`) não conta como citação. Sonda: `a.py` importado por `tests/test_a.py` e citado só em prosa por `tests/test_doc.py` dá `selected` apenas com `tests/test_a.py`. Isso estreita a seleção de R5 quando a citação está em prosa, mas não fere R6: se não houver outro teste, o mudado cai em `run-all`.

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `cmp scripts/impact.py dist/*/scripts/impact.py`: as 5 cópias são iguais.
- `python scripts/check_decisions.py`: OK (DECISIONS.md atualizado no mesmo commit 103b26b).
- `claude plugin validate dist/claude --strict`: Validation passed.
- `python -m unittest discover -s tests`: OK (skipped=1).
- `git diff main...HEAD | python scripts/review/scan_bypasses.py`: 0 candidatos.
- Sondas `impact.select` em repositórios temporários: 28 casos. A fronteira se comporta como esperado, exceto nos 2 residuais.

## Pesquisa
nenhuma superfície externa
