# Changelog

Todas as mudanças relevantes do StarCode ficam neste arquivo.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota o
[Versionamento Semântico](https://semver.org/lang/pt-BR/) (Semantic Versioning): `MAJOR.MINOR.PATCH`.
A versão vive no arquivo `VERSION` e `python tools/build.py` a propaga para os manifestos.

## [Unreleased]

### Adicionado

- Cabeçalho de apresentação: cada tripulante abre a etapa mostrando nome, papel, CLI e modelo e o bordão (`scripts/crew_live.py start`).
- Arquivos ao vivo para painéis em `.starcode/live/`: `crew.json` (quem está trabalhando, 0/1) e `progress.json` (tickets integrados / total, em %).
- Statusline do Claude Code (`scripts/statusline.py`): tripulantes ativos e barra de progresso em degradê azul.

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
