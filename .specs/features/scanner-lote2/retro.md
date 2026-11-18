# Retro: scanner-lote2

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | Achado do Q (linha 24): a isenção de host local era contornada por `@localhost:5432@evil.com`; corrigido em 34d9ae8 | Quando a spec cria uma isenção num gate de segurança, o template breve exige um check de contorno (entrada maliciosa que tenta usar a isenção), escrito já na spec. |
| 2 | alta | instructions without effect | L2 voltou pela 13ª feature e L32 pela 8ª (achados C2, C5 e C7) | Mesma proposta das últimas três retros: o esqueleto dos testes de saída exata e de `test_decisions_<slug>` vem pronto no brief do LaForge. |
| 3 | média | automatic checks | Primeiro `run_gates.py done` vermelho: o `validate_verification` leu `\|` dentro de uma célula de evidência do Q como divisor de coluna | O `gates_common` respeita `\|` escapado ao dividir as linhas da tabela, ou o brief do Q proíbe `\|` e pede `&#124;`. |
| 4 | média | tool economy | Handoff: "Q precisou de Enter manual para iniciar"; o usuário viu o worker travado | `dispatch.py` (ou o Picard) confere o terminal do worker codex depois do `worker-start` e envia Enter quando o prompt fica parado. |
