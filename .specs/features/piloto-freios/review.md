**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR

APPROVE.
- O gate passa a validar a aprovação `piloto:` por `approval_valid_in` (`scripts/piloto.py:177-190`). Exige mandato com citação do usuário e status `ativo` ou `encerrado`; com o piloto encerrado, o carimbo da decisão precisa ser menor ou igual ao do `**Encerrado:**`. Os carimbos são ISO em UTC, com sufixo `Z` e precisão de segundo, então a comparação lexicográfica é correta.
- O freio conta as entradas `⚠️ revisar` já gravadas e recusa a próxima com `BrakeError` (exit 3, stderr). Essa checagem vem depois da checagem de categoria.
- O "devolvido ao usuário" sai sem a marca e não conta no freio, e a categoria sem `M<n>` é recusada também para ele (`scripts/piloto.py:227-241`).
- Os únicos chamadores são os gates, em `scripts/gates/gates_common.py:208-238`.

Arquivos mecânicos fora do review: `dist/`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|

Sem achados.

## Escada determinística

- `python tools/build.py --check`: OK, `dist/` em dia
- `python scripts/check_decisions.py`: OK
- `python -m unittest discover -s tests -p test_piloto.py`: 37 testes, OK
- `python -m unittest discover -s tests -p test_validate_*.py`: 36 testes, OK
- `claude plugin validate dist/claude --strict`: Validation passed
- Suíte inteira nas provas: 949 OK (1 ignorado)
- `scan_bypasses.py`: 0 candidatos

## Pesquisa

Nenhuma superfície externa: só código, testes e skill do repo (biblioteca padrão).
