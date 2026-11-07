# Fase 6: Empacotamento e distribuição (release v1.0): Spec

**Approved**: 2026-11-06 - user: "sim"

**Size**: LARGE
**Risk triggers**: CI, release irreversível (tag v1.0), distribuição em 4 CLIs, dependência externa (GitHub privado `freire-andre/starcode`)
**Status**: Approved

## Context

O StarCode funciona nos 4 CLIs (Claude, Codex, Antigravity, OpenCode) desde as Fases 1–5, mas só a partir de um clone local. Não há CI (`.github/` não existe), então um merge pode levar `dist/` desatualizado, gate quebrado ou decisão sem registro. A versão continua 0.1.0, não há changelog e o README diz "Fase 1".

Duas pendências da Fase 5 (SC-61) atrapalham a instalação limpa:
- o `install_local --cli opencode` acumula entradas em `skills.paths`;
- o banner sugere `/starcode:setup`, que é comando do Claude, no Codex e no Antigravity.

Sucesso:
- a CI barra regressões nos PRs;
- a instalação a partir do GitHub privado funciona numa máquina limpa em cada CLI;
- um dia de missão completo roda no `starcode-sandbox`;
- sai o release v1.0.0 com tag e GitHub Release.

Discovery: `.specs/features/fase-6-release/context.md`. Issues: SC-13 e SC-61.

## Scope

- `.github/workflows/ci.yml`: checagens em PR e push para `main`, e job de eval na tag `v*` e no disparo manual.
- `.github/workflows/release.yml`, ou um job no mesmo arquivo: confere se a tag bate com `VERSION`.
- `VERSION` 1.0.0 e `CHANGELOG.md`. O `dist/` e o `.claude-plugin/marketplace.json` são regenerados pelo build.
- README: estado v1.0 e instalação a partir do GitHub privado por CLI.
- `tools/install_local.py` (`_opencode`): `skills.paths` sem duplicatas nem caminhos de outras cópias do StarCode (SC-61).
- `hooks/scripts/banner.py`: os comandos de setup e engajar no formato de cada CLI (SC-61).
- Aceite registrado em `docs/aceite/fase-6.md`:
  - instalação limpa nos 4 CLIs;
  - dia de missão no `starcode-sandbox`.
- Decisões F6-n em `DECISIONS.md`.
- Tag anotada `v1.0.0` e GitHub Release privado.

## Non-Goals

- Modo Frota (Fase 7), Uhura, Scotty e Kirk (Fase 8).
- Marketplace público e publicação fora do GitHub privado.
- Instalador num comando só. O usuário escolheu clone + `install_local`.
- Banner por hook no OpenCode (F5-3).
- Mudar os gates, as skills da tripulação ou os hooks além do que a SC-61 pede.

## Requirements

### CI de PR

- **R1** - WHEN um pull request para `main` é aberto ou atualizado, ou há push em `main`, THEN the system SHALL rodar o workflow `.github/workflows/ci.yml`. Cada checagem é um step separado, com o nome da checagem: `build --check`, `unittest`, `check_decisions` e `plugin validate`.
- **R2** - The system SHALL rodar os steps de R1 numa matriz com `ubuntu-latest` e `windows-latest`, ambos com Python 3.12.
- **R3** - The system SHALL rodar no step `build --check` o comando `python tools/build.py --check`, no step `unittest` o comando `python -m unittest discover -s tests -v` e no step `check_decisions` o comando `python scripts/check_decisions.py`.
- **R4** - The system SHALL instalar o Claude Code via npm, com a versão fixada no workflow, e rodar no step `plugin validate` o comando `claude plugin validate dist/claude --strict`, sem chave da Anthropic.
- **R5** - IF qualquer step de R1 sai com código diferente de 0 THEN the system SHALL terminar o job em falha. Nenhum step usa `continue-on-error`.
- **R6** - WHEN chega um novo push no mesmo ramo com uma execução de CI em andamento THEN the system SHALL cancelar a execução anterior, com `concurrency` por ramo e `cancel-in-progress: true`.

### Eval

- **R7** - WHEN o workflow é disparado manualmente (`workflow_dispatch`) THEN the system SHALL rodar o job `eval` (revisada em 2026-11-07, F6-5, user: "2a": sem o gatilho de tag). Ele executa `claude plugin eval dist/claude --tag risk-sizing --ablation none --trust-plugin --no-publish` e depois o mesmo comando com `--tag routing`.
- **R8** - The system SHALL ler o secret `ANTHROPIC_API_KEY` só no job `eval`. Esse job não roda em eventos `pull_request`.
- **R9** - IF o secret `ANTHROPIC_API_KEY` está vazio no job `eval` THEN the system SHALL falhar o job com a mensagem `ANTHROPIC_API_KEY ausente: configure o secret do repositório`, sem pular o eval.
- **R10** - WHEN o job `eval` termina THEN the system SHALL anexar `dist/claude/evals/results/` como artefato da execução e escrever no resumo do job a nota de cada suíte.

### Versão e changelog

- **R11** - The system SHALL ter `VERSION` igual a `1.0.0`. Depois do build, o `version` de `.claude-plugin/marketplace.json` e dos manifestos `dist/claude/.claude-plugin/plugin.json`, `dist/codex/.codex-plugin/plugin.json` e `dist/antigravity/plugin.json` deve ser igual a `1.0.0`.
- **R12** - IF a versão de algum manifesto de R11 diverge de `VERSION` THEN `python tools/build.py --check` SHALL sair com código diferente de 0.
- **R13** - The system SHALL ter na raiz um `CHANGELOG.md` no formato Keep a Changelog, em PT-BR, com uma seção `## [1.0.0] - <data do release>` que resume as entregas das Fases 1 a 6.
- **R14** - WHEN uma tag `v*` é enviada THEN the system SHALL comparar o nome da tag com `v` + o conteúdo de `VERSION`. IF divergirem THEN the system SHALL falhar com a mensagem `tag <tag> diverge de VERSION <versão>`.

### Instalação a partir do GitHub privado

- **R15** - The system SHALL ter no `README.md` uma seção de instalação por CLI, com os comandos a partir de `freire-andre/starcode`: **Claude:** `/plugin marketplace add freire-andre/starcode` e `/plugin install starcode@starcode`; **Codex:** `codex plugin marketplace add freire-andre/starcode`, `codex plugin add starcode@starcode` e o passo de trust em `/hooks`; **Antigravity e OpenCode:** `git clone` do repositório e `python tools/install_local.py --cli antigravity|opencode`.
- **R16** - The system SHALL dizer no `README.md` que o estado é v1.0 e citar o pré-requisito de acesso ao repositório privado: `gh auth login` ou uma credencial Git com acesso a `freire-andre/starcode`.

### SC-61

- **R17** - WHEN `python tools/install_local.py --cli opencode` roda THEN the system SHALL deixar em `skills.paths` do `opencode.json` exatamente os caminhos das skills de `dist/opencode/skills/` do clone de onde o comando roda: remove as entradas de outras cópias do StarCode (caminhos que terminam em `dist/opencode/skills/<skill do StarCode>`); preserva as demais entradas na ordem original.
- **R18** - WHEN o install do OpenCode roda duas vezes seguidas, ou a partir de dois clones diferentes, THEN the system SHALL deixar em `skills.paths` uma entrada por skill do StarCode, sem duplicatas.
- **R19** - WHEN `banner.py --cli <cli>` mostra o comando de setup ou de engajar THEN the system SHALL usar o formato do CLI, igual ao `cmd_ref` de `tools/build.py`: `/starcode:setup` no Claude; `/sc-setup` no OpenCode; "a skill `setup` do StarCode" no Codex e no Antigravity; o mesmo padrão para `engajar`.

### Aceite e release

- **R20** - The system SHALL registrar em `docs/aceite/fase-6.md`, para cada um dos 4 CLIs, uma instalação feita pelas instruções do README a partir do GitHub privado. O registro inclui: a versão do CLI; os comandos usados; o banner exibido; as skills carregadas; o bloqueio de `git push --force` onde a matriz diz `hooks: ok`; o resultado: aprovado ou reprovado.
- **R21** - The system SHALL registrar em `docs/aceite/fase-6.md` um dia de missão no `starcode-sandbox`: uma feature GRANDE no modo Git 2, do engajar ao gate `done` verde, com o slug, os IDs Linear, os hashes e o veredito do Q.
- **R22** - The system SHALL registrar em `DECISIONS.md` a decisão F6-1: o dia de missão roda no `starcode-sandbox` em vez de um "projeto real", com a escolha do usuário como motivo.
- **R23** - WHEN os aceites de R20 e R21 estão aprovados, o PR da fase foi mesclado em `main` e a CI de `main` está verde, THEN the system SHALL criar a tag anotada `v1.0.0` em `main` e um GitHub Release privado com as notas da seção 1.0.0 do CHANGELOG, só depois da confirmação explícita do usuário.
- **R24** - IF a tag `v1.0.0` já existe no remoto THEN the system SHALL recusar a criação e reportar a tag existente, sem `--force`.

## Data & Contracts

- Defaults da descoberta, sem pergunta ao usuário e sujeitos à aprovação desta spec: CI em `ubuntu-latest` e `windows-latest`, Python 3.12, CHANGELOG no formato Keep a Changelog.

- `ci.yml`: gatilhos `pull_request` (branches: main), `push` (branches: main; tags: `v*`) e `workflow_dispatch`. Jobs:
  - `checks`, com a matriz de R2;
  - `eval`, com `if:` em tag ou dispatch;
  - `release-check`, com `if:` em tag.
- `opencode.json`: `skills` pode ser uma lista ou um objeto com `paths`, e os dois formatos são aceitos (o código atual já trata isso).
- CHANGELOG: cabeçalho Keep a Changelog e seções `### Adicionado`, `### Alterado` e `### Corrigido`.

## States

- CI: verde (todos os steps 0), vermelho (o step que falhou fica nomeado) ou cancelada (R6).
- Aceite por CLI: aprovado ou reprovado. Um reprovado não bloqueia o registro dos outros, mas bloqueia R23.

## Edge Cases

- **Windows na CI:** caminhos com `\` nos testes e fim de linha CRLF no `build --check`. O build já normaliza para LF (Fase 3). Se o runner mostrar outra coisa, isso vira achado.
- **`opencode.json` ausente ou com `skills` em outro formato:** o install cria o objeto com `paths`, como já faz.
- **Clone do usuário com espaço no caminho:** o install do Antigravity recusa, como já faz (F5, R12 da Fase 5).
- **Repositório privado sem credencial:** o comando do CLI falha com o erro dele, e o README diz como autenticar (R16).
- **A versão fixada do npm do Claude Code mudou o `plugin validate`:** a CI fica vermelha. A correção é atualizar a versão fixada num PR.

## Decisions

| Item | Options | Status |
|---|---|---|
| Projeto do dia de missão | ApuraBolsa · OuveAI · Genesis_Aprimorado · starcode-sandbox | approved - user: "starcode-sandbox" |
| Eval na CI | só na tag e sob demanda (sem custo por PR) · todo PR (mais cobertura, custo por PR) · só local | approved - user: "Só na tag e sob demanda (Recommended)" |
| Instalação no Antigravity e no OpenCode | clone + install_local (caminho já testado) · script único (código novo) | approved - user: "Clone + install_local (Recommended)" |
| Release | tag + GitHub Release · só tag | approved - user: "Tag + GitHub Release (Recommended)" |
| SC-61 no escopo | entra · separada | approved - user: "Sim, entra (Recommended)" |

## Open Questions
None.
