# Retro: lote1-correcoes

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | Handoff: "test_decisions_piloto_freios depende da SC-187 ser a última entrada"; correção em 8183cfe (regex com `.*` guloso) | Um helper comum nos testes, `decision_section(text, "SC-<n>")`, que devolve só a seção da entrada, para os `test_decisions_*` não dependerem da posição no `DECISIONS.md`. |
| 2 | alta | instructions without effect | L32 voltou pela 6ª feature (achado C7, linha 26) | Gerar no brief do LaForge o esqueleto de `test_decisions_<slug>` com uma asserção por requisito, em frase, em vez de depender da lição (repete a sugestão 2 de piloto-freios). |
| 3 | média | automatic checks | Achado R5 (linha 24): `_is_binary` olhava só 8000 caracteres, e a spec não falava em recorte | Quando o requisito diz "contém", o template breve pede um caso de borda além de qualquer limite interno do código. |
| 4 | baixa | tool economy | Relatório do T1-fix: o gate do ticket precisou da base fcb008d, porque a base do merge incluía commits alheios | `dispatch.py` grava no Handoff a base do despacho do fix, e o `run_gates.py ticket` usa essa base quando ninguém passa o intervalo. |
