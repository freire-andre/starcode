# Retro: versao-e-retro

**Feature**: versao-e-retro (SC-212, MÉDIA)
**Done**: `run_gates.py done --strict` verde em 45365c9
**Lições**: L20 (recorrência, achado 1), L88 (achado 2), L10 (recorrência, achado 3), L89 (achado 4) e L90 (achado 5)

| # | Severidade | Categoria | Evidência | Ação proposta | Estado |
|---|---|---|---|---|---|
| 1 | alta | information access | O LaForge parou porque um teste fora do May change comparava o fix-brief inteiro (`tests/test_licoes_no_brief.py`). O Picard ampliou o escopo em 953828a. É a segunda feature seguida com o mesmo padrão: na restauracao-e-telas, um helper de PNG ficou fora do escopo. | Antes de fechar o May change, a spec roda `grep -l` pelos textos que a mudança altera (aqui, o cabeçalho do brief) em `tests/` e inclui os arquivos achados. | aberto |
| 2 | média | automatic checks | Achado 2 do Q: dois dos quatro briefs não começavam pelo título (a318913). Nenhum teste anterior conferia a primeira linha dos briefs. | Um teste comum confere a estrutura de topo de todo brief gerado pelo `dispatch.py` (título, Plugin, Repositório), e não um teste por brief. | aberto |
| 3 | média | tool economy | A correção pós-Q foi integrada à mão de novo (43962a1). É a quinta feature seguida. | `dispatch.py settle` aceita a correção pós-Q, como nas retros de restauracao-e-telas e catalogo-e-orca. Esta já pode ser marcada com `retros.py estado` quando for feita. | aberto |
| 4 | baixa | information access | Um arquivo do usuário na raiz (`starcode-gargalo-e-plano-2026-11-21.md`) deixou a árvore suja, e o gate proofs reprovou. O Picard o acrescentou ao `.git/info/exclude`. | O `check_proofs` diz no erro que um arquivo não rastreado de fora do projeto pode ir para o `.git/info/exclude`, em vez de só apontar "árvore suja". | aberto |
