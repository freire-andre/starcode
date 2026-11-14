# Retro: piloto-decisao-citada

Lições registradas: L30 (nova), L20 (recorrência, 4 features, `confirmed`).

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | instructions without effect | `verification.md` achados 2 e 3 (`assertIn` e `startswith` em C3 e C6); L20 em 4 features, já sugerida como regra verificável na retro da despacho-media-escopo | Aplicar a sugestão anterior: um check estático na suíte que recusa `assertIn`/`startswith` sobre a mensagem citada por um check da spec, ou o brief do LaForge exige `assertEqual` com a mensagem inteira. |
| 2 | média | automatic checks | `verification.md` achado 1: `int()` sobre `D\d+` sem limite em `gates_common.py:200` | Ao revisar regex que capturam números (`\d+`), conferir que toda captura tem limite de dígitos (`\d{1,6}`), por teste ou por regra do Worf. |
| 3 | baixa | information access | `verification.md` Limits: provas no HEAD 514729d, verificação no b003660 | Gravar as provas depois do último commit de código antes de despachar o Q, para os dois HEADs coincidirem. |
