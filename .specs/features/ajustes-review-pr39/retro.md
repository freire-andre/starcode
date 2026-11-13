# Retro: ajustes-review-pr39

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | Spec citou `scripts/gate_common.py`, mas o módulo existente era `gates_common.py`; o worker criou um módulo novo e o usuário aprovou a mudança para `gates_common.py` (b6c6fbe). | Antes da aprovação da spec, validar que todo caminho de módulo citado existe no repositório (check no gate da spec). |
| 2 | alta | automatic checks | Q deu FAIL com 2 achados de prova fraca: C2 não exercitava o gate das tasks (verification.md, achado 1) e C8 aceitava qualquer texto com fragmentos do contrato (achado 2). Fechados em 22e7907 e 2b4d7e1. | Exigir, para cada check de regra compartilhada ou de contrato de skill, uma verificação que falhe ao quebrar a regra (mutação ou asserção do texto completo) antes de marcar o check como coberto. |
| 3 | média | automatic checks | verification.md, seção Limits: nenhum check cobre o `-` na linha de aviso de exit 3 quando o recibo vem sem dispatch id. | Acrescentar um check dedicado para o recibo sem dispatch id, ou registrar esse caso como lacuna explícita na spec. |
| 4 | baixa | tool economy | verification.md, seção Limits: suíte completa com 767 testes levou 343,9 s, o que desestimula rodar a suíte inteira a cada ajuste de gate. | Separar um subconjunto rápido (gates e skills) para o ciclo de TDD, mantendo a suíte completa para o gate final. |
