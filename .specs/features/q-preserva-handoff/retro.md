# Retro: q-preserva-handoff

Lições: L40 (nova, porcelain com renomeação) e L2 (recorrência, agora em 3 features).

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | Handoff, Reports: "Q parado: provas vermelhas ... Q despachado por engano e interrompido antes de escrever"; commit fdfef2e commitou um `proofs.md` vermelho e o Q foi despachado em seguida | O `dispatch.py q-brief` recusa (saída 2) quando o `proofs.md` da feature não está verde no HEAD, para que o Q nunca parta de provas vermelhas. |
| 2 | alta | instructions without effect | `verification.md` achados 2–4 (C4, C5, C6): asserções por trecho, de novo, apesar de L2 confirmada e citada no brief | Igual à retro de `guardas-add-commit-powershell`, item 1: aviso automático para `assertIn`/`startswith` em teste citado por check que fixa texto exato; L2 já está em 3 features. |
| 3 | média | spec precision | Commits 8daa42f e 7a47959 (May change ampliado duas vezes): `tests/test_skills_exec.py` e `tests/test_q_skill.py` afirmavam o texto antigo; a spec só citou `test_q_brief_fills_placeholders` | O Spock busca no repositório (`grep` em `tests/`) as asserções sobre o texto que a feature muda e lista cada teste que muda de sentido no Edge Cases e no May change. |
| 4 | média | automatic checks | Relatório do worker pós-Q: "não repeti a suíte completa inteira nem o run_gates ticket" | O brief da correção pós-Q exige a suíte completa e o gate do ticket, com a saída deles no relatório. |
