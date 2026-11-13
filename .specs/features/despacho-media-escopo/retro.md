# Retro: despacho-media-escopo

Lições registradas: L20 (recorrência, 3 features), L25 (recorrência; promovida a `confirmed`), L29 (nova).

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | instructions without effect | `verification.md` achados C5 e C13; L20 em 3 features, com a regra já escrita no brief desta feature ("comparam a linha inteira esperada") | Tornar a regra verificável: o gate da spec recusa check de mensagem sem o texto exato entre crases, e o brief do LaForge cita a L20 como regra fixa, não só na seção de lições. |
| 2 | média | automatic checks | `verification.md` achado "ID em minúscula"; `spec.md` Edge Cases sem check correspondente | `validate_spec.py` avisa quando um item de `## Edge Cases` não aparece em nenhum check pelo trecho literal ou pelo ID do requisito. |
| 3 | média | automatic checks | `verification.md` achado C9: R9 dizia "um subcomando do `dispatch.py`" e o teste cobria só `next` | Quando um requisito vale para "cada subcomando" ou "cada gate", o check lista os chamadores pelo nome, para o teste não poder cobrir só um. |
| 4 | baixa | tool economy | Handoff: despacho do T1 e do Q com `worker-start` e `--dispatch-add` à mão, porque a correção era a própria feature | Na próxima MÉDIA, usar `dispatch.py start` e `settle` e conferir que o fluxo manual sumiu do `execute.md`. |
