# Fase 6: Empacotamento e distribuição (release v1.0): Tasks

**Approved**: 2026-11-06 - user: "sim"

**Spec**: `.specs/features/fase-6-release/spec.md`
**Status**: Approved
**Integration branch**: `feature/fase-6-release`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only, no generator change | `python -m unittest discover -s tests -v` |
| full | task that changes `skills/`, `scripts/`, `hooks/`, `src/`, `VERSION` or `tools/build.py` (F3-1: `dist/` regenerated in the same commit) | `python tools/build.py && python tools/build.py --check && python -m unittest discover -s tests -v` |
| build | records task, or after the last code task | `python tools/build.py && python tools/build.py --check && claude plugin validate dist/claude --strict && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |

## Tasks

### T1: install_local do OpenCode sem caminhos de skill acumulados
**Linear**: SC-62
**Depends on**: none
**Requirements**: R17, R18
**Tests**: unit
**Gate**: quick

#### TASK
Em `tools/install_local.py` (`_opencode`, linha ~95), trocar a lógica que só acrescenta caminhos em `skills.paths` (ou na lista `skills`). Depois da instalação, a lista deve ter:
- exatamente os caminhos de `dist/opencode/skills/<skill>` do clone atual, uma entrada por skill;
- nenhuma entrada de outra cópia do StarCode, ou seja, nenhum caminho que termine em `dist/opencode/skills/<nome de skill do StarCode>`, com `/` ou `\` (Windows);
- as entradas que não são do StarCode, intactas e na ordem original.

O `--dry-run` deve dizer quantas entradas serão removidas e quantas gravadas.

Testes em `tests/test_install_local.py`:
- `opencode.json` com caminhos de outro clone (`C:\x\f5-integ\dist\opencode\skills\engajar` e um POSIX) mais um caminho alheio;
- duas instalações seguidas a partir de dois clones diferentes.

#### CONTEXT
Spec: `.specs/features/fase-6-release/spec.md` (R17, R18). Checks: C1, C2, C3.
Na Fase 5, reinstalar a partir de vários worktrees deixou 32 entradas (SC-61). O teste existente `test_install_twice_keeps_single_registration` cobre só `starcode.js` e `hooks.json`. Os testes usam `--home` temporário e `run_cli` (veja `tests/test_install_local.py`).

#### BOUNDARIES
May change: `tools/install_local.py`, `tests/test_install_local.py`
Do not touch: `tools/build.py`, `hooks/`, `dist/`, `skills/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T2: Banner com os comandos de setup e engajar no formato de cada CLI
**Linear**: SC-63
**Depends on**: none
**Requirements**: R19
**Tests**: unit
**Gate**: full

#### TASK
Em `hooks/scripts/banner.py`, trocar o texto fixo `/starcode:setup` e `/starcode:engajar` (linhas ~85, 200, 208 e 243) por uma função que recebe o CLI de `--cli`:
- `claude` → `/starcode:<skill>`;
- `opencode` → `/sc-<skill>`;
- `codex` e `antigravity` → "a skill `<skill>` do StarCode".

Sem `--cli`, o formato é o do Claude. O mapeamento deve ser igual ao de `cmd_ref` em `tools/build.py`. Não importe o `build.py` no banner, que roda instalado sem `tools/`: duplique as 3 regras e adicione um teste que compara as duas implementações.

Testes em `tests/test_banner.py`, para os 4 CLIs, com config de repositório ausente e com repositório sem StarCode. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-6-release/spec.md` (R19). Checks: C4, C5.
Achado da Fase 5 (`docs/aceite/fase-5.md`, seções Codex e Antigravity): o banner no Codex dizia `rode /starcode:setup`. O banner roda como hook (SessionStart) e pelo engajar com `--full --text --cli <cli>`.

#### BOUNDARIES
May change: `hooks/scripts/banner.py`, `tests/test_banner.py`, `dist/`
Do not touch: `tools/`, `skills/`, `scripts/`, `VERSION`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T3: Versão 1.0.0 sincronizada e CHANGELOG
**Linear**: SC-64
**Depends on**: T2
**Requirements**: R11, R12, R13
**Tests**: unit
**Gate**: full

#### TASK
- `VERSION` passa a `1.0.0`. Rode `python tools/build.py`, que propaga a versão para `.claude-plugin/marketplace.json` e para os manifestos `dist/claude/.claude-plugin/plugin.json`, `dist/codex/.codex-plugin/plugin.json` e `dist/antigravity/plugin.json`.
- Garanta que `python tools/build.py --check` sai com código diferente de 0 quando o `version` de qualquer um desses arquivos diverge de `VERSION`. Se o `--check` já cobre isso, o trabalho é só o teste.
- Crie `CHANGELOG.md` na raiz no formato Keep a Changelog, em PT-BR:
  - um cabeçalho explicando o formato e o SemVer;
  - uma seção `## [Unreleased]` vazia;
  - uma seção `## [1.0.0] - AAAA-MM-DD` com `### Adicionado`, `### Alterado` e `### Corrigido`, resumindo as Fases 1 a 6.
  - A data fica como o literal `AAAA-MM-DD`; o Picard troca pela data real no release.

Testes em `tests/test_build.py` (versão e divergência) e `tests/test_release_docs.py` (CHANGELOG).

#### CONTEXT
Spec: `.specs/features/fase-6-release/spec.md` (R11, R12, R13). Checks: C6, C7, C8.
`tools/build.py` lê `VERSION` (linha ~96) e grava a versão nos manifestos (linhas ~226, 270, 285, 295 e 328). Fontes para o resumo: `PLANO_STARCODE.md` seção 10, `docs/aceite/fase-1.md` a `fase-5.md` e `DECISIONS.md`.

#### BOUNDARIES
May change: `VERSION`, `CHANGELOG.md`, `tools/build.py`, `tests/test_build.py`, `tests/test_release_docs.py`, `.claude-plugin/marketplace.json`, `dist/`
Do not touch: `hooks/`, `skills/`, `tools/install_local.py`, `README.md`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T4: Script de release com conferência de tag
**Linear**: SC-65
**Depends on**: T3
**Requirements**: R14, R23, R24
**Tests**: unit
**Gate**: quick

#### TASK
Criar `tools/release.py`, só com a stdlib, com três subcomandos:

- **`check --tag <tag>`**
  - Sai com 0 se a tag é `v` + `VERSION`.
  - Senão, sai com 1 e escreve em stderr `tag <tag> diverge de VERSION <versão>`.
- **`notes`**
  - Imprime o corpo da seção `## [<VERSION>]` do `CHANGELOG.md`, sem o título.
  - Sai com 1 se a seção não existe.
- **`create [--yes]`**
  - Primeiro roda `check` com `v<VERSION>`.
  - Depois consulta `git ls-remote --tags origin v<VERSION>`. Se a tag existe, sai com 1 e escreve `tag v<VERSION> já existe no remoto`. Nunca usa `--force`.
  - Sem `--yes`, só imprime os comandos que rodaria e sai com 0: `git tag -a v<VERSION> -m "StarCode v<VERSION>"`, `git push origin v<VERSION>` e `gh release create v<VERSION> --notes-file <arquivo temporário com notes>`.
  - Com `--yes`, roda os três comandos.

Os comandos externos passam por um `runner` injetável, como em `tools/install_local.py`, para os testes não tocarem o Git real. Testes em `tests/test_release.py`.

#### CONTEXT
Spec: `.specs/features/fase-6-release/spec.md` (R14, R23, R24). Checks: C9, C10, C11, C12.
A CI (T5) chama `python tools/release.py check --tag "$GITHUB_REF_NAME"` na tag. O Picard roda `create --yes` só depois da confirmação do usuário. O padrão de `runner` injetável está em `tools/install_local.py` (`_run`, `main(argv, runner=...)`).

#### BOUNDARIES
May change: `tools/release.py`, `tests/test_release.py`
Do not touch: `tools/build.py`, `tools/install_local.py`, `CHANGELOG.md`, `VERSION`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca crie tag nem release de verdade.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T5: Workflow de CI no GitHub Actions
**Linear**: SC-66
**Depends on**: T4
**Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R14
**Tests**: unit
**Gate**: quick
**Runs alone**: yes

#### TASK
Criar `.github/workflows/ci.yml` com:
- **Gatilhos:** `pull_request` (branches: main), `push` (branches: main; tags: `v*`) e `workflow_dispatch`.
- **Concurrency:** `group: ci-${{ github.ref }}` e `cancel-in-progress: true`.
- **Job `checks`:**
  - matriz `os: [ubuntu-latest, windows-latest]`, Python 3.12 (`actions/setup-python`) e Node (`actions/setup-node`);
  - instala o Claude Code com `npm install -g @anthropic-ai/claude-code@2.1.319` (versão fixada);
  - steps com `name` exato e `run`:
    - `build --check`: `python tools/build.py --check`;
    - `unittest`: `python -m unittest discover -s tests -v`;
    - `check_decisions`: `python scripts/check_decisions.py`;
    - `plugin validate`: `claude plugin validate dist/claude --strict`.
- **Job `eval`:**
  - `if:` tag `refs/tags/v` ou `workflow_dispatch`;
  - `env: ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}` só neste job;
  - primeiro step: falha com `ANTHROPIC_API_KEY ausente: configure o secret do repositório` se a variável está vazia;
  - roda os dois evals: `claude plugin eval dist/claude --tag risk-sizing --ablation none --trust-plugin --no-publish` e o mesmo com `--tag routing`;
  - `actions/upload-artifact` de `dist/claude/evals/results/` com `if: always()`;
  - escreve a nota de cada suíte em `$GITHUB_STEP_SUMMARY`.
- **Job `release-check`:** `if:` tag e roda `python tools/release.py check --tag "${{ github.ref_name }}"`.
- Nenhum `continue-on-error`, nenhum segredo em job de `pull_request`.

Testes em `tests/test_ci_workflow.py`, que leem o YAML. Não adicione dependência: PyYAML não está garantido na CI. Use `tools/miniyaml.py` se o workflow evitar blocos `|`, ou verifique a estrutura por texto. Atenção: em YAML 1.1 a chave `on:` vira `True`.

#### CONTEXT
Spec: `.specs/features/fase-6-release/spec.md` (R1–R10, R14). Checks: C13–C23.
- Comandos dos evals: `evals/README.md`.
- Claude Code desta máquina: 2.1.319.
- `tools/release.py check` vem da T4.
- O repositório é privado (`freire-andre/starcode`); o secret é configurado pelo usuário depois, fora desta task.
- A execução real da CI acontece quando o Picard abre o PR.

#### BOUNDARIES
May change: `.github/workflows/ci.yml`, `tests/test_ci_workflow.py`
Do not touch: `tools/`, `scripts/`, `hooks/`, `skills/`, `dist/`, `evals/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T6: README do v1.0 com a instalação por CLI
**Linear**: SC-67
**Depends on**: T1, T5
**Requirements**: R15, R16
**Tests**: unit
**Gate**: quick

#### TASK
Reescrever `README.md`:
- **Estado:** v1.0, com os 4 CLIs suportados e um link para `docs/compatibilidade.md`.
- **Pré-requisitos:**
  - acesso ao repositório privado: `gh auth login` ou uma credencial Git com acesso a `freire-andre/starcode`;
  - Python 3 no PATH;
  - Orca e Linear.
- **Instalação, uma subseção por CLI:**
  - **Claude:** `/plugin marketplace add freire-andre/starcode` e `/plugin install starcode@starcode`.
  - **Codex:** `codex plugin marketplace add freire-andre/starcode`, `codex plugin add starcode@starcode` e o trust em `/hooks`, aprovado pelo usuário.
  - **Antigravity:** `git clone https://github.com/freire-andre/starcode.git` (caminho sem espaço) e `python tools/install_local.py --cli antigravity`.
  - **OpenCode:** clone e `python tools/install_local.py --cli opencode`.
- **Primeiros passos:** setup e engajar por CLI, no formato do `cmd_ref`.
- **Desenvolvimento:** os comandos atuais, mais o CI e o `tools/release.py`.

Testes em `tests/test_release_docs.py`: os comandos de cada CLI e o pré-requisito aparecem; o texto "Fase 1" não aparece.

#### CONTEXT
Spec: `.specs/features/fase-6-release/spec.md` (R15, R16). Checks: C24, C25.
- O Codex 0.166 aceita `owner/repo[@ref]` em `codex plugin marketplace add`.
- Passos de setup por CLI: `skills/setup/SKILL.md`.
- O install do Antigravity recusa caminho com espaço (Fase 5).
- `tests/test_release_docs.py` é criado na T3; aqui você só acrescenta testes.

#### BOUNDARIES
May change: `README.md`, `tests/test_release_docs.py`
Do not touch: `CHANGELOG.md`, `tools/`, `skills/`, `dist/`, `.github/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T7: Roteiros do aceite da Fase 6 e decisão F6-1
**Linear**: SC-68
**Depends on**: T6
**Requirements**: R22
**Tests**: unit
**Gate**: build

#### TASK
- Criar `docs/aceite/roteiros-fase-6/` com um roteiro por CLI: `claude.md`, `codex.md`, `antigravity.md` e `opencode.md`. Cada roteiro de instalação limpa a partir do GitHub privado tem:
  - **Remoção da instalação atual do StarCode naquele CLI:** a lista dos comandos, executados só com a confirmação do usuário. Para o Codex, inclua remover o marketplace `starcode` local.
  - **Instalação pelos comandos do README,** usando o ref `feature/fase-6-release` enquanto o PR não foi mesclado (o Picard faz o push com a confirmação do usuário).
  - **Conferências:** banner, skills carregadas, `git push --force origin main` bloqueado onde `hooks: ok`, versão 1.0.0.
- Criar `docs/aceite/roteiros-fase-6/dia-de-missao.md`: uma feature GRANDE no `starcode-sandbox`, modo Git 2, do engajar ao gate `done`, com o que registrar.
- Criar o esqueleto de `docs/aceite/fase-6.md`:
  - seções Claude, Codex, Antigravity, OpenCode e Dia de missão, cada uma com `**Resultado**: pendente`;
  - uma tabela de versões.
- Registrar em `DECISIONS.md`:
  - **F6-1:** dia de missão no `starcode-sandbox` em vez de um "projeto real". Motivo: escolha do usuário em 2026-11-06. "Por que não é bug": o sandbox exercita o fluxo completo sem risco a um projeto em produção.
  - Uma decisão F6-n para cada mudança das T1–T6 em `hooks/`, `scripts/` ou `tools/` que o `check_decisions.py` exigir.

Testes em `tests/test_acceptance_doc_f6.py`: os roteiros existem e o esqueleto tem as 5 seções. Teste de F6-1 em `tests/test_check_decisions.py`. **Não crie** testes com os nomes das provas da T8–T10 (C27–C29). Esses testes nascem nas próprias tasks.

#### CONTEXT
Spec: `.specs/features/fase-6-release/spec.md` (R22). Checks: C26.
- Formato de referência: `docs/aceite/roteiros-fase-5/*.md`, `docs/aceite/fase-5.md` e `tests/test_acceptance_doc_f5.py`.
- `scripts/check_decisions.py` (D30) bloqueia quando `skills/`, `scripts/` ou outras pastas mudam sem decisão posterior.
- Regras do aceite: nunca usar modelo pago no OpenCode; o trust do Codex é dado só pelo usuário.

#### BOUNDARIES
May change: `docs/aceite/roteiros-fase-6/`, `docs/aceite/fase-6.md`, `DECISIONS.md`, `tests/test_acceptance_doc_f6.py`, `tests/test_check_decisions.py`
Do not touch: `tools/`, `hooks/`, `skills/`, `dist/`, `README.md`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T8: Aceite de instalação limpa no Claude e no Codex
**Linear**: SC-69
**Depends on**: T7
**Requirements**: R20
**Tests**: unit
**Gate**: quick

#### TASK
Rodar `docs/aceite/roteiros-fase-6/claude.md` e `codex.md` com o usuário, a partir do GitHub privado, no ref indicado no roteiro. Cada remoção de instalação existente e o trust em `/hooks` do Codex são feitos ou confirmados pelo usuário: peça e espere.

Gravar nas seções Claude e Codex de `docs/aceite/fase-6.md`:
- a versão do CLI;
- os comandos;
- o banner;
- as skills;
- o bloqueio;
- a versão do plugin;
- `**Resultado**: aprovado` ou `reprovado (<passo>)`.

Um reprovado vira ticket próprio; não corrija código aqui. Testes em `tests/test_acceptance_doc_f6.py`, que conferem as duas seções preenchidas.

#### CONTEXT
Spec: `.specs/features/fase-6-release/spec.md` (R20). Checks: C27.
Claude Code 2.1.319 e Codex 0.166 nesta máquina. Na Fase 5, o trust do Codex ficou gravado em `~/.codex/config.toml` (`[hooks.state."starcode@starcode:..."]`). Um marketplace de outra fonte exige um novo trust.

#### BOUNDARIES
May change: `docs/aceite/fase-6.md`, `tests/test_acceptance_doc_f6.py`, `docs/aceite/roteiros-fase-6/claude.md`, `docs/aceite/roteiros-fase-6/codex.md`
Do not touch: `tools/`, `hooks/`, `skills/`, `dist/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca use `--dangerously-bypass-hook-trust`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T9: Aceite de instalação limpa no Antigravity e no OpenCode
**Linear**: SC-70
**Depends on**: T8
**Requirements**: R20
**Tests**: unit
**Gate**: quick

#### TASK
Rodar `docs/aceite/roteiros-fase-6/antigravity.md` e `opencode.md` com um clone novo do GitHub privado, numa pasta sem espaço fora deste worktree, e o `install_local` desse clone. Remoções da instalação existente, só com a confirmação do usuário.

No OpenCode, use só modelo gratuito. Confira também que `skills.paths` ficou só com as skills do clone novo (R17).

Gravar nas seções Antigravity e OpenCode de `docs/aceite/fase-6.md`, com `**Resultado**`. Estender `tests/test_acceptance_doc_f6.py`. Depois do aceite, reinstale a partir de `F:/Projetos/StarCode`, com a confirmação do usuário, e registre isso na seção.

#### CONTEXT
Spec: `.specs/features/fase-6-release/spec.md` (R20). Checks: C28.
`agy` 1.5.2 e OpenCode 2.2.3 nesta máquina; aceite anterior em `docs/aceite/fase-5.md`. O Antigravity instala em `~/.gemini/config/plugins/starcode`; o OpenCode, em `~/.config/opencode/`.

#### BOUNDARIES
May change: `docs/aceite/fase-6.md`, `tests/test_acceptance_doc_f6.py`
Do not touch: `tools/`, `hooks/`, `skills/`, `dist/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca use modelo pago no OpenCode.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T10: Dia de missão no starcode-sandbox
**Linear**: SC-71
**Depends on**: T9
**Requirements**: R21
**Tests**: unit
**Gate**: build

#### TASK
Acompanhar o dia de missão descrito em `docs/aceite/roteiros-fase-6/dia-de-missao.md`:
- o usuário roda o `/starcode:engajar` numa sessão interativa do Claude em `F:/Projetos/starcode-sandbox`, com o StarCode 1.0.0 instalado do GitHub;
- é uma feature GRANDE no modo Git 2, da descoberta ao gate `done` verde, com o Q no Codex.

Depois, registre na seção Dia de missão de `docs/aceite/fase-6.md`:
- o slug;
- os IDs Linear;
- os hashes do ramo de integração;
- os vereditos dos gates;
- o veredito do Q;
- os achados;
- `**Resultado**`.

Achados que pedem código viram ticket próprio. Estenda `tests/test_acceptance_doc_f6.py`.

#### CONTEXT
Spec: `.specs/features/fase-6-release/spec.md` (R21). Checks: C29.
O `starcode-sandbox` já recebeu features nas Fases 2–4 (`task-priority`, `csv-import-export`, `limpar-concluidas`). A decisão de usar o sandbox está em F6-1 (T7).

#### BOUNDARIES
May change: `docs/aceite/fase-6.md`, `tests/test_acceptance_doc_f6.py`
Do not touch: `tools/`, `hooks/`, `skills/`, `dist/`, `src/`

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

**C1** - O install do OpenCode remove de `skills.paths` os caminhos de skill de outro clone do StarCode, Windows e POSIX, e grava os do clone atual (R17)
Proof: run unit | test_opencode_install_replaces_starcode_skill_paths_from_other_clones ... ok

**C2** - Entradas de `skills.paths` que não são do StarCode ficam intactas e na ordem original (R17)
Proof: run unit | test_opencode_install_keeps_foreign_skill_paths_in_order ... ok

**C3** - Duas instalações seguidas, a partir de dois clones, deixam uma entrada por skill do StarCode (R18)
Proof: run unit | test_opencode_install_twice_from_two_clones_no_duplicates ... ok

**C4** - O banner mostra o comando de setup no formato de cada CLI: `/starcode:setup`, `/sc-setup` e "a skill `setup` do StarCode" (R19)
Proof: run unit | test_banner_setup_command_per_cli ... ok

**C5** - O banner mostra o comando de engajar no formato de cada CLI, igual ao `cmd_ref` do build (R19)
Proof: run unit | test_banner_engajar_command_matches_cmd_ref ... ok

**C6** - `VERSION`, `marketplace.json` e os 3 manifestos do `dist/` têm a versão `1.0.0` (R11)
Proof: run unit | test_version_is_1_0_0_in_all_manifests ... ok

**C7** - `build.py --check` sai com código diferente de 0 quando a versão do `marketplace.json` diverge de `VERSION` (R12)
Proof: run unit | test_check_fails_when_manifest_version_diverges ... ok

**C8** - `CHANGELOG.md` segue o Keep a Changelog e tem a seção `[1.0.0]` com Adicionado, Alterado e Corrigido (R13)
Proof: run unit | test_changelog_has_1_0_0_section ... ok

**C9** - `release.py check` com uma tag diferente de `v`+VERSION sai com 1 e escreve `tag <tag> diverge de VERSION <versão>` (R14)
Proof: run unit | test_release_check_rejects_tag_diverging_from_version ... ok

**C10** - `release.py create` recusa uma tag que já existe no remoto, com `já existe no remoto` e sem `--force` (R24)
Proof: run unit | test_release_refuses_existing_remote_tag ... ok

**C11** - `release.py notes` imprime o corpo da seção da versão no CHANGELOG (R23)
Proof: run unit | test_release_notes_extracted_from_changelog ... ok

**C12** - `release.py create` sem `--yes` só imprime os comandos; com `--yes`, roda a tag anotada, o push e o `gh release create` (R23)
Proof: run unit | test_release_create_requires_yes_flag ... ok

**C13** - O CI dispara em `pull_request` e `push` para `main`, em tags `v*` e em `workflow_dispatch` (R1)
Proof: run unit | test_ci_triggers ... ok

**C14** - O job `checks` tem os steps `build --check`, `unittest`, `check_decisions` e `plugin validate`, com os comandos exatos (R1, R3)
Proof: run unit | test_ci_checks_steps_and_commands ... ok

**C15** - O job `checks` roda na matriz `ubuntu-latest` e `windows-latest`, com Python 3.12 (R2)
Proof: run unit | test_ci_matrix_ubuntu_windows_python_312 ... ok

**C16** - O CI instala `@anthropic-ai/claude-code` com a versão fixada e roda `claude plugin validate dist/claude --strict` (R4)
Proof: run unit | test_ci_plugin_validate_with_pinned_claude_code ... ok

**C17** - Nenhum job ou step do CI tem `continue-on-error` (R5)
Proof: run unit | test_ci_has_no_continue_on_error ... ok

**C18** - O CI tem `concurrency` por ref com `cancel-in-progress: true` (R6)
Proof: run unit | test_ci_concurrency_cancels_in_progress ... ok

**C19** - O job `eval` só roda em tag `v*` ou em `workflow_dispatch` e executa as suítes `risk-sizing` e `routing` (R7)
Proof: run unit | test_ci_eval_job_only_on_tag_or_dispatch ... ok

**C20** - `ANTHROPIC_API_KEY` aparece só no job `eval` (R8)
Proof: run unit | test_ci_secret_only_in_eval_job ... ok

**C21** - O job `eval` falha com `ANTHROPIC_API_KEY ausente: configure o secret do repositório` quando o secret está vazio (R9)
Proof: run unit | test_ci_eval_fails_without_secret ... ok

**C22** - O job `eval` envia `dist/claude/evals/results/` como artefato e escreve as notas em `$GITHUB_STEP_SUMMARY` (R10)
Proof: run unit | test_ci_eval_uploads_results_and_summary ... ok

**C23** - O job `release-check` roda `tools/release.py check --tag` com o nome da tag (R14)
Proof: run unit | test_ci_release_check_runs_release_py ... ok

**C24** - O README tem os comandos de instalação dos 4 CLIs a partir de `freire-andre/starcode` (R15)
Proof: run unit | test_readme_install_commands_per_cli ... ok

**C25** - O README diz v1.0, cita `gh auth login` como pré-requisito e não contém "Fase 1" (R16)
Proof: run unit | test_readme_states_v1_and_private_access ... ok

**C26** - `DECISIONS.md` registra F6-1 (dia de missão no `starcode-sandbox`) (R22)
Proof: run unit | test_decisions_f6_1_sandbox_mission_day ... ok

**C27** - `docs/aceite/fase-6.md` tem as seções Claude e Codex preenchidas, com versão do CLI e `**Resultado**: aprovado` (R20)
Proof: run unit | test_acceptance_doc_f6_claude_codex_filled ... ok

**C28** - `docs/aceite/fase-6.md` tem as seções Antigravity e OpenCode preenchidas, com `**Resultado**: aprovado` (R20)
Proof: run unit | test_acceptance_doc_f6_antigravity_opencode_filled ... ok

**C29** - `docs/aceite/fase-6.md` tem o Dia de missão com slug, IDs Linear, veredito do Q e `**Resultado**: aprovado` (R21)
Proof: run unit | test_acceptance_doc_f6_mission_day_filled ... ok

## Handoff

**Phase:** published
**Size:** LARGE
**Git mode:** 3
**Next:** T8: aceite Claude e Codex
**Linear:** SC-13 (issue-mãe); T1–T10 = SC-62..SC-71; SC-61 relacionada
**Integration branch:** feature/fase-6-release
**Last integrated:** 9b99f56
**Dispatched:** none
**Settled:** 2026-11-06: spec aprovada: "sim"; 2026-11-06: tasks aprovadas e publicação: "sim"; 2026-11-06: push do ramo para o aceite: "Sim"
**Attempts:** none
**Reports:** none
**Breaker:** closed
