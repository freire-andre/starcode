# Fase 10 — Painel Orca "Ponte" (v1.4): Spec

**Approved**: 2026-11-09 - user: "sim"

**Size**: LARGE
**Risk triggers**: none
**Status**: Approved

## Context

O estado do StarCode fica espalhado em arquivos e só aparece no banner, quando uma sessão começa. Os arquivos são: tripulação em `.starcode/live/sessions.json` e `crew.json`, progresso em `progress.json`, modo Git em `<git-dir>/starcode/session.json` e fase e workers no `tasks.md ## Handoff`. Na Orca, o usuário trabalha com vários worktrees e workers e não tem uma visão contínua do worktree em foco. A Fase 10 do plano entrega o painel "Ponte", um plugin da Orca que mostra tripulação, modo Git, issue do worktree, fase SDD, workers da Frota e atalhos. O painel se atualiza sozinho quando um evento de agente acontece. A pedido do usuário, a fase também entrega a "Cena da Ponte": um segundo painel, em pixel art, com a tripulação e os workers trabalhando nas estações da ponte. A ideia vem do Pixel Agents e do Habblaud (análise em `.specs/features/fase-10-ponte/analise-referencias.md`).

Sucesso: o painel, a cena e o item da barra de status refletem o estado real do worktree em foco e mudam quando o foco muda ou um agente muda de estado, sem recarregar.

Discovery: `.specs/features/fase-10-ponte/context.md`. Issue: SC-17.

## Scope

- `scripts/ponte.py` (novo, Python stdlib): `snapshot --path <worktree> --json` lê o estado do StarCode de um worktree e imprime um JSON único (contrato em Data & Contracts). Reusa `scripts/crew_live.py` (validade das sessões) e o leitor do Handoff de `scripts/handoff.py`.
- `src/orca/` (novo): fonte do plugin da Orca "Ponte":
  - `orca-plugin.json` (`trusted-worker`, `main`, um painel de componentes `.tsx`, um item na barra de status, comandos);
  - `src/worker.ts`: escuta `workspace.changed` e `agent.status.changed`, roda o `ponte.py` e `orca linear issue --current --json`, atende o painel com `orca.panels.handle` e atualiza a barra de status;
  - `src/panel.tsx`, `src/protocol.ts`;
  - `src/scene-model.ts` (modelo da cena: estações, personagens e estados, sem desenho) e `src/scene.html` + `src/scene.ts` (painel HTML `ponte-cena` com canvas e arte de pixel gerada por código);
  - testes do plugin (`orca plugin test`) e estados do `src/panel.check.ts`.
- `tools/build.py`: gera `dist/orca/`, que leva o plugin e uma cópia do `ponte.py` e dos módulos que ele importa. O `--check` também cobre `dist/orca/`.
- `tools/install_local.py`: alvo `orca` (`orca plugin install dist/orca`). Mostra o pedido de aprovação da Orca e nunca aprova sozinho.
- Testes `unittest` do `ponte.py`, do build e do `install_local` (sem Orca real: binário falso).
- Registros:
  - `DECISIONS.md`: entradas F10-n;
  - `CHANGELOG.md`: `## [1.4.0] - não lançada`;
  - `docs/compatibilidade.md`: linha do painel;
  - `README.md`: instalação do painel;
  - `.github/workflows/ci.yml`: `orca plugin validate` só se o binário existir, senão pula com aviso;
  - `dist/` regenerado.
- `CREDITS.md`: Pixel Agents e Habblaud como inspiração (nenhum código ou arte copiado).
- Aceite real em `docs/aceite/fase-10.md`, com captura (`orca plugin shot`) do painel, da cena e da barra de status em dois worktrees diferentes e depois de um evento de agente.

## Non-Goals

- Publicar o plugin no catálogo da Orca ou num repo próprio.
- Qualquer escrita de estado pelo plugin: `.specs/`, `.starcode/live/`, Handoff (D28), `session.json`, Linear.
- Verificação de telas (Fase 11); snapshot e raio de impacto (Fase 12).
- Painel nos outros CLIs (o painel é da Orca, vale para qualquer agente que rode nela).
- Controlar workers (parar, reenviar, responder) pelo painel.
- Na cena: copiar código ou sprites do Pixel Agents ou do Habblaud; ler transcripts `.jsonl` ou mostrar o tipo de ferramenta (lendo/editando/rodando); servidor local, porta, som, eventos do GitHub, editor de layout; semelhança com atores ou arte oficial de Star Trek.

## Requirements

### Snapshot do estado (`ponte.py`)

- **R1** - WHEN `python scripts/ponte.py snapshot --path <worktree> --json` roda num worktree com StarCode THEN the system SHALL imprimir um objeto JSON com as chaves `schemaVersion` (1), `worktree`, `starcode`, `crew`, `gitMode`, `feature`, `workers`, `errors` e sair com 0.
- **R2** - WHEN o snapshot lê a tripulação THEN the system SHALL contar os tripulantes ativos a partir de `sessions.json` no worktree principal, com a mesma validade do `crew_live.py` (15 min `hook`, 60 min `cli`). Cada item de `crew` tem `member`, `emoji`, `name`, `count` (>0 só para os ativos), `lastAt` (a hora ISO da sessão válida mais recente do tripulante, ou `null`) e `cliModel` vindo da config pela precedência D17.
- **R3** - WHEN o snapshot lê o modo Git THEN the system SHALL devolver em `gitMode` o `mode` (1–4), o `label` e o `recordedAt` do `<git-dir>/starcode/session.json` do próprio worktree. Sem o arquivo, devolve `null`.
- **R4** - WHEN há features em `.specs/features/` THEN the system SHALL escolher como `feature` a de `**Phase:**` diferente de `done` com o Handoff mais recente (data de modificação do arquivo do Handoff). Se todas estiverem `done`, escolhe a mais recente, com `done: true`.
- **R5** - WHEN uma feature é escolhida THEN the system SHALL devolver `slug`, `phase`, `size`, `linear` (os IDs do campo `**Linear:**`), `integrationBranch`, `progress` (`done`, `total`, `percent` do `progress.json` ou da contagem de tasks), `breaker` (`open`/`closed`) e os caminhos absolutos existentes de `context.md`, `spec.md` e `tasks.md`.
- **R6** - WHEN o Handoff da feature tem linhas `**Dispatched:**` THEN the system SHALL devolver em `workers` um item por despacho, com `label`, `issues`, `base`, `dispatch` e `model`, na ordem do arquivo.
- **R7** - IF o worktree não tem `.starcode/config.json` nem `.specs/` THEN the system SHALL devolver `starcode: false`, com `crew`, `workers` vazios e `gitMode`, `feature` nulos, e sair com 0.
- **R8** - IF uma fonte está ausente, ilegível, com JSON inválido ou passa de 1 MiB THEN the system SHALL deixar a seção correspondente nula ou vazia e acrescentar em `errors` um item `{ "source": "<caminho relativo>", "message": "<motivo em PT-BR, uma linha>" }`, sem abortar e sem stack trace.
- **R9** - IF `--path` não existe ou não é um repositório Git THEN the system SHALL imprimir `{"schemaVersion":1,"error":"worktree inválido: <path>"}` e sair com 2.
- **R10** - The system SHALL ler apenas: o snapshot nunca cria, altera ou apaga arquivo (testado comparando a árvore e os `mtime` antes e depois).

### Worker do plugin

- **R11** - WHEN o worker recebe `workspace.changed` com `context` não nulo THEN the system SHALL achar o caminho do worktree em foco em `workspace.list` pelo workspace com o mesmo ramo (`branch`, aceitando a forma `refs/heads/<ramo>`) e o mesmo nome (`name` igual a `context.displayName`); com um único workspace no ramo, ele vale mesmo sem casar o nome; e rodar o snapshot desse caminho (emenda 2026-11-10: o aceite real mostrou três worktrees de repositórios diferentes no ramo `main`, e o primeiro, de outro repositório, era escolhido).
- **R12** - IF nenhum workspace de `workspace.list` casa com o ramo do foco, vários casam com o ramo e nenhum com o nome, ou `context` é nulo THEN the system SHALL devolver ao painel o estado `sem-worktree` com a frase "Nenhum worktree em foco".
- **R13** - WHEN o worker recebe `agent.status.changed` THEN the system SHALL refazer o snapshot do worktree em foco e enviar o novo estado aos painéis abertos (`orca.panels.post('ponte.state', ...)`).
- **R14** - WHEN chegam vários eventos em menos de 300 ms THEN the system SHALL rodar um único snapshot depois do último (debounce de 300 ms).
- **R15** - IF o foco muda enquanto um snapshot está em andamento THEN the system SHALL descartar o resultado antigo e publicar só o do worktree em foco atual.
- **R16** - WHEN o worktree em foco tem issue do Linear vinculada na Orca (`linkedLinearIssue` de `orca worktree show --worktree path:<caminho> --json`) THEN the system SHALL obter ID, título e estado com `orca linear issue <ID> --json` e guardar o resultado em cache por 60 s por worktree (emenda 2026-11-10: `orca linear issue --current` usa o worktree do terminal que chama, não o `cwd`, e no worker sempre responde "não vinculado").
- **R17** - IF `orca linear issue` falha, demora mais de 10 s ou o worktree não tem issue vinculada THEN the system SHALL mostrar só o primeiro ID do campo `**Linear:**` (ou nada) com a nota "Linear indisponível" ou "Sem issue vinculada", sem repetir a chamada antes de vencer o cache.
- **R18** - IF o `python` não roda, o `ponte.py` sai com código diferente de 0 ou demora mais de 10 s THEN the system SHALL mostrar o estado `erro` com a primeira linha do erro e manter o último estado bom com a marca "desatualizado".
- **R19** - WHEN o estado do worktree em foco muda THEN the system SHALL atualizar o item da barra de status `ponte` com o texto `🖖 <slug> · <phase> · modo <N>`. Sem feature: `🖖 StarCode · modo <N>`. Sem StarCode: o item fica escondido (`visible: false`). O `tone` é `warning` com o disjuntor aberto ou com algum agente do worktree em foco em `blocked` ou `waiting`, e `neutral` nos outros casos.
- **R20** - WHEN o usuário pressiona o item da barra de status THEN the system SHALL rodar o comando `starcode-ponte.toggle`, de ação nativa `sidebar.right.toggle`, que mostra ou esconde a barra lateral direita onde fica o painel Ponte (a API de plugins da Orca 1.4.255 não abre um painel específico).

### Painel

- **R21** - WHEN o painel abre THEN the system SHALL pedir o estado ao worker (`plugin.request('ponte.state')`, tempo limite de 15 s) e mostrar as seções Tripulação, Modo Git, Issue, Fase SDD, Workers da Frota e Atalhos, com a hora da última atualização em `RelativeTime`.
- **R22** - WHEN o worker publica `ponte.state` THEN the system SHALL redesenhar o painel com o novo estado sem ação do usuário.
- **R23** - The system SHALL mostrar na seção Tripulação só os tripulantes com `count > 0`, cada um com emoji, nome, `cli · modelo` e a contagem quando ela passar de 1. Sem nenhum ativo, mostra "Tripulação em repouso".
- **R24** - The system SHALL mostrar na seção Fase SDD o slug, a fase, o tamanho e a barra de progresso `done/total (percent%)`, e o aviso "Disjuntor aberto" quando `breaker` for `open`.
- **R25** - The system SHALL mostrar na seção Workers da Frota uma linha por item de `workers` (rótulo, issues, modelo). Quando o terminal de um agente de `agents.list` tiver no título o rótulo ou o ID da issue, a linha mostra o estado do agente (`working`, `blocked`, `waiting`, `done`). Sem workers: "Nenhum worker despachado".
- **R26** - IF o estado é `starcode: false` THEN the system SHALL mostrar só a frase "StarCode não configurado neste worktree" e o atalho Atualizar agora.
- **R27** - IF uma seção tem erro em `errors` THEN the system SHALL mostrar nessa seção "indisponível" e o motivo em uma linha, mantendo as outras seções.

### Atalhos

- **R28** - WHEN o usuário pressiona Abrir spec, Abrir tasks ou Abrir Handoff THEN the system SHALL abrir o arquivo correspondente da feature numa aba do editor da Orca (`editor.open` com o caminho relativo à raiz do worktree em foco, separado por `/`; emenda 2026-11-10: o reaceite mostrou "path must be relative and inside the workspace" com o caminho absoluto do snapshot). O Handoff abre o arquivo onde está a seção `## Handoff`. O botão de um arquivo que não existe fica desabilitado.
- **R29** - WHEN o usuário pressiona Abrir a issue no Linear THEN the system SHALL abrir a URL da issue no navegador (`shell.openExternal`). Sem URL conhecida, o botão fica desabilitado.
- **R30** - WHEN o usuário pressiona Iniciar o Picard THEN the system SHALL iniciar um agente no worktree em foco (`agent.launch`), com o agente do Picard pela precedência D17 e o prompt `/starcode:engajar` (Claude) ou o equivalente do CLI, e desabilitar o botão até o lançamento responder; com sucesso, o painel mostra "Picard iniciado em segundo plano" e o worker registra o `terminalId` no log do plugin; o botão avisa que o agente abre em segundo plano (emenda 2026-11-10: no reaceite a tela mudou e nenhum terminal novo ficou no worktree, sem erro visível).
- **R31** - IF o agente do Picard não é um agente que a Orca lança THEN the system SHALL mostrar "Agente " seguido do nome do agente e " não pode ser iniciado pela Orca" (ex.: "Agente gemini não pode ser iniciado pela Orca") e não lançar nada.
- **R32** - WHEN o usuário pressiona Atualizar agora THEN the system SHALL refazer o snapshot e a consulta ao Linear ignorando o cache.

### Cena da Ponte

- **R38** - WHEN o painel `ponte-cena` abre THEN the system SHALL desenhar num canvas a ponte em pixel art gerada por código (sem arquivo de imagem), em layout vertical que ocupa a largura do painel: telão no topo, a cadeira do Picard no centro, as demais estações em semicírculo com o emoji e o nome de cada tripulante sempre legíveis embaixo (LaForge no cabeçalho da engenharia) e a engenharia como faixa inferior para os workers, usando o mesmo estado `ponte.state` do painel de componentes (emenda 2026-11-11, user: "Ponte vista de cima": a cena anterior tinha estações sem nome, inativos empilhados e espaço vazio).
- **R39** - WHILE um tripulante tem `count > 0` the system SHALL desenhá-lo sentado na sua estação com a animação "trabalhando" (2 quadros alternados a cada 250 ms). Com `count = 0`, ele fica na própria estação, apagado (cores esmaecidas) e parado; nenhum rótulo se sobrepõe a outro (emenda 2026-11-11: o turbolift sai da cena).
- **R40** - WHEN um agente da Orca está em `blocked` ou `waiting` THEN the system SHALL mostrar um balão "!" acima do personagem ligado a ele: o LaForge do worker cujo rótulo ou issue aparece no título do agente, ou, sem casamento, o tripulante ativo com `lastAt` mais recente (Picard se nenhum estiver ativo).
- **R41** - WHEN há workers em `workers` THEN the system SHALL desenhar uma vaga na faixa da engenharia por worker, com um LaForge e o rótulo do ticket embaixo, até 6, e um marcador "+N" para os demais. Worker com agente `done` mostra "✓".
- **R42** - IF o estado é `starcode: false`, `sem-worktree` ou `erro` sem estado bom anterior THEN the system SHALL desenhar a ponte vazia com a frase do estado (as mesmas de R12, R18 e R26) no telão.
- **R43** - The system SHALL calcular posições, estados e balões da cena numa função pura `buildScene(estado, agentes)` em `scene-model.ts`, sem acesso ao DOM, e o desenho só lê o resultado dela.

### Diário de bordo

- **R44** - WHEN o worker publica um estado com mudança de estado de agente, de worktree em foco ou de fase THEN the system SHALL acrescentar uma entrada `{ at, text }` em PT-BR ao diário (no máximo 20, as mais antigas saem), enviá-lo junto com `ponte.state` e mostrar as 10 mais recentes na seção "Diário de bordo" do painel de componentes. O diário vive só na memória do worker.
- **R45** - WHEN o painel `ponte-cena` carrega na Orca instalada THEN the system SHALL desenhar a cena: o `entry` do painel é o módulo `src/scene.ts` (a Orca transpila e gera a página), o script cria o canvas quando a página não tem um, e todo import em tempo de execução do código do painel usa um caminho que a Orca serve (emenda 2026-11-10: o aceite real mostrou a cena em branco porque `scene.html` carregava `./scene.ts` sem transpilar e importava `./scene-model` sem extensão).
- **R46** - IF a issue do painel vem do Handoff (sem vínculo ou com o Linear falhando) THEN the system SHALL mostrar a nota ("Sem issue vinculada" ou "Linear indisponível") junto do ID, em vez de título e estado vazios (emenda 2026-11-10).
- **R47** - WHEN o painel `ponte` tem 240 px de largura ou menos THEN the system SHALL quebrar os botões dos Atalhos em linhas, sem rolagem horizontal nem botão cortado (emenda 2026-11-10: com 237 px "Abrir tasks" e "Iniciar o Picard" ficavam cortados).
- **R48** - IF uma chamada externa do worker falha (processo `orca` ou `python`, `editor.open`, `agent.launch`) THEN the system SHALL registrar no log do plugin (`console.error`) uma linha com a ação e a mensagem do erro, sem stack trace e sem segredo, e a issue sem vínculo confirmado pelo `orca worktree show` mostra "Sem issue vinculada", nunca "Linear indisponível" (emenda 2026-11-10: no reaceite a issue de um worktree sem vínculo mostrou "Linear indisponível" e o erro não apareceu em `orca plugin logs`).
- **R49** - The system SHALL registrar no aceite, no DECISIONS e em `docs/compatibilidade.md` as duas limitações conhecidas da Orca 1.4.255 achadas no reaceite: `agent.launch` abre o agente num terminal em segundo plano, sem aba visível e sem o prompt enviado; e o processo `orca` chamado de dentro do worker do plugin falha (`node:internal/modules/cjs/loader`), então a issue mostra só o ID do Handoff com a nota "Linear indisponível" (emenda 2026-11-10, user: "Limitações registradas (Recommended)").
- **R50** - WHILE há uma feature no estado the system SHALL mostrar no telão o slug, a fase e a barra de progresso (`done/total`, percentual) e, embaixo da cena, a legenda "aceso = trabalhando · apagado = livre"; o texto da cena tem altura mínima de 10 px na largura de 240 px (emenda 2026-11-11).
- **R51** - The system SHALL desenhar a ponte com um console em arco ao redor da cadeira do capitão (Picard maior que os demais, no centro) e piso com o desenho da ponte, e cada tripulante como um boneco em pixel art (cabeça e corpo na cor da divisão, emoji como insígnia): sentado e digitando quando ativo, de pé e parado quando livre (emenda 2026-11-11, user: "Os quatro itens").
- **R52** - WHILE um tripulante está ativo the system SHALL acender o console dele com brilho na cor da divisão e mostrar embaixo "há N min" a partir de `lastAt`; o livre fica com no máximo 40% da opacidade; o telão mostra "N tripulantes ativos" (ou "tripulação em repouso") (emenda 2026-11-11).
- **R53** - The system SHALL desenhar na engenharia só os workers existentes (até 6, depois "+N"); sem workers, uma única linha "Nenhum worker na engenharia", e a altura liberada vai para a ponte (emenda 2026-11-11).

### Build, instalação e registros

- **R33** - WHEN `python tools/build.py` roda THEN the system SHALL gerar `dist/orca/` com o plugin e os scripts Python que ele usa. O `build.py --check` falha se `dist/orca/` estiver diferente da fonte.
- **R34** - WHEN `python tools/install_local.py orca` roda THEN the system SHALL executar `orca plugin validate dist/orca --json` e depois `orca plugin install <abs>/dist/orca --json`. Com exit 3 (`approval_required`), mostra a lista de acessos e o comando com `--approve <fingerprint>` que a Orca devolveu, sai com 3 e nunca passa `--approve` sozinho.
- **R35** - The system SHALL declarar no manifesto os painéis `ponte` (componentes) e `ponte-cena` (HTML) e só as capabilities `workspace:read`, `agent:read`, `workspace:write`, `agent:launch` e `storage:own`, com `engines.orca` `>=1.4.248`.
- **R36** - The system SHALL ter em `DECISIONS.md` as entradas F10-n, no `CREDITS.md` as linhas do Pixel Agents e do Habblaud como inspiração, no `CHANGELOG.md` a seção `## [1.4.0] - não lançada`, em `docs/compatibilidade.md` a linha do painel e no `README.md` a instalação do painel.
- **R37** - WHEN o aceite roda THEN the system SHALL registrar em `docs/aceite/fase-10.md` as seções Instalação, Worktree A, Worktree B, Evento de agente, Cena e Atalhos, cada uma com `**Resultado**` e o caminho da captura.

## Data & Contracts

Saída de `ponte.py snapshot --json` (schemaVersion 1):

```json
{
  "schemaVersion": 1,
  "worktree": "F:/Projetos/StarCode",
  "starcode": true,
  "crew": [{"member": "troi", "emoji": "💜", "name": "Troi", "count": 1, "lastAt": "2026-11-09T23:10:10+00:00", "cliModel": "claude · claude-sonnet-5-5"}],
  "gitMode": {"mode": 3, "label": "branch + PR", "recordedAt": "2026-11-09T15:48:08+00:00"},
  "feature": {
    "slug": "fase-10-ponte", "phase": "spec", "size": "GRANDE", "done": false,
    "linear": ["SC-17"], "integrationBranch": null,
    "progress": {"done": 0, "total": 0, "percent": 0},
    "breaker": "closed",
    "files": {"context": "<abs>", "spec": "<abs>", "tasks": null, "handoff": "<abs>"}
  },
  "workers": [{"label": "T1", "issues": ["SC-120"], "base": "abc1234", "dispatch": "ctx_...", "model": "claude-sonnet-5-5"}],
  "errors": []
}
```

Protocolo painel ↔ worker (`src/protocol.ts`):
- requisições: `ponte.state` (`{ force?: boolean }` → estado), `ponte.open` (`{ file: "spec"|"tasks"|"handoff" }` → `{ opened }`), `ponte.launchPicard` (`{}` → `{ terminalId }` ou erro `not_launchable`);
- evento: `ponte.state` (estado completo).
- Estado enviado ao painel: `{ status: "ok"|"sem-worktree"|"erro", stale: boolean, updatedAt: number, snapshot, issue: { id, title, state, url } | null, issueNote: string | null, agents: [...], log: { at: number, text: string }[], error: string | null }`.

Manifesto: `id` `starcode-ponte`, sem `publisher`, `execution: trusted-worker`, `main: src/worker.ts`, painel `ponte` (`ui: components`, ícone `rocket`), painel `ponte-cena` (`ui: html`, `entry` `src/scene.html`, ícone `star`), item de status `ponte` com o comando declarativo `starcode-ponte.toggle` (`action: sidebar.right.toggle`), `contributes.events` `workspace.changed` e `agent.status.changed`.

## States

- **carregando**: o painel abriu e aguarda o primeiro `ponte.state`.
- **ok**: snapshot válido; seções com erro individual mostram "indisponível".
- **sem-worktree**: nenhum worktree em foco ou nenhum casamento de ramo.
- **sem StarCode**: `starcode: false`.
- **erro**: snapshot falhou; mostra o último estado bom com a marca "desatualizado", ou só o erro se nunca houve um.

## Edge Cases

- Dois worktrees no mesmo ramo (raro na Orca): usa o primeiro de `workspace.list` cujo `path` existe e anota em `errors`.
- `sessions.json` com hora futura ou origem desconhecida: a entrada é ignorada (mesma regra da F7-13).
- Worktree de ticket da Frota (sem `.starcode/live/` próprio): a tripulação vem do worktree principal (F6-7), o modo Git do próprio worktree.
- Handoff com vários `**Dispatched:**` ou nenhum; `**Linear:**` com faixas (`SC-102..SC-113`) e URLs: os IDs saem na ordem e as faixas ficam como estão no texto.
- Rajada de `agent.status.changed` com vários workers: debounce (R14).
- Caminhos com espaço e barras do Windows: o worker passa `--path` como argumento, sem shell.
- Worker reiniciado (salvamento ou ocioso): o cache do Linear e o diário de bordo se perdem e a primeira consulta refaz a chamada.
- Cena com o painel escondido: a animação usa `requestAnimationFrame`, que o navegador pausa em quadro escondido; não há temporizador próprio.
- Painel `ponte-cena` estreito: o canvas escala inteiro (sem cortar estações), com pixels sem suavização.
- Mais de 6 workers: 6 personagens e "+N" (R41).

## Decisions

| Item | Options | Status |
|---|---|---|
| Distribuição | neste repo, `dist/orca` + `install_local.py` (privado, sem catálogo) · repo próprio publicado (público, usa a identidade do GitHub) | approved - user: "Neste repo, instalação local (Recommended)" |
| Atalhos | abrir spec/tasks/Handoff · abrir a issue no Linear · iniciar o Picard · atualizar agora | approved - user: "Abrir spec/tasks/Handoff, Abrir a issue no Linear, Iniciar o Picard, Atualizar agora" |
| Barra de status | sim (resumo sem abrir o painel) · não | approved - user: "Sim (Recommended)" |
| Clique na barra de status (R20) | abrir o painel (impossível: a API não abre painel) · `sidebar.right.toggle` (mostra a barra lateral do painel) | adjusted - user: "sim" (2026-11-09, aprovação da spec ajustada) |
| Cena viva (Pixel Agents / Habblaud) | segundo painel HTML com a ponte em pixel art gerada por código, na Fase 10 · deixar para outra fase · copiar código/sprites (licença dos sprites do Pixel Agents não declarada) | adjusted - user: "sim" (2026-11-09, depois do pedido "verifique se da pra colocar algo") |
| Issue do worktree | ID, título e estado via `orca linear issue --current` com cache · só o ID | approved - user: "ID, título e estado (Recommended)" |
| Defeitos do aceite real (cena em branco, issue errada, botões cortados; depois, worktree errado com ramos iguais em repositórios diferentes; depois, atalhos de arquivo e Picard no reaceite manual) | ticket de correção antes do Q · deixar para a rodada pós-Q · entregar com pendências | adjusted - user: "Ticket de correção (Recommended)" (2026-11-10, depois do aceite da T9) |
| Melhorias da cena após a T14 | os quatro itens (engenharia compacta, contraste, ponte em arco, bonecos) · só engenharia e contraste · aceitar | adjusted - user: "Os quatro itens (Recommended)" (2026-11-11) |
| Visual da Cena da Ponte | ponte vista de cima (telão, semicírculo, engenharia embaixo) · cartões da tripulação | adjusted - user: "Ponte vista de cima (Recommended)" (2026-11-11) |
| Picard em segundo plano e `orca` falhando no worker (limitações da Orca) | registrar como limitação e seguir · mais uma rodada (T13 com terminal:send) · remover os dois recursos | adjusted - user: "Limitações registradas (Recommended)" (2026-11-10) |

Padrões da descoberta (não perguntados, valem com a aprovação desta spec): a leitura do estado fica em Python (`ponte.py`) e o worker só orquestra; feature exibida, worktree sem StarCode, workers, agente do Picard e idioma seguem a tabela Gray Areas do `context.md`.

## Open Questions
None.

## Sources

- Skill `orca-plugin-authoring` da Orca 1.4.255 e suas referências (`events`, `host-api`, `recipes`, `manifest`, `cli`): binding para a API do plugin.
- `PLANO_STARCODE.md` §10, Fase 10: binding para o escopo e o aceite.

## Differences from the Source

None - o produto segue a fonte. Fatos não verificados (verificar no primeiro ticket): o worker `trusted-worker` pode usar `node:child_process` para rodar `python` e `orca` (a skill diz que imports seguem o Node, mas não cita processos); e `agent.launch` aceita o prompt `/starcode:engajar` como primeira mensagem.
