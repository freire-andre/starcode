# Fase 10 — Painel Orca "Ponte" (v1.4): Tasks

**Approved**: 2026-11-09 - user: "sim"

**Spec**: `.specs/features/fase-10-ponte/spec.md`
**Status**: Approved
**Integration branch**: `feature/fase-10-ponte`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only, no generator change | `python -m unittest discover -s tests -v` |
| full | task that changes `scripts/`, `src/`, `tools/` or `tests/` (F3-1: `dist/` regenerated in the same commit) | `python tools/build.py && python tools/build.py --check && python -m unittest discover -s tests -v` |
| plugin | task that changes `src/orca/` | `orca plugin validate src/orca --json && orca plugin test src/orca && orca plugin check src/orca --json && python tools/build.py && python tools/build.py --check && python -m unittest discover -s tests -v` |
| build | records task, or after the last code task | `python tools/build.py && python tools/build.py --check && claude plugin validate dist/claude --strict && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |

## Tasks

### T1: Snapshot do estado do worktree (ponte.py)
**Linear**: SC-115
**Depends on**: none
**Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/ponte.py` (só stdlib, sem rede), com o subcomando `snapshot --path <worktree> --json`, que imprime o JSON de "Data & Contracts" da spec (`schemaVersion` 1):
- `crew`: um item por tripulante do `crew.json` da fonte (`src/crew.yaml` via o mesmo carregamento do `crew_live.crew_members()`), com `member`, `emoji`, `name`, `count` (contado de `sessions.json` com `crew_live.count_members`, mesma validade 15/60 min e mesma regra de hora futura/origem desconhecida), `lastAt` (hora ISO da sessão válida mais recente do tripulante, ou `null`) e `cliModel` (`"<cli> · <modelo>"` pela precedência D17: config do usuário > `crew.yaml`, como o banner já faz). `sessions.json` fica no worktree principal (`crew_live.live_dir`).
- `gitMode`: `mode`, `label`, `recordedAt` de `<git-dir>/starcode/session.json` do próprio worktree (use o leitor do `git_mode.py`); sem arquivo, `null`.
- `feature`: regra do R4 (Phase diferente de `done` com o arquivo do Handoff mais recente por `mtime`; senão a mais recente com `done: true`); campos do R5. `progress` vem de `.starcode/live/progress.json` (chave = slug) e, sem ela, da contagem de tasks (`crew_live.count_tasks`). `linear`: IDs `[A-Z]+-\d+` do campo `**Linear:**`, na ordem, mantendo faixas `SC-1..SC-9` como texto. `files.handoff` = arquivo onde está `## Handoff`.
- `workers`: uma entrada por linha `**Dispatched:**` (`<label> · <issues> · base <hash> · dispatch <ctx> · model <m>`, vários despachos separados por `; ` quando houver), na ordem do arquivo.
- `starcode: false` (R7), `errors` (R8: fonte ausente/ilegível/JSON inválido/>1 MiB vira item `{source, message}`, seção nula), saída 2 com `{"schemaVersion":1,"error":"worktree inválido: <path>"}` (R9).
- Nunca escreve nada (R10). Leitura e escrita em UTF-8 explícito; `print(json.dumps(..., ensure_ascii=False))` com `sys.stdout.reconfigure(encoding="utf-8")`.

Testes em `tests/test_ponte.py` (use `TempRepoCase` de `tests/helpers.py`) e fixtures em `tests/fixtures/ponte/`. Nomes obrigatórios dos testes (provas dos checks): `test_snapshot_keys`, `test_snapshot_crew_ttl`, `test_snapshot_git_mode`, `test_snapshot_feature_choice`, `test_snapshot_feature_fields`, `test_snapshot_workers`, `test_snapshot_sem_starcode`, `test_snapshot_fonte_invalida`, `test_snapshot_worktree_invalido`, `test_snapshot_somente_leitura`. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R1–R10; contrato em Data & Contracts). Checks: C1–C10.
Reuse, sem duplicar: `scripts/crew_live.py` (`main_worktree`, `live_dir`, `crew_members`, `count_members`, `entry_valid`, `count_tasks`, `handoff_phase`), `scripts/handoff.py` (leitura dos campos do Handoff), `scripts/git_mode.py` (leitura do `session.json`), `hooks/scripts/banner.py` (como o banner monta `cli · modelo`). Exemplo real de Handoff com `**Dispatched:**` e `**Linear:**` com faixa: `.specs/features/fase-9-worf-guinan-diagnostico/tasks.md`. `tools/build.py` copia `scripts/` para `dist/<cli>/scripts/`.

#### BOUNDARIES
May change: `scripts/ponte.py`, `tests/test_ponte.py`, `tests/fixtures/ponte/`, `dist/`
Do not touch: `scripts/crew_live.py`, `scripts/handoff.py`, `scripts/git_mode.py`, `src/`, `tools/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T2: Plugin da Orca: manifesto e worker
**Linear**: SC-116
**Depends on**: T1
**Requirements**: R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R32, R35
**Tests**: unit
**Gate**: plugin
**Runs alone**: yes

#### TASK
Criar o plugin em `src/orca/` partindo do modelo oficial (`orca plugin create <pasta temporária> --template worker-panel --json`, copie e adapte; nunca rode o create dentro do repo por cima de arquivos):
- `src/orca/orca-plugin.json`: `id` `starcode-ponte`, `name` `StarCode Ponte`, `version` igual ao `VERSION` do repo, sem `publisher`, `engines.orca` `>=1.4.248`, `execution` `trusted-worker`, `pluginApi` 1, `main` `src/worker.ts`; painel `ponte` (`title` `Ponte`, `icon` `rocket`, `entry` `src/panel.tsx`, `ui` `components`); `contributes.events` `workspace.changed` e `agent.status.changed`; `contributes.commands` `starcode-ponte.toggle` (`action` `sidebar.right.toggle`) e `starcode-ponte.refresh` (worker); `contributes.statusBarItems` `ponte` (ícone `rocket`, `command` `starcode-ponte.toggle`); capabilities exatamente `workspace:read`, `agent:read`, `workspace:write`, `agent:launch`, `storage:own` (R35).
- `src/orca/src/protocol.ts`: requisições `ponte.state`, `ponte.open`, `ponte.launchPicard` e o evento `ponte.state`, com o tipo do estado de "Data & Contracts".
- `src/orca/src/worker.ts` (`export default function activate(orca)`):
  - acha o caminho em foco cruzando `context.branch` com `workspace.list` (R11); sem casamento ou `context` nulo → `status: "sem-worktree"` (R12);
  - roda `python <ponte.py> snapshot --path <path> --json` com `node:child_process` `execFile` (sem shell, tempo limite 10 s; tenta `python` e depois `python3`). `<ponte.py>` = `scripts/ponte.py` relativo à raiz do plugin (layout de `dist/orca`), e se não existir `../../scripts/ponte.py` (layout da fonte `src/orca`);
  - `agent.status.changed` e `workspace.changed` → debounce de 300 ms → snapshot → `orca.panels.post('ponte.state', estado)` (R13, R14); resultado de um foco antigo é descartado (R15);
  - issue: `orca linear issue --current --json` no `cwd` do worktree, limite 10 s, cache de 60 s por worktree (R16); falha/sem vínculo → primeiro ID de `feature.linear` com a nota "Linear indisponível" ou "Sem issue vinculada", sem repetir antes do cache vencer (R17);
  - snapshot falho → `status: "erro"`, `stale: true`, último estado bom mantido (R18);
  - barra de status `ponte` com `statusBar.update` (texto, `tone`, `visible`) pela regra do R19 (`warning` com disjuntor aberto ou com agente do foco em `blocked`/`waiting`, via `agents.list` e `agent.status.changed`);
  - handler `ponte.state` com `{ force: true }` e o comando `starcode-ponte.refresh` ignoram o cache (R32).
  - `ponte.open` e `ponte.launchPicard` respondem `not_implemented` (T4 implementa).
- `src/orca/tsconfig.json` (estende `./.orca/types/tsconfig.json`, como no modelo); `.orca/` fica fora do Git (acrescente `src/orca/.orca/` ao `.gitignore`).
- Testes em `src/orca/src/worker.test.ts` com `mountWorker`/`mockHost` de `orca/testing`, com o processo filho falso (injete um executor: `activate` usa `globalThis.__ponteExec` quando definido, só para testes). Nomes obrigatórios: `worker acha o worktree em foco pelo ramo`, `worker sem worktree em foco`, `worker publica o estado após agent.status.changed`, `worker agrupa eventos em 300 ms`, `worker descarta snapshot de foco antigo`, `worker consulta a issue e guarda em cache por 60 s`, `worker sem Linear mostra o ID do Handoff`, `worker com snapshot falho marca desatualizado`, `worker atualiza a barra de status`, `atualizar agora ignora o cache`.
- Teste `unittest` `tests/test_orca_manifest.py` com `test_manifest_capabilities_e_engines` (R35) e `test_manifest_toggle_da_barra` (R20: comando `starcode-ponte.toggle` com `action` `sidebar.right.toggle` ligado ao item `ponte`).

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R11–R20, R32, R35; protocolo e manifesto em Data & Contracts). Checks: C11–C20, C32, C35.
API: rode `orca skills get orca-plugin-authoring` e as referências `recipes`, `events`, `host-api`, `testing`, `manifest` (`--reference references/<nome>.md`). Fatos já sondados no Orca 1.4.255: `orca plugin test` imprime `✔ <nome do teste> (<ms>)` e ignora pastas `dist`; `node:child_process` funciona dentro de `mountWorker`; um comando não consegue abrir um painel específico (só ações nativas, daí o `sidebar.right.toggle`). O `scripts/ponte.py` (T1) já existe.

#### BOUNDARIES
May change: `src/orca/orca-plugin.json`, `src/orca/tsconfig.json`, `src/orca/src/protocol.ts`, `src/orca/src/worker.ts`, `src/orca/src/worker.test.ts`, `tests/test_orca_manifest.py`, `.gitignore`
Do not touch: `scripts/`, `tools/`, `src/orca/src/panel.tsx`, `src/orca/src/scene-model.ts`, `src/orca/src/scene.ts`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca rode `orca plugin enable`, `install` ou `dev load` com `--approve`: aprovação é do usuário.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T3: Painel Ponte (componentes)
**Linear**: SC-117
**Depends on**: T2
**Requirements**: R21, R22, R23, R24, R25, R26, R27
**Tests**: unit
**Gate**: plugin

#### TASK
Criar `src/orca/src/panel.tsx` (painel de componentes, sem hooks nem DOM; estado em atoms com chave), em PT-BR:
- ao abrir, `plugin.request('ponte.state', {}, { timeoutMs: 15000 })` e estado "carregando" até a resposta (R21); seções Tripulação, Modo Git, Issue, Fase SDD, Workers da Frota, Atalhos e a hora da última atualização com `RelativeTime`;
- `plugin.on('ponte.state', ...)` redesenha sem ação do usuário (R22);
- Tripulação: só `count > 0`, com emoji, nome, `cli · modelo` e contagem quando > 1; senão "Tripulação em repouso" (R23);
- Fase SDD: slug, fase, tamanho, progresso `done/total (percent%)`, aviso "Disjuntor aberto" (R24);
- Workers da Frota: uma linha por item; com `agents.list`/`agent.status.changed`, mostra o estado do agente cujo título contém o rótulo ou o ID da issue; senão "Nenhum worker despachado" (R25);
- `starcode: false` → só "StarCode não configurado neste worktree" e Atualizar agora (R26); `sem-worktree` → "Nenhum worktree em foco";
- erro de uma seção em `errors` → "indisponível" + motivo, sem esconder as outras (R27); `stale` → marca "desatualizado".
- Atalhos nesta task: só o botão Atualizar agora (`ponte.state` com `force: true`); os outros três ficam para a T4.
- `src/orca/src/panel.check.ts` com os cenários `ok`, `vazio`, `sem-starcode`, `erro-secao`, `desatualizado`.
- Testes em `src/orca/src/panel.test.tsx` com `mount`/`mockHost`. Nomes obrigatórios: `painel pede o estado ao abrir`, `painel redesenha com ponte.state`, `painel mostra só tripulantes ativos`, `painel mostra fase e progresso`, `painel casa worker com agente`, `painel sem StarCode`, `painel com seção indisponível`.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R21–R27; estados em States). Checks: C21–C27.
API de componentes: `orca skills get orca-plugin-authoring --reference references/components.md` e `testing.md`. O protocolo e o worker (T2) já existem em `src/orca/src/protocol.ts` e `worker.ts`. Use `orca plugin shot src/orca --panel ponte` (ou o `dev watch --shot`) para olhar o painel desenhado.

#### BOUNDARIES
May change: `src/orca/src/panel.tsx`, `src/orca/src/panel.check.ts`, `src/orca/src/panel.test.tsx`
Do not touch: `src/orca/src/worker.ts`, `src/orca/src/protocol.ts`, `src/orca/orca-plugin.json`, `scripts/`, `tools/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove plugin (`--approve`).

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T4: Atalhos e diário de bordo
**Linear**: SC-118
**Depends on**: T3
**Requirements**: R28, R29, R30, R31, R44
**Tests**: unit
**Gate**: plugin

#### TASK
Implementar os três atalhos que faltam, no worker e no painel:
- `ponte.open` (`{ file: "spec"|"tasks"|"handoff" }`): `editor.open` com o `workspaceId` em foco e o caminho de `snapshot.feature.files`; botão desabilitado quando o arquivo é `null` (R28).
- Abrir a issue no Linear: `shell.openExternal(issue.url)` no clique; desabilitado sem URL (R29).
- `ponte.launchPicard`: agente e modelo do Picard a partir do item `picard` de `snapshot.crew` (`cliModel`), `agent.launch` com `{ workspaceId, agent, prompt }`; prompt `/starcode:engajar` para `claude`, `$starcode:engajar` para `codex`, `engajar` para os demais; botão desabilitado até a resposta (R30). Agentes que a Orca lança: `claude`, `codex`, `antigravity`, `opencode` (lista do `orca orchestration worker-start --help`); outro → erro `not_launchable` e a mensagem "Agente " + nome + " não pode ser iniciado pela Orca" no painel (ex.: "Agente gemini não pode ser iniciado pela Orca"), sem lançar (R31).
- Diário de bordo (R44): o worker acrescenta `{ at, text }` em PT-BR a cada mudança de estado de agente, de worktree em foco ou de fase (máximo 20, em memória) e envia em `log` dentro do `ponte.state` (tipo em `protocol.ts`); o painel mostra as 10 mais recentes na seção "Diário de bordo" com `RelativeTime`.
- Testes novos em `src/orca/src/worker.test.ts` e `src/orca/src/panel.test.tsx`. Nomes obrigatórios: `atalho abre spec tasks e handoff`, `atalho abre a issue no navegador`, `atalho inicia o Picard uma vez`, `atalho recusa agente que a Orca não lança`, `diário guarda 20 entradas e o painel mostra 10`.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R28–R31, R44). Checks: C28–C31, C44.
`editor.open`/`agent.launch` pedem `workspace:write`/`agent:launch` (já no manifesto da T2); `shell.openExternal` precisa de um clique (`panel.press` no teste concede o gesto). Referência `host-api.md` da skill `orca-plugin-authoring`.

#### BOUNDARIES
May change: `src/orca/src/worker.ts`, `src/orca/src/worker.test.ts`, `src/orca/src/panel.tsx`, `src/orca/src/panel.test.tsx`, `src/orca/src/protocol.ts`
Do not touch: `src/orca/orca-plugin.json`, `src/orca/src/scene-model.ts`, `src/orca/src/scene.ts`, `src/orca/src/scene.html`, `scripts/`, `tools/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove plugin (`--approve`).

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T5: Modelo da Cena da Ponte (buildScene)
**Linear**: SC-119
**Depends on**: T2
**Requirements**: R38, R39, R40, R41, R42, R43
**Tests**: unit
**Gate**: plugin

#### TASK
Criar `src/orca/src/scene-model.ts`, módulo puro (sem DOM, sem host), com `buildScene(estado, agentes, agoraMs)` que devolve a cena a desenhar:
- grade lógica fixa (ex.: 64×40 células) com uma estação por tripulante dos 12 (`picard` na cadeira central, `data`/`troi` ao lado, `laforge` na engenharia, os demais nas laterais), a área do turbolift e a área de engenharia para os workers (R38);
- um personagem por tripulante: `sentado` + quadro de animação `Math.floor(agoraMs / 250) % 2` quando `count > 0`; `de-pe` no turbolift, parado, com `count = 0` (R39); cor da divisão (comando, operações, ciências) e o emoji do tripulante;
- balão `!` no personagem ligado a um agente em `blocked`/`waiting` pela regra do R40 (worker cujo rótulo ou issue está no título do agente; senão o ativo de `lastAt` mais recente; senão o Picard);
- um LaForge por worker na engenharia com o rótulo do ticket, até 6, e `maisN` com o restante; agente `done` → `concluido: true` (R41);
- `starcode: false`, `sem-worktree` ou `erro` sem estado bom → cena vazia com `mensagem` igual às frases de R12, R18 e R26 (R42);
- só dados: nada de canvas aqui (R43).
Testes em `src/orca/src/scene-model.test.ts`. Nomes obrigatórios: `cena tem uma estação por tripulante e a engenharia`, `cena senta tripulante ativo e anima a cada 250 ms`, `cena põe o balão no personagem do agente bloqueado`, `cena desenha até 6 workers e +N`, `cena vazia mostra a frase do estado`.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R38–R43; estado em Data & Contracts). Checks: C38–C42.
Análise das referências: `.specs/features/fase-10-ponte/analise-referencias.md` (Pixel Agents e Habblaud: só a ideia; nada copiado). O tipo do estado está em `src/orca/src/protocol.ts` (T2); importe só o tipo. `orca plugin test src/orca` roda `*.test.ts` com `node:test`.

#### BOUNDARIES
May change: `src/orca/src/scene-model.ts`, `src/orca/src/scene-model.test.ts`
Do not touch: `src/orca/src/protocol.ts`, `src/orca/src/worker.ts`, `src/orca/src/panel.tsx`, `src/orca/orca-plugin.json`, `scripts/`, `tools/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove plugin (`--approve`). Não copie código nem arte do Pixel Agents ou do Habblaud: escreva do zero.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T6: Painel HTML da Cena (desenho em canvas)
**Linear**: SC-120
**Depends on**: T5
**Requirements**: R38, R43, R35
**Tests**: unit
**Gate**: plugin

#### TASK
- `src/orca/src/scene.html` + `src/orca/src/scene.ts`: painel HTML `ponte-cena` com um `<canvas>` que escala inteiro na largura do painel (`image-rendering: pixelated`, sem cortar estações). Pede `orca.plugin.request('ponte.state')` ao abrir, ouve `orca.plugin.on('ponte.state')` e `orca.on('agent.status.changed')`, chama `buildScene` e desenha com `requestAnimationFrame` (sem `setInterval`).
- `paint(ctx, cena, escala)` exportado: desenha piso, consoles, estações, personagens (corpo em retângulos de pixel com a cor da divisão, emoji acima), balões `!`, `✓`, rótulos dos workers, `+N` e a `mensagem` central. Só `fillRect`/`fillText`/`strokeRect`: nenhuma imagem, `drawImage` ou arquivo de arte (R38). Lê só o resultado de `buildScene` (R43).
- `src/orca/orca-plugin.json`: acrescenta o painel `ponte-cena` (`title` `Cena da Ponte`, `icon` `star`, `entry` `src/scene.html`, `ui` `html`).
- Testes: `src/orca/src/scene.test.ts` com um contexto de canvas falso que grava as chamadas; nome obrigatório `pintura da cena só lê o modelo e não usa imagem`. Em `tests/test_orca_manifest.py`, estenda `test_manifest_capabilities_e_engines` para exigir os painéis `ponte` (components) e `ponte-cena` (html) (R35).
- Olhe a cena desenhada com `orca plugin dev watch src/orca --shot src/orca/.orca/shots` e `orca plugin shot` do painel `ponte-cena`; ajuste até as 12 estações ficarem legíveis numa largura de 360 px.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R38, R43, R35; casos de borda da cena). Checks: C43, C35.
Painéis HTML: referências `host-api.md` (frame: `orca.on`, `orca.plugin.request`) e `recipes.md` da skill `orca-plugin-authoring`; sem rede, sem pacote npm (imports só relativos ou `orca/*`). `buildScene` (T5) está em `src/orca/src/scene-model.ts`.

#### BOUNDARIES
May change: `src/orca/src/scene.html`, `src/orca/src/scene.ts`, `src/orca/src/scene.test.ts`, `src/orca/orca-plugin.json`, `tests/test_orca_manifest.py`
Do not touch: `src/orca/src/scene-model.ts`, `src/orca/src/worker.ts`, `src/orca/src/panel.tsx`, `src/orca/src/protocol.ts`, `scripts/`, `tools/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove plugin (`--approve`). Não copie código nem arte do Pixel Agents ou do Habblaud: escreva do zero.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T7: Build de dist/orca e instalação local
**Linear**: SC-121
**Depends on**: T4, T6
**Requirements**: R33, R34
**Tests**: unit
**Gate**: full

#### TASK
- `tools/build.py`: gerar `dist/orca/` com `src/orca/` (sem `.orca/` e sem `*.test.ts(x)`) e `dist/orca/scripts/` com `ponte.py` e os módulos que ele importa (copiados da fonte, mesma regra de "nunca editado à mão"). O `version` do manifesto em `dist/orca` vem do `VERSION`. O `--check` compara `dist/orca/` também (R33). `orca` não entra em `CLIS` das skills: é um alvo à parte.
- `tools/install_local.py`: `--cli orca` → `orca plugin validate dist/orca --json`, depois `orca plugin install <abs>/dist/orca --json`. Exit 3 (`approval_required`): imprime a lista de acessos de `error.data` e o comando com `--approve <fingerprint>` que a Orca devolveu, sai com 3 e nunca passa `--approve` (R34). `--dry-run` só mostra o plano.
- Testes: em `tests/test_build.py`, `test_build_gera_dist_orca` e `test_build_check_cobre_dist_orca`; em `tests/test_install_local.py`, `test_install_orca_valida_e_instala` e `test_install_orca_aprovacao_nunca_automatica` (binário e runner falsos, como os testes existentes). Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R33, R34). Checks: C33, C34. O plugin completo (painéis `ponte` e `ponte-cena`, worker, cena) já está em `src/orca/` (T2–T6).
`tools/build.py` (`build`, `compare`, `CLIS`, `copy_tree`) e `tools/install_local.py` (`BINARIES`, `_codex`, `_antigravity`, `main` com `runner`/`which` injetáveis). Ajuste o `test_build` existente se ele listar as pastas de `dist/`. A saída de exit 3 da Orca: `{"ok": false, "error": {"code": "approval_required", "data": {...}}}` (referência `cli.md` da skill `orca-plugin-authoring`).

#### BOUNDARIES
May change: `tools/build.py`, `tools/install_local.py`, `tests/test_build.py`, `tests/test_install_local.py`, `dist/`
Do not touch: `src/orca/`, `scripts/`, `.github/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca rode a instalação real nem aprove plugin.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T8: Registros e CI
**Linear**: SC-122
**Depends on**: T7
**Requirements**: R36
**Tests**: unit
**Gate**: build
**Runs alone**: yes

#### TASK
- `DECISIONS.md`: entradas F10-1.. (pelo menos: estado lido em Python pelo `ponte.py`, worker só orquestra; `dist/orca` com instalação local sem catálogo; R20 com `sidebar.right.toggle` porque a API não abre painel; capabilities mínimas e aprovação sempre do usuário; Cena da Ponte em painel HTML com arte gerada por código, inspirada no Pixel Agents e no Habblaud, sem copiar código nem sprites).
- `CREDITS.md`: Pixel Agents (`pixel-agents-hq/pixel-agents`, MIT) e Habblaud (`marmottajr/habblaud`, MIT) como inspiração da Cena da Ponte, sem código nem arte copiados.
- `CHANGELOG.md`: `## [1.4.0] - não lançada` com o painel Ponte.
- `docs/compatibilidade.md`: linha do painel Ponte (Orca ≥ 1.4.248, independente do CLI).
- `README.md`: seção de instalação do painel (`python tools/install_local.py --cli orca`, aprovação na Orca).
- `.github/workflows/ci.yml`: passo `orca plugin validate src/orca --json` que roda só se `orca` existir no PATH, senão imprime "orca ausente: validação do plugin pulada" e passa.
- Testes `tests/test_release_docs_f10.py` (`test_release_docs_f10`) e, em `tests/test_ci_workflow.py`, `test_ci_valida_plugin_orca_condicional`.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R36). Check: C36.
Modelos: `tests/test_release_docs_f9.py`, entradas F9-n em `DECISIONS.md` (formato verificado por `scripts/check_decisions.py`), seção 1.3.0 do `CHANGELOG.md`.

#### BOUNDARIES
May change: `DECISIONS.md`, `CREDITS.md`, `CHANGELOG.md`, `docs/compatibilidade.md`, `README.md`, `.github/workflows/ci.yml`, `tests/test_release_docs_f10.py`, `tests/test_ci_workflow.py`
Do not touch: `src/`, `scripts/`, `tools/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T9: Aceite real do painel e da cena
**Linear**: SC-123
**Depends on**: T8
**Requirements**: R37
**Tests**: unit
**Gate**: build

#### TASK
Antes deste ticket o Picard instala o plugin com o usuário (`python tools/install_local.py --cli orca`, aprovação dada pelo usuário na Orca). Com o plugin instalado e habilitado:
- Worktree A (este repo, feature com Handoff) e Worktree B (outro worktree, ex.: o sandbox `F:/Projetos/starcode-sandbox` ou um worktree sem StarCode): `orca plugin open local.starcode-ponte --panel ponte` (confira a chave com `orca plugin list --json`), foco em cada um, `orca plugin shot <chave> --panel ponte --out docs/aceite/fase-10/<nome>.png` e `--status-bar`.
- Evento de agente: com o painel aberto, um agente muda de estado (ex.: este próprio worker), e uma nova captura mostra a mudança (tripulação ou hora de atualização).
- Cena: `orca plugin shot <chave> --panel ponte-cena` com um tripulante ativo e, se houver, um worker; uma segunda captura depois de um evento de agente.
- Atalhos: Atualizar agora e Abrir spec (o Iniciar o Picard só se o usuário estiver junto; senão "não executado" com o motivo).
- `docs/aceite/fase-10.md` com as seções `## Instalação`, `## Worktree A`, `## Worktree B`, `## Evento de agente`, `## Cena`, `## Atalhos`, cada uma com `**Resultado**: aprovado` ou `reprovado` e o caminho da captura (R37). Achados que pedem código viram pendência, não correção aqui.
- Teste `tests/test_acceptance_doc_f10.py` (`test_fase10_acceptance_sections`).

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R37 e Success). Check: C37.
Modelo: `docs/aceite/fase-9.md` e `tests/test_acceptance_doc_f9.py`. CLI: `orca plugin open|shot|list` (referência `cli.md` da skill `orca-plugin-authoring`).

#### BOUNDARIES
May change: `docs/aceite/fase-10.md`, `docs/aceite/fase-10/`, `tests/test_acceptance_doc_f10.py`
Do not touch: `src/`, `scripts/`, `tools/`, `dist/`, `.github/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove, instale nem desinstale plugin.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T10: Correções do aceite real (cena, issue, largura)
**Linear**: SC-124
**Depends on**: T9
**Requirements**: R16, R45, R46, R47
**Tests**: plugin
**Gate**: plugin

#### TASK
O aceite real (T9, `docs/aceite/fase-10.md`) achou três defeitos no plugin instalado. Corrija cada um com um teste que falha antes da correção:
- Cena (R45): o painel `ponte-cena` saiu em branco e depois "stopped responding". `scene.html` carrega `<script type="module" src="./scene.ts">` (a Orca só transpila quando o `entry` do manifesto é `.ts`) e `scene.ts` importa `./scene-model` sem extensão. Troque o `entry` para `src/scene.ts`, faça o script criar o canvas quando a página não tiver `#cena`, e garanta que o import de `buildScene` chega ao navegador (caminho com extensão que a Orca serve, ou outra forma documentada na skill `orca-plugin-authoring`). Remova `scene.html` se ele deixar de ser usado. Teste: o manifesto aponta `ponte-cena` para `src/scene.ts` e o código do painel não tem import relativo sem extensão.
- Issue (R16, R46): `orca linear issue --current` usa o worktree do terminal que chama e, no worker, responde `linear_no_linked_issue` mesmo com o worktree vinculado. Leia `linkedLinearIssue` de `orca worktree show --worktree path:<caminho> --json` e consulte `orca linear issue <ID> --json` (mesmo limite de 10 s e cache de 60 s por worktree). Sem vínculo → fallback do Handoff com a nota; o painel mostra a nota junto do ID quando título e estado faltam.
- Largura (R47): com 237 px os botões "Abrir tasks" e "Iniciar o Picard" ficam cortados e há rolagem horizontal. Quebre os botões em linhas (componente/propriedade de quebra da Orca) e acrescente um cenário de 240 px ao `panel.check.ts`.
Atualize o `dist/orca` com `python tools/build.py` e acrescente uma entrada F10-n em DECISIONS (cena com entry `.ts`, issue pelo vínculo do worktree).

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R16, R45, R46, R47). Checks: C16, C45, C46, C47. Aceite: `docs/aceite/fase-10.md`.
Teste real feito pelo Picard: `orca linear issue SC-123 --json` → ok, título e estado; `orca linear issue --current --json` num worktree vinculado → `linear_no_linked_issue`; `orca worktree show --worktree path:<caminho> --json` → `linkedLinearIssue: "SC-123"`.
Referências da API: `entry` de painel aceita `.ts` e, num painel `html`, a Orca gera a página em volta (manifesto, `engines.orca >=1.4.246`).

#### BOUNDARIES
May change: `src/orca/`, `dist/orca/`, `tests/test_orca_manifest.py`, `DECISIONS.md`, `tests/test_build.py`
Do not touch: `scripts/`, `tools/`, `.github/`, `docs/aceite/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove, instale nem desinstale plugin; se precisar carregar o plugin na Orca para provar a cena, pergunte ao Picard.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T11: Worktree em foco com ramos iguais (correção do reaceite)
**Linear**: SC-125
**Depends on**: T10
**Requirements**: R11, R12
**Tests**: plugin
**Gate**: plugin

#### TASK
No reaceite depois da T10, com o foco em `F:/Projetos/StarCode` (ramo `main`), o painel e a cena mostraram "StarCode não configurado neste worktree": `workspace.list` tem três worktrees no ramo `main` (ApuraBolsa, OuveAI, StarCode, de repositórios diferentes) e o worker pega o primeiro só pelo ramo. Corrija com teste que falha antes:
- Uma função única em `worker.ts` resolve o foco (hoje o casamento está duplicado em `focus()` e em `refresh()`): mesmo ramo (aceitando `refs/heads/<ramo>` dos dois lados) e `name === context.displayName`; um único workspace no ramo vale mesmo sem casar o nome; vários no ramo e nenhum com o nome → `sem-worktree` (R12).
- Testes: `worker acha o worktree em foco pelo ramo` continua; novo `worker desempata ramo igual pelo nome` (três workspaces no `main`, o do meio com o `displayName` do contexto, espera o caminho dele); novo cenário em `worker sem worktree em foco` para ramo repetido sem nome casado.
Atualize `dist/orca` com `python tools/build.py`.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R11, R12). Checks: C11, C12, C48.
Tipos da Orca (`orca plugin types src/orca`): `workspace.readContext` → `{ branch, displayName, terminals } | null`; `workspace.list` → `{ workspaces: { id, kind, name, path, branch, hostId }[] }`. `orca worktree list --json` mostra `displayName` "StarCode" para `F:\Projetos\StarCode` e `branch` `refs/heads/main`.

#### BOUNDARIES
May change: `src/orca/`, `dist/orca/`
Do not touch: `scripts/`, `tools/`, `tests/`, `.github/`, `docs/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove, instale nem desinstale plugin.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T12: Atalhos, log de erros e turbolift (correções do reaceite manual)
**Linear**: SC-126
**Depends on**: T11
**Requirements**: R28, R30, R39, R48
**Tests**: plugin
**Gate**: plugin

#### TASK
No reaceite manual do usuário (plugin instalado, foco em `F:/Projetos/StarCode`):
- Abrir spec, Abrir tasks e Abrir Handoff mostraram "path: path must be relative and inside the workspace": o snapshot traz caminhos absolutos (`F:/Projetos/StarCode/.specs/...`) e `editor.open` exige caminho relativo ao worktree. Converta para relativo à raiz do worktree em foco, com `/`, aceitando `\` e letra de unidade em maiúscula ou minúscula; caminho fora do worktree → erro `file_missing` (R28).
- Iniciar Picard: a tela mudou e nenhum terminal novo ficou no worktree, sem erro visível. Registre o `terminalId` devolvido no log (`console.log`) e mostre "Picard iniciado" no painel; erro do `agent.launch` vai para o log e para a linha de erro do painel (R30, R48). Confira na skill `orca-plugin-authoring` (host-api) se o `agent` e o `prompt` estão no formato que a Orca espera e registre o que achar no relatório.
- Issue: num worktree sem vínculo o painel mostrou "Linear indisponível" (o CLI responde `linkedLinearIssue: null` em 0,6 s). Toda falha de processo externo vai para o log com a ação e a mensagem; `linkedLinearIssue` nulo → "Sem issue vinculada"; só falha do processo ou JSON inválido → "Linear indisponível" (R48). Se o `orca` não for achado pelo worker, tente também o binário ao lado do `process.execPath` ou a variável de ambiente que a Orca expõe, e diga no relatório.
- Turbolift: os 11 inativos ficam no mesmo ponto com rótulos sobrepostos. Distribua em posições distintas na área do turbolift (grade), sem rótulo sobreposto (R39), mantendo `buildScene` pura.
Teste que falha antes para cada item; atualize `dist/orca` com `python tools/build.py`.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R28, R30, R39, R48). Checks: C28, C30, C39, C49, C50.
Prints do usuário: erro "path: path must be relative and inside the workspace" nos três botões; Diário com "Agente Claude Code: concluído." (evento de agente funcionando).
`agent.launch`: "Starts an agent's CLI in a new terminal of a workspace, in the background, and returns as soon as it starts; a `prompt` is sent once the agent is ready" → `{ terminalId }`. `editor.open`: `{ workspaceId, path }`, caminho de um arquivo dentro do workspace.

#### BOUNDARIES
May change: `src/orca/`, `dist/orca/`
Do not touch: `scripts/`, `tools/`, `tests/`, `.github/`, `docs/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove, instale nem desinstale plugin; não clique no Iniciar Picard do plugin instalado.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T13: Registro do reaceite e das limitações da Orca
**Linear**: SC-127
**Depends on**: T12
**Requirements**: R30, R37, R49
**Tests**: plugin
**Gate**: plugin

#### TASK
Feche o aceite da Fase 10 com o reaceite feito depois das T10 a T12:
- `docs/aceite/fase-10.md`: mantenha as seis seções e acrescente `## Reaceite` com `**Resultado**: aprovado com limitações` e as capturas. Resultados do reaceite (usuário e Picard, 2026-11-10, plugin reinstalado do `dist/orca` sem nova aprovação, mesmo acesso): Worktree principal `F:/Projetos/StarCode` (ramo `main`, três worktrees no mesmo ramo) agora resolvido pelo nome (T11); Cena desenha as 12 estações e os inativos no turbolift em grade (T10, T12); Evento de agente aprovado: o Diário registrou "Agente Claude Code: concluído." sem clique; Atalhos: Atualizar agora, Abrir spec, Abrir tasks e Abrir Handoff aprovados pelo usuário (abriram `spec.md` e `tasks.md`); Iniciar Picard: a Orca criou o terminal (`terminalId` no Diário) com o Claude Code aberto, mas em segundo plano, sem aba visível e sem o prompt `/starcode:engajar` enviado (limitação); Issue: só o ID do Handoff com "Linear indisponível", porque o `orca` chamado de dentro do worker falha com `node:internal/modules/cjs/loader:1575` (limitação). Atualize o `**Resultado**` de Evento de agente, Cena e Atalhos para `aprovado` ou `aprovado com limitações`, citando o reaceite.
- Copie as capturas de `C:/Users/freir/AppData/Local/Temp/claude/b416d939b0d0400b/46830551-f773-4dfe-a78a-9d5c633764bf/scratchpad/reaceite` para `docs/aceite/fase-10/` (nomes: `reaceite-atalhos-erro-antes.png`, `reaceite-picard-diario.png`, `reaceite-ponte-worktree-principal.png`, `reaceite-cena-turbolift.png`) e tire mais uma captura atual da Ponte e da Cena com `orca plugin shot local.starcode-ponte --panel <id> --out ...`.
- Painel (R30): o texto de sucesso vira "Picard iniciado em segundo plano" e o botão tem um aviso (tooltip ou texto auxiliar) de que o agente abre em segundo plano; ajuste o teste.
- DECISIONS: uma entrada F10-n com as duas limitações e a escolha do usuário. `docs/compatibilidade.md`: as duas limitações na linha da Orca.
- `tests/test_acceptance_doc_f10.py`: exija também a seção `## Reaceite`.
Atualize `dist/orca` com `python tools/build.py`.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R30, R37, R49). Checks: C30, C37, C51.
Handoff (`**Reports:**`) tem o histórico das T9 a T12.

#### BOUNDARIES
May change: `docs/aceite/fase-10.md`, `docs/aceite/fase-10/`, `tests/test_acceptance_doc_f10.py`, `DECISIONS.md`, `docs/compatibilidade.md`, `src/orca/`, `dist/orca/`
Do not touch: `scripts/`, `tools/`, `.github/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove, instale nem desinstale plugin; não clique no Iniciar Picard.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T14: Novo visual da Cena da Ponte (ponte vista de cima)
**Linear**: SC-128
**Depends on**: T13
**Requirements**: R38, R39, R41, R42, R43, R50
**Tests**: plugin
**Gate**: plugin

#### TASK
O usuário achou a cena confusa (estações sem nome, inativos empilhados no turbolift com rótulos sobrepostos, engenharia grande e vazia, desenho horizontal pequeno numa lateral alta) e escolheu "Ponte vista de cima". Redesenhe `scene-model.ts` (pura) e `scene.ts` (pintura):
- Grade vertical (ex.: 48 colunas x 72 linhas, escala inteira pela largura do painel; nunca mais estreita que 240 px): telão no topo (slug, fase, barra de progresso `done/total` e percentual; ou a frase do estado vazio, R42/R50); cadeira do Picard no centro; as outras estações em semicírculo, cada uma com o emoji e o nome embaixo; LaForge no cabeçalho da faixa da engenharia; faixa da engenharia embaixo com até 6 vagas de worker (LaForge + rótulo do ticket, "✓" quando `done`, "+N" para o resto); legenda "aceso = trabalhando · apagado = livre" embaixo.
- Ativo (`count > 0`): sentado, cores vivas, 2 quadros a cada 250 ms. Inativo: na própria estação, esmaecido, parado. Sem turbolift.
- Balão "!" segue a regra do R40.
- Texto legível: altura mínima de 10 px a 240 px de largura; `buildScene` devolve as caixas dos rótulos para o teste provar que nenhuma se sobrepõe.
- Pixel art gerada por código (só `fillRect`/`fillText`/`strokeRect`, nenhuma imagem), personagens genéricos com a cor da divisão e o emoji (sem arte oficial).
Testes (nomes exatos): ajuste os existentes de C38, C39, C41, C42 e C50 ao novo layout e crie `cena mostra o telão com fase e progresso` (C52). Atualize `dist/orca` com `python tools/build.py`. Tire uma captura de conferência com `orca plugin shot` de um plugin carregado só se não precisar de aprovação; senão, use o `plugin shot --scenario` do check, se existir para o painel HTML, ou descreva o layout no relatório.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R38 a R43, R50). Checks: C38, C39, C40, C41, C42, C43, C50, C52.
Captura atual (antes): turbolift no canto com 11 tripulantes empilhados, estações como caixas vazias, engenharia vazia à direita.

#### BOUNDARIES
May change: `src/orca/src/scene-model.ts`, `src/orca/src/scene-model.test.ts`, `src/orca/src/scene.ts`, `src/orca/src/scene.test.ts`, `dist/orca/`, `DECISIONS.md`
Do not touch: `scripts/`, `tools/`, `tests/`, `.github/`, `docs/`, `src/orca/src/worker.ts`, `src/orca/src/panel.tsx`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove, instale nem desinstale plugin.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T15: Cena da Ponte com vida (arco, bonecos, contraste, engenharia compacta)
**Linear**: SC-129
**Depends on**: T14
**Requirements**: R39, R41, R51, R52, R53
**Tests**: plugin
**Gate**: plugin

#### TASK
A avaliação da T14 com o usuário: a cena ficou legível, mas parece um painel de caixas (grade de estações iguais, Picard sem destaque), ativo e livre quase não se distinguem, a engenharia ocupa um terço da altura com 6 vagas vazias e falta "vida" (emoji num pedestal não é personagem). O usuário escolheu os quatro itens:
1. Engenharia compacta (R53): só os workers reais (até 6 e "+N"); sem workers, uma linha "Nenhum worker na engenharia"; a altura liberada vai para a ponte.
2. Contraste de estado (R52): console do ativo aceso com brilho na cor da divisão e "há N min" embaixo (de `lastAt`); livre com no máximo 40% de opacidade; telão com "N tripulantes ativos" ou "tripulação em repouso".
3. Formato de ponte (R51): console em arco ao redor da cadeira do capitão, Picard maior no centro, piso com o desenho da ponte; estações posicionadas no arco, não em grade.
4. Bonecos em pixel art (R51, R39): cabeça e corpo na cor da divisão, emoji como insígnia; ativo sentado digitando (2 quadros a 250 ms); livre de pé parado.
Mantenha: telão (R50), balão "!" (R40), rótulos sem sobreposição e texto de no mínimo 10 px a 240 px (C50), `buildScene` pura (R43), só `fillRect`/`fillText`/`strokeRect` e nenhuma imagem; personagens genéricos, sem semelhança com atores ou arte oficial.
Testes (nomes exatos): `cena compacta a engenharia sem workers` (C53), `cena acende o ativo e conta os ativos no telão` (C54), `cena desenha a ponte em arco com bonecos` (C55); ajuste os existentes se o layout mudar. Atualize `dist/orca` com `python tools/build.py` e registre uma entrada F10-n no DECISIONS.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R38 a R43, R50 a R53). Checks: C38 a C43, C50, C52 a C55.
Captura da T14 (antes): telão bom; 11 caixas iguais em grade; Guinan acesa só pela moldura amarela; engenharia com 6 vagas vazias ocupando um terço; legenda com pouco contraste.
Inspiração (só ideia, sem copiar código nem arte): Pixel Agents e Habblaud (personagens que sentam, digitam e levantam).

#### BOUNDARIES
May change: `src/orca/src/scene-model.ts`, `src/orca/src/scene-model.test.ts`, `src/orca/src/scene.ts`, `src/orca/src/scene.test.ts`, `dist/orca/`, `DECISIONS.md`
Do not touch: `scripts/`, `tools/`, `tests/`, `.github/`, `docs/`, `src/orca/src/worker.ts`, `src/orca/src/panel.tsx`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove, instale nem desinstale plugin.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T16: Ajustes finos da Cena da Ponte
**Linear**: SC-130
**Depends on**: T15
**Requirements**: R52, R54
**Tests**: plugin
**Gate**: plugin

#### TASK
Na captura da T15 o usuário pediu três ajustes (R54):
1. "há 0 min" vira "agora" quando `lastAt` tem menos de 1 minuto (manter "há N min", "há N h", "há N d" depois).
2. Bonecos maiores: pelo menos 16 px de altura a 240 px de largura, com sentado (ativo) e de pé (livre) claramente diferentes nessa escala.
3. O anel da ponte estica para ocupar a altura do painel: a grade acompanha a proporção largura/altura do painel (o `scene.ts` mede o palco e redesenha quando ele muda de tamanho, ex.: `ResizeObserver`), sem faixa vazia abaixo da legenda. `buildScene` continua pura, recebendo a proporção (ou o número de linhas) como parâmetro.
Mantenha tudo das T14/T15 (telão, balão "!", rótulos sem sobreposição, texto de no mínimo 10 px, engenharia compacta, só `fillRect`/`fillText`/`strokeRect`).
Testes (nomes exatos): `cena mostra agora para atividade recente` (C56) e `cena estica o anel e aumenta os bonecos` (C57); ajuste os existentes se preciso. Atualize `dist/orca` com `python tools/build.py` e registre uma entrada F10-n no DECISIONS.

#### CONTEXT
Spec: `.specs/features/fase-10-ponte/spec.md` (R50 a R54). Checks: C50, C52 a C57.
Captura da T15 (antes): anel com o Picard no centro e 11 estações; Guinan ativa com "há 0 min"; bonecos pequenos; faixa vazia abaixo da legenda numa lateral alta.

#### BOUNDARIES
May change: `src/orca/src/scene-model.ts`, `src/orca/src/scene-model.test.ts`, `src/orca/src/scene.ts`, `src/orca/src/scene.test.ts`, `dist/orca/`, `DECISIONS.md`
Do not touch: `scripts/`, `tools/`, `tests/`, `.github/`, `docs/`, `src/orca/src/worker.ts`, `src/orca/src/panel.tsx`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca aprove, instale nem desinstale plugin.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

## Checks

**Build**: `python tools/build.py --check`; `orca plugin validate src/orca --json`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v`
**Run plugin**: `orca plugin test src/orca`

**C1** - O snapshot imprime as chaves do contrato com `schemaVersion` 1 e sai com 0 (R1)
Proof: run unit | test_snapshot_keys ... ok

**C2** - A tripulação conta só sessões válidas (15 min hook, 60 min cli) e traz `lastAt` e `cli · modelo` pela D17 (R2)
Proof: run unit | test_snapshot_crew_ttl ... ok

**C3** - `gitMode` traz mode, label e recordedAt do `session.json` do worktree, ou null sem ele (R3)
Proof: run unit | test_snapshot_git_mode ... ok

**C4** - A feature escolhida é a não `done` com o Handoff mais recente; todas `done` → a mais recente com `done: true` (R4)
Proof: run unit | test_snapshot_feature_choice ... ok

**C5** - A feature traz slug, phase, size, linear, integrationBranch, progress, breaker e os caminhos existentes (R5)
Proof: run unit | test_snapshot_feature_fields ... ok

**C6** - Cada `**Dispatched:**` vira um worker com label, issues, base, dispatch e model, na ordem (R6)
Proof: run unit | test_snapshot_workers ... ok

**C7** - Worktree sem `.starcode/config.json` nem `.specs/` → `starcode: false`, seções vazias, exit 0 (R7)
Proof: run unit | test_snapshot_sem_starcode ... ok

**C8** - Fonte ausente, JSON inválido ou maior que 1 MiB vira item em `errors` sem abortar (R8)
Proof: run unit | test_snapshot_fonte_invalida ... ok

**C9** - `--path` inexistente ou fora do Git imprime `worktree inválido: <path>` e sai com 2 (R9)
Proof: run unit | test_snapshot_worktree_invalido ... ok

**C10** - O snapshot não cria, altera nem apaga arquivo (árvore e mtimes iguais) (R10)
Proof: run unit | test_snapshot_somente_leitura ... ok

**C11** - O worker acha o caminho em foco cruzando o ramo com `workspace.list` (R11)
Proof: run plugin | ✔ worker acha o worktree em foco pelo ramo

**C12** - Sem casamento de ramo, com ramo repetido sem nome casado ou com contexto nulo, o estado é `sem-worktree` (R12)
Proof: run plugin | ✔ worker sem worktree em foco

**C13** - `agent.status.changed` gera um novo snapshot publicado em `ponte.state` (R13)
Proof: run plugin | ✔ worker publica o estado após agent.status.changed

**C14** - Eventos em menos de 300 ms geram um único snapshot (R14)
Proof: run plugin | ✔ worker agrupa eventos em 300 ms

**C15** - O resultado de um foco antigo é descartado (R15)
Proof: run plugin | ✔ worker descarta snapshot de foco antigo

**C16** - A issue vem do `linkedLinearIssue` do worktree via `orca linear issue <ID> --json` e fica em cache por 60 s (R16)
Proof: run plugin | ✔ worker consulta a issue vinculada e guarda em cache por 60 s

**C17** - Com o Linear falhando, o painel recebe o ID do Handoff e a nota "Linear indisponível", sem nova chamada antes do cache (R17)
Proof: run plugin | ✔ worker sem Linear mostra o ID do Handoff

**C18** - Snapshot falho → `status: erro`, `stale: true` e último estado bom mantido (R18)
Proof: run plugin | ✔ worker com snapshot falho marca desatualizado

**C19** - A barra de status mostra `🖖 <slug> · <phase> · modo <N>`, some sem StarCode e fica `warning` com disjuntor aberto ou agente em `blocked`/`waiting` (R19)
Proof: run plugin | ✔ worker atualiza a barra de status

**C20** - O item `ponte` da barra roda `starcode-ponte.toggle` com a ação `sidebar.right.toggle` (R20)
Proof: run unit | test_manifest_toggle_da_barra ... ok

**C21** - Ao abrir, o painel pede `ponte.state` e mostra as seis seções e a hora da atualização (R21)
Proof: run plugin | ✔ painel pede o estado ao abrir

**C22** - Um `ponte.state` publicado redesenha o painel sem ação do usuário (R22)
Proof: run plugin | ✔ painel redesenha com ponte.state

**C23** - A seção Tripulação mostra só `count > 0`, ou "Tripulação em repouso" (R23)
Proof: run plugin | ✔ painel mostra só tripulantes ativos

**C24** - A seção Fase SDD mostra slug, fase, tamanho, `done/total (percent%)` e "Disjuntor aberto" (R24)
Proof: run plugin | ✔ painel mostra fase e progresso

**C25** - Um worker cujo agente tem o rótulo no título mostra o estado do agente; sem workers, "Nenhum worker despachado" (R25)
Proof: run plugin | ✔ painel casa worker com agente

**C26** - Com `starcode: false`, o painel mostra só "StarCode não configurado neste worktree" e Atualizar agora (R26)
Proof: run plugin | ✔ painel sem StarCode

**C27** - Uma seção com erro mostra "indisponível" e o motivo, e as outras continuam (R27)
Proof: run plugin | ✔ painel com seção indisponível

**C28** - Abrir spec/tasks/Handoff chama `editor.open` com o caminho relativo ao worktree; arquivo ausente desabilita o botão (R28)
Proof: run plugin | ✔ atalho abre spec tasks e handoff

**C29** - Abrir a issue chama `shell.openExternal` com a URL; sem URL o botão fica desabilitado (R29)
Proof: run plugin | ✔ atalho abre a issue no navegador

**C30** - Iniciar o Picard chama `agent.launch` uma vez com o agente do Picard e o prompt de engajar (R30)
Proof: run plugin | ✔ atalho inicia o Picard uma vez

**C31** - Agente que a Orca não lança mostra a mensagem e não chama `agent.launch` (R31)
Proof: run plugin | ✔ atalho recusa agente que a Orca não lança

**C32** - Atualizar agora refaz snapshot e consulta ao Linear ignorando o cache (R32)
Proof: run plugin | ✔ atualizar agora ignora o cache

**C33** - O build gera `dist/orca` e o `--check` falha quando ele está desatualizado (R33)
Proof: run unit | test_build_check_cobre_dist_orca ... ok

**C34** - `install_local.py --cli orca` valida, instala e, com exit 3, mostra o pedido de aprovação sem passar `--approve` (R34)
Proof: run unit | test_install_orca_aprovacao_nunca_automatica ... ok

**C35** - O manifesto declara os painéis `ponte` e `ponte-cena`, só as cinco capabilities e `engines.orca` `>=1.4.248` (R35)
Proof: run unit | test_manifest_capabilities_e_engines ... ok

**C36** - DECISIONS tem F10-n, CREDITS cita Pixel Agents e Habblaud, CHANGELOG tem `## [1.4.0] - não lançada`, compatibilidade e README citam o painel (R36)
Proof: run unit | test_release_docs_f10 ... ok

**C37** - `docs/aceite/fase-10.md` tem as seis seções e o `## Reaceite` com `**Resultado**` e o caminho da captura (R37)
Proof: run unit | test_fase10_acceptance_sections ... ok

**C38** - A cena tem layout vertical com telão, uma estação por tripulante (12) com emoji e nome, e a faixa da engenharia (R38)
Proof: run plugin | ✔ cena tem uma estação por tripulante e a engenharia

**C39** - Tripulante com `count > 0` fica sentado e alterna 2 quadros a cada 250 ms; com 0 fica apagado na própria estação (R39)
Proof: run plugin | ✔ cena senta tripulante ativo e anima a cada 250 ms

**C40** - Agente em `blocked`/`waiting` põe o balão "!" no worker casado, senão no ativo mais recente, senão no Picard (R40)
Proof: run plugin | ✔ cena põe o balão no personagem do agente bloqueado

**C41** - Até 6 workers desenhados na engenharia com rótulo, o resto em "+N", e `done` com "✓" (R41)
Proof: run plugin | ✔ cena desenha até 6 workers e +N

**C42** - Sem StarCode, sem worktree ou com erro sem estado bom, a cena fica vazia com a frase do estado (R42)
Proof: run plugin | ✔ cena vazia mostra a frase do estado

**C43** - A pintura só lê o resultado de `buildScene` e nunca chama `drawImage` (R43, R38)
Proof: run plugin | ✔ pintura da cena só lê o modelo e não usa imagem

**C44** - O diário guarda no máximo 20 entradas e o painel mostra as 10 mais recentes (R44)
Proof: run plugin | ✔ diário guarda 20 entradas e o painel mostra 10

**C45** - O painel `ponte-cena` tem `entry` `src/scene.ts`, o script cria o canvas quando falta e o código do painel não tem import relativo sem extensão (R45)
Proof: run plugin | ✔ cena cria o canvas e importa com caminho servido

**C46** - Sem issue vinculada ou com o Linear falhando, o painel mostra a nota junto do ID do Handoff (R46)
Proof: run plugin | ✔ painel mostra a nota da issue do Handoff

**C47** - Com 240 px os botões dos Atalhos quebram em linhas, sem rolagem horizontal (R47)
Proof: run plugin | ✔ painel estreito quebra os atalhos

**C48** - Com vários workspaces no mesmo ramo, o worker escolhe o de `name` igual ao `displayName` do foco (R11)
Proof: run plugin | ✔ worker desempata ramo igual pelo nome

**C49** - Falha de processo externo, `editor.open` ou `agent.launch` gera uma linha no log com a ação e a mensagem, e vínculo nulo mostra "Sem issue vinculada" (R48)
Proof: run plugin | ✔ worker registra falhas no log

**C50** - Nenhum rótulo da cena se sobrepõe a outro e o texto tem pelo menos 10 px a 240 px de largura (R39, R50)
Proof: run plugin | ✔ cena sem rótulos sobrepostos

**C51** - DECISIONS, `docs/compatibilidade.md` e o aceite registram as duas limitações da Orca (Picard em segundo plano, `orca` falhando no worker) (R49)
Proof: run unit | test_fase10_limitacoes_registradas ... ok

**C52** - O telão mostra slug, fase e progresso da feature, e a legenda aparece embaixo (R50)
Proof: run plugin | ✔ cena mostra o telão com fase e progresso

**C53** - Sem workers, a engenharia vira uma linha "Nenhum worker na engenharia" e a ponte ganha a altura; com workers, só os reais (até 6 e "+N") (R53)
Proof: run plugin | ✔ cena compacta a engenharia sem workers

**C54** - O ativo tem console aceso e "há N min", o livre fica com no máximo 40% de opacidade e o telão conta os ativos (R52)
Proof: run plugin | ✔ cena acende o ativo e conta os ativos no telão

**C55** - As estações ficam num arco ao redor do Picard, maior no centro, e cada tripulante é um boneco sentado (ativo) ou de pé (livre) (R51)
Proof: run plugin | ✔ cena desenha a ponte em arco com bonecos

**C56** - Com `lastAt` há menos de 1 minuto, o ativo mostra "agora" (R54)
Proof: run plugin | ✔ cena mostra agora para atividade recente

**C57** - O anel ocupa a altura do painel em proporções diferentes e cada boneco tem pelo menos 16 px a 240 px de largura (R54)
Proof: run plugin | ✔ cena estica o anel e aumenta os bonecos

## Handoff

**Phase:** published
**Size:** GRANDE
**Git mode:** 3
**Next:** T14 (novo visual da cena), depois provas, Q das checks novas, push e PR
**Linear:** SC-17; SC-115..SC-130; doc https://linear.app/cifren/document/spec-fase-10-painel-orca-ponte-74f5047c87b7
**Integration branch:** feature/fase-10-ponte
**Last integrated:** T16 r2 via 4524bd6
**Dispatched:** none
**Settled:** 2026-11-09: spec aprovada: user "sim"; 2026-11-09: pedido do usuário: analisar Pixel Agents/Habblaud; análise em analise-referencias.md; spec volta a Draft com R38-R44; 2026-11-09: spec ajustada e tasks aprovadas e publicadas: user "sim"; 2026-11-10: aceite real com 3 defeitos; user: "Ticket de correção (Recommended)"; T10 (SC-124) com R45-R47 e R16 emendado; 2026-11-10: reaceite: reinstalação sem nova aprovação (mesmo acesso); cena desenha; foco em main casava ApuraBolsa; T11 (SC-125) com R11/R12 emendados, sob a escolha "Ticket de correção"; 2026-11-10: reaceite manual do usuário: evento de agente ok; Abrir spec/tasks/Handoff com 'path must be relative'; Iniciar Picard sem terminal; T12 (SC-126) com R28/R30/R39 emendados e R48, sob a escolha "Ticket de correção"; 2026-11-10: reaceite: atalhos de arquivo ok; Picard em segundo plano sem prompt e orca falhando no worker; user: "Limitações registradas (Recommended)"; terminais ociosos do teste fechados (user: "Fechar os dois"); T13 (SC-127) com R49; 2026-11-11: usuário achou a cena confusa; escolheu "Ponte vista de cima (Recommended)"; T14 (SC-128) com R38-R43 emendados e R50; push/PR ainda não confirmados; 2026-11-11: avaliação da cena da T14: user "Os quatro itens (Recommended)"; T15 (SC-129) com R51-R53; 2026-11-11: captura da T15: user "faz os três ajustes"; T16 (SC-130) com R54
**Attempts:** gate-T7=1, gate-T10=1, proofs=2, gate-T16=1
**Reports:** 2026-11-09: T1: ponte.py snapshot + 10 testes + dist; suíte 583 OK; commit 531e244; integrado em a3d315c; 2026-11-09: T2: manifesto, worker, protocol, 11 testes do plugin, test_orca_manifest; validate falha até a T3 criar src/panel.tsx (manifesto aponta para ele, fatiamento do Data); commit 359b579; integrado em 90b14a4; 2026-11-10: T3: painel de componentes + check + 7 testes; validate/check/test do plugin verdes (18 testes); commit f25debb; integrado em d83029b; 2026-11-10: T5: buildScene + 5 testes; no ramo de integração validate/check/test verdes (23 testes); commit 49837b5; integrado em ac10fc8; 2026-11-10: T4: atalhos (editor.open, openExternal, agent.launch com trava, recusa) e diário de bordo; plugin 32 testes verdes; commit 4bcc434; integrado em 7b0be63; 2026-11-10: T6: painel HTML ponte-cena (canvas, sem drawImage), 2 testes, manifesto com 2 painéis; integração: plugin 34 testes; commit 961a09f; integrado em deb24a6; 2026-11-10: T7 r1: dist/orca/ponte.py falha ao ler a tripulação (falta crew.json gerado; cai em miniyaml); suíte 592 OK; redespacho no mesmo worktree; 2026-11-10: T7: dist/orca + install_local --cli orca + crew.json (r2) + regressão por subprocesso; suíte 593 OK; integrado em 291fb1d; 2026-11-10: T8: DECISIONS F10-n, CREDITS, CHANGELOG 1.4.0, compatibilidade, README, CI condicional; check_decisions OK; aviso: cabeçalho do commit com 101 caracteres (aceito); integrado em 7392422; 2026-11-10: T9: aceite com 3 aprovados (instalação, worktree A, worktree B) e 3 reprovados (evento de agente, cena em branco, atalhos não clicáveis pela CLI); pendências de código: cena (entry html carrega .ts sem transpilar), issue via --current ignora o cwd, botões cortados em 237 px; integrado em 6b940d7; 2026-11-10: T10 r1: plugin 37/37, validate/check ok; suíte 1 falha: test_build exige src/scene.html removido; May change ampliado (tests/test_build.py); devolvido ao worker; 2026-11-10: T10 r2: test_build ajustado; suíte 596 OK; plugin 37/37; integrado em 2ef3055; falta reinstalar e refazer o aceite com o usuário; 2026-11-10: T11: pickFocus (ramo + nome); plugin 38/38; suíte 596 OK; integrado em 80a0aaf; 2026-11-10: reaceite r2 (Picard, capturas): painel e cena seguem o worktree principal (modo 3, fase-10-ponte, 11/11, Data); cena desenha 12 estações; pendências: issue mostra 'Linear indisponível' num worktree sem vínculo (o CLI responde linkedLinearIssue null em 0,6 s: o exec do 'orca' falha dentro do worker, erro engolido sem log); tripulantes inativos empilhados no turbolift; 2026-11-10: T12: caminhos relativos, terminalId no log, falhas no log, fallback do binário orca, turbolift em grade; plugin 40/40; integrado em 0c85583; 2026-11-10: proofs r1: C51 falhou por formato (docstring no teste quebra a linha 'nome ... ok' do -v); devolvido ao worker da T13; 2026-11-10: T13: aceite com Reaceite (aprovado com limitações), DECISIONS F10-9, compatibilidade, aviso do Picard; suíte 597 OK; plugin 40/40; integrado em 73f8957; 2026-11-10: proofs: 51 checks verdes (r2 após docstring da C51); 2026-11-10: Q (codex): FAIL; achados: R8 handoff >1 MiB silencioso; C8/C21/C26 fracos; linear_ids duplica IDs; rodada única pós-Q; 2026-11-10: pós-Q: handoff >1 MiB e ilegível em errors, linear_ids sem duplicatas, C8/C21/C26 reforçadas; suíte 599 OK; plugin 40/40; integrado em 4a73a95; proofs refeitas no HEAD; 2026-11-10: proofs r3: Build vermelho (check_decisions: scripts/ mudou em ca7c8ba sem entrada F10-n); devolvido ao worker pós-Q; 2026-11-10: proofs r4 verdes no HEAD 29aff98; achados do Q fechados em ca7c8ba e 0232e19; 2026-11-10: Guinan: lições L4-L7; retro com 7 sugestões (não aplicadas); 2026-11-11: T14: cena vertical (telão, semicírculo, engenharia embaixo, legenda); integrado em 62bbc6c; 2026-11-11: T15: ponte em arco com bonecos, contraste e engenharia compacta; plugin 44/44; integrado em bc78974; 2026-11-11: T16: agora, bonecos 1,3x, anel na altura do painel; plugin 46/46; integrado em 43982fd; 2026-11-11: T16 r1 na Orca: anel, agora e bonecos ok; página mais alta que o painel (barra de rolagem, legenda cortada); devolvido ao worker; 2026-11-11: T16 r2: cena cabe no painel com a legenda visível; integrado em 4524bd6; 2026-11-11: provas regeradas e verdes após a T16 r2; Q dos checks novos a despachar; 2026-11-11: Q r2 (codex, reverificação após T14-T16): PASS nos 57 checks; sem achados; gate done verde; 2026-11-11: PR #24 aberto para a main
**Breaker:** closed
