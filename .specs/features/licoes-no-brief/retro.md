# Retro: licoes-no-brief

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | Commit `e7427ef`: a spec entrou com o gate `execute` vermelho (PEQUENA com 4 arquivos), porque o `\| head -1` escondeu o código de saída; a reclassificação para MÉDIA veio depois da integração | O `check_commit.py`, ou um hook, recusar commit de `spec.md` quando `run_gates.py execute` estiver vermelho; até lá, o Picard grava a saída em arquivo e confere o código antes de commitar |
| 2 | média | information access | Handoff: a spec PEQUENA não listou `tests/test_dispatch_lessons.py`, que já testava a posição e a ordem das lições; o worker parou no `check_scope` | Antes da spec, procurar em `tests/` os testes da função que muda (`grep` pelo nome) e listá-los no May change; mesma ação da retro de roteamento-worf-mccoy (item 2), agora recorrente |
| 3 | média | automatic checks | Achados 2 e 3 (recorrências L20, agora em 10 features, e L32, em 13): mesmo com as lições no topo do brief, o primeiro despacho veio com teste por fragmentos | Medir na próxima feature se a lição no topo muda o resultado; se não mudar, o `check_proofs` pode recusar teste de texto gerado sem comparação de igualdade |
| 4 | baixa | tool economy | Ao usar o `fix-brief` pela primeira vez, o Picard viu 3 defeitos (título com `: Spec`, `<ID do Linear>`, `<ticket>`) que o teste por fragmentos não pegava | Usar cada gerador novo do Picard uma vez na própria feature antes do Q, quando der |
