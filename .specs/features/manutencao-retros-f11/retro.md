# Retro: manutencao-retros-f11

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | Handoff, Reports: "proofs vermelho: check_decisions sem entrada para o T7" (75fe604, 3a3eba7); correção em 94abab1 (F12-15) | Fazer o gate do ticket rodar o check_decisions sobre o diff do próprio ticket, para que mudança em skill sem entrada no DECISIONS.md reprove antes da integração. |
| 2 | alta | information access | Handoff, Reports T2 e T7: brief gerado pelo plugin instalado 1.6.1, sem a regra do T3; proofs.md saiu com CRLF pelo check_proofs antigo (correção 34296bb) | Gravar no brief e no Handoff a versão do plugin que gerou o brief e rodou o gate, e recusar o despacho quando ela diferir do código-fonte do repositório. |
| 3 | alta | automatic checks | Handoff, Reports T4: o novo gate de tasks reprovaria as fases 3 a 12 já concluídas (só se reexecutadas) | Dar ao gate de tasks uma linha de base das fases fechadas, para que uma regra nova valha só para tasks escritas ou reexecutadas depois dela. |
| 4 | média | automatic checks | Commit dbbe1b1 e Reports T7: 10 testes antigos em tests/test_skills_exec.py exigiam o texto que o R18 removia; o arquivo não estava no May change | Quando a spec remove um texto, um check listar os testes que ainda o asserem, e o Picard incluí-los no May change antes do despacho. |
| 5 | média | instructions without effect | Reports T8: o worker não viu o teste falhar antes da implementação; o Picard conferiu contra o brief antigo | Exigir que o relato do LaForge cite a execução vermelha do teste novo antes do commit, verificável pelo Picard. |
| 6 | média | automatic checks | verification.md, Q (FAIL): R23 (data 2026-99-99 aceita), R20/R21 (caminho com `..` coberto), C32 (prova de idioma fraca) | Incluir no brief de teste a regra de pelo menos um caso negativo por check de validação (data inválida, caminho com `..`, idioma errado). |
