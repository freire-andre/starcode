# Retro: roteamento-worf-mccoy

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | information access | Handoff: o caso `pos-piloto-automatico` foi especificado esperando roteamento para uma skill com `invocation: user` (`src/crew.yaml`), que o build converte em `disable-model-invocation: true`; o caso não podia passar, e a descoberta custou dois despachos (`3394a55` e a reversão `c3e9e2f`) | Na descoberta de qualquer caso de roteamento, conferir o `invocation` da skill no `src/crew.yaml` e o frontmatter gerado no `dist/` antes de escrever o caso |
| 2 | média | automatic checks | Escalada do T1: `tests/test_worf_skill.py:28` exigia na descrição os gatilhos genéricos que o R1 mandou tirar; o arquivo não estava no May change | Antes de mudar uma descrição de skill, procurar em `tests/` os trechos atuais da descrição e listar esses testes no May change |
| 3 | média | instructions without effect | Achados 1, 2, 4 e 5 (recorrências L2 e L32 e as lições L70 e L71): testes com trecho solto em vez de estrutura ou igualdade | Repetir no brief do LaForge a lista das lições mais recorrentes (já sugerido nas retros de fecha-achado e sessions-concorrente; terceira vez) |
| 4 | baixa | tool economy | O primeiro `claude plugin eval` não achou casos: o filtro `--case` usa o `name` do caso (`routing-<pasta>`) e só fica com o último valor quando é repetido | Documentar no `evals/README.md` o filtro por caso (`--case "routing-<pasta>"`, um por execução) |
