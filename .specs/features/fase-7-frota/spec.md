# Fase 7: Modo Frota (v1.1): Spec

**Approved**: 2026-11-07 - user: "sim"

**Size**: LARGE
**Risk triggers**: Concorrência e estado (workers em paralelo, timeout, falha parcial, dono de arquivo)
**Status**: Approved

## Context

Hoje o Picard despacha os tickets de uma feature GRANDE um por vez (`references/execute.md`, seção 2). Por isso o tempo total é a soma dos tickets, mesmo quando eles não dividem arquivos. A seção 4.4 do plano define o Modo Frota: despachar em paralelo os tickets independentes, com estes limites:
- fronteira por dono de arquivo;
- arquivos sensíveis rodam sozinhos;
- lote máximo, com custo e confirmação;
- timeout vira bloqueio;
- cancelamento preserva o worktree;
- falha parcial fica isolada.

O `validate_tasks` já garante que tickets que podem rodar ao mesmo tempo não dividem arquivo e que ticket com arquivo sensível tem `**Runs alone**: yes` (`gc.paths_overlap`, `gc.is_sensitive`, `DEFAULT_SENSITIVE`). Falta o lado da execução: calcular o lote, despachar vários workers, acompanhar vários despachos abertos e tratar timeout, falha e cancelamento por ticket.

Discovery: `.specs/features/fase-7-frota/context.md`. Issue: SC-14.

## Scope

- `scripts/dispatch.py`:
  - subcomando `batch` (cálculo do lote, atribuição de CLI/modelo, faixa de custo);
  - subcomando `overdue` (despachos que passaram do timeout);
  - `next` e `q-cli` cientes de vários despachos e de várias famílias de LaForge.
- `scripts/handoff.py`: vários despachos abertos em `**Dispatched:**`, com adicionar e remover por ticket.
- `scripts/config/validate_config.py` e `schemas/config.md`: chave `fleet.workers` no config do usuário.
- `src/crew.yaml`: mapa `costTiers` (modelo → faixa) e regra para modelos gratuitos.
- `scripts/crew_live.py`: `set laforge <n>` com a contagem de workers ativos (0–10).
- `src/skills/engajar/references/execute.md` (nova seção Frota) e `src/skills/engajar/SKILL.md` (passo 5b): fluxo do lote, confirmação, espera, timeout, falha, cancelamento.
- `skills/setup`: menção a `fleet.workers` junto das chaves `fleet.*` que já existem.
- Testes `unittest` dos itens acima.
- `DECISIONS.md` (F7-n), `CHANGELOG.md` (seção da 1.1.0, ainda não lançada), `dist/` regenerado.
- Aceite real em `docs/aceite/fase-7.md` (sandbox, time PROJ).

## Non-Goals

- Painel "Ponte" (Fase 10), Uhura, Scotty, Kirk, Worf e Guinan (Fases 8–9).
- Relançamento automático de worker, e `worker-stop`/`worker-abandon` sem confirmação.
- Merge automático em `main`, e paralelismo entre features diferentes.
- Frota no modo Git 1.
- Mudar as regras do `validate_tasks` (fronteira e `Runs alone` já existem) ou o fluxo do Q além da escolha da família.
- Tag/release da v1.1.0: fica para quando a fase for aceita, com confirmação própria.

## Requirements

### Lote (fronteira e limites)

- **R1** - WHEN `python dispatch.py batch <slug>` roda THEN the system SHALL escolher como candidatos os tickets de `tasks.md` que satisfazem tudo isto:
  - não estão integrados em `feature/<slug>` (mesma evidência do Git que o `next` usa);
  - não estão ativos em `**Dispatched:**`;
  - têm todas as dependências (`Depends on`) integradas.
- **R2** - The system SHALL montar o lote percorrendo os candidatos na ordem de `tasks.md` e acrescentar um ticket só se nenhum caminho do `May change` dele se sobrepõe (`gc.paths_overlap`) a um caminho de um ticket ativo ou de um ticket já escolhido no lote.
- **R3** - IF um candidato tem `**Runs alone**: yes` ou um caminho sensível (`gc.is_sensitive` com `DEFAULT_SENSITIVE` + `sensitiveFiles` do repo) THEN the system SHALL deixá-lo fora de qualquer lote com outros tickets, com o motivo `roda sozinho: <padrão>`. Ele forma um lote de 1 só quando não há nenhum ticket ativo e ele é o primeiro candidato.
- **R4** - The system SHALL limitar o lote a `fleet.maxBatch` do config do usuário (padrão 3) menos o número de tickets ativos. Com resultado ≤ 0, o lote fica vazio e o motivo é `limite de N workers ativos`.
- **R5** - The system SHALL imprimir, com `--json`, um objeto com `batch` (lista de `{ticket, linear, title, cli, model, cost}`), `costTotal`, `excluded` (lista de `{ticket, reason}`) e `active` (tickets ativos). Cada candidato fora do lote aparece em `excluded` com um destes motivos:
  - `espera <Tn>`;
  - `arquivo em comum com <Tn>: <caminho>`;
  - `roda sozinho: <padrão>`;
  - `limite de N workers ativos`.
- **R6** - The system SHALL sair com 0 quando o lote tem 1 ou mais tickets, 1 quando está vazio e 2 em erro de uso ou de leitura (tasks.md ausente, config inválido).
- **R7** - IF um ticket não tem caminhos em `May change` THEN the system SHALL excluí-lo com o motivo `sem May change`. Ele nunca entra em lote.

### CLI/modelo e custo

- **R8** - The system SHALL aceitar no config do usuário a chave `fleet.workers`: uma lista de 1 a 10 strings únicas no formato `<cli>:<model>`, com `<cli>` em `claude`, `codex`, `antigravity`, `opencode` e `<model>` não vazio. Valor fora disso é erro do `validate_config` com o caminho da chave.
- **R9** - WHEN `fleet.workers` existe THEN `batch` SHALL atribuir os workers aos tickets do lote em rodízio, na ordem da lista, começando depois do último par usado pelos tickets ativos. WHEN `fleet.workers` não existe THEN `batch` SHALL usar o CLI e o modelo efetivos do LaForge (sessão > config do usuário > `crew.yaml`) para todos.
- **R10** - WHEN `batch` recebe `--assign <Tn>=<cli>:<model>` (pode repetir) THEN the system SHALL usar esse par para o ticket. Isso permite a troca pedida na confirmação. Um par inválido segue as regras de R8 e sai com código 2.
- **R11** - The system SHALL atribuir a faixa de custo de cada ticket assim:
  - pelo mapa `costTiers` do `crew.yaml` (valores `grátis`, `$`, `$$`, `$$$`);
  - modelo com sufixo `:free` ou `-free` sem entrada no mapa → `grátis`;
  - modelo sem entrada e sem sufixo → `?` ("faixa desconhecida").

  Nunca se mostra preço em moeda.
- **R12** - The system SHALL calcular `costTotal` como a contagem de tickets por faixa, por exemplo `2× $$ + 1× grátis`. Sem faixa conhecida, o total é `1× ?`.

### Despacho e registro

- **R13** - WHEN o Picard chega ao passo de despacho com o modo Git 2, 3 ou 4 e `batch` devolve 2 ou mais tickets THEN the system SHALL mostrar o lote numa só mensagem e pedir uma confirmação: uma linha por ticket (ticket, issue, CLI, modelo, faixa), a faixa total e os excluídos com o motivo. A resposta pode trocar pares, o que gera `--assign`. WHEN `batch` devolve 1 ticket THEN o Picard SHALL seguir o fluxo sequencial da Fase 3, sem pergunta.
- **R14** - The system SHALL registrar cada ticket do lote no Handoff **antes** de iniciar o worker dele, com `python handoff.py set <slug> --dispatch-add "<Tn> · <ID> · base <sha> · <cli>:<model> · <ISO-8601 UTC>"`. Depois do `worker-start`, completa a mesma entrada com o dispatch id e o modelo do recibo (`--dispatch-add` com o mesmo `<Tn>` substitui a entrada).
- **R15** - The system SHALL guardar em `**Dispatched:**` várias entradas separadas por `; `, uma por ticket ativo, ou `none` quando não houver nenhuma. `--dispatch-remove <Tn>` tira só a entrada daquele ticket. `--dispatched` continua substituindo o campo inteiro (compatibilidade com o fluxo sequencial).
- **R16** - The system SHALL iniciar cada worker do lote com `orca orchestration worker-start ... --base-branch feature/<slug> --spec-file <brief>`, e com `--worktree new-child` (ou um worktree criado antes, para OpenCode, como no sequencial). Depois vincula cada worktree à issue com `orca worktree set --linear-issue`. O `--deps` não é usado, porque todo ticket do lote já tem as dependências integradas (R1).
- **R17** - IF o `worker-start` de um ticket falha (trust do Codex, limite de aninhamento, CLI indisponível) THEN the system SHALL tirar esse ticket do Handoff com `--dispatch-remove`, relatar o motivo dele numa linha e manter os workers já iniciados.
- **R18** - WHILE há tickets ativos, the system SHALL manter `.starcode/live/crew.json` com `laforge` igual ao número de entradas em `**Dispatched:**`, via `crew_live.py set laforge <n>` (0 a 10).
- **R19** - `next` SHALL continuar devolvendo exit 3 com uma ou mais entradas abertas em `**Dispatched:**` que ainda não estão integradas. O fluxo sequencial não muda.

### Espera, integração, timeout, falha e cancelamento

- **R20** - WHILE há tickets ativos, the system SHALL esperar com `orca orchestration check --wait --types worker_done,question --timeout-ms <ms até o prazo mais próximo>`. O prazo de cada ticket é o horário do despacho somado a `fleet.timeoutMinutes` (padrão 30). O `--timeout-ms` do `worker-start` só limita a espera pelo início do worker, não a duração do trabalho.
- **R21** - WHEN chega um `worker_done` com sucesso THEN the system SHALL integrar só aquele ticket, um merge por vez: `run_gates.py ticket` seguido de `git merge --no-ff` em `feature/<slug>`. Depois roda `--dispatch-remove <Tn>`, `--last-integrated <sha>`, `crew_live.py progress` e comenta "integrado" na issue. Os outros workers seguem rodando.
- **R22** - WHEN `python dispatch.py overdue <slug> [--minutes N]` roda THEN the system SHALL listar, um por linha, os tickets de `**Dispatched:**` cujo horário de despacho + N minutos (padrão `fleet.timeoutMinutes`) já passou. Sai com 0 quando há algum atrasado e 1 quando não há.
- **R23** - WHEN um ticket fica atrasado (R22) THEN the system SHALL:
  - mover a issue para o estado `blocked` do config do repositório; se ele for `null`, comentar na issue `bloqueado: worker sem resposta após <N> min (dispatch <id>)`;
  - avisar o usuário numa linha;
  - manter o ticket em `**Dispatched:**` com o sufixo ` · blocked`, porque os arquivos dele continuam reservados.

  Não há `worker-stop`, `worker-abandon` nem novo despacho automático.
- **R24** - WHEN o usuário confirma o cancelamento de um ticket ativo ou bloqueado THEN the system SHALL rodar `orca orchestration worker-stop --dispatch <id>`, `--dispatch-remove <Tn>` e comentar `cancelado; worktree preservado: <caminho>` na issue. O worktree só é removido com outra confirmação.
- **R25** - IF um worker termina com falha (outcome failed, sem relatório, ou gates do ticket vermelhos) THEN the system SHALL tirar o ticket de `**Dispatched:**`, contar `--attempt worker-<Tn>=fail` (ou `gate-<Tn>`), comentar o motivo na issue e devolver o ticket à fila. Os outros workers do lote seguem rodando, e os tickets que dependem dele continuam fora de qualquer lote até ele ser integrado.
- **R26** - IF o merge de um ticket em `feature/<slug>` dá conflito THEN the system SHALL rodar `git merge --abort`, deixar `feature/<slug>` no commit anterior, devolver o ticket à fila com a lista de arquivos em conflito e continuar com os outros workers. O resumo do fim do lote mostra o conflito com as opções da Fase 3 (redespachar sobre `feature/<slug>` ou repensar o corte).
- **R27** - WHEN não há ticket ativo e `batch` devolve um lote novo THEN the system SHALL repetir R13. Quando todos os tickets estão integrados, segue para as provas e o Q da Fase 3.
- **R28** - IF o modo Git é 1 THEN the system SHALL não usar o Modo Frota, avisar numa linha `Frota indisponível no modo 1 (um só worktree)` e seguir sequencial.

### Q

- **R29** - WHEN o Picard escolhe o CLI do Q depois de uma feature com tickets de CLIs/modelos diferentes THEN `dispatch.py q-cli` SHALL aceitar `--laforge` repetido e escolher, na ordem já existente (`codex` → `antigravity` → `opencode`), o primeiro CLI cuja família difere de **todas** as famílias de LaForge informadas. IF nenhum serve THEN the system SHALL devolver `self-verified` e o Picard registra `**Verification:** degraded`.

### Aceite e registros

- **R30** - The system SHALL registrar em `docs/aceite/fase-7.md` um aceite real no `starcode-sandbox` (time PROJ, modo Git 2 ou 3). O aceite cobre:
  - um lote de 3 tickets em paralelo em 3 pares CLI:modelo diferentes, todos com base em `feature/<slug>`, com `check_scope` verde em cada um (nenhum arquivo fora do `May change`);
  - um ticket com lockfile excluído do lote com `roda sozinho`;
  - um worker que passa do timeout (`fleet.timeoutMinutes` reduzido para o teste) e vira bloqueio no Linear;
  - um ticket com falha forçada enquanto os outros são integrados.

  Para cada cenário: slug, IDs Linear, dispatch ids, modelos pedidos e efetivos, hashes e o resultado (aprovado ou reprovado).
- **R31** - The system SHALL registrar em `DECISIONS.md`:
  - as decisões F7-n desta fase (pool `fleet.workers`, faixa de custo relativa, integração na chegada, oferta por lote, timeout pela espera e não pelo `worker-start`, sem `--deps`);
  - uma seção `## [1.1.0] - não lançada` no `CHANGELOG.md`.

## Data & Contracts

- **`fleet.workers`** (config do usuário): `["claude:claude-sonnet-5-5", "codex:gpt-6-luna", "opencode:opencode/mimo-v2.6-flash-free"]`. O `schemas/config.md` ganha a linha da chave.
- **`costTiers`** (`src/crew.yaml`, raiz): `{claude-opus-5-5: "$$$", claude-sonnet-5-5: "$$", claude-haiku-5-5: "$", gpt-6-luna: "$$", gemini-3.8-flash-high: "$", ...}`. Os valores são declarados pelo dono do repositório. Mudar um valor não muda nenhuma regra.
- **`dispatch.py batch <slug> [--branch feature/<slug>] [--base <ref>] [--assign Tn=cli:model]... [--json]`**: saída de R5. Sem `--json`, uma linha por ticket do lote, depois a linha `total: <costTotal>`, depois uma linha por excluído.
- **`dispatch.py overdue <slug> [--minutes N] [--now <ISO>]`**: o `--now` existe para teste.
- **`dispatch.py q-cli --laforge <cli:model> [--laforge ...]`**: o argumento posicional antigo continua aceito.
- **Entrada de `**Dispatched:**`**: `<Tn> · <ID> · base <sha7> · <cli>:<model> · <ISO-8601 UTC>[ · <dispatch id>][ · model <recibo>][ · blocked]`, separadas por `; `.
- **`handoff.py set`**: novas opções `--dispatch-add "<entrada>"` (substitui a entrada do mesmo `<Tn>` ou acrescenta) e `--dispatch-remove <Tn>`. As duas podem vir na mesma chamada que as outras opções.
- **`crew_live.py set laforge <n>`**: `n` de 0 a 10. Os outros tripulantes continuam 0/1.

## States

- **Ticket:** na fila → ativo (entrada gravada antes do `worker-start`) → integrado | falhou (volta à fila) | bloqueado (timeout, arquivos reservados) | cancelado (worktree preservado, volta à fila).
- **Lote:** vazio (exit 1: todos integrados, todos esperando ou limite atingido) | 1 ticket (sequencial) | 2 a N tickets (confirmação).
- **Falha parcial:** um lote com tickets integrados, falhos e bloqueados ao mesmo tempo é um estado válido. O resumo do fim do lote lista cada um.

## Edge Cases

- **Sessão interrompida com o lote em andamento:** na retomada, o Picard lê as entradas de `**Dispatched:**` e confere cada dispatch id com `worker-show`, porque a evidência do Git vence a anotação. Ticket já integrado sai da lista.
- **Dois `worker_done` quase ao mesmo tempo:** a integração é serial. O segundo espera o merge do primeiro terminar.
- **Ticket com arquivo fora do `May change`:** o `check_scope` (gate do ticket) fica vermelho e o caso segue R25. Nunca é integrado.
- **Pool com mais pares que tickets:** sobram pares, sem erro. Pool com menos: o rodízio repete pares.
- **`fleet.maxBatch` = 1:** todo lote tem 1 ticket, e o fluxo fica idêntico ao sequencial.
- **Timeout com o worker vivo e terminando depois:** o `worker_done` tardio de um ticket `· blocked` é integrado normalmente (R21). A issue volta para `started` e recebe um comentário.
- **Relógio:** os horários do Handoff ficam em UTC. `overdue` compara com o UTC atual.
- **Codex sem trust dos hooks:** R17 vale só para aquele ticket. A orientação de `/hooks` da Fase 3 aparece uma vez.

## Decisions

| Item | Options | Status |
|---|---|---|
| CLI/modelo por ticket | pool `fleet.workers` no config + troca na confirmação · campo `Agent:` no ticket · só na confirmação | approved - user: "Pool no config + troca (Recommended)" |
| Estimativa de custo | faixa relativa por modelo · tokens estimados · preço em US$ | approved - user: "Faixa relativa (Recommended)" |
| Momento da integração | assim que cada worker termina · no fim do lote | approved - user: "Assim que termina (Recommended)" |
| Ativação | oferta a cada lote com ≥2 elegíveis · opt-in por feature · sempre que elegível | approved - user: "Oferta a cada lote (Recommended)" |

## Open Questions
None.

## Sources

- PLANO_STARCODE.md, seção 4.4 (limites da Frota) e Fase 7 (aceite): binding.
- Orca 1.4.251, `orca orchestration worker-start --help`, `check --help` e o guia `orca skills get orchestration --full` ("a startup timeout ... never proves exit"): binding para os comandos usados.

## Differences from the Source

- **Timeout:** a 4.4 diz que "o `--timeout-ms` da Orca encerra a espera". Na Orca 1.4.251, o `--timeout-ms` do `worker-start` é a espera pelo início do worker. Por isso o timeout do trabalho usa o `--timeout-ms` do `check --wait` e o prazo gravado no Handoff (R20, R22). O comportamento visível é o mesmo: o worker parado vira bloqueio, sem relançar.
- **`--deps`:** a 4.4 manda derivar `--deps` das relações `blocks`. Aqui um ticket só entra no lote com as dependências já integradas (R1), então o `--deps` não teria efeito e não é usado (R16).
