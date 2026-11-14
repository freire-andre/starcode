**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE. A aprovação do piloto passa a exigir a decisão citada registrada e o `piloto.md` ganha um leitor só no `gates_common.py`; R1 a R9 têm teste e os 23 testes de `test_piloto` passam. Dois nits: o `registrar` ainda aceita mandato sem `- user:` (o `ativo` recusa) e um ID gigante no `piloto.md` derruba o gate com `ValueError`. Fora do review: `dist/` (gerado, `build --check` OK).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟡 nit | scripts/piloto.py:179 | `record()` confere o mandato só pela data (`CONFIRMED_RE`), e `ativo` e os gates exigem `- user:`; trocar por `_active_confirmed(doc)` ou `USER_CONFIRMED_RE`. | scripts/piloto.py:179 | aberto |
| W2 | 🟡 nit | scripts/piloto.py:169 | `registered_decisions_in` faz `int()` sem limite; `### D<5000 dígitos> · ` no `piloto.md` faz `gc.approved()` sair com `ValueError` (sondado em diretório temporário). Limitar a 6 dígitos como no lado citado. | scripts/piloto.py:169 | aberto |

## Escada determinística
- `python tools/build.py --check`: OK, `dist/` em dia.
- `python scripts/check_decisions.py`: OK.
- `python -m unittest test_piloto` (a partir de `tests/`): 23 testes OK.
- `python -m unittest discover -s tests -v`: 844 OK, 1 skip (informado pelo Picard; CI do PR em andamento).
- `git diff main...HEAD | python scripts/review/scan_bypasses.py`: 1 candidato, `# noqa: E402` em `dist/orca/scripts/piloto.py:32`. É cópia gerada de código que já existia em `scripts/piloto.py` (o `dist/orca` passou a levar o `piloto.py` porque o `gates_common.py` agora o importa); sem achado.

Arquivos mecânicos fora do review: `dist/**`.

## Pesquisa
nenhuma superfície externa (só stdlib).
