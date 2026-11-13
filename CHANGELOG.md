# Changelog

Todas as mudanças relevantes do StarCode ficam neste arquivo.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota o
[Versionamento Semântico](https://semver.org/lang/pt-BR/) (Semantic Versioning): `MAJOR.MINOR.PATCH`.
A versão vive no arquivo `VERSION` e `python tools/build.py` a propaga para os manifestos.

## [Unreleased]

### Adicionado

- Manutenção das retros (SC-148), item 1: `dispatch.py brief` acrescenta `DECISIONS.md` ao May change de ticket que mexe em `scripts/`.
- Item 2: `proofs.md` é gravado só com LF.
- Item 3: `dispatch.py start` e `dispatch.py settle` fazem o despacho e a integração de um ticket, e o `execute.md` passa a usá-los.
- Item 4: o brief do Q exige comando e saída literal na Evidence dos achados vindos de sondagem.
- Item 5: o gate das tasks recusa arquivo citado no TASK fora do May change, e o brief repete a regra de assinatura de commits.
- Item 6: `handoff.py set --report` não duplica a data.
- Item 7: `docs/compatibilidade.md` registra a limitação do `orca plugin test`/`check` por drive, com rascunho do relato à Orca.
- Item 8: os testes da Ponte falham quando o host recusa uma chamada.
- Item 9: o `execute.md` usa `worker-read`/`worker-show` com `--dispatch` e diz onde ler o modelo efetivo.

## [1.6.1] - 2026-11-13

### Corrigido

- Codex: o hook `SessionEnd` do StarCode passa a usar timeout de 3 s (o limite do Codex); com 10 s o Codex o marcava como inválido.

## [1.6.0] - 2026-11-12

### Adicionado

- Fase 12: `scripts/snapshot.py` guarda um snapshot por ticket no modo 1 (`refs/starcode/snapshots/<slug>/<ticket>`, índice temporário, sem commit no branch) e `restore` com confirmação só toca o `May change`.
- Fase 12: `scripts/impact.py` calcula o raio de impacto (grafo de imports Python e TS/JS) e escolhe os testes de regressão; na dúvida, "rodar tudo".
- Fase 12: o brief do Q leva a seleção de regressão do raio de impacto e o McCoy roda os testes escolhidos antes do gate.

### Corrigido

- Fase 12: a seleção de regressão trata renomeação como arquivo apagado, roda tudo quando um `conftest.py` muda e usa a árvore de trabalho no modo 1; o brief do Q aceita caminhos com `{{...}}`; `restore --yes` troca arquivo por pasta de mesmo nome sem falhar.

## [1.5.1] - 2026-11-12

### Corrigido

- `scaffold.py checks`: cada item com `cwd` roda num subshell (`(cd <cwd> && <cmd>)`); no perfil tauri a linha Build repetia `cd src-tauri` e os comandos seguintes rodavam dentro dele (SC-143).
- Painel Ponte: com a feature do worktree em foco concluída (ou sem feature), o painel e a barra de status mostram a missão ativa de outro worktree do mesmo repositório, com "e mais N" e o botão "Focar worktree" (`workspace.open`, sem capacidade nova); os atalhos de arquivo ficam desabilitados nesse caso e os erros do outro worktree aparecem com a fonte `worktrees` (SC-142).

## [1.5.0] - 2026-11-12

### Adicionado

- Fase 11: verificação de telas. As regras de captura (`captures/`, `screens.md`) voltam à spec e ao gate final; `scripts/screens.py` tira a foto pelo navegador da Orca, `scripts/gates/images.py` lê o tamanho das imagens (escala pelo nome) e o juiz de telas roda como worker separado (`briefs/screens-verify.md`), nos 4 CLIs.
- Fase 11: perfil Tauri com `screens` e mocks de IPC só em desenvolvimento.
- Fase 11: template Tauri com `.gitattributes` em LF, para o biome passar num checkout do Windows com `core.autocrlf=true`.
- Fase 11: o app de aceite vive no repositório como fixture (`aceite/telas/`); `python tools/aceite.py preparar telas` cria a cópia de trabalho fora do repositório. `aceite/` não entra no `dist/`.

### Corrigido

- Gates de telas: PNG truncado é recusado, captura com tamanho que a escala não divide dá erro e `screens.md` precisa de veredito para cada captura vinculante.
- `screens.py capture` valida a URL inteira (`https://` vazio e URL com espaço eram aceitos).

## [1.4.0] - 2026-11-11

### Adicionado

- Painel Ponte para a Orca: plugin em `dist/orca` (instalação local por `python tools/install_local.py --cli orca`, sem catálogo), com a Cena da Ponte em HTML e arte gerada por código; o `ponte.py` lê o estado (`crew.json`, `progress.json`) e a aprovação do plugin é sempre do usuário.
- CI: passo `orca plugin validate src/orca --json`, que só roda se `orca` existir no PATH.
- Créditos: Pixel Agents e Habblaud como inspiração da Cena da Ponte, sem código nem arte copiados.

### Corrigido

- Painel Ponte: o `orca` chamado de dentro do worker do plugin passa a funcionar (CLI por caminho explícito e env completo), e a Issue mostra título, estado e o link do Linear (F10-14).
- Painel Ponte: Iniciar Picard abre o agente numa aba visível da Orca, com o prompt enviado, pelo `orca agent launch`; se o CLI falhar, volta ao segundo plano e o painel avisa (F10-15, SC-131).

## [1.3.0] - 2026-11-09

### Adicionado

- Fase 9: skills `worf` (review de PR com publicação confirmada e portão de evidência de segurança), `guinan` (retro e lições por repo) e `diagnostico` (maturidade do harness; tracks B e C só com aprovação de custo por execução), nos 4 CLIs.
- Fase 9: `scripts/review/` (`review_gate.py`, `post_review.py`, `scan_bypasses.py`, adaptados do the-judge 1.4.0) e `scripts/harness/` (Track A do harness-eval 1.8.3).
- Fase 9: `scripts/lessons.py` (lições por repo, sinal `review_finding`) e `scripts/diagnostico.py` (`harness-score` fixado via `npx` e Track A juntos); `.harness-eval/` no `.gitignore`.
- Fase 9: 9 casos de roteamento em `evals/routing/` e fontes novas em `CREDITS.md`.

### Corrigido

- Review do Worf: o comentário inline não repete o emoji da severidade (F9-10).

## [1.2.0] - 2026-11-09

### Adicionado

- Claude Code: `hooks/scripts/crew_hook.py` mostra o cabeçalho do tripulante e marca o status sozinho (sem depender do modelo), com `sessions.json` ao lado do `crew.json`; entradas vencem em 15 min (hook) ou 60 min (CLI) e o `crew.json` é recalculado a cada escrita.
- Statusline: validade das entradas e `🔧 LaForge ×<n>`; banner: aviso quando o plugin instalado está atrás do repositório do StarCode.
- Codex: `crew_hook.py --cli codex` mostra o cabeçalho e marca o status por hook (leitura do `SKILL.md` pelo shell ou `$starcode:<skill>` no prompt), registrado em `dist/codex/hooks/hooks.json`; as skills do Codex deixam de pedir `crew_live.py start/stop`.
- Banner do Codex: aviso quando os hooks da tripulação ainda não têm confiança em `hooks.state`.
- Antigravity e OpenCode: `crew_hook.py --cli antigravity|opencode` marca o status por hook e manda o modelo repetir o cabeçalho (`injectSteps` no agy, `ctx.session.synthetic` no OpenCode); grupo `starcode-crew` em `dist/antigravity/hooks.json` e as skills dos dois CLIs deixam de pedir `crew_live.py start/stop`.
- Fase 8: perfis de stack em `profiles/` (`python-flask`, `rust`, `tauri`, `typescript`, `gpui` experimental, `postgresql`, `mysql`) com templates de marcadores `{{version:<pacote>}}`, CI e `.gitignore`; o `tools/build.py` copia `profiles/` para `dist/<cli>/profiles/` nos 4 CLIs.
- Fase 8: skills `uhura` (cache de documentação em `.specs/stack/`), `scotty` (detecta e registra a stack em `.starcode/stack.json`) e `nova-missao` (Kirk: projeto novo a partir de um perfil), com evals de roteamento.
- Fase 8: `scripts/scaffold.py` (versões pelos registros, série testada, `--pin`, `--allow-new`) e `scripts/ephemeral_db.py` (banco efêmero em Docker, `--reuse-env`).

### Alterado

- Fase 8: o `evals/README.md` descreve as 24 frases de roteamento (a edição antes feita na cópia gerada foi para a fonte).

## [1.1.0] - 2026-11-07

### Adicionado

- Fase 7: Modo Frota. `dispatch.py batch` calcula o lote de tickets independentes (fronteira por dono de arquivo, arquivos sensíveis sozinhos, limite `fleet.maxBatch`) com atribuição de CLI/modelo e faixa de custo relativa; `dispatch.py overdue` lista os despachos que passaram do timeout.
- Fase 7: chave `fleet.workers` (pool de pares `<cli>:<model>`), mapa `costTiers` no `crew.yaml` e fluxo da Frota no Picard (confirmação do lote, integração na chegada, timeout, falha e cancelamento por ticket).
- Cabeçalho de apresentação: cada tripulante abre a etapa mostrando nome, papel, CLI e modelo e o bordão (`scripts/crew_live.py start`).
- Arquivos ao vivo para painéis em `.starcode/live/`: `crew.json` (quem está trabalhando, 0/1) e `progress.json` (tickets integrados / total, em %).
- Statusline do Claude Code (`scripts/statusline.py`): tripulantes ativos e barra de progresso em degradê azul.

### Alterado

- Fase 7: o Handoff guarda vários despachos abertos em `**Dispatched:**` (`--dispatch-add` e `--dispatch-remove`), e `dispatch.py next` e `q-cli` entendem vários despachos e várias famílias de LaForge.
- Fase 7: `.starcode/live/crew.json` passa a guardar a contagem de LaForges ativos (0 a 10) em vez de 0/1.

### Corrigido

- `tools/release.py` recusa seção sem data e confere os aceites da Fase 6 em diante (SC-81).

## [1.0.0] - 2026-11-07

### Adicionado

- Fase 1: núcleo do plugin (`src/crew.yaml`, `src/context/STARCODE.md`), gerador `tools/build.py` com uma pasta por CLI em `dist/`, configs com `schemaVersion: 1` e validador, hooks `git_guard`, `secret_scan` e `banner`, skills `engajar` e `setup`, referências compartilhadas e evals de dimensionamento de risco e roteamento.
- Fase 2: planejamento com Troi (descoberta), Spock (spec) e Data (tasks e publicação no Linear), gates `validate_spec` e `validate_tasks` e o comando único `run_gates.py`.
- Fase 3: execução sequencial com LaForge (um ticket por worker de contexto limpo), McCoy (diagnóstico de bugs) e Q (verificação independente), ramo de integração por feature, ciclo de correção pós-Q, disjuntor e Handoff com escritor único.
- Fase 4: paridade com Codex, Antigravity e OpenCode, com matriz de recursos por CLI e fallback informado pelo banner.
- Fase 5: hooks de bloqueio e banner registrados no Codex, no Antigravity e no OpenCode.
- Fase 6: marketplace privado, instalação local nos 4 CLIs, CI e este changelog.

### Alterado

- Fase 1: plugin renomeado para `starcode`, com hooks registrados só no adaptador do Claude (a paridade veio na Fase 5).
- Fase 4: `dist/` passou a emitir adaptadores nativos por CLI, incluindo plugin do OpenCode na API V2 e manifesto próprio do Antigravity.
- Fase 5: o banner de hook entrega o texto de `--full --text`, e o `secret_scan` examina todo o diff staged.
- Fase 6: a instalação local do OpenCode troca os caminhos de skill em vez de acumulá-los, e o banner mostra os comandos de setup e engajar no formato de cada CLI.
- Versão do plugin sincronizada em `VERSION`, no marketplace e nos manifestos de `dist/`; `build.py --check` falha se divergirem.

### Corrigido

- Fase 4: ajustes de instalação e de carregamento de skills e hooks encontrados nos aceites reais de cada CLI.
- Fase 5: hooks do Antigravity sem aspas no caminho, repositório lido de `workspacePaths`, e plugin do OpenCode lendo o diretório do evento (`input.workdir`).
- Fase 6: reinstalações do OpenCode não duplicam mais caminhos de skill.
