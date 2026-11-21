# Retro: ponte-manutencao

Lições: L32 (recorrência, achado 4), L20 (recorrência, achado 3), L76 (achado 1), L77 (achado 2), L78 (achado 5).

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | tool economy | No F:, o gate proofs deu `C4`, `C5`, `C6: fail (run plugin ...)`. Foi preciso um worktree destacado no C: (`sc207-proofs`), e um `proofs.md` velho que sobrou nele bloqueou o checkout seguinte. | Dar ao `run_gates.py proofs` uma opção que rode a linha `Run plugin` num worktree destacado no drive da Orca, criado e apagado pelo próprio gate. |
| 2 | alta | tool economy | Na reintegração pós-Q, `dispatch.py settle ... T1` respondeu `settle recusado: T1 não tem entrada em Dispatched`. O Picard rodou o gate ticket e o merge `62a1844` à mão. | Fazer o `settle` aceitar `--fix` para reintegrar o ramo do worker já integrado: gate ticket sobre `<integração>..<ramo>` e merge `--no-ff`. |
| 3 | média | automatic checks | Achados 3 e 4: prefixo de mensagem e termos soltos na seção Decisão de novo. A L20 já está em 12 features e a L32 em 15, e as duas vão no brief desde a SC-205. | Fazer o Q rodar uma checagem automática dos testes citados: um `assertIn` com trecho menor que a mensagem exigida pelo requisito vira achado. |
| 4 | média | automatic checks | O `check_proofs` leu a nota entre parênteses da linha `**Run plugin**` como parte do comando (exit 2). Corrigido no commit da linha `run plugin` sem nota. | Fazer o `validate_spec` recusar uma linha `**Run ...**:` com texto fora das crases. |
| 5 | média | information access | Achado 5: `shutil.which("bash")` achou o bash do WSL no Windows (L78). | Pôr em `tests/helpers.py` uma função `git_bash()` e citá-la no `AGENTS.md` como o jeito de executar passos do CI nos testes. |
| 6 | baixa | instructions without effect | O `close-finding` recusou `--test` com o erro `the following arguments are required: --cover`. | Citar `--cover` no exemplo do `execute.md` ou aceitar `--test` como apelido. |
| 7 | baixa | information access | O fix-brief com as notas do Picard (bash do Git, drive da Orca) fechou os 5 achados em uma rodada (c4fdc40 a 2d18fb2). | Registrar no `execute.md` que as notas do Picard levam o ambiente quando um achado depende dele. |
