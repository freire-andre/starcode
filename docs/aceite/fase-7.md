# Aceite da Fase 7 (SC-72): Frota de workers

Roteiro: `docs/aceite/roteiros-fase-7/frota.md`. Executado em 2026-11-07 no `F:/Projetos/starcode-sandbox` (time PROJ, modo Git 2), com os scripts e as skills do ramo de integração `feature/fase-7-frota` (`dist/claude`, por caminho absoluto; a instalação do plugin não foi alterada). O Picard foi o worker T8 da Orca (nível 1) e despachou os LaForges do sandbox (nível 2): o aninhamento 2 funcionou, sem `nested_worker_depth_exceeded`.

Feature de fixture: `frota-aceite` (spec e tasks em `.specs/features/frota-aceite/` do sandbox, ramo `feature/frota-aceite`, 8 tickets PROJ-26 a PROJ-33). Dependências: T1, T2, T3 e T4 sem dependência; T4 com `**Runs alone**: yes` (lockfile); T5 (lento por desenho, quatro `sleep 60`) depende de T4; T6 (falha de propósito: o teste exigido fica fora do `May change`), T7 e T8 dependem de T5. Hash da base do ramo de integração: `87a054a`.

## Versões

| Item | Versão |
| --- | --- |
| StarCode | 1.0.0 (arquivo `VERSION` do ramo; a 1.1.0 está no CHANGELOG como não lançada); ramo `feature/fase-7-frota` em `b48d05e` |
| Orca | 1.4.251 |
| Claude Code | 2.1.319 |
| Codex | codex-cli 0.167.0 |
| OpenCode | v2.2.3 |
| Antigravity | tela do worker: Gemini 3.8 Flash (High); versão do CLI não consultada |

## Lote paralelo

**Resultado**: aprovado

- **Slug**: `frota-aceite`
- **IDs Linear**: T1=PROJ-26, T2=PROJ-27, T3=PROJ-28 (lote); T4=PROJ-29 a T8=PROJ-33 nos outros cenários.
- **Lote**: `dispatch.py batch frota-aceite --json` trouxe T1, T2, T3 em `batch` (`2× $$ + 1× grátis`) e, em `excluded`, T4 (`roda sozinho: Runs alone`) e T5 a T8 (`espera T4` / `espera T5`). Todos os ramos partiram de `feature/frota-aceite` (base `87a054a`).
- **Dispatch ids**: T1 `ctx_3602d633e418` (claude); T2 `ctx_3e8e1a0bda1c` (codex); T3 em OpenCode `ctx_bc174766da70` (mimo), `ctx_1188e28183ae` (deepseek) e `ctx_903c38605c15` (glm), os três sem trabalho por cota; T3 final `ctx_1cc367e936cd` (antigravity).
- **Modelos pedidos e efetivos**: T1 pedido e efetivo `claude:claude-sonnet-5-5`; T2 `codex:gpt-6-luna` (o recibo da Orca traz `model` igual ao pedido; sem confirmação à parte do efetivo); T3 pedido `opencode:opencode/mimo-v2.6-flash-free`, com `opencode/deepseek-v4.1-flash-free` e `opencode/glm-5.3-flash-free` como reservas: os três falharam com `Free limit reached` ("You've used today's free messages", reset 21:00Z, o worker terminou sem commit). Por decisão do usuário, T3 foi redespachado com `--assign T3=antigravity:gemini-3.8-flash-high`; modelo efetivo na tela do worker: Gemini 3.8 Flash (High). CLIs efetivos do lote: claude, codex e antigravity. Nenhum modelo pago foi usado.
- **Hashes**: base `87a054a`; commits dos tickets T1 `b3c7891`, T2 `153132f`, T3 em `freire-andre/feat-is-iso-date`; merges `2dbca53` (T1), `b4245ae` (T2) e `93d790f` (T3), um por vez, cada um com o `run_gates.py ticket` verde.
- **`check_scope`**: verde nos três tickets (0 erros, nenhum arquivo fora do `May change`), com o intervalo `<base do ticket>..<ramo do ticket>`; a suíte do sandbox passou com 62 testes depois do T3.
- **Falha isolada pela cota**: a falha do OpenCode não afetou T1 e T2, que foram integrados normalmente (achado 1).

## Lockfile

**Resultado**: aprovado

- **Ticket e IDs Linear**: T4, PROJ-29 (`package-lock.json`, `**Runs alone**: yes`).
- **`excluded` (`roda sozinho`)**: no primeiro `batch`, `{"ticket": "T4", "reason": "roda sozinho: Runs alone"}`. O texto traz `Runs alone` e não o padrão do arquivo (`package-lock.json`) que o roteiro cita (achado 2).
- **Lote seguinte**: com T1, T2 e T3 integrados e nenhum ticket ativo, o `batch` trouxe T4 sozinho (`claude:claude-sonnet-5-5`, `1× $$`), com T5 a T8 em `excluded` por dependência. Dispatch `ctx_a7e9761d1ea7`, base `93d790f`.
- **Hashes**: commit do ticket `dc46814`; merge `455b4d2`; `run_gates.py ticket` verde.

## Timeout

**Resultado**: aprovado

- **`fleet.timeoutMinutes` (teste e restaurado)**: o original não existia no config (padrão 30). Teste: 2. Restaurado: a chave removida e o arquivo copiado do backup; `sha256` `8041be17…97ffd` igual ao do original e `diff` vazio.
- **Dispatch id**: T5 (PROJ-30), `ctx_3d5aa3b9ec02`, `claude:claude-sonnet-5-5`, despachado em 2026-11-07T19:17:23Z, base `455b4d2`.
- **Saída do `overdue`**: depois de 2 min, `dispatch.py overdue frota-aceite` saiu com código 0 e imprimiu `T5 · PROJ-30 · 2 min · ctx_3d5aa3b9ec02`.
- **Comentário de bloqueio na issue PROJ-30**: `bloqueado: worker sem resposta após 2 min (dispatch ctx_3d5aa3b9ec02)` (o config do sandbox não tem estado `blocked`); a entrada de `**Dispatched:**` ficou com ` · blocked`.
- **O que aconteceu com o worker**: sem parada nem redespacho automáticos; o worker terminou o `sleep` e entregou `worker_done` com `outcome succeeded`, gate verde, commit `1c2485c`.
- **Hashes**: merge tardio `108ab8b` (gate do ticket verde).

## Falha isolada

**Resultado**: aprovado

- **Ticket com falha forçada e IDs Linear**: T6 (PROJ-31), `**May change**` só com `tarefas/extra.py` e prova C6 em `tests/test_extra.py`.
- **Dispatch ids dos outros tickets**: T6 `ctx_64b8d2522f82` (claude); T7 em Codex `ctx_0ccdb3010fbd` (parou no trust dos hooks: `agent-hooks-review-prompt`, só para esse ticket, sem tentativa contada; o trust é do usuário e não foi dado), redespachado em `claude:claude-sonnet-5-5` como `ctx_b1d6ebfb8f8c`; T8 `ctx_9864b2c4cb57` (antigravity:gemini-3.8-flash-high, por causa da cota do OpenCode). Base `108ab8b`.
- **Saída do T6**: `worker_done` com `outcome failed` ("C6 sem prova (teste fora do May change)"), commit `41868e6`. O `run_gates.py ticket` do T6 ficou verde (só `check_scope` e `check_commit`, que não rodam testes); a prova C6 ficou vermelha: a linha `test_answer_is_42 ... ok` não existe na branch (0 ocorrências). Tratado como falha: `--dispatch-remove T6`, `--attempt worker-T6=fail`, comentário em PROJ-31, não integrado (achado 3).
- **Ordem de chegada**: T6 (falha), T7, T8.
- **Integração dos outros (hashes)**: T7 `edf6244` → merge `5ca834a`; T8 → merge `4780187`; um merge por vez, com o gate do ticket verde. Suíte do sandbox: 66 testes OK.
- **Ticket de volta à fila**: T6 voltou à fila: o `batch` seguinte o traz sozinho (`T6 PROJ-31`, `claude:claude-sonnet-5-5`), sem redespacho automático (`**Attempts**` com `worker-T6=1`).

## Achados e pendências

Cada item abaixo pede código ou ajuste de roteiro e vira ticket próprio; nada foi corrigido neste ticket.

1. **Cota diária do OpenCode gratuito**: três modelos gratuitos esgotaram em sequência; o worker termina sem `worker_done` útil e o brief fica no campo de entrada. O Picard precisa tratar a cota (`Free limit reached`) como falha de worker e propor o par de reserva.
2. **Texto do `excluded`**: `roda sozinho: Runs alone` (`dispatch.py`); o roteiro cita `roda sozinho: <padrão>`. Alinhar roteiro ou script.
3. **Gate do ticket não prova testes**: `run_gates.py ticket` ficou verde com `outcome failed` e prova C6 inexistente; só o `proofs` pega a falta.
4. **`Refs:` na spec**: um commit com `Refs: <ID>` fora de um ticket faz o `dispatch.py` tratar esse ticket como integrado (erro de um commit de fixture, corrigido antes do despacho).
5. **Codex e trust**: o `worker-start` do T7 parou em `agent-hooks-review-prompt` depois de um T2 que tinha iniciado; o trust continua com o usuário.
6. **`tools/release.py`** não trata `não lançada` como não pronta (pendência já conhecida).
7. **Limpeza**: as issues PROJ-26 a PROJ-33 e os worktrees do sandbox ficam para o usuário decidir; T6 continua na fila.
