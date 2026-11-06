# Fase 4 — Paridade com Codex, Antigravity e OpenCode: Tasks

**Approved**: 2026-11-05 - user: "SIM"

**Spec**: `.specs/features/fase-4-paridade/spec.md`
**Status**: Approved
**Integration branch**: `feature/fase-4-paridade`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only, no generator change | `python -m unittest discover -s tests -v` |
| full | task that changes `skills/`, `scripts/`, `hooks/`, `src/` or `tools/build.py` (F3-1: `dist/` regenerated in the same commit) | `python tools/build.py && python tools/build.py --check && python -m unittest discover -s tests -v` |
| build | records task, or after the last code task | `python tools/build.py && python tools/build.py --check && claude plugin validate dist/claude --strict && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |

## Tasks

### T1: Matriz de recursos por CLI e marcadores {{CMD}} e {{CLI}} no gerador
**Linear**: SC-30
**Depends on**: none
**Requirements**: R1, R2, R6
**Tests**: unit
**Gate**: full

#### TASK
Criar `src/capabilities.yaml` com, para cada CLI (claude, codex, antigravity, opencode), os extras `hooks`, `banner_hook`, `linear_mcp`, `subagent_model` e `orca_worker`, cada um com `status` (`ok`/`unavailable`) e `fallback` quando `unavailable`. Em `tools/build.py`:
- gravar `dist/<cli>/capabilities.json` só com os extras daquele CLI;
- falhar com `BuildError` se um extra `unavailable` não tiver `fallback`;
- renderizar `{{CMD:<skill>}}` em qualquer arquivo de skill como `/starcode:<skill>` (claude), `/sc-<skill>` (opencode) e "a skill `<skill>` do StarCode" (codex, antigravity);
- renderizar `{{CLI}}` como o nome do CLI.

Testes em `tests/test_build.py`.

#### CONTEXT
Spec: `.specs/features/fase-4-paridade/spec.md` (R1, R2, R6; formatos em `## Data & Contracts`). Checks: C1, C2, C3.

Valores iniciais da matriz (Fase 0, `docs/compatibilidade.md`):
- claude: tudo `ok`.
- codex: `hooks`/`banner_hook` `unavailable` (fallback "Fase 5; o banner vem do engajar"), `linear_mcp` `unavailable` (fallback "issue-mãe pelo orca linear"), `subagent_model` `unavailable` (fallback "Q por worker da Orca"), `orca_worker` `ok`.
- antigravity: igual ao codex.
- opencode: igual ao codex, com `banner_hook` `unavailable` (fallback "sem evento de início de sessão; o banner vem do engajar").

O YAML é lido com o parser mínimo de `scripts/config/miniyaml.py` (`src/crew.yaml` é o exemplo). Os marcadores existentes ficam em `tools/build.py` (`PLACEHOLDER`, `render`); `{{PLUGIN_ROOT}}` continua só em SKILL.md.

#### BOUNDARIES
May change: `src/capabilities.yaml`, `tools/build.py`, `tests/test_build.py`, `dist/`
Do not touch: `skills/`, `hooks/`, `scripts/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T2: Skills com {{CMD}} e banner do engajar com --cli
**Linear**: SC-31
**Depends on**: T1
**Requirements**: R7, R8
**Tests**: unit
**Gate**: full

#### TASK
Trocar toda referência literal `/starcode:<skill>` nas skills (incluindo `references/`) por `{{CMD:<skill>}}`. Fazer o passo 1 do `engajar` rodar `banner.py --full --text --cli {{CLI}}`. Teste novo em `tests/test_skills_cli.py`: nenhum `dist/<cli>` que não seja o do Claude contém `/starcode:`, e o `engajar` de cada CLI chama o banner com `--cli <cli>`.

#### CONTEXT
Spec: `.specs/features/fase-4-paridade/spec.md` (R7, R8). Checks: C4, C5.
Ocorrências hoje: `skills/engajar/SKILL.md` (2), `skills/engajar/references/linear-contract.md`, `skills/data/references/linear-publish.md` (2); confira com `grep -rn "/starcode:" skills src`. O `banner.py` só ganha `--cli` na T3, que depende desta. Por isso, este ticket muda só o texto da skill, e o teste confere o texto gerado, não a execução do banner.

#### BOUNDARIES
May change: `skills/`, `tests/test_skills_cli.py`, `tests/test_skills_exec.py`, `dist/`
Do not touch: `tools/`, `hooks/`, `scripts/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T3: Banner com CLI, extras indisponíveis e marcador de verificação degradada
**Linear**: SC-32
**Depends on**: T2
**Requirements**: R3, R4, R5
**Tests**: unit
**Gate**: full

#### TASK
Em `hooks/scripts/banner.py`, adicionar `--cli <cli>` (padrão `claude`):
- imprimir `CLI: <cli>` e, para cada extra `unavailable` do `capabilities.json` do plugin, a linha `Indisponível neste CLI: <extra> → <fallback>`;
- sem `--cli`, manter a saída da Fase 3, sem a linha `CLI:`;
- quando o `capabilities.json` não existe ao lado do plugin (rodando da fonte), ler `src/capabilities.yaml`.

Corrigir o falso positivo: a verificação degradada só conta com uma linha que **comece** com `**Verification:** degraded` ou `**Verification:** self-verified`. Testes em `tests/test_banner.py`, incluindo o caso de um `verification.md` que só cita `self-verified` numa tabela.

#### CONTEXT
Spec: `.specs/features/fase-4-paridade/spec.md` (R3, R4, R5). Checks: C6, C7, C8.
Hoje `work_in_progress` usa `re.search(r"self-verified|\*\*Verification:\*\*\s*degraded", vtext)` e acusa o `.specs/features/fase-3-execucao/verification.md`, que só cita `self-verified` numa linha da tabela de checks. A raiz do plugin vem de `starcode_common.PLUGIN_ROOT`.

#### BOUNDARIES
May change: `hooks/scripts/banner.py`, `tests/test_banner.py`, `dist/`
Do not touch: `skills/`, `tools/`, `scripts/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T4: Instalação local nos três CLIs (tools/install_local.py)
**Linear**: SC-33
**Depends on**: none
**Requirements**: R9, R10, R11, R12, R13, R14
**Tests**: unit
**Gate**: quick

#### TASK
Criar `tools/install_local.py --cli codex|antigravity|opencode [--dry-run] [--home DIR]`:
- **codex:** registra o marketplace do repositório e instala `starcode` com o próprio CLI do Codex.
- **antigravity:** `agy plugin validate dist/antigravity --strict`; só com sucesso, `agy plugin install <abs>/dist/antigravity`.
- **opencode:** grava no `opencode.json` global os caminhos absolutos das pastas de `dist/opencode/skills` e copia `dist/opencode/commands/*.md` para a pasta de comandos global, preservando as chaves existentes.

Regras gerais:
- Idempotente.
- Binário ou pasta ausente: código 2 e `<cli>: <binário ou pasta> não encontrado`, sem alterar nada.
- `--dry-run`: só imprime as ações.
- `--home`: troca a pasta do usuário, para os testes.

Testes em `tests/test_install_local.py`, com os comandos externos substituídos por um executor falso.

#### CONTEXT
Spec: `.specs/features/fase-4-paridade/spec.md` (R9–R14; contrato de saída em `## Data & Contracts`; casos de borda: `opencode.json` sem `skills` cria a chave, JSON inválido sai com código 2 sem gravar). Checks: C9, C10, C11, C12, C13, C14.
Procedimentos da Fase 0 em `docs/compatibilidade.md` → `## Procedimentos`:
- Codex: `codex plugin marketplace add <repo>` + install, com o marketplace em `.agents/plugins/marketplace.json`, gerado pelo `tools/build.py`.
- Antigravity: `agy plugin install`.
- OpenCode: skills por caminho absoluto em `opencode.json` (`~/.config/opencode/opencode.json`), comandos em `~/.config/opencode/commands/`.

Confira a sintaxe exata com `codex plugin --help` e `agy plugin --help` antes de escrever; não invente flags.

#### BOUNDARIES
May change: `tools/install_local.py`, `tests/test_install_local.py`
Do not touch: `dist/`, `skills/`, `scripts/`, `hooks/`, `tools/build.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Não rode a instalação de verdade nos testes.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T5: dispatch.py: briefing MÉDIA, famílias novas e CLI do Q
**Linear**: SC-34
**Depends on**: T3
**Requirements**: R18, R19, R23, R24, R25
**Tests**: unit
**Gate**: full

#### TASK
Em `scripts/dispatch.py`:
- **`brief`:** numa feature sem `tasks.md`, monta o briefing a partir do `spec.md` (título, `**Linear**:`, `## Scope`, `## Requirements`, `## Checks`) mais as regras fixas do worker. Sem `## Checks`, sai com código 2 e `spec sem ## Checks: não há o que entregar ao worker`.
- **`family`:** `deepseek*` vira `deepseek`, `gpt-oss*` vira `openai`, e `openrouter/<vendor>/<modelo>` vira a família do vendor (`unknown` para outro).
- **Subcomando novo `q-cli --laforge <cli:modelo> [--configured <cli[:modelo]>]`:** imprime o primeiro CLI, na ordem (configurado, codex, antigravity, opencode), com família diferente da do LaForge e `orca_worker` `ok` no `capabilities.json`; sem nenhum, imprime `self-verified` e sai com código 1.

Testes em `tests/test_dispatch.py`.

#### CONTEXT
Spec: `.specs/features/fase-4-paridade/spec.md` (R18, R19, R23, R24, R25; casos de borda "LaForge e Q do mesmo vendor" e "MÉDIA sem `**Linear**:`"). Checks: C18, C19, C23, C24, C25.
O `dispatch.py` atual tem `worker_brief` (só `tasks.md`), `family`/`compare`, `PREFIX_FAMILIES`, `CLI_FAMILIES` e `WORKER_RULES`. A família de um CLI sem modelo vem de `CLI_FAMILIES`; o opencode sem modelo é `unknown`.

#### BOUNDARIES
May change: `scripts/dispatch.py`, `tests/test_dispatch.py`, `dist/`
Do not touch: `skills/`, `hooks/`, `tools/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T6: Data publica com issue-mãe quando o MCP do Linear não existe
**Linear**: SC-35
**Depends on**: T5
**Requirements**: R15, R16, R17
**Tests**: unit
**Gate**: full

#### TASK
Em `skills/data/SKILL.md` e `skills/data/references/linear-publish.md`, quando o extra `linear_mcp` do `capabilities.json` do plugin é `unavailable`:
- criar com `orca linear create` uma issue-mãe (título da feature, spec como descrição) e cada ticket como sub-issue (`--parent`);
- criar as relações `blocks`;
- gravar os IDs com `tasks_export.py record`;
- dizer em uma linha qual caminho usou.

Teste de conteúdo em `tests/test_data_skill.py`, mais um teste em `tests/test_gates.py` mostrando que `run_gates.py publish` passa num `tasks.md` com IDs e sem Projeto.

#### CONTEXT
Spec: `.specs/features/fase-4-paridade/spec.md` (R15, R16, R17). Checks: C15, C16, C17.
Hoje o `linear-publish.md` cria Projeto e Documento pelo MCP e, sem o MCP, só avisa. O estágio `publish` do `run_gates.py` roda `validate_tasks --published`, que exige apenas `**Linear**: <ID>` em cada task. Antes de escrever, confira a sintaxe com `orca linear create --help` (`--parent`, `--team`, `--description`) e `orca linear relation add --help`.

#### BOUNDARIES
May change: `skills/data/`, `tests/test_data_skill.py`, `tests/test_gates.py`, `dist/`
Do not touch: `scripts/`, `hooks/`, `tools/`, `skills/engajar/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T7: Picard nos outros CLIs: Q por família, OpenCode, worktree de integração e aninhamento
**Linear**: SC-36
**Depends on**: T6
**Requirements**: R18, R19, R20, R21, R22
**Tests**: unit
**Gate**: full

#### TASK
Atualizar `skills/engajar/references/execute.md` (e, se preciso, o passo 5b do `skills/engajar/SKILL.md`):
- **Q:** o CLI vem de `dispatch.py q-cli`; com `self-verified`, marcar `**Verification:** self-verified`.
- **LaForge no `opencode`:** criar antes o worktree com `orca worktree create --base-branch feature/<slug>`, depois `worker-start --agent opencode --model <m> --worktree <ele>`.
- **Ramo de integração `I`:** criar ou reutilizar um worktree da Orca para `I`; o Handoff, o `proofs.md` e o `verification.md` são gravados nele.
- **`worker-start` com `nested_worker_depth_exceeded`:** parar com a linha do limite (Settings → Orchestration, 2 ou mais), sem contar tentativa.

Testes de conteúdo em `tests/test_skills_exec.py`.

#### CONTEXT
Spec: `.specs/features/fase-4-paridade/spec.md` (R18–R22). Checks: C20, C21, C22.
O `execute.md` atual (Fase 3) cria `I` com `git branch` sem worktree e grava o Handoff no worktree principal; o `docs/aceite/fase-3.md` (observações 4 e 5) explica por que isso separou o Handoff das provas. Mensagem exata da Orca: `nested_worker_depth_exceeded: Sub-worker dispatch is not permitted at depth 2 (max 1)`.

#### BOUNDARIES
May change: `skills/engajar/`, `tests/test_skills_exec.py`, `dist/`
Do not touch: `scripts/`, `hooks/`, `tools/`, `skills/data/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.
F3-1: regenere o `dist/` (`python tools/build.py`) no mesmo commit.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T8: Roteiros de aceite por CLI e registros da fase
**Linear**: SC-37
**Depends on**: T4, T7
**Requirements**: R26
**Tests**: unit
**Gate**: build

#### TASK
Escrever `docs/aceite/roteiros-fase-4/codex.md`, `antigravity.md` e `opencode.md`, cada um com `## Missão`, `## Respostas`, `## Aprovações`, `## Tripulação` e `## Relatório esperado`:
- **Missões:** Codex, data de vencimento (`add --vence AAAA-MM-DD`, `list` marca vencidas); Antigravity, busca por texto (`buscar TERMO`); OpenCode, exportar para Markdown (`exportar-md ARQ`).
- **Aprovações:** marcadas `roteiro pré-aprovado em 2026-11-05`.
- **Tripulação:** Codex `gpt-6-luna` com o Q no antigravity `gemini-3.8-flash-high`; Antigravity `gemini-3.8-flash-high` com o Q no codex; OpenCode `openrouter/deepseek/deepseek-v4-pro` com o Q no codex.

Também:
- registrar em `DECISIONS.md` as decisões F4-1 em diante (matriz de recursos, issue-mãe sem MCP, limite de aninhamento 2, worktree de integração do Picard);
- acrescentar a linha da revisão no `PLANO_STARCODE.md`.

Teste `tests/test_acceptance_scripts_f4.py` confere as cinco seções em cada roteiro.

#### CONTEXT
Spec: `.specs/features/fase-4-paridade/spec.md` (R26; decisões em `## Decisions`); context.md (Gray Areas com as missões e modelos). Check: C26.
Sandbox: `F:\Projetos\starcode-sandbox` (projeto Python `tarefas`, stdlib, `python -m unittest -v`), time PROJ do Linear; nunca time SC. Modelo de decisão: `DECISIONS.md` (problema → decisão → motivo → por que não é bug).

#### BOUNDARIES
May change: `docs/aceite/roteiros-fase-4/`, `tests/test_acceptance_scripts_f4.py`, `DECISIONS.md`, `PLANO_STARCODE.md`
Do not touch: `dist/`, `skills/`, `scripts/`, `hooks/`, `tools/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T9: Aceite no Codex
**Linear**: SC-38
**Depends on**: T8
**Requirements**: R27, R29
**Tests**: unit
**Gate**: build

#### TASK
Rodar o roteiro `docs/aceite/roteiros-fase-4/codex.md` no sandbox: instalar com `tools/install_local.py --cli codex` e despachar o Picard do Codex como worker da Orca com o roteiro. Registrar a seção `## Codex` em `docs/aceite/fase-4.md` com o resultado (`aprovado` ou `reprovado (<passo>)` com a linha exata do erro) e a evidência: commits, issues PROJ, vereditos dos gates e modelos efetivos. Atualizar a coluna Codex da matriz em `docs/compatibilidade.md`.

#### CONTEXT
Spec: `.specs/features/fase-4-paridade/spec.md` (R27, R29). Checks: C27, C29.
O limite de aninhamento da Orca precisa ser 2 ou mais (Settings → Orchestration), trocado pelo usuário. Sem ele, o passo para (R22). Modelo de evidência: `docs/aceite/fase-3.md`.

#### BOUNDARIES
May change: `docs/aceite/fase-4.md`, `docs/compatibilidade.md`
Do not touch: `dist/`, `skills/`, `scripts/`, `hooks/`, `tools/`

#### RULES
Leia AGENTS.md. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca crie projeto de teste no time SC.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T10: Aceite no Antigravity
**Linear**: SC-39
**Depends on**: T9
**Requirements**: R27, R29
**Tests**: unit
**Gate**: build

#### TASK
Rodar o roteiro `docs/aceite/roteiros-fase-4/antigravity.md` no sandbox, como no T9, com `tools/install_local.py --cli antigravity`. Registrar a seção `## Antigravity` em `docs/aceite/fase-4.md` e atualizar a coluna Antigravity da matriz em `docs/compatibilidade.md`.

#### CONTEXT
Spec: `.specs/features/fase-4-paridade/spec.md` (R27, R29; caso de borda do subagente no Antigravity). Checks: C27, C29.
O worker do Antigravity roda com permissões estreitas (`--settings` com allow por regex, F0-1); nunca `--dangerously-skip-permissions`.

#### BOUNDARIES
May change: `docs/aceite/fase-4.md`, `docs/compatibilidade.md`
Do not touch: `dist/`, `skills/`, `scripts/`, `hooks/`, `tools/`

#### RULES
Leia AGENTS.md. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca crie projeto de teste no time SC.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T11: Aceite no OpenCode e evidência final
**Linear**: SC-40
**Depends on**: T10
**Requirements**: R27, R28, R29
**Tests**: unit
**Gate**: build

#### TASK
Rodar o roteiro `docs/aceite/roteiros-fase-4/opencode.md` no sandbox, como no T9, com `tools/install_local.py --cli opencode` e o modelo `openrouter/deepseek/deepseek-v4-pro`. Registrar a seção `## OpenCode` em `docs/aceite/fase-4.md` e atualizar a coluna OpenCode da matriz. Teste `tests/test_acceptance_doc_f4.py` confere:
- as três seções, com `**Resultado**:` e `**Evidência**:`;
- que todo hash citado é commit real (do StarCode ou do sandbox);
- que `docs/compatibilidade.md` tem a seção da Fase 4 com o status de cada extra por CLI.

#### CONTEXT
Spec: `.specs/features/fase-4-paridade/spec.md` (R27, R28, R29; caso de borda de saldo no OpenRouter). Checks: C27, C28, C29.
Modelo do teste: `tests/test_acceptance_doc.py` (Fase 3).

#### BOUNDARIES
May change: `docs/aceite/fase-4.md`, `docs/compatibilidade.md`, `tests/test_acceptance_doc_f4.py`
Do not touch: `dist/`, `skills/`, `scripts/`, `hooks/`, `tools/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Nunca crie projeto de teste no time SC.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `src/capabilities.yaml` tem os 5 extras por CLI com status, e o build grava `capabilities.json` só com os extras de cada CLI (R1, R2)
Proof: run unit | test_capabilities_json_per_cli ... ok

**C2** - Extra `unavailable` sem `fallback` faz o build falhar com `BuildError` (R2)
Proof: run unit | test_unavailable_extra_without_fallback_fails ... ok

**C3** - `{{CMD:<skill>}}` vira `/starcode:<skill>`, `/sc-<skill>` ou "a skill `<skill>` do StarCode" conforme o CLI, e `{{CLI}}` vira o nome do CLI (R6)
Proof: run unit | test_cmd_and_cli_placeholders_per_cli ... ok

**C4** - Nenhum `dist/<cli>` que não seja o do Claude contém `/starcode:` (R7)
Proof: run unit | test_no_claude_commands_outside_claude_dist ... ok

**C5** - O `engajar` de cada CLI roda `banner.py --full --text --cli <cli>` (R8)
Proof: run unit | test_engajar_banner_uses_cli ... ok

**C6** - `banner.py --cli codex` imprime `CLI: codex` e uma linha `Indisponível neste CLI: <extra> → <fallback>` por extra indisponível (R3)
Proof: run unit | test_banner_lists_unavailable_extras ... ok

**C7** - Sem `--cli`, o banner não imprime a linha `CLI:` (R4)
Proof: run unit | test_banner_without_cli_keeps_phase3_output ... ok

**C8** - Um `verification.md` que só cita `self-verified` fora da linha-marcador não marca verificação degradada (R5)
Proof: run unit | test_degraded_only_from_marker_line ... ok

**C9** - `install_local.py --cli codex` registra o marketplace e instala o plugin pelo CLI do Codex, imprimindo o comando (R9)
Proof: run unit | test_install_codex_runs_marketplace_and_install ... ok

**C10** - `install_local.py --cli antigravity` só instala depois do `validate --strict` com sucesso (R10)
Proof: run unit | test_install_antigravity_validates_first ... ok

**C11** - `install_local.py --cli opencode` grava as skills com caminho absoluto e copia os comandos, preservando as chaves do `opencode.json` (R11)
Proof: run unit | test_install_opencode_writes_skills_and_commands ... ok

**C12** - Rodar a instalação duas vezes não duplica entradas (R12)
Proof: run unit | test_install_is_idempotent ... ok

**C13** - Binário ou `dist/<cli>` ausente sai com código 2 e `<cli>: <x> não encontrado`, sem alterar nada (R13)
Proof: run unit | test_install_missing_binary_exits_2 ... ok

**C14** - `--dry-run` imprime as ações e não altera arquivos nem roda a instalação (R14)
Proof: run unit | test_install_dry_run_changes_nothing ... ok

**C15** - Com `linear_mcp` indisponível, o Data cria a issue-mãe com a spec e cada ticket como sub-issue com `--parent` (R15)
Proof: run unit | test_data_parent_issue_fallback ... ok

**C16** - `run_gates.py publish` passa num `tasks.md` com IDs e sem Projeto, e o Data cria as relações `blocks` e grava os IDs (R16)
Proof: run unit | test_publish_gate_accepts_parent_issue ... ok

**C17** - O Data diz em uma linha qual caminho de publicação usou (R17)
Proof: run unit | test_data_reports_publish_path ... ok

**C18** - `dispatch.py q-cli` escolhe o primeiro CLI da ordem com família diferente da do LaForge e `orca_worker` ok (R18)
Proof: run unit | test_q_cli_picks_other_family ... ok

**C19** - Sem CLI de outra família, `q-cli` imprime `self-verified` e sai com código 1 (R19)
Proof: run unit | test_q_cli_self_verified_when_none ... ok

**C20** - O `execute.md` cria o worktree antes do `worker-start` quando o LaForge é `opencode` e usa `dispatch.py q-cli` para o Q (R18, R20)
Proof: run unit | test_execute_ref_opencode_and_q_cli ... ok

**C21** - O `execute.md` cria ou reutiliza um worktree da Orca para `I` e grava Handoff, provas e verificação nele (R21)
Proof: run unit | test_execute_ref_integration_worktree ... ok

**C22** - O `execute.md` para com a linha do limite de aninhamento ao ver `nested_worker_depth_exceeded`, sem contar tentativa (R22)
Proof: run unit | test_execute_ref_nested_depth_stop ... ok

**C23** - `dispatch.py brief` numa feature MÉDIA monta o briefing com Scope, Requirements, Checks e as regras do worker (R23)
Proof: run unit | test_medium_brief_from_spec ... ok

**C24** - Spec MÉDIA sem `## Checks` faz o `brief` sair com código 2 e a mensagem definida (R24)
Proof: run unit | test_medium_brief_without_checks_exits_2 ... ok

**C25** - `family` classifica `deepseek*`, `gpt-oss*` e `openrouter/<vendor>/...` (R25)
Proof: run unit | test_family_deepseek_gptoss_openrouter ... ok

**C26** - Cada roteiro de aceite tem Missão, Respostas, Aprovações, Tripulação e Relatório esperado (R26)
Proof: run unit | test_acceptance_scripts_have_sections ... ok

**C27** - `docs/aceite/fase-4.md` tem as seções Codex, Antigravity e OpenCode, cada uma com resultado e evidência citando commits reais (R27)
Proof: run unit | test_acceptance_doc_f4_has_all_clis ... ok

**C28** - `docs/compatibilidade.md` tem a seção da Fase 4 com o status de cada extra por CLI (R28)
Proof: run unit | test_compat_matrix_has_phase4 ... ok

**C29** - Um CLI reprovado é registrado como `reprovado (<passo>)` com a linha do erro, nunca como extra indisponível (R29)
Proof: run unit | test_failed_cli_recorded_as_reprovado ... ok

## Handoff

**Phase:** review
**Size:** LARGE
**Git mode:** 3
**Next:** T14 (SC-44) fecha os achados do Q; depois fechar Closed, done, PR
**Linear:** sub-issues da SC-11: T1=SC-30 … T11=SC-40 (Todo, crew:data, blocks em cadeia)
**Integration branch:** feature/fase-4-paridade
**Last integrated:** 6c2470b
**Dispatched:** none
**Settled:** 2026-11-05: spec aprovada: "sim"; 2026-11-05: tasks aprovadas e publicação: "SIM"; 2026-11-05: limite de aninhamento da Orca subido para 3 pelo usuário: "já subi o limite de aninhamento para 3"; 2026-11-05: T9: marketplace starcode do Codex re-apontado para o worktree f4-integ durante o aceite; restaurar para F:/Projetos/StarCode após o merge; achado: install_local não trata marketplace com outra fonte; 2026-11-05: T11: modelo do OpenCode trocado pelo usuário de deepseek-v4-pro (pago) para openrouter/nvidia/nemotron-3.5-super-vl:free; Picard e LaForge do OpenCode parados e redespachados; 2026-11-05: T11: fallback de modelo gratuito no OpenCode se o nemotron for bloqueado: opencode/mimo-v2.6-flash-free → opencode/deepseek-v4.1-flash-free → opencode/glm-5.3-flash-free; nunca modelo pago; 2026-11-06: T14: worker interrompido pelo reinício da máquina em 2026-11-06; redespachado no mesmo worktree f4-t14
**Attempts:** none
**Reports:** 2026-11-05: T1: capabilities.yaml/json e marcadores CMD/CLI, 6b3e805; integrada em 8ea1d2b; suíte de integração com 1 falha alheia (sandbox não achado no worktree da Orca); 2026-11-05: ajuste sandbox (9c6231e): teste de aceite acha o sandbox pelo git-common-dir; suíte 180 OK; 2026-11-05: T2: 5 referências /starcode: viraram {{CMD}} e o engajar chama o banner com --cli; 3 testes; commit 76d1200; gates verdes; disjuntor none; 2026-11-05: T3: banner com --cli, extras indisponíveis e marcador degradado só na linha-marcador; 15 testes; commit 7541ba3; gates verdes (aviso: cabeçalho com 77 chars); despacho inicial não chegou ao worker (turn_start_unobserved), briefing reenviado no terminal; disjuntor none; 2026-11-05: T4: tools/install_local.py (--cli codex|antigravity|opencode, --dry-run, --home) + 10 testes; ddf2bc5, 81384a9; gates verdes. Pendência: formato do campo skills no opencode.json ({"skills":{"paths":[...]}}) não verificado; checar no aceite T11.; 2026-11-05: T5: dispatch.py: briefing MÉDIA a partir do spec.md, famílias deepseek/gpt-oss/openrouter e subcomando q-cli; 11 testes; 7408162; gates verdes.; 2026-11-05: T6: Data: seção 2b (issue-mãe via orca linear create, sub-issues --parent, blocks, record, publish) em SKILL.md e linear-publish.md; testes novos; d5e19fb; suíte 214 verde.; 2026-11-05: T7: execute.md: q-cli por família (self-verified), LaForge opencode com worktree prévio, worktree de integração do Picard, parada em nested_worker_depth_exceeded; 4 testes; 61bc897; suíte 218 verde.; 2026-11-05: T8: roteiros codex/antigravity/opencode (5 seções), test_acceptance_scripts_f4.py, DECISIONS F4-1..F4-4 (F4-3: limite 3), Revisão 4.7 no PLANO; f737d4b, a611f7b; suíte 221 verde.; 2026-11-05: T9: aceite Codex APROVADO: PROJ-11/12/13 (issue-mãe), commits 37b7dd4/ed077ff/f5298c1, run_gates done VERDE, Q antigravity gemini-3.8-flash-high PASS; 25a0260. Achados: install_local com marketplace de outra fonte; q-cli self-verified sem capability record; marketplace a re-apontar após merge.; 2026-11-05: T10: aceite Antigravity REPROVADO (instalação): agy 1.5.1 plugin validate recusa rules/starcode.md sem frontmatter trigger; d76291a. Correção em issue própria e aceite repetido.; 2026-11-05: T10a: rules/starcode.md do Antigravity com trigger always_on; agy plugin validate --strict passa (3b0348c); 2026-11-05: T10: reaceite Antigravity APROVADO (tentativa 2): agy 1.5.1, PROJ-14/15/16, commits ca78587/532e192/1b01009, run_gates done VERDE, Q codex gpt-6-luna; 730c6b7. Achados: hooks/agents 0 no adaptador (Fase 5), MCP Linear indisponível (orca linear), starcode-hello ainda instalado, verification.md do sandbox com Verdict FAIL após achado fechado.; 2026-11-05: T11: aceite OpenCode APROVADO com nemotron-3.5-super-vl:free (troca pedida pelo usuário; sem fallback): PROJ-17/18/19, run_gates done VERDE no sandbox, Q codex; formato skills.paths do opencode.json confirmado (8 skills). 67846b0. Achados: Picard não commitou .specs antes do despacho (F2-7), Handoff desatualizado, proofs/verification sem commit.; 2026-11-05: proofs VERMELHO: 24/32 checks sem o teste de nome esperado (briefing sem linhas Proof); ciclo de correção SC-42 e SC-43; 2026-11-05: T12: install_local troca marketplace de outra fonte; q-cli sem self-verified indevido; brief com linhas Proof; brief recusa planejamento sem commit; F4-5..F4-7 (5159d09); 2026-11-05: T13: 23 testes renomeados às linhas Proof + C19 criado (d5b218b); proofs VERDE; 2026-11-05: Q (codex): FAIL com 4 achados (C15/C16 fracos, fallback só espaços, openrouter sem modelo, C27 fraco); 2026-11-06: T14: 4 achados do Q corrigidos (8d59c1e); Closed preenchido; proofs VERDE
**Breaker:** closed
