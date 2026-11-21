**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE, sem achados.

O `covers` troca o `fnmatch` por `_glob_re`, uma expressão regular montada por segmento:
- diferencia maiúsculas;
- `*` e `?` não atravessam `/`;
- `**` como segmento casa zero ou mais segmentos, inclusive no início (`**/x.py` cobre `x.py`);
- `[` e `]` são literais.

A regra de pasta, a igualdade e a recusa de caminho absoluto ou com `..` não mudaram.

O teste de tabela força o `os.name` e o `normcase` do Windows. O `fnmatch` antigo falharia nesse modo, porque o `normcase` dele passa tudo para minúsculas.

O `is_sensitive` e o `paths_overlap` continuam com `fnmatch` e ficam fora do R.9. O `paths_overlap` recorre ao prefixo literal, então, se errar, é sempre apontando sobreposição a mais.

Ficaram fora do review os arquivos mecânicos (`dist/`).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|

## Escada determinística
- **CI na `7141b1c`** (evidência do PR): verdes o `build --check`, o `check_decisions`, o `claude plugin validate --strict` e a suíte inteira (1066 testes, 1 pulado).
- **Módulos tocados no head `e72be9d`:** todos OK.
  - `test_coverage_rule`: 9 testes;
  - `test_check_scope*`: 8;
  - `test_validate_tasks*`: 6.
- **Sonda manual do `covers`:** `**/x.py`, maiúsculas e `a/*`.
- **`scan_bypasses.py`:** 0 candidatos.

## Pesquisa
Nenhuma superfície externa: só a biblioteca padrão (`re`, `functools`), já usada no repositório.
