**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR

APPROVE. As três correções de código cumprem o prometido pela 1.8.0 sem efeito colateral:
- `piloto.status` marca cada decisão `baixa` com `⚠️ revisar` (`scripts/piloto.py:226`).
- `model_info.fit` separa contexto `0` (conhecido, avisa) de contexto ausente (sem aviso), com checagem de tipo que exclui `bool` (`scripts/model_info.py:185-186`).
- `piloto.actives` passa a usar `_active_confirmed`, a mesma regra de `is_active` (`scripts/piloto.py:235`). O único chamador é `hooks/scripts/banner.py:156`, cuja linha diz que o Picard decide no lugar do usuário, o que só vale com mandato confirmado.

Os testes reforçados cobrem os três casos. Escopo da revisão: as 3 correções de código e os testes delas; a verificação retroativa em si é do Q (D-j). Arquivos mecânicos fora do review: `dist/`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|

Sem achados.

## Escada determinística

- `python tools/build.py --check`: OK, `dist/` em dia
- `python scripts/check_decisions.py`: OK
- `python -m unittest discover -s tests -p test_piloto.py`: 26 testes, OK
- `python -m unittest discover -s tests -p test_model_info.py`: OK
- `python -m unittest discover -s tests -p test_banner*.py`: OK
- `claude plugin validate dist/claude --strict`: Validation passed
- Suíte inteira nas provas: 938 OK (1 ignorado)
- `scan_bypasses.py`: 0 candidatos

## Pesquisa

Nenhuma superfície externa: só código e testes do repo (biblioteca padrão).
