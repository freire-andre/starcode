# Roteiro do aceite da Frota (F7-T7)

Uma feature GRANDE de fixture no `F:/Projetos/starcode-sandbox`, time **PROJ**, **modo Git 2 ou 3** (o modo 1 não tem Frota). Quatro cenários, registrados em `docs/aceite/fase-7.md`. Use o Claude Code como Picard.

## Pré-requisitos

- **Orca**: aninhamento ≥ 2 (o Picard é worker e despacha workers). Sem isso o `worker-start` para com `nested_worker_depth_exceeded`; registre o valor.
- **Codex**: o **trust** (`/hooks`) é dado pelo usuário; o agente nunca o dá. Codex no Windows precisa da instrução de UTF-8 sem BOM no briefing.
- **OpenCode**: só modelos gratuitos (`opencode/*-free`). Nunca modelo pago.
- **Linear**: nada no time SC; só issues no time PROJ.
- `fleet.workers` no config do usuário: `["claude:claude-sonnet-5-5", "codex:gpt-6-luna", "opencode:opencode/mimo-v2.6-flash-free"]`. Para o lote (a), troque os pares na confirmação (`--assign`) conforme o cenário.

## Fixture

Feature GRANDE com pelo menos **5 tickets**:

1. **T1, T2, T3**: independentes, cada um com `May change` próprio, sem arquivo em comum.
2. **T4**: toca num lockfile (`package-lock.json` ou similar) e tem `**Runs alone**: yes`.
3. **T5**: falha de propósito (o gate do ticket não pode ficar verde, por exemplo um teste que exige o contrário do que o `May change` permite).

Gere com Troi, Spock e Data como no dia de missão da Fase 6 (`roteiros-fase-6/dia-de-missao.md`), publicando no time PROJ.

## Cuidados (lições das Fases 3–4)

- Depois de cada `worker-start`, confira `orca orchestration worker-show <dispatch>` com stage `input_accepted`; sem isso o briefing não chegou.
- Espere com `orca orchestration check --wait --types worker_done,question`.
- Codex no Windows: o briefing manda gravar arquivos em UTF-8 sem BOM.

## Cenários

### (a) Lote de 3 em 3 pares CLI:modelo diferentes

1. `python scripts/dispatch.py batch <slug> --json` deve trazer T1, T2, T3 em `batch` e T4, T5 fora com o motivo.
2. Pares pedidos: `claude:claude-sonnet-5-5`, `codex:gpt-6-luna` e um OpenCode **gratuito**: `opencode/mimo-v2.6-flash-free`, com `opencode/deepseek-v4.1-flash-free` e depois `opencode/glm-5.3-flash-free` como reservas, nessa ordem, se o limite gratuito estourar.
3. Todos os ramos partem de `feature/<slug>`; rode `check_scope` em cada um (verde, nenhum arquivo fora do `May change`).
4. Registre: slug, IDs Linear, dispatch id, modelo pedido e modelo efetivo (campo `model` do recibo e do `worker-show`), hash da base, hash de cada merge, resultado do `check_scope`.

### (b) Ticket do lockfile fora do lote

1. No `batch --json`, T4 aparece em `excluded` com `roda sozinho: <padrão>`.
2. Ele só roda quando não há nenhum ticket ativo, como lote de 1.
3. Registre: ID Linear de T4, o texto exato do `excluded`, o `batch` seguinte com T4 sozinho, hash do merge.

### (c) Worker que passa do timeout

1. No config do usuário do teste, reduza `fleet.timeoutMinutes` para 1 a 2 (anote o valor original).
2. Despache um ticket cujo worker demore mais que isso e espere o prazo.
3. `python scripts/dispatch.py overdue <slug>` lista o ticket (saída 0). O Picard avisa em uma linha e comenta na issue PROJ `bloqueado: worker sem resposta após <N> min (dispatch <id>)` (ou usa o estado `blocked` do config). Sem parada nem redespacho automáticos.
4. **Restaure** `fleet.timeoutMinutes` ao valor original e confira.
5. Registre: valores de `fleet.timeoutMinutes` (teste e restaurado), dispatch id, saída do `overdue`, texto do comentário de bloqueio, o que aconteceu com o worker, hash de qualquer merge tardio.

### (d) Falha forçada enquanto os outros são integrados

1. Despache T5 (falha de propósito) junto com tickets que passam.
2. T5 termina com `outcome failed` ou gate vermelho: `--dispatch-remove T5`, `--attempt worker-T5=fail` (ou `gate-T5=fail`), comentário com o motivo e T5 volta à fila.
3. Os outros tickets continuam e são integrados na chegada, um merge por vez.
4. Registre: dispatch ids de todos, a saída do gate vermelho de T5, a ordem de chegada, hashes dos merges dos outros, estado final de T5 na fila.

## O que registrar em cada cenário

Em `docs/aceite/fase-7.md`, por cenário: slug, IDs Linear, dispatch id de cada worker, modelo pedido e modelo efetivo, hash (base e merges) e `**Resultado**: aprovado` ou `reprovado (<passo>)`. Preencha também a tabela de versões (StarCode, Orca, CLIs). A prova C30 (teste de todos os cenários aprovados) é da T8; este roteiro só prepara o aceite.
