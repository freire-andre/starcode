# Retro: ponte-missao-ativa

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | information access | Primeiro `run_gates.py proofs` no checkout principal: C5–C7 e Build falharam com `orca-testing.mjs: cannot import "./orca-runtime.mjs"`; a mesma árvore passou num worktree no drive C: (proofs em 61fec64) | Documentar em AGENTS.md/execute.md que `orca plugin test`/`check` (Orca 1.4.257) só rodam com o plugin no mesmo drive da instalação da Orca, e reportar o defeito à Orca |
| 2 | alta | automatic checks | verification.md rodada 1, R7: `notifications.show` sem `notifications:show` no manifesto; o mock do teste aceitava qualquer chamada | Fazer o `mockHost` dos testes do painel recusar chamadas cuja capacidade não está em `orca-plugin.json` (ou um teste que cruze chamadas `host.call` com as capacidades) |
| 3 | média | instructions without effect | Brief da correção da rodada 2 sem `DECISIONS.md` no May change; o worker parou com `check_decisions` rc=1 (7400f47 veio depois de autorização) | Fazer o `dispatch.py` acrescentar `DECISIONS.md` ao May change sempre que ele incluir arquivos de `scripts/` |
| 4 | média | tool economy | Célula `Closed` editada à mão ficou com coluna extra e o gate done reprovou (2 erros) antes de 146cb6a | Um subcomando (`verification.py close <slug> <achado> <commit> <evidência>`) que preencha a célula sem edição manual da tabela |
| 5 | baixa | navigation | `worker-read <dispatch>` falhou (precisa de `--dispatch`) e o modelo efetivo do Q não aparece na saída; o Verifier ficou `effective unconfirmed` | Corrigir o exemplo do execute.md para `worker-read --dispatch <id>` e dizer onde ler o modelo efetivo |
