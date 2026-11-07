# Fase 7: Modo Frota (v1.1): Tasks

**Approved**: 2026-11-07 - user: "sim"

**Spec**: `.specs/features/fase-7-frota/spec.md`
**Status**: Approved
**Integration branch**: `feature/fase-7-frota`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only, no generator change | `python -m unittest discover -s tests -v` |
| full | task that changes `skills/`, `scripts/`, `hooks/`, `src/`, `schemas/` or `tools/build.py` (F3-1: `dist/` regenerated in the same commit) | `python tools/build.py && python tools/build.py --check && python -m unittest discover -s tests -v` |
| build | records task, or after the last code task | `python tools/build.py && python tools/build.py --check && claude plugin validate dist/claude --strict && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |

## Tasks

### T1: Handoff com vários despachos abertos
**Linear**: SC-73
**Depends on**: none
**Requirements**: R14, R15
**Tests**: unit
**Gate**: full

#### TASK
Em `scripts/handoff.py`, acrescentar ao subcomando `set` duas opções:
- `--dispatch-add "<entrada>"`: a entrada começa com `<Tn>` (ex.: `T2 · PROJ-8 · base abc1234 · claude:claude-sonnet-5-5 · 2026-11-07T16:40:00Z`). Se `**Dispatched:**` já tem uma entrada do mesmo `<Tn>`, ela é substituída na mesma posição; senão, é acrescentada ao fim. Com o campo em `none`, a entrada vira o único valor.
- `--dispatch-remove <Tn>`: tira só a entrada daquele ticket; sem entradas restantes, o campo volta a `none`. Remover um ticket ausente não é erro (imprime que não havia entrada).

As entradas ficam separadas por `; ` numa única linha `**Dispatched:**`. `--dispatched` continua substituindo o campo inteiro. As duas novas opções podem vir junto com as demais (`--report`, `--attempt`, `--last-integrated`) na mesma chamada. Atualize a docstring do módulo.

Testes em `tests/test_handoff.py`. Regenere o `dist/` (`python tools/build.py`).

#### CONTEXT
Spec: `.specs/features/fase-7-frota/spec.md` (R14, R15; contrato em Data & Contracts). Checks: C14, C15.
Hoje `FIELDS` em `scripts/handoff.py` tem `("dispatched", "Dispatched", "none")`, um valor só, e o `dispatch.py next` lê esse campo para sair com código 3. Os testes existentes de `handoff.py` mostram como criar uma feature temporária com `context.md`/`tasks.md`.

#### BOUNDARIES
May change: `scripts/handoff.py`, `tests/test_handoff.py`, `dist/`
Do not touch: `scripts/dispatch.py`, `scripts/crew_live.py`, `skills/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T2: fleet.workers, faixas de custo e contagem de LaForges ativos
**Linear**: SC-74
**Depends on**: T1
**Requirements**: R8, R11, R18
**Tests**: unit
**Gate**: full

#### TASK
- `scripts/config/validate_config.py`: no objeto `fleet` do config do usuário, a chave `workers`. É uma lista de 1 a 10 strings únicas no formato `<cli>:<model>`, com `<cli>` em `claude`, `codex`, `antigravity`, `opencode` e `<model>` não vazio. O modelo pode conter `/` e `:`, como em `opencode:openrouter/nvidia/x:free`; separe só no primeiro `:`. O erro cita o caminho `fleet.workers[<i>]`.
- `schemas/config.md`: linha de `fleet.workers` na tabela do config do usuário e no exemplo JSON.
- `src/crew.yaml`: mapa de raiz `costTiers` (modelo → `grátis`, `$`, `$$` ou `$$$`) para os modelos de `families`: opus `$$$`; sonnet e gpt-6-luna `$$`; haiku e gemini-3.8-flash-* `$`. Comentário: valores declarados pelo dono do repositório, sem preço.
- Uma função `cost_tier(model, tiers)` num lugar que o `dispatch.py` possa importar (`scripts/starcode_common.py`):
  - devolve o valor do mapa;
  - senão, `grátis` para sufixo `:free` ou `-free`;
  - senão, `?`.
- `tools/build.py` deve levar `costTiers` para o `crew.json` gerado, se ainda não levar o mapa inteiro.
- `scripts/crew_live.py`: `set laforge <n>` aceita de 0 a 10. Os outros membros continuam 0/1, e valores fora disso dão erro de uso com código 2.

Testes em `tests/test_validate_config.py`, `tests/test_crew_live.py` e `tests/test_build.py`. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-7-frota/spec.md` (R8, R11, R18). Checks: C8, C11, C18.
`fleet.maxBatch` e `fleet.timeoutMinutes` já existem em `validate_config.py` (linha ~57). O `crew.json` gerado vem de `src/crew.yaml` via `tools/build.py` e `tools/miniyaml.py` (subconjunto: sem âncoras nem strings multilinha). `crew_live.set_status` grava `.starcode/live/crew.json` (F6-7).

#### BOUNDARIES
May change: `scripts/config/validate_config.py`, `schemas/config.md`, `src/crew.yaml`, `scripts/starcode_common.py`, `scripts/crew_live.py`, `tools/build.py`, `tests/test_validate_config.py`, `tests/test_crew_live.py`, `tests/test_build.py`, `dist/`
Do not touch: `scripts/dispatch.py`, `scripts/handoff.py`, `skills/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T3: dispatch.py batch: lote, atribuição e custo
**Linear**: SC-75
**Depends on**: T2
**Requirements**: R1, R2, R3, R4, R5, R6, R7, R9, R10, R12
**Tests**: unit
**Gate**: full

#### TASK
Novo subcomando em `scripts/dispatch.py`:

    dispatch.py batch <slug> [--branch feature/<slug>] [--base <ref>] [--assign Tn=cli:model]... [--json]

1. **Candidatos (R1):** os tickets que satisfazem as três condições:
   - não integrados (reuse `integrated()`);
   - não ativos (entradas de `**Dispatched:**` separadas por `; `, lidas com `handoff_values`);
   - com todos os `Depends on` integrados.

   Os demais saem como `espera <Tn>`.
2. **Ordem e fronteira (R2):** percorra os candidatos na ordem de `tasks.md`. Um ticket entra no lote se nenhum caminho do `May change` dele se sobrepõe (`gc.paths_overlap`) a um ticket ativo ou a um já escolhido. Os ativos são os tickets das entradas abertas, com o `May change` lido do `tasks.md`. Sobreposição → `arquivo em comum com <Tn>: <caminho>`.
3. **Sensível (R3):** com `**Runs alone**: yes`, ou com caminho em `gc.is_sensitive(p, gc.sensitive_patterns(root))`, o ticket fica fora (`roda sozinho: <padrão ou "Runs alone">`). A exceção é quando não há ativos e ele é o primeiro candidato: aí o lote é só ele.
4. **Sem May change (R7):** o ticket fica fora com `sem May change`.
5. **Limite (R4):** `fleet.maxBatch` do config do usuário (padrão 3) menos os ativos. Os candidatos que sobram saem como `limite de N workers ativos`.
6. **Atribuição (R9, R10):**
   - com `fleet.workers` no config do usuário, rodízio na ordem da lista, começando depois do último par usado pelas entradas ativas (o par é o 4º campo da entrada);
   - sem `fleet.workers`, o LaForge efetivo (config do usuário `crew.laforge` > `crew.yaml`);
   - `--assign` sobrepõe; par inválido → código 2 com a mesma regra do `validate_config`.
7. **Custo (R11, R12):** `cost` por ticket via `cost_tier` (T2) com `costTiers`, e `costTotal` como `2× $$ + 1× grátis`, em ordem `$$$`, `$$`, `$`, `grátis`, `?`.
8. **Saída (R5, R6):** com `--json`, `{batch:[{ticket,linear,title,cli,model,cost}], costTotal, excluded:[{ticket,reason}], active:[...]}`; sem `--json`, uma linha por ticket, `total: ...` e uma linha por excluído. Exit 0 com lote ≥1, 1 com lote vazio, 2 em erro de uso ou leitura.

Testes em `tests/test_dispatch.py`, com repositório Git temporário e `tasks.md` de fixture. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-7-frota/spec.md` (R1–R7, R9, R10, R12; contrato em Data & Contracts). Checks: C1–C7, C9, C10, C12.
- `next_ticket()` já tem a lógica de integração pelo Git (`Refs:` ou `integra T<n>`) e de dependências.
- `validate_tasks.Task` tem `may_change`, `deps` e `runs_alone`.
- `gates_common` tem `paths_overlap`, `is_sensitive` e `sensitive_patterns`.
- Config do usuário: `sc.load_user_config` ou equivalente em `scripts/starcode_common.py` (`STARCODE_HOME` muda a pasta nos testes).
- O formato da entrada de `**Dispatched:**` está em Data & Contracts e vem da T1.

#### BOUNDARIES
May change: `scripts/dispatch.py`, `tests/test_dispatch.py`, `dist/`
Do not touch: `scripts/handoff.py`, `scripts/starcode_common.py`, `scripts/gates/`, `skills/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T4: dispatch.py overdue, next com vários despachos e q-cli com várias famílias
**Linear**: SC-76
**Depends on**: T3
**Requirements**: R19, R22, R29
**Tests**: unit
**Gate**: full

#### TASK
Em `scripts/dispatch.py`:
- **`next` (R19):** com várias entradas em `**Dispatched:**`, sai com 3 se alguma delas ainda não está integrada, e cita todas as abertas na mensagem. Com todas integradas, segue normalmente.
- **`overdue <slug> [--minutes N] [--now <ISO-8601>]` (R22):**
  - lista uma linha por entrada ativa cujo horário (5º campo, UTC) + N minutos já passou: `<Tn> · <ID> · <minutos> min · <dispatch id ou ->`;
  - N tem padrão `fleet.timeoutMinutes` do config do usuário (30 se ausente), e `--now` serve para teste;
  - exit 0 com algum atrasado, 1 sem nenhum, 2 com uma entrada sem horário legível (cita a entrada).
- **`q-cli` (R29):** aceita `--laforge <cli:model>` repetido, além do posicional antigo. Escolhe, na ordem `Q_CLI_ORDER`, o primeiro CLI cuja família difere de todas as famílias informadas e cujo worker está disponível (regras atuais). Sem nenhum, devolve `self-verified`.

Atualize a docstring do módulo. Testes em `tests/test_dispatch.py`. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-7-frota/spec.md` (R19, R22, R29). Checks: C19, C22, C29.
`q_cli()` e `family()` já existem. A T3 deixou o parser das entradas de `**Dispatched:**` em `dispatch.py`: reuse-o.

#### BOUNDARIES
May change: `scripts/dispatch.py`, `tests/test_dispatch.py`, `dist/`
Do not touch: `scripts/handoff.py`, `scripts/gates/`, `skills/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T5: Fluxo da Frota no Picard (execute.md, engajar e setup)
**Linear**: SC-77
**Depends on**: T4
**Requirements**: R13, R16, R17, R20, R21, R23, R24, R25, R26, R27, R28
**Tests**: unit
**Gate**: full

#### TASK
- **`skills/engajar/references/execute.md`:** nova seção `## 2F. Fleet (v1.1)` entre a 2 e a 3, em inglês como o resto do arquivo. A seção 2 passa a dizer que o lote vem primeiro. Ela descreve:
  - **R13:** `dispatch.py batch <slug> --json`. Com ≥2 tickets: uma mensagem com uma linha por ticket (ticket, issue, CLI, modelo, faixa), o total e os excluídos com o motivo, mais uma confirmação; trocas viram `--assign`. Com 1 ticket: seção 2 sem pergunta. Exit 1: seção 4 ou espera.
  - **R16:** por ticket, nesta ordem:
    - `handoff.py set --dispatch-add` antes do `worker-start`;
    - `worker-start --base-branch feature/<slug> --spec-file ... --worktree new-child` (OpenCode: worktree criado antes);
    - `--dispatch-add` de novo, com o dispatch id e o modelo do recibo;
    - `orca worktree set --linear-issue`;
    - sem `--deps`, com a razão.
  - **R17:** falha do `worker-start` de um ticket: `--dispatch-remove`, uma linha de motivo, os outros seguem. A parada de trust do Codex e a de aninhamento valem só para aquele ticket.
  - **R18:** `crew_live.py set laforge <n>` com o número de entradas, a cada mudança.
  - **R20:** espera com `orca orchestration check --wait --types worker_done,question --timeout-ms <ms até o prazo mais próximo>`. O prazo é o despacho + `fleet.timeoutMinutes`. O `--timeout-ms` do `worker-start` é só a espera pelo início.
  - **R21:** `worker_done` com sucesso: `run_gates.py ticket` e `merge --no-ff`, um merge por vez, e depois `--dispatch-remove`, `--last-integrated`, `crew_live.py progress` e o comentário na issue. Os outros seguem.
  - **R23:** `dispatch.py overdue`: estado `blocked` do config, ou comentário `bloqueado: worker sem resposta após <N> min (dispatch <id>)`. O aviso tem uma linha. A entrada fica com ` · blocked`. Sem stop, abandon nem redespacho automáticos. Um `worker_done` tardio é integrado e a issue volta a `started`.
  - **R24:** cancelamento só com confirmação: `worker-stop --dispatch <id>`, `--dispatch-remove`, o comentário `cancelado; worktree preservado: <caminho>` e remoção do worktree só com outra confirmação.
  - **R25:** falha (outcome failed, sem relatório, gate vermelho): `--dispatch-remove`, `--attempt worker-<Tn>=fail` ou `gate-<Tn>`, comentário, o ticket volta à fila. Os outros seguem e os dependentes ficam fora.
  - **R26:** conflito: `git merge --abort`, o ticket volta à fila com os arquivos, os outros seguem. O resumo do fim do lote dá as opções da seção 3.
  - **R27:** sem ativos → novo `batch`. Todos integrados → seção 4.
  - **R28:** modo Git 1: `Frota indisponível no modo 1 (um só worktree)` e seção 7.
  - **Retomada:** conferir cada entrada com `worker-show`.
- **`skills/engajar/SKILL.md`:** o passo 5b cita o lote da Frota e a seção `2F`.
- **`skills/setup/SKILL.md`:** cita `fleet.workers` junto de `fleet.maxBatch`/`fleet.timeoutMinutes`.

Testes de conteúdo em `tests/test_skills_exec.py`. Mantenha verdes os que já leem `execute.md`, como `tests/test_crew_live.py` e `tests/test_worker_skills.py`. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-7-frota/spec.md` (R13, R16, R17, R20, R21, R23–R28; Edge Cases). Checks: C13, C16, C17, C20, C21, C23–C28.
- `execute.md` hoje: seções 0–7, com despacho sequencial na seção 2 ("one at a time per feature").
- Os comandos `dispatch.py batch`, `overdue` e `handoff.py --dispatch-add/--dispatch-remove` vêm das T1–T4.
- Estados do Linear vêm do config do repositório. A regra de bloqueio com `blocked: null` está em `skills/engajar/references/linear-contract.md`, linha ~41.
- `tests/test_skills_exec.py` tem o helper `assertAll(texto, *trechos)`.

#### BOUNDARIES
May change: `skills/engajar/references/execute.md`, `skills/engajar/SKILL.md`, `skills/setup/SKILL.md`, `tests/test_skills_exec.py`, `dist/`
Do not touch: `scripts/`, `src/crew.yaml`, `skills/engajar/references/linear-contract.md`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T6: Decisões F7 e CHANGELOG da 1.1.0
**Linear**: SC-78
**Depends on**: T5
**Requirements**: R31
**Tests**: unit
**Gate**: build

#### TASK
- **`DECISIONS.md`:** uma decisão F7-n para cada item, no formato das F6-n, com "por que não é bug" quando for contraintuitiva:
  - pool `fleet.workers` com troca na confirmação;
  - faixa de custo relativa, sem preço;
  - integração na chegada, serial;
  - oferta do lote a cada rodada (≥2 elegíveis);
  - timeout pelo `check --wait` e prazo no Handoff, não pelo `--timeout-ms` do `worker-start`;
  - sem `--deps` no lote;
  - `crew.json` com a contagem de LaForges.

  Inclua também o que o `scripts/check_decisions.py` exigir pelas mudanças das T1–T5.
- **`CHANGELOG.md`:** seção `## [1.1.0] - não lançada`, acima da 1.0.0, com `### Adicionado` (Modo Frota) e `### Alterado` (Handoff com vários despachos, `crew.json`).

Teste `test_decisions_and_changelog_record_fase_7` em `tests/test_release_docs.py` (as F7 existem e a seção 1.1.0 não lançada existe); ajuste `tests/test_check_decisions.py` só se o gate exigir. Os testes atuais de release, que exigem a 1.0.0 datada, continuam verdes. O `tools/release.py` não pode tratar "não lançada" como pronta para tag.

#### CONTEXT
Spec: `.specs/features/fase-7-frota/spec.md` (R31). Checks: C31.
Formato: as entradas F6-1..F6-9 de `DECISIONS.md` e a seção 1.0.0 de `CHANGELOG.md`. `tools/release.py` confere o CHANGELOG antes de tag (F6). Leia-o para não quebrar a regra.

#### BOUNDARIES
May change: `DECISIONS.md`, `CHANGELOG.md`, `tests/test_check_decisions.py`, `tests/test_release_docs.py`
Do not touch: `tools/release.py`, `VERSION`, `scripts/`, `skills/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T7: Roteiro e esqueleto do aceite da Fase 7
**Linear**: SC-79
**Depends on**: T5
**Requirements**: R30
**Tests**: unit
**Gate**: quick

#### TASK
- **`docs/aceite/roteiros-fase-7/frota.md`:** roteiro no `F:/Projetos/starcode-sandbox`, time PROJ, modo Git 2 ou 3, com uma feature GRANDE de fixture. Ela tem pelo menos 5 tickets:
  - 3 independentes, sem arquivo em comum;
  - 1 que toca num lockfile (`Runs alone`);
  - 1 que vai falhar de propósito (gate que não pode ficar verde).

  Os 4 cenários:
  - **(a)** lote de 3 em 3 pares CLI:modelo diferentes, por exemplo `claude:claude-sonnet-5-5`, `codex:gpt-6-luna` e um OpenCode **gratuito** (`opencode/mimo-v2.6-flash-free` → `opencode/deepseek-v4.1-flash-free` → `opencode/glm-5.3-flash-free`), com `check_scope` verde em cada um;
  - **(b)** o ticket do lockfile em `excluded` com `roda sozinho`;
  - **(c)** um worker que passa do timeout, com `fleet.timeoutMinutes` reduzido a 1–2 min no config do usuário do teste e restaurado depois, e que vira comentário de bloqueio na issue PROJ;
  - **(d)** a falha forçada enquanto os outros são integrados.

  Para cada cenário: o que registrar, com slug, IDs, dispatch ids, modelos pedidos e efetivos, hashes e resultado. Inclua os pré-requisitos: aninhamento da Orca ≥ 2, trust do Codex dado pelo usuário, nada no time SC.
- **`docs/aceite/fase-7.md`:** esqueleto com as seções Lote paralelo, Lockfile, Timeout e Falha isolada, cada uma com `**Resultado**: pendente`, mais uma tabela de versões (orca, CLIs).

Testes em `tests/test_acceptance_doc_f7.py`: o roteiro existe e o esqueleto tem as 4 seções. **Não crie** o teste da prova C30 (`test_fase7_acceptance_all_scenarios_approved`), que nasce na T8.

#### CONTEXT
Spec: `.specs/features/fase-7-frota/spec.md` (R30). Checks: C30 (só o esqueleto aqui).
- Formato de referência: `docs/aceite/roteiros-fase-6/`, `docs/aceite/fase-6.md` e `tests/test_acceptance_doc_f6.py`.
- Lições das Fases 3–4 (`docs/aceite/fase-3.md`, `fase-4.md`): conferir `worker-show` stage `input_accepted`; esperar `worker_done,question`; Codex no Windows precisa da instrução de UTF-8.

#### BOUNDARIES
May change: `docs/aceite/roteiros-fase-7/`, `docs/aceite/fase-7.md`, `tests/test_acceptance_doc_f7.py`
Do not touch: `scripts/`, `skills/`, `dist/`, `DECISIONS.md`, `CHANGELOG.md`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T8: Aceite real do Modo Frota no starcode-sandbox
**Linear**: SC-80
**Depends on**: T6, T7
**Requirements**: R30
**Tests**: unit
**Gate**: build

#### TASK
Executar `docs/aceite/roteiros-fase-7/frota.md` no `F:/Projetos/starcode-sandbox`, com o StarCode deste ramo de integração instalado (`python tools/install_local.py` ou o marketplace local apontando para este worktree). Antes de mudar a instalação ou o config do usuário, peça confirmação, e restaure tudo no fim. O Picard do sandbox roda o lote como um worker da Orca.

Registre os 4 cenários em `docs/aceite/fase-7.md` com `**Resultado**: aprovado` ou `reprovado` e a evidência pedida no roteiro. Achados que pedem código viram ticket próprio: liste-os em pendências, não corrija aqui.

Estenda `tests/test_acceptance_doc_f7.py` com `test_fase7_acceptance_all_scenarios_approved`: as 4 seções com `**Resultado**: aprovado` e com dispatch ids e hashes preenchidos.

#### CONTEXT
Spec: `.specs/features/fase-7-frota/spec.md` (R30). Checks: C30.
- O sandbox já recebeu features nas Fases 2–6. Use o time PROJ (`.starcode/config.json` do sandbox) e nunca o time SC.
- OpenCode só com modelos gratuitos. O trust do Codex é dado só pelo usuário.
- Workers sem resposta: entregue o brief com `orca terminal send` e confira `worker-read`.

#### BOUNDARIES
May change: `docs/aceite/fase-7.md`, `tests/test_acceptance_doc_f7.py`
Do not touch: `scripts/`, `skills/`, `dist/`, `docs/aceite/roteiros-fase-7/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `batch` deixa fora os tickets integrados, os ativos e os que esperam dependência (`espera T1`) (R1)
Proof: run unit | test_batch_skips_integrated_active_and_waiting_tickets ... ok

**C2** - `batch` exclui um candidato que divide caminho com um ticket ativo ou já escolhido, com `arquivo em comum com <Tn>: <caminho>` (R2)
Proof: run unit | test_batch_excludes_ticket_sharing_path_with_active ... ok

**C3** - Um ticket com lockfile ou `Runs alone` fica fora de lote com outros (`roda sozinho`) e forma lote de 1 só sem ativos e em 1º lugar (R3)
Proof: run unit | test_batch_sensitive_ticket_runs_alone_only_when_idle ... ok

**C4** - Com `fleet.maxBatch` 3 e 1 ativo, o lote tem no máximo 2 e o resto sai com `limite de N workers ativos` (R4)
Proof: run unit | test_batch_limit_counts_active_workers ... ok

**C5** - `batch --json` devolve `batch`, `costTotal`, `excluded` e `active` com os campos do contrato (R5)
Proof: run unit | test_batch_json_contract ... ok

**C6** - `batch` sai com 0 com lote, 1 com lote vazio e 2 com tasks.md ausente (R6)
Proof: run unit | test_batch_exit_codes ... ok

**C7** - Ticket sem `May change` sai com `sem May change` (R7)
Proof: run unit | test_batch_excludes_ticket_without_may_change ... ok

**C8** - `validate_config` aceita `fleet.workers` válido (inclusive modelo com `/` e `:`) e recusa CLI desconhecido, item repetido, lista vazia e mais de 10 itens, citando `fleet.workers[<i>]` (R8)
Proof: run unit | test_fleet_workers_accepts_valid_pairs_and_rejects_invalid ... ok

**C9** - `batch` distribui `fleet.workers` em rodízio a partir do par seguinte ao último ativo e, sem pool, usa o LaForge efetivo (R9)
Proof: run unit | test_batch_round_robin_from_fleet_workers ... ok

**C10** - `--assign T2=codex:gpt-6-luna` troca o par do T2, e um par inválido sai com 2 (R10)
Proof: run unit | test_batch_assign_overrides_pair ... ok

**C11** - `cost_tier` devolve o valor do mapa, `grátis` para `:free`/`-free` e `?` para o desconhecido (R11)
Proof: run unit | test_cost_tier_from_map_free_suffix_and_unknown ... ok

**C12** - `costTotal` conta os tickets por faixa, por exemplo `2× $$ + 1× grátis` (R12)
Proof: run unit | test_batch_cost_total_counts_tiers ... ok

**C13** - `execute.md` manda mostrar o lote com uma confirmação quando há ≥2 tickets e seguir sequencial sem pergunta quando há 1 (R13)
Proof: run unit | test_execute_fleet_batch_confirmation ... ok

**C14** - `--dispatch-add` acrescenta uma entrada e substitui a do mesmo ticket na mesma posição (R14)
Proof: run unit | test_dispatch_add_appends_and_replaces_same_ticket ... ok

**C15** - `--dispatch-remove T2` tira só a entrada do T2, volta a `none` sem entradas, e `--dispatched` ainda substitui o campo inteiro (R15)
Proof: run unit | test_dispatch_remove_keeps_other_entries ... ok

**C16** - `execute.md` registra `--dispatch-add` antes do `worker-start` com `--base-branch feature/<slug>`, vincula a issue e não usa `--deps` (R16)
Proof: run unit | test_execute_fleet_worker_start_flags ... ok

**C17** - `execute.md` trata a falha do `worker-start` de um ticket com `--dispatch-remove`, sem parar os outros (R17)
Proof: run unit | test_execute_fleet_start_failure_isolated ... ok

**C18** - `crew_live.py set laforge 3` grava 3, aceita até 10, e um outro membro com 2 sai com 2 (R18)
Proof: run unit | test_set_laforge_count_up_to_ten ... ok

**C19** - `next` sai com 3 quando há duas entradas abertas e uma ainda não está integrada (R19)
Proof: run unit | test_next_open_dispatch_with_multiple_entries ... ok

**C20** - `execute.md` espera com `check --wait --types worker_done,question --timeout-ms` até o prazo mais próximo, com `fleet.timeoutMinutes` (R20)
Proof: run unit | test_execute_fleet_wait_uses_nearest_deadline ... ok

**C21** - `execute.md` integra cada ticket ao chegar, um merge por vez, enquanto os outros seguem (R21)
Proof: run unit | test_execute_fleet_integrates_on_arrival ... ok

**C22** - `overdue --minutes 30 --now <ISO>` lista só as entradas com mais de 30 min, sai com 0 com atrasados e 1 sem (R22)
Proof: run unit | test_overdue_lists_tickets_past_deadline ... ok

**C23** - `execute.md` transforma o atraso em `blocked` ou comentário, marca ` · blocked` e não relança (R23)
Proof: run unit | test_execute_fleet_timeout_blocks_without_relaunch ... ok

**C24** - `execute.md` cancela só com confirmação, com `worker-stop` e o worktree preservado (R24)
Proof: run unit | test_execute_fleet_cancel_preserves_worktree ... ok

**C25** - `execute.md` devolve à fila o ticket que falhou, conta a tentativa e mantém os outros (R25)
Proof: run unit | test_execute_fleet_failure_returns_ticket_to_queue ... ok

**C26** - `execute.md` aborta o merge em conflito, devolve o ticket com os arquivos e continua (R26)
Proof: run unit | test_execute_fleet_merge_conflict_continues ... ok

**C27** - `execute.md` repete o `batch` sem ativos e segue para as provas com tudo integrado (R27)
Proof: run unit | test_execute_fleet_next_batch_then_proofs ... ok

**C28** - `execute.md` diz `Frota indisponível no modo 1 (um só worktree)` e segue sequencial (R28)
Proof: run unit | test_execute_fleet_unavailable_in_mode_1 ... ok

**C29** - `q-cli --laforge claude:claude-sonnet-5-5 --laforge codex:gpt-6-luna` escolhe um CLI de família diferente das duas, ou `self-verified` (R29)
Proof: run unit | test_q_cli_differs_from_all_laforge_families ... ok

**C30** - `docs/aceite/fase-7.md` tem os 4 cenários com `**Resultado**: aprovado`, dispatch ids e hashes (R30)
Proof: run unit | test_fase7_acceptance_all_scenarios_approved ... ok

**C31** - `DECISIONS.md` tem as decisões F7 e o `CHANGELOG.md` tem `## [1.1.0] - não lançada` (R31)
Proof: run unit | test_decisions_and_changelog_record_fase_7 ... ok

## Handoff

**Phase:** published
**Size:** GRANDE
**Git mode:** 3
**Next:** ramo de integração e primeiro ticket
**Linear:** SC-14 (mãe); T1=SC-73 T2=SC-74 T3=SC-75 T4=SC-76 T5=SC-77 T6=SC-78 T7=SC-79 T8=SC-80
**Integration branch:** not created
**Last integrated:** none
**Dispatched:** none
**Settled:** 2026-11-07: spec aprovada: "sim"; 2026-11-07: tasks aprovadas e publicadas: "sim"
**Attempts:** none
**Reports:** none
**Breaker:** closed
