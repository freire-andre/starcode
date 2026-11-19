# Retro: sessions-concorrente

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | média | information access | Achado 3 do `verification.md`: o T1 (`d88fc17`) gravou no `DECISIONS.md` os números de uma reprodução própria (9, 13 e 17; 7 e 8), diferentes dos registrados no `context.md` (9, 11 e 13; 10, 6 e 11) | Quando o requisito citar números de uma reprodução, copiar os números para a própria spec (não só para o `context.md`), para que o worker use a fonte única |
| 2 | média | automatic checks | Achado 1: o R4 dizia "o `write_session` [...] SHALL usar esse caminho" e "64 chaves", o que deixou ambíguo se a prova era pelo `write_session` (substituição) ou pelo `update_session`; o Q leu do primeiro jeito | Ao mudar uma função cuja semântica é substituir tudo, escrever na spec qual função tem a garantia de concorrência e qual mantém a semântica antiga |
| 3 | baixa | instructions without effect | Achados 2 e 4 (recorrências L32 e L25): teste de nova tentativa sem o limite e teste de timeout com um só comando entre três | Repetir no brief do LaForge a lista das lições mais recorrentes (sugestão já aberta na retro de fecha-achado) |
| 4 | baixa | instructions without effect | Handoff: depois do `dispatch.py start` não houve commit do Handoff junto com outra mudança, e o `settle` passou na primeira (a armadilha de frota-travada não se repetiu) | Manter; registrar a regra no `execute.md` seção 2 se ela voltar a falhar |
