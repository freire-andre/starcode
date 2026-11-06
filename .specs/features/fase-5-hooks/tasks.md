# Fase 5: Hooks nos outros CLIs: Tasks

**Approved**: 2026-11-06 - user: "Sim"

**Spec**: `.specs/features/fase-5-hooks/spec.md`
**Status**: Approved
**Integration branch**: `feature/fase-5-hooks`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only, no generator change | `python -m unittest discover -s tests -v` |
| full | task that changes `skills/`, `scripts/`, `hooks/`, `src/` or `tools/build.py` (F3-1: `dist/` regenerated in the same commit) | `python tools/build.py && python tools/build.py --check && python -m unittest discover -s tests -v` |
| build | records task, or after the last code task | `python tools/build.py && python tools/build.py --check && claude plugin validate dist/claude --strict && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |

## Tasks

### T1: Build gera os hooks.json do Codex e do Antigravity
**Linear**: SC-45
**Depends on**: none
**Requirements**: R1, R2, R4, R10
**Tests**: unit
**Gate**: full

#### TASK
Em `tools/build.py`, gerar:
- `dist/codex/hooks/hooks.json`: `PreToolUse` matcher `Bash` com `git_guard.py` (timeout 15) e `secret_scan.py` (timeout 30); `SessionStart` matcher `startup|resume|clear|compact` com `banner.py --cli codex` (timeout 30). Comando no formato `python "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/<script>"`, igual ao Claude.
- `dist/antigravity/hooks.json` na raiz, no formato nativo com hooks nomeados: `PreToolUse` matcher `run_command` com `git_guard.py --agy` e `secret_scan.py --agy`; `SessionStart` com `banner.py --agy --cli antigravity`. O caminho dos scripts usa o marcador literal `{{STARCODE_ROOT}}`, que o `install_local` troca pelo caminho absoluto na cópia instalada (T4).

Nenhum arquivo do `dist/` pode conter caminho absoluto de máquina (`F:/`, `C:\`, `/home/`, `/Users/`). Testes em `tests/test_build.py`.

#### CONTEXT
Spec: `.specs/features/fase-5-hooks/spec.md` (R1, R2, R4, R10; formatos em `## Data & Contracts`). Checks: C1, C2, C3, C4.
Hoje `tools/build.py` tem `claude_hooks()` (linha ~235) e grava só `dist/claude/hooks/hooks.json`. Formato nativo do Antigravity: `DECISIONS.md` F0-6 e `docs/compatibilidade.md` nota 1 (hooks nomeados, `plugin.json` na raiz). O probe da Fase 0 está no commit `83e3c67` (`git show 83e3c67:dist/antigravity/hooks.json`): use-o como referência de formato. Os scripts já aceitam `--agy` e `--cli`.

#### BOUNDARIES
May change: `tools/build.py`, `tests/test_build.py`, `dist/`
Do not touch: `hooks/scripts/`, `skills/`, `scripts/`, `tools/install_local.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T2: Plugin do OpenCode que chama os guards
**Linear**: SC-46
**Depends on**: T1
**Requirements**: R3, R6, R9
**Tests**: unit
**Gate**: full

#### TASK
Criar `hooks/opencode/starcode.js`: objeto puro `export default { id: "starcode", async setup(ctx) {...} }`, sem import de pacote. Em `ctx.tool.hook("execute.before", ...)`, quando `event.input.command` é string:
- roda `python <raiz>/hooks/scripts/git_guard.py` e depois `secret_scan.py` com `child_process.spawnSync`, passando na entrada padrão o JSON `{"tool_input":{"command":...},"cwd":<process.cwd()>}`;
- se a saída tiver `hookSpecificOutput.permissionDecision == "deny"`, lança `new Error(<permissionDecisionReason>)`;
- se o Python não roda, sai com código diferente de 0 ou devolve JSON inválido, escreve em stderr uma linha que começa com `StarCode hook:` e deixa passar.
A raiz vem da constante `STARCODE_ROOT = "{{STARCODE_ROOT}}"` (trocada pelo `install_local`, T4). Em `tools/build.py`, copiar o arquivo para `dist/opencode/plugins/starcode.js`.
Testes em `tests/test_opencode_plugin.py`: rodam o plugin com `node` e um `ctx` falso (o teste troca `{{STARCODE_ROOT}}` pela raiz do repo numa cópia temporária).

#### CONTEXT
Spec: `.specs/features/fase-5-hooks/spec.md` (R3, R6, R9). Checks: C5, C6, C7, C8.
Probe da Fase 0: `git show 83e3c67:dist/opencode/plugins/starcode.ts` (mesma API, `throw` bloqueia). Regras do OpenCode: `docs/compatibilidade.md` nota 2 e `docs/adr/ADR-0001-formatos-e-layout.md` (bloqueio por `throw` em `execute.before`). Node v24 está no PATH desta máquina. Comando que o `git_guard` bloqueia em qualquer modo: `git push --force origin main`.

#### BOUNDARIES
May change: `hooks/opencode/starcode.js`, `tools/build.py`, `tests/test_opencode_plugin.py`, `dist/`
Do not touch: `hooks/scripts/`, `skills/`, `tools/install_local.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T3: Guards com aviso de falha e testes por payload de cada CLI
**Linear**: SC-47
**Depends on**: T2
**Requirements**: R5, R7, R9
**Tests**: unit
**Gate**: full

#### TASK
Em `hooks/scripts/git_guard.py` e `hooks/scripts/secret_scan.py`: quando o JSON de entrada é inválido ou a avaliação levanta exceção, escrever em stderr uma linha que começa com `StarCode hook:` e sair com 0 sem deny (fail-open). Payload sem comando continua passando em silêncio.
Testes novos com payloads gravados de cada CLI (Codex no formato do Claude, Antigravity com `toolCall.args.CommandLine`):
- `git push --force origin main` bloqueado no Codex e no Antigravity;
- commit com segredo staged bloqueado no Codex e no Antigravity;
- comandos normais do fluxo (`git status`, `git add .`, `git commit -m "feat: x"` sem segredo, `git switch -c feature/x`, `git merge --no-ff feature/x` no ramo de integração, `orca linear issue SC-1 --json`, `python scripts/gates/run_gates.py ticket x`, `python -m unittest discover -s tests -v`) passam sem deny e sem stderr.

#### CONTEXT
Spec: `.specs/features/fase-5-hooks/spec.md` (R5, R7, R9; formatos em `## Data & Contracts`). Checks: C9, C10, C11, C12.
Testes existentes: `tests/test_git_guard.py` e `tests/test_secret_scan.py` (estilo e helpers de repo temporário). `extract()` e `main()` do `git_guard.py` (fim do arquivo) mostram o caminho atual de falha (`return 0` silencioso). Regras de bloqueio: `DECISIONS.md` F1-1 a F1-3; não mudar o que é bloqueado.

#### BOUNDARIES
May change: `hooks/scripts/git_guard.py`, `hooks/scripts/secret_scan.py`, `tests/test_git_guard.py`, `tests/test_secret_scan.py`, `dist/`
Do not touch: `hooks/scripts/banner.py`, `hooks/opencode/`, `tools/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T4: install_local grava caminhos absolutos e instala o plugin do OpenCode
**Linear**: SC-48
**Depends on**: T3
**Requirements**: R8, R15
**Tests**: unit
**Gate**: quick

#### TASK
Em `tools/install_local.py`:
- `--cli antigravity`: depois do `agy plugin install`, trocar `{{STARCODE_ROOT}}` pelo caminho absoluto da cópia instalada (`<home>/.gemini/config/plugins/starcode`, barras `/`) no `hooks.json` dessa cópia.
- `--cli opencode`: copiar `dist/opencode/plugins/starcode.js` para `<home>/.config/opencode/plugins/starcode.js` trocando `{{STARCODE_ROOT}}` pelo caminho absoluto do `dist/opencode`, e informar o caminho gravado.
- Rodar de novo não duplica: o arquivo é sobrescrito, nunca há dois `starcode*.js` nem entradas repetidas no `hooks.json`.
- `--dry-run` só imprime o plano.
Testes em `tests/test_install_local.py` com `--home` temporário e runner falso.

#### CONTEXT
Spec: `.specs/features/fase-5-hooks/spec.md` (R8, R15). Checks: C13, C14.
`tools/install_local.py` já instala os 3 CLIs (`_codex`, Antigravity com `agy plugin validate` antes, OpenCode escrevendo `skills.paths` no `opencode.json`); os testes atuais usam runner falso e `--home`. Pasta global do OpenCode: `DECISIONS.md` F0-3. Codex não precisa de troca (usa `${CLAUDE_PLUGIN_ROOT}`, T1).

#### BOUNDARIES
May change: `tools/install_local.py`, `tests/test_install_local.py`
Do not touch: `tools/build.py`, `hooks/`, `skills/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T5: Banner avisa hooks do Codex sem trust
**Linear**: SC-49
**Depends on**: T4
**Requirements**: R16, R10
**Tests**: unit
**Gate**: full

#### TASK
Em `hooks/scripts/banner.py`, com `--cli codex`: ler `<home>/.codex/config.toml` (home trocável por variável de ambiente `STARCODE_HOME` nos testes) e, se não houver nenhuma chave `[hooks.state."starcode@starcode:hooks/hooks.json:..."]` com `trusted_hash`, ou se alguma delas tiver `enabled = false`, imprimir a linha `Hooks do Codex sem trust: aprove em /hooks`. Arquivo ausente conta como sem trust. Leitura com `tomllib`; erro de leitura não quebra o banner. Confirmar por teste que `banner.py --cli codex` sem `--text` (modo hook) devolve `hookSpecificOutput.additionalContext` com o mesmo texto do modo `--text`, e `--agy` devolve `injectSteps[0].ephemeralMessage`.
Testes em `tests/test_banner.py`.

#### CONTEXT
Spec: `.specs/features/fase-5-hooks/spec.md` (R16, R10). Checks: C15, C16.
Formato das chaves de trust (lido do `~/.codex/config.toml` desta máquina): `[hooks.state."impeccable@impeccable:hooks/hooks.json:session_start:0:0"]` com `trusted_hash = "sha256:..."` e, às vezes, `enabled = false`. O banner não confere o hash. `main()` do `banner.py` já tem os três formatos de saída.

#### BOUNDARIES
May change: `hooks/scripts/banner.py`, `tests/test_banner.py`, `dist/`
Do not touch: `hooks/scripts/git_guard.py`, `hooks/scripts/secret_scan.py`, `skills/`, `tools/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T6: Setup por CLI e starcode-hello no relatório de concorrentes
**Linear**: SC-50
**Depends on**: T5
**Requirements**: R11, R12, R13, R14
**Tests**: unit
**Gate**: full

#### TASK
- `skills/setup/SKILL.md`, seção 6 vira "Passos por CLI" (com `{{CLI}}`): Codex: mostrar o passo de trust (abrir `/hooks` e aprovar os hooks do `starcode`), nunca dar o trust; OpenCode: pedir confirmação e então rodar `python tools/install_local.py --cli opencode` (ou o passo equivalente) e informar o caminho gravado; todos: checar `python --version` e, se falhar, mostrar `Python não encontrado: os hooks do StarCode não vão rodar neste CLI`.
- `scripts/conflicts.py`: se `<home>/.codex/config.toml` tiver `[plugins."starcode-hello@starcode"]` sem `enabled = false`, listar o item com o comando `codex plugin remove starcode-hello@starcode` (confira o nome do subcomando em `codex plugin --help` antes de escrever), sem remover nada.
Testes: `tests/test_support.py` (conflicts) e `tests/test_skills_cli.py` (texto do setup por CLI).

#### CONTEXT
Spec: `.specs/features/fase-5-hooks/spec.md` (R11, R12, R13, R14). Checks: C17, C18, C19, C20.
Setup atual: `skills/setup/SKILL.md` (seção 5 roda `conflicts.py`; seção 6 diz que os passos por CLI vêm depois). Regra de concorrentes: D31 (nunca desativar sozinho). `{{CLI}}` e `{{CMD:...}}` são renderizados por `tools/build.py` (Fase 4). Esta máquina ainda tem `[plugins."starcode-hello@starcode"]` no `~/.codex/config.toml`.

#### BOUNDARIES
May change: `skills/setup/SKILL.md`, `scripts/conflicts.py`, `tests/test_support.py`, `tests/test_skills_cli.py`, `dist/`
Do not touch: `hooks/`, `tools/`, `skills/engajar/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T7: Picard para quando o worker do Codex trava em hooks pendentes
**Linear**: SC-51
**Depends on**: T6
**Requirements**: R17
**Tests**: unit
**Gate**: full

#### TASK
Em `skills/engajar/references/execute.md`: se o `worker-start` de um worker Codex falhar com `agent-hooks-review-prompt` (ou `agent_readiness` com hooks pendentes), o Picard para o despacho, mostra o passo de trust (`/hooks`, aprovar os hooks do `starcode`) e não tenta de novo nem usa `--dangerously-bypass-hook-trust`. Teste em `tests/test_worker_skills.py` que confere o texto gerado no `dist/` de cada CLI.

#### CONTEXT
Spec: `.specs/features/fase-5-hooks/spec.md` (R17). Check: C21.
Erro real da Fase 0: `agent_readiness: Agent startup blocked: agent-hooks-review-prompt` (`docs/compatibilidade.md` nota 5). `execute.md` já tem a parada em `nested_worker_depth_exceeded` (Fase 4, T7): siga o mesmo padrão.

#### BOUNDARIES
May change: `skills/engajar/references/execute.md`, `tests/test_worker_skills.py`, `dist/`
Do not touch: `hooks/`, `tools/`, `skills/setup/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T8: Roteiros de aceite da Fase 5 e decisões
**Linear**: SC-52
**Depends on**: T7
**Requirements**: R19
**Tests**: unit
**Gate**: build

#### TASK
Criar `docs/aceite/roteiros-fase-5/codex.md`, `antigravity.md` e `opencode.md`, cada um com as seções: Instalação (incl. trust no Codex), Bloqueio (`git push --force origin main` e commit com um segredo de teste num repo sandbox), Fluxo normal (a lista de comandos normais da spec), Banner (Codex e Antigravity; OpenCode: n/a) e Evidência (o que copiar para `docs/aceite/fase-5.md`). Criar `docs/aceite/fase-5.md` com uma seção por CLI e o campo `**Resultado**: pendente`. Registrar em `DECISIONS.md` as decisões F5-1 (`${CLAUDE_PLUGIN_ROOT}` no Codex, caminho absoluto na cópia instalada no Antigravity e no OpenCode), F5-2 (fail-open com aviso `StarCode hook:`) e F5-3 (sem banner por hook no OpenCode). Testes em `tests/test_acceptance_scripts_f5.py`.

#### CONTEXT
Spec: `.specs/features/fase-5-hooks/spec.md` (R19). Check: C22.
Modelo: `docs/aceite/roteiros-fase-4/` e `tests/test_acceptance_scripts_f4.py`. Formato das decisões: `DECISIONS.md` (seções F4-n). O segredo de teste deve ser um padrão que o `secret_scan` detecta, sem ser uma credencial real (veja `tests/test_secret_scan.py`).

#### BOUNDARIES
May change: `docs/aceite/roteiros-fase-5/`, `docs/aceite/fase-5.md`, `DECISIONS.md`, `tests/test_acceptance_scripts_f5.py`
Do not touch: `hooks/`, `tools/`, `skills/`, `dist/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T9: Aceite no Codex
**Linear**: SC-53
**Depends on**: T8
**Requirements**: R5, R7, R10, R11, R16, R19
**Tests**: unit
**Gate**: quick

#### TASK
Rodar `docs/aceite/roteiros-fase-5/codex.md` numa sessão real do Codex com o `starcode` instalado pelo `install_local` a partir deste worktree. O trust em `/hooks` é dado pelo usuário: peça e espere. Gravar a evidência na seção Codex de `docs/aceite/fase-5.md` (versão do CLI, bloqueios, comandos normais que passaram, banner, `**Resultado**: aprovado` ou `reprovado (<passo>)`). Se `${CLAUDE_PLUGIN_ROOT}` não for expandido, registre como reprovado e o motivo; a correção vira ticket próprio. Teste em `tests/test_acceptance_doc_f5.py` que confere a seção Codex preenchida.

#### CONTEXT
Spec: `.specs/features/fase-5-hooks/spec.md` (R5, R7, R10, R11, R16, R19). Checks: C23.
Codex 0.166 desta máquina; trust em `DECISIONS.md` F0-1; formato do aceite anterior: `docs/aceite/fase-4.md` e `tests/test_acceptance_doc_f4.py`. O plugin legado `starcode-hello` ainda está instalado: anote se os hooks dele aparecerem.

#### BOUNDARIES
May change: `docs/aceite/fase-5.md`, `tests/test_acceptance_doc_f5.py`
Do not touch: `hooks/`, `tools/`, `skills/`, `dist/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca use `--dangerously-bypass-hook-trust`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T10: Aceite no Antigravity
**Linear**: SC-54
**Depends on**: T9
**Requirements**: R5, R7, R8, R10, R19
**Tests**: unit
**Gate**: quick

#### TASK
Rodar `docs/aceite/roteiros-fase-5/antigravity.md` numa sessão real do `agy` com o `starcode` instalado pelo `install_local` (`agy plugin validate --strict` antes). Conferir que `agy` conta `hooks` > 0 para o plugin. Gravar a evidência na seção Antigravity de `docs/aceite/fase-5.md` com `**Resultado**`. Estender `tests/test_acceptance_doc_f5.py` para a seção Antigravity.

#### CONTEXT
Spec: `.specs/features/fase-5-hooks/spec.md` (R5, R7, R8, R10, R19). Checks: C24.
`agy` 1.5.1 desta máquina; no aceite da Fase 4 ele contou `hooks 0` porque não havia `hooks.json` na raiz (`docs/compatibilidade.md` nota 12). Formato nativo: F0-6.

#### BOUNDARIES
May change: `docs/aceite/fase-5.md`, `tests/test_acceptance_doc_f5.py`
Do not touch: `hooks/`, `tools/`, `skills/`, `dist/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T11: Aceite no OpenCode, matriz e compatibilidade
**Linear**: SC-55
**Depends on**: T10
**Requirements**: R5, R6, R7, R12, R18, R19
**Tests**: unit
**Gate**: build

#### TASK
Rodar `docs/aceite/roteiros-fase-5/opencode.md` numa sessão real do OpenCode com o plugin copiado para `~/.config/opencode/plugins/` pelo `install_local` (com o usuário confirmando a cópia). Gravar a seção OpenCode de `docs/aceite/fase-5.md`. Depois, com os três resultados, atualizar `src/capabilities.yaml` (R18: `hooks: ok` nos CLIs aprovados, `banner_hook: ok` no Codex e no Antigravity se aprovados, OpenCode mantém `banner_hook: unavailable`; reprovado mantém `unavailable` com o motivo), regenerar o `dist/` e atualizar `docs/compatibilidade.md` (tabela de extras e nota da Fase 5). Testes em `tests/test_acceptance_doc_f5.py` (seção OpenCode e coerência matriz × aceite).

#### CONTEXT
Spec: `.specs/features/fase-5-hooks/spec.md` (R5, R6, R7, R12, R18, R19). Checks: C25, C26.
OpenCode 2.2.3; modelo gratuito usado na Fase 4: `openrouter/nvidia/nemotron-3.5-super-vl:free`, com fallback gratuito `opencode/mimo-v2.6-flash-free` → `opencode/deepseek-v4.1-flash-free` → `opencode/glm-5.3-flash-free`; nunca modelo pago. Coerência matriz × doc: `tests/test_acceptance_doc_f4.py` tem o padrão.

#### BOUNDARIES
May change: `docs/aceite/fase-5.md`, `tests/test_acceptance_doc_f5.py`, `src/capabilities.yaml`, `docs/compatibilidade.md`, `dist/`
Do not touch: `hooks/`, `tools/`, `skills/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca modelo pago no OpenCode.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - O build grava `dist/codex/hooks/hooks.json` com PreToolUse `Bash` (git_guard, secret_scan) e SessionStart com `banner.py --cli codex` (R1)
Proof: run unit | test_codex_hooks_json_registers_guards_and_banner ... ok

**C2** - O build grava `dist/antigravity/hooks.json` na raiz com `run_command`, `--agy` nos guards e banner `--agy --cli antigravity` (R2)
Proof: run unit | test_antigravity_hooks_json_native_format ... ok

**C3** - Nenhum arquivo do `dist/` contém caminho absoluto de máquina (R4)
Proof: run unit | test_dist_has_no_machine_absolute_paths ... ok

**C4** - O SessionStart do Codex e do Antigravity chama o banner no modo hook (sem `--text`) (R10)
Proof: run unit | test_session_start_banner_runs_in_hook_mode ... ok

**C5** - O build copia o plugin para `dist/opencode/plugins/starcode.js`, sem import de pacote e com `execute.before` (R3)
Proof: run unit | test_opencode_plugin_in_dist_is_pure_object ... ok

**C6** - O plugin do OpenCode lança erro com o motivo quando o guard nega `git push --force origin main` (R6)
Proof: run unit | test_opencode_plugin_throws_on_guard_deny ... ok

**C7** - O plugin do OpenCode deixa passar um comando normal sem erro (R6)
Proof: run unit | test_opencode_plugin_allows_normal_command ... ok

**C8** - Sem Python executável, o plugin do OpenCode deixa passar e escreve `StarCode hook:` em stderr (R9)
Proof: run unit | test_opencode_plugin_fails_open_with_warning ... ok

**C9** - `git push --force origin main` é negado com payload do Codex e do Antigravity (R5)
Proof: run unit | test_force_push_denied_codex_and_antigravity_payloads ... ok

**C10** - Commit com segredo staged é negado com payload do Codex e do Antigravity (R5)
Proof: run unit | test_secret_commit_denied_codex_and_antigravity_payloads ... ok

**C11** - Os comandos normais do fluxo passam sem deny e sem stderr nos dois formatos de payload (R7)
Proof: run unit | test_normal_flow_commands_pass_all_payloads ... ok

**C12** - JSON inválido no `git_guard` e no `secret_scan` deixa passar e escreve `StarCode hook:` em stderr (R9)
Proof: run unit | test_invalid_payload_fails_open_with_warning ... ok

**C13** - `install_local --cli antigravity` e `--cli opencode` trocam `{{STARCODE_ROOT}}` pelo caminho absoluto na cópia instalada (R8)
Proof: run unit | test_install_writes_absolute_paths_in_installed_copy ... ok

**C14** - Rodar o `install_local` duas vezes deixa um único `starcode.js` e um único registro de cada hook (R15)
Proof: run unit | test_install_twice_keeps_single_registration ... ok

**C15** - Sem `trusted_hash` dos hooks do `starcode` (ou com `enabled = false`), o banner `--cli codex` imprime `Hooks do Codex sem trust: aprove em /hooks` (R16)
Proof: run unit | test_codex_banner_warns_hooks_without_trust ... ok

**C16** - O banner em modo hook devolve o texto do `--text` em `additionalContext` (Codex) e em `injectSteps[0].ephemeralMessage` (Antigravity) (R10)
Proof: run unit | test_banner_hook_mode_matches_text_per_cli ... ok

**C17** - O setup do Codex mostra o passo de trust em `/hooks` e proíbe dar o trust pelo usuário (R11)
Proof: run unit | test_setup_codex_shows_trust_step ... ok

**C18** - O setup do OpenCode pede confirmação antes de copiar o plugin para a pasta global (R12)
Proof: run unit | test_setup_opencode_confirms_plugin_copy ... ok

**C19** - O setup de cada CLI tem a checagem do Python com a linha `Python não encontrado: os hooks do StarCode não vão rodar neste CLI` (R13)
Proof: run unit | test_setup_checks_python_per_cli ... ok

**C20** - `conflicts.py` lista o `starcode-hello@starcode` habilitado com o comando de remoção, sem remover (R14)
Proof: run unit | test_conflicts_lists_starcode_hello ... ok

**C21** - O `execute.md` de cada CLI manda parar e mostrar `/hooks` quando o worker Codex falha com `agent-hooks-review-prompt` (R17)
Proof: run unit | test_execute_stops_on_codex_hooks_review ... ok

**C22** - Os 3 roteiros da Fase 5 têm as seções Instalação, Bloqueio, Fluxo normal, Banner e Evidência, e `fase-5.md` tem uma seção por CLI (R19)
Proof: run unit | test_acceptance_scripts_f5_have_sections ... ok

**C23** - A seção Codex de `fase-5.md` tem versão, bloqueio de push forçado e de segredo, comandos normais, banner e Resultado (R5, R7, R10, R11, R16, R19)
Proof: run unit | test_acceptance_doc_f5_codex_filled ... ok

**C24** - A seção Antigravity de `fase-5.md` tem versão, contagem de hooks, bloqueios, comandos normais, banner e Resultado (R5, R7, R8, R10, R19)
Proof: run unit | test_acceptance_doc_f5_antigravity_filled ... ok

**C25** - A seção OpenCode de `fase-5.md` tem versão, plugin na pasta global, bloqueios, comandos normais e Resultado (R5, R6, R7, R12, R19)
Proof: run unit | test_acceptance_doc_f5_opencode_filled ... ok

**C26** - `src/capabilities.yaml` bate com os resultados de `fase-5.md`: aprovado = `hooks: ok`; OpenCode mantém `banner_hook: unavailable` (R18)
Proof: run unit | test_capabilities_match_f5_acceptance ... ok

## Handoff

**Phase:** published
**Size:** LARGE
**Git mode:** 3
**Next:** ramo de integração e primeiro ticket
**Linear:** issue-mãe SC-12; T1=SC-45 … T11=SC-55 (Todo, crew:data, blocks em cadeia)
**Integration branch:** not created
**Last integrated:** none
**Dispatched:** none
**Settled:** 2026-11-06: 2026-11-06: spec aprovada: "Sim"; 2026-11-06: 2026-11-06: tasks aprovadas e publicação: "Sim"
**Attempts:** none
**Reports:** none
**Breaker:** closed
