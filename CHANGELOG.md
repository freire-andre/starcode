# Changelog

Todas as mudanças relevantes do StarCode ficam neste arquivo.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota o
[Versionamento Semântico](https://semver.org/lang/pt-BR/) (Semantic Versioning): `MAJOR.MINOR.PATCH`.
A versão vive no arquivo `VERSION` e `python tools/build.py` a propaga para os manifestos.

## [Unreleased]

### Adicionado

- Claude Code: `hooks/scripts/crew_hook.py` mostra o cabeçalho do tripulante e marca o status sozinho (sem depender do modelo), com `sessions.json` ao lado do `crew.json`; entradas vencem em 15 min (hook) ou 60 min (CLI) e o `crew.json` é recalculado a cada escrita.
- Statusline: validade das entradas e `🔧 LaForge ×<n>`; banner: aviso quando o plugin instalado está atrás do repositório do StarCode.
- Codex: `crew_hook.py --cli codex` mostra o cabeçalho e marca o status por hook (leitura do `SKILL.md` pelo shell ou `$starcode:<skill>` no prompt), registrado em `dist/codex/hooks/hooks.json`; as skills do Codex deixam de pedir `crew_live.py start/stop`.
- Banner do Codex: aviso quando os hooks da tripulação ainda não têm confiança em `hooks.state`.
- Antigravity e OpenCode: `crew_hook.py --cli antigravity|opencode` marca o status por hook e manda o modelo repetir o cabeçalho (`injectSteps` no agy, `ctx.session.synthetic` no OpenCode); grupo `starcode-crew` em `dist/antigravity/hooks.json` e as skills dos dois CLIs deixam de pedir `crew_live.py start/stop`.

## [1.2.0] - não lançada

### Adicionado

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
