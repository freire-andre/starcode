# Retro: guardas-add-commit-powershell

Lições: L2 e L4 registradas como recorrência (texto idêntico), as duas promovidas a `confirmed`. Nenhuma lição nova.

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | instructions without effect | `verification.md` achado 1: C1, C3, C4 e C6 conferiam o achado por prefixo e trecho, embora a spec, o brief e as lições L33, L37, L38 e L39 pedissem comparação integral; mesma classe nas cinco features anteriores | Pôr no `check_proofs` (ou num lint dos testes citados por checks) um aviso para `assertIn`/`startswith` sobre a saída comparada num check cujo requisito fixa um formato exato; texto no brief já não muda o comportamento. |
| 2 | média | automatic checks | `verification.md` achado 2: o caminho novo `untracked_findings` (`secret_scan.py:196`) nega arquivo grande, mas só o caminho antigo (diff rastreado) tinha teste de limite | Na spec, todo requisito de limite ou negação existente que ganha caminho novo de código recebe um check próprio para esse caminho; o Spock lista no Edge Cases os limites herdados (`MAX_DIFF_BYTES`, ilegível). |
| 3 | baixa | information access | Handoff: o ticket gate com base explícita (`482b692..HEAD`, depois `8a318fd..HEAD`) rodou verde sem relatório falso, ao contrário da feature anterior | Manter a base explícita no brief como padrão do `dispatch.py brief`, gerando a linha a partir do commit da spec ou da verificação. |
