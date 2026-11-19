# Retro: fecha-achado

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | média | automatic checks | Achados 1 e 2 do `verification.md`: o T1 (`557a601`) aceitava `def test_x` dentro de string e ignorava linha de tabela sem pipe inicial; os casos de borda da spec não citavam esses dois formatos | No template da spec breve, pedir em `## Edge Cases` um caso de entrada que imita o formato válido sem ser (texto dentro de string, linha sem delimitador inicial) quando o requisito lê código ou Markdown |
| 2 | média | instructions without effect | Achados 3, 4 e 5 (recorrências L25, L20, L32): o teste do T1 cobria só um chamador da validação compartilhada, filtrava erros e conferia termos soltos na Decisão | Incluir no brief do LaForge as lições confirmadas com mais recorrência (L2, L20, L32, L25) como lista de conferência antes do commit |
| 3 | baixa | automatic checks | `65c39ef`: o `close-finding` fechou os 5 achados sem erro, e a evidência do Q com `&#124;` não quebrou a tabela (o `done --strict` passou sem ajuste manual) | Manter; acompanhar na próxima feature se o Q segue escrevendo `&#124;` sem lembrete extra no brief do Picard |
| 4 | baixa | automatic checks | O teste `test_done_acusa_celulas` ainda filtra os erros da tabela `## Checks` por "células" (só a de `## Findings` compara a lista inteira) | Na próxima mudança desse teste, comparar a lista inteira de erros também na tabela `## Checks` |
