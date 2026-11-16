# Retro: q-strategy

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | Achado C8 em `verification.md` (linha 27); Handoff: "prova de C8 trocada pelo Picard por teste de conteúdo" | O `validate_spec` passa a avisar quando um requisito que pede conteúdo de `DECISIONS.md` ou `CHANGELOG.md` tem como prova só `check_decisions.py`, que confere a data e não o conteúdo. A spec já deve sair com o teste de conteúdo. |
| 2 | alta | instructions without effect | L20 e L32 voltaram nesta feature (L20 em 6 features, L32 em 4); achados C4 e C8 | Pôr L20 e L32 como regras fixas no brief do LaForge, no bloco RULES, com o exemplo "saída integral com a quebra de linha" e "termos de cada requisito na seção Decisão". Hoje elas reaparecem mesmo promovidas. |
| 3 | média | automatic checks | Handoff: "C8 com prova no formato avulso (sem \| marcador)"; primeira rodada do `run_gates.py proofs` vermelha com exit 2 | O `validate_spec` passa a rejeitar `Proof: \`cmd\` \| marcador` (forma avulsa com marcador), ou o `check_proofs` passa a aceitar essa forma. Hoje o gate da spec aprova uma prova que o gate de provas não sabe ler. |
| 4 | média | information access | Achado C5 (linha 26): o critério R5 cita a saída e o exit do comando, e o teste cobria só `q_cli` | O template breve da spec (seção Checks) ganha uma linha: quando o critério cita stdout, stderr ou exit, a prova exercita o comando. |
| 5 | baixa | tool economy | Commit 66d55e0 (coluna Closed corrigida depois do gate done vermelho) | Um subcomando que fecha os achados (`handoff.py` ou `dispatch.py close-findings <slug> <sha>`) e preenche a coluna `Closed` sem edição manual da tabela. |
