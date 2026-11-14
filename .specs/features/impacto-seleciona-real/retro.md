# Retro: impacto-seleciona-real

Lições registradas: L38 e L39 (novas). Não foi possível registrar como recorrência de L37 e L34: o `lessons.py add` não aceita `--id`, e a recorrência só conta por texto idêntico (item N.1 da triagem).

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | instructions without effect | `verification.md` achados C7 e C8; mesmo tipo de achado em setup-grava-config (C4), snapshot-restauracao-segura (achado 3), q-familia-revendedor (C9) e despacho-media-escopo (C5): asserção por trecho ou termo faltando no teste | Implementar o N.1 (recorrência por ID no `lessons.py add`) e um helper de teste compartilhado para entradas do `DECISIONS.md` que receba a lista de termos exigidos pela spec; as lições por frase nova não estão mudando o comportamento. |
| 2 | média | automatic checks | Handoff: o comando de provas e `done` passou de 600 s com a suíte completa (882 testes) e foi para segundo plano | Separar um conjunto rápido para o ciclo de correção (item N.3) e deixar a suíte inteira só para `proofs` e o CI. |
| 3 | média | information access | Relatório do worker pós-Q: rodou `run_gates.py ticket` com base `72d7301~1`, que incluía o merge e os arquivos do Picard, e relatou erros falsos | O brief da correção pós-Q informa o intervalo exato do gate do ticket (`<commit da verificação>..HEAD`). |
