# Retro: pequena-minima

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | O `done --strict` ficou vermelho antes de `8bb50f9`: a edição por script da coluna `Closed` gerou `&#124;&#124; <sha> &#124;`, com uma célula a mais, e o gate não achou o commit | Implementar o item 3.7 da triagem (subcomando que preenche a célula `Closed` e confere o commit), no lugar da edição manual da tabela |
| 2 | média | AGENTS/CLAUDE.md | O primeiro commit (fechamento do Handoff de guard-lote2) foi recusado pelo `check_commit` com `Refs SC-196`; o `AGENTS.md` diz "`Refs SC-<n>` no corpo", e o gate exige o rodapé `Refs: SC-<n>` | Trocar no `AGENTS.md` a regra de commits para "rodapé `Refs: SC-<n>` separado do corpo por linha em branco" |
| 3 | média | instructions without effect | O `q-check` listou o `spec.md` fora da lista: o Picard gravou `--dispatched` no Handoff depois do commit pré-Q e antes de o Q terminar, contra a regra SC-181 W2 do `execute.md` | Fazer o `q-check` separar as mudanças do `## Handoff` (feitas pelo Picard) das do Q, ou fazer o `handoff.py set` recusar a escrita enquanto houver um Q despachado sem `worker_done` |
| 4 | baixa | automatic checks | Achado 1 do Q: `WAIVED_RE` aceitava `waivedness`; o mesmo padrão sem limite vale para `DEGRADED_RE` | Revisar os marcadores lidos por regex nos gates (`DEGRADED_RE`, `TREE_RE`) e exigir palavra inteira, com teste de valor que só começa igual |
