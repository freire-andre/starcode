# Retro: pr-review

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | O `done --strict` ficou vermelho antes de `f7e3093`: na evidência do Q, os pipes (`\|` e um `|` cru dentro do código Python) deslocaram a coluna `Closed` do achado 2. Na feature anterior (pequena-minima), o mesmo gate falhou por `&#124;&#124;` | Fazer o `validate_verification` acusar a linha da tabela com número de células diferente do cabeçalho, com o número da linha; e mandar no brief do Q que pipes na evidência sejam escritos como `&#124;` |
| 2 | média | instructions without effect | O brief pós-Q pedia "um commit por achado", e o LaForge juntou 3 achados e o P1 em `48d7055` e 2 achados em `ca5b699` | Tirar a regra do brief (o `Closed` aceita o mesmo commit em vários achados) ou fazer o gate `ticket` conferir um `Refs`/achado por commit |
| 3 | baixa | automatic checks | Achado 1 do Q: o passo novo da seção "Review (Worf)" contradizia a parada da rodada 3 da mesma seção | Ao mudar uma seção de fluxo do `execute.md`, um teste de não contradição: frases que mandam pedir o merge precisam trazer a condição "no `blocker` or `should-fix` open" |
