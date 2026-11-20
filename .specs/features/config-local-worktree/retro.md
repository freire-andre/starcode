# Retro: config-local-worktree

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | média | automatic checks | Achados 4 e 5 (recorrências L20, em 11 features, e L32, em 14): primeira feature com as lições no topo do brief e a linha do Q, e o C5 e o C6 ainda vieram com comparação parcial | Seguir a ação 3 da retro de licoes-no-brief: o `check_proofs`, ou um gate novo, recusa teste de texto gerado ou de seção de decisão sem comparação de igualdade |
| 2 | média | information access | Achado 3: o R3 dizia "nas três configs", e a config do repositório não tem modelo; o Picard escreveu a spec sem abrir o schema | Na spec, toda regra que vale "em todas as configs" cita os campos do schema (`validate_config.py`) que ela cobre |
| 3 | baixa | tool economy | A espera de 40 min do primeiro despacho expirou com o worker ainda rodando a suíte (25 min de trabalho), e foi preciso uma segunda espera | Usar `--timeout-ms 3000000` nas esperas de worker de MÉDIA, como já se faz no Q |
| 4 | baixa | automatic checks | O `fix-brief` funcionou na primeira correção real fora da própria feature: 5 achados, um commit por achado, nenhum marcador sem preencher | Nenhuma; manter |
