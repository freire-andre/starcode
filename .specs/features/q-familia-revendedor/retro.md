# Retro: q-familia-revendedor

Lições registradas: L31 e L32 (novas).

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | média | automatic checks | `verification.md` achado C7: R7 fixa 15 prefixos e o check citava só exemplos ("ex.: ...") | Quando o requisito fixa uma tabela, o check da spec lista todos os valores da tabela, nunca "ex.:", para o teste não poder cobrir só parte. |
| 2 | média | instructions without effect | `verification.md` achado C9; a mesma falha (entrada do DECISIONS.md conferida por palavras soltas) já apareceu na despacho-media-escopo (achado C5) | Um helper de teste compartilhado para as entradas do DECISIONS.md que exige, na seção Decisão, uma lista de termos por requisito, usado por todo check de "entrada da issue". |
| 3 | baixa | information access | `context.md`/`spec.md`: "não verificada" se o catálogo real traz `canonical_model_id` nos revendedores (sem cache nesta máquina) | Registrar no `.specs/stack/` um recorte do catálogo do models.dev com as entradas dos revendedores, para a próxima feature de família não depender de suposição. |
