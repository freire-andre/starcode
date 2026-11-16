# Retro: piloto-freios

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | Achado R8 em `verification.md` (linha 28): `devolvido ao usuário` com `--categoria` sem `M<n>` gravava com exit 0; corrigido em 7896313 | Quando a spec cria uma exceção restrita (R7 isenta só do freio), o template breve pede um check que exercite o caso isento contra cada outra regra do mesmo comando. |
| 2 | alta | instructions without effect | L32 voltou nesta feature (5 features); achado C11 (linha 31) | Gerar o esqueleto do teste de entrada do `DECISIONS.md` (`test_decisions_<slug>`) com a asserção dos termos de cada requisito já no brief do LaForge, em vez de depender da lição. |
| 3 | média | automatic checks | Achados C6 e C7 (linhas 29-30): sucesso impresso sem conferir o `piloto.md` | O brief do LaForge, quando o requisito diz "SHALL gravar", lembra de asserir a entrada persistida (L50). |
| 4 | baixa | information access | Brief da Guinan desta feature listou à mão as lições fundidas no N.1 para evitar o erro de `ci-licoes-n1` da feature anterior | `lessons.py list` mostra "fundida em L<n>" nas repetidas, para o `--id` não depender de memória. |
