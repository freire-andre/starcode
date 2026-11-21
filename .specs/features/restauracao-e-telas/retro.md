# Restauracao-e-telas: Retro

**Feature**: restauracao-e-telas (SC-210, MÉDIA)
**Done**: `run_gates.py done --strict` verde em 709d778
**Lições**: L10 (recorrência, achado 1), L84 (nova, achado 2)

## Sugestões

| # | Categoria | Evidência | Ação proposta |
|---|---|---|---|
| 1 | tooling | As regras extras do Q vinham de um arquivo no scratchpad do Picard, que sumiu. O Q começou sem elas e recebeu as regras por mensagem depois do início (despacho ctx_953df7b41a72, mensagem msg_f06604c16064). | O `dispatch.py q-brief` passa a emitir as regras fixas do Q no próprio briefing: não fazer commit, não limpar a árvore, não chamar a Orca de verdade e o formato do `unittest discover`. O briefing deixa de depender de arquivo temporário. |
| 2 | tooling | O settle não reintegra a correção pós-Q. A integração foi feita à mão com `run_gates.py ticket` e `git merge --no-ff` (45f9b43). É a terceira feature seguida em que isso acontece. | O `dispatch.py settle` passa a aceitar a correção pós-Q (por exemplo, `--fix`): roda o gate do ticket sobre o intervalo novo e faz o merge sem exigir que a entrada esteja em Dispatched. |
| 3 | spec | O LaForge parou para pedir `tests/test_validate_verification_screens.py`, que estava fora do May change (mensagem msg_fd2170c103c0). O Picard ampliou o escopo em 4f7c295. | Quando um requisito endurece um validador, a spec lista no May change os testes que geram a entrada validada. Um `grep` pelo construtor (aqui, o helper que monta PNG) antes de fechar o escopo resolve. |
| 4 | spec | Achado 1 do Q: o check C1 afirmava duas coisas e a prova citava só um teste. O Picard fechou o achado sem worker (b34590b). | O `validate_spec` avisa quando um check com mais de uma afirmação (separadas por `;`) tem uma única linha `Proof:`. |
| 5 | test | Achado 2 do Q: o PNG com `IDAT` truncado passava, porque o teste original só cobria o arquivo sem `IDAT`. | Para leitores binários, a spec pede no check a tabela de truncamento (cabeçalho, dados, CRC e comprimento zero), e não só a ausência do chunk. |

## Notas
- O achado 1 era só da spec, e o Picard fechou sem despachar worker. Isso funcionou: o achado não tinha código para corrigir.
