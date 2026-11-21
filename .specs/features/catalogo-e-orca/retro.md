# Catalogo-e-orca: Retro

**Feature**: catalogo-e-orca (SC-211, MÉDIA)
**Done**: `run_gates.py done --strict` verde em 7ca9a3c
**Lições**: L85 (achado 1), L86 (achado 2), L87 (achado 3), L2 (recorrência, achado 4) e L32 (recorrência, achado 5)

## Sugestões

| # | Categoria | Evidência | Ação proposta |
|---|---|---|---|
| 1 | spec | Achado 2 do Q: o R4 pedia que o `run` devolvesse 127, 124 e 126 nas falhas de execução, códigos que o `orca` também pode devolver. O `screens.py` passou a trocar o diagnóstico (59729cf). | Quando a spec define códigos sentinela num adaptador de processo, ela também exige um campo que diga a origem da falha e um check com o processo devolvendo esses mesmos códigos. |
| 2 | test | Achados 3, 4 e 5 do Q: três checks provados por palavras soltas ou padrão textual (25af2a6, a41c89e, 8392819). L2 e L32 voltam, agora em 18 e 17 features. | O briefing do LaForge passa a trazer as lições confirmadas L2, L20 e L32 como regra explícita, para checks de documento e de "ninguém chama X". |
| 3 | test | Achado 1 do Q: a memoização guardava só o resultado válido (1a02ebc). | Num requisito de "lido uma vez", o check lista na spec também o caso inválido ou ausente. |
| 4 | tooling | A correção pós-Q foi integrada à mão de novo, com `run_gates.py ticket` e `git merge --no-ff` (f968a18). É a quarta feature seguida. | Mesma ação da retro de restauracao-e-telas: o `dispatch.py settle` aceita a correção pós-Q. |
| 5 | tooling | Desta vez as regras extras do Q foram anexadas ao briefing antes do início, a partir do arquivo recriado no scratchpad. O arquivo continua fora do repositório. | Mesma ação da retro de restauracao-e-telas: o `q-brief` passa a emitir as regras fixas. |
