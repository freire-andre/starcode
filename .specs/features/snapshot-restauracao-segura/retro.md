# Retro: snapshot-restauracao-segura

Lições registradas: L35, L36 e L37 (novas).

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | instructions without effect | `context.md`, Gray Areas: "Recusa tudo" para linhas "voltar" fora do ticket contradizia o cenário de aceite F12-2 (`test_cenario_aceite_disjuntor_modo_1`, edição do usuário fora do ticket); o Spock teve de perguntar de novo ("Só arquivo ausente") | Antes de oferecer opções que mudam uma decisão registrada, o Picard confere os testes de aceite dessa decisão e descreve na pergunta o caso que cada opção quebra. |
| 2 | média | automatic checks | Commit `5b26c06`: a correção pós-Q mudou `scripts/snapshot.py` sem regerar o `dist/`; `build --check` só foi rodado pelo Picard depois do `worker_done` | Incluir `python tools/build.py --check` no `run_gates.py ticket` quando o intervalo toca `scripts/`, `skills/` ou `hooks/`, para o worker não entregar `dist/` desatualizado. |
| 3 | média | automatic checks | `verification.md` achados 1 e 2: a spec fixou o caminho do plano e a limpeza, mas não o arquivo ilegível nem a falha ao apagar | Quando a spec cria um arquivo de estado, o template de Edge Cases pede uma linha para "arquivo ilegível" e outra para "falha ao gravar/apagar". |
| 4 | baixa | information access | `verification.md` Limits: C8 simula a falha do `pre-restore` por mock, não por falha real do `git update-ref` | Registrar em `tests/` um helper que faz o `update-ref` falhar de verdade (ref travado com `.lock`), para os próximos testes de falha de Git. |
