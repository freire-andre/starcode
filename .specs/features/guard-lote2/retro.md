# Retro: guard-lote2

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | Achado do Q (linha 25): `echo ok # <<EOF` escondia um `git reset --hard` real; corrigido em e077846 | O template breve de spec ganha, para hooks de segurança, um check de contorno: para cada parte do texto que o parser ignora, um teste com o marcador dentro de comentário e de aspas. Na SC-195 foi a isenção de host; aqui, o heredoc. |
| 2 | alta | instructions without effect | L2 voltou pela 14ª feature, L32 pela 9ª (C1, C3, C4, C5 e C8) | Mesma proposta das últimas retros: o esqueleto de `test_decisions_<slug>` e dos testes de cobertura por item vem pronto no brief do LaForge. |
| 3 | média | tool economy | Handoff da SC-195: na r1, o Worf achou 3 isenções depois do Q; aqui, o Picard sondou 34 e 30 entradas antes de integrar | O brief do LaForge para hooks de segurança pede uma sondagem de contornos (lista de entradas maliciosas) no próprio teste, não só no Picard. |
