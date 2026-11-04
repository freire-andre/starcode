# Fase 3 — Execução sequencial e verificação: Tasks

**Approved**: 2026-11-04 - user: "sim"

**Spec**: `.specs/features/fase-3-execucao/spec.md`
**Status**: Approved
**Integration branch**: `feature/fase-3-execucao`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only | `python -m unittest discover -s tests -v` |
| full | task with unit tests that also touches the generator | `python tools/build.py && python -m unittest discover -s tests -v` |
| build | config-only task, or after the last task | `python tools/build.py && python tools/build.py --check && claude plugin validate dist/claude --strict && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |

## Tasks

### T1: Gate check_proofs.py
**Linear**: SC-20
**Depends on**: none
**Requirements**: R1, R2, R3
**Tests**: unit
**Gate**: quick

#### TASK
Criar `scripts/gates/check_proofs.py <slug> [--root DIR]`, adaptado do `check_proofs.py` do tlc-spec-driven (sem captura de tela nem `walk`, D25): lê o `## Checks` do `tasks.md` (ou do `spec.md` na MÉDIA), executa cada comando `**Build**:`, cada `**Run <name>**:` uma vez e cada `Proof:` isolado, e grava `.specs/features/<slug>/proofs.md`. Testes em `tests/test_check_proofs.py`.

#### CONTEXT
Spec: `.specs/features/fase-3-execucao/spec.md` (R1, R2, R3; formato em `## Data & Contracts`). Checks: C1, C2, C3.
Fonte: `docs/reference/tlc-spec-driven.zip` → `tlc-spec-driven/scripts/check_proofs.py` e `scripts/fixtures/proofs.md`. Gates existentes seguem `scripts/gates/gates_common.py` (seções, raiz do projeto, saída em PT-BR) e `scripts/gates/validate_tasks.py` (leitura dos checks). No Windows, comandos rodam no bash do Git for Windows, como no tlc. Testes existentes de gates: `tests/test_gates.py`, `tests/helpers.py`.
`proofs.md`: `**HEAD**:`, `**Tree**: clean | dirty (modo 1)`, `**Result**: <n> pass, <m> fail`, tabela `| Check | Proof | Result |` com uma linha por check e uma `Build`, `## Output`.

#### BOUNDARIES
May change: `scripts/gates/check_proofs.py`, `scripts/gates/gates_common.py`, `tests/test_check_proofs.py`, `tests/fixtures/proofs/`
Do not touch: `dist/`, `skills/`, `scripts/handoff.py`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T2: Gate validate_verification.py
**Linear**: SC-21
**Depends on**: T1
**Requirements**: R4, R5
**Tests**: unit
**Gate**: quick

#### TASK
Criar `scripts/gates/validate_verification.py [slug] [--root DIR] [--strict]`, adaptado do tlc sem as regras de telas, `walk` e rodadas de captura (D25), com o aviso `verificação degradada` para `**Verification:** degraded | self-verified`. Testes em `tests/test_validate_verification.py`.

#### CONTEXT
Spec: `.specs/features/fase-3-execucao/spec.md` (R4, R5; formato de `verification.md` em `## Data & Contracts`). Checks: C4, C5, C6.
Fonte: `docs/reference/tlc-spec-driven.zip` → `scripts/validate_verification.py` e `scripts/fixtures/verification.md`. Reusar a leitura do `proofs.md` do `scripts/gates/check_proofs.py` (T1) e as funções de `scripts/gates/gates_common.py` (aprovação, seções).

#### BOUNDARIES
May change: `scripts/gates/validate_verification.py`, `scripts/gates/gates_common.py`, `tests/test_validate_verification.py`, `tests/fixtures/verification/`
Do not touch: `dist/`, `skills/`, `scripts/handoff.py`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T3: Gate check_scope.py e estágios novos do run_gates
**Linear**: SC-22
**Depends on**: T2
**Requirements**: R6, R7
**Tests**: unit
**Gate**: quick

#### TASK
Criar `scripts/gates/check_scope.py <slug> <ticket> <base>..<head>` (arquivos fora do `**May change**:`, `.specs/STATE.md` e mudanças na seção `## Handoff` reprovam) e acrescentar ao `scripts/gates/run_gates.py` os estágios `ticket` (`check_scope` + `check_commit` em cada commit do intervalo), `proofs` (`check_proofs`) e `done` (`validate_verification`). Testes em `tests/test_check_scope.py` e `tests/test_run_gates_exec.py`.

#### CONTEXT
Spec: `.specs/features/fase-3-execucao/spec.md` (R6, R7). Checks: C7, C8, C9.
`run_gates.py` já imprime `VEREDITO:` primeiro e uma linha por gate; os estágios novos seguem o mesmo formato. `**May change**:` é lido como em `scripts/gates/validate_tasks.py` e `scripts/gates/tasks_export.py`. Uma entrada que termina em `/` vale para a pasta inteira. `check_commit.py --message` já valida um commit.

#### BOUNDARIES
May change: `scripts/gates/check_scope.py`, `scripts/gates/run_gates.py`, `scripts/gates/gates_common.py`, `tests/test_check_scope.py`, `tests/test_run_gates_exec.py`
Do not touch: `dist/`, `skills/`, `scripts/handoff.py`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T4: Campos de execução no handoff.py e linhas novas do banner
**Linear**: SC-23
**Depends on**: none
**Requirements**: R30, R34, R35, R36, R39
**Tests**: unit
**Gate**: quick

#### TASK
Em `scripts/handoff.py set`, acrescentar `--dispatched`, `--integration-branch`, `--last-integrated`, `--report` (acrescenta item em `**Reports:**`) e `--attempt <id>=fail|ok` (conta em `**Attempts:**`, zera no `ok` e grava `**Breaker:** open (<id>, attempts 3/3)` na 3ª falha), além de `--breaker closed`. No `hooks/scripts/banner.py`, mostrar `Disjuntor aberto: <slug> (<id>)` e `Verificação: degradada (<slug>)` quando o `verification.md` da feature tiver `**Verification:** degraded | self-verified`.

#### CONTEXT
Spec: `.specs/features/fase-3-execucao/spec.md` (R30, R34, R35, R36, R39; campos em `## Data & Contracts`). Checks: C10, C11, C12, C13, C14.
`scripts/handoff.py` já move a seção para o artefato mais avançado e preserva os campos não passados (`tests/test_handoff.py`). O banner já lê `**Phase:**` e `**Breaker:**` (`hooks/scripts/banner.py`); conferir o que já existe antes de duplicar. Formato do Handoff: `skills/engajar/references/state-format.md`.

#### BOUNDARIES
May change: `scripts/handoff.py`, `hooks/scripts/banner.py`, `tests/test_handoff.py`, `tests/test_banner.py`
Do not touch: `dist/`, `skills/`, `scripts/gates/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T5: Skill q e briefing q-verify.md
**Linear**: SC-24
**Depends on**: T2
**Requirements**: R44, R22
**Tests**: unit
**Gate**: quick

#### TASK
Criar `src/briefs/q-verify.md` (briefing autossuficiente com os marcadores `{{spec}}`, `{{tasks}}`, `{{proofs}}`, `{{range}}`, `{{output}}`, que funciona sem o StarCode instalado no CLI do Q) e `skills/q/SKILL.md` (Q em inglês, saída PT-BR, escreve só o `verification.md` no formato do `validate_verification.py`, relatório de até 5 linhas). Testes de conteúdo em `tests/test_q_skill.py`.

#### CONTEXT
Spec: `.specs/features/fase-3-execucao/spec.md` (R44, R22; contrato do Q em `PLANO_STARCODE.md` §4.3). Checks: C15, C16.
Fonte não vinculante: `docs/reference/tlc-spec-driven.zip` → `references/validate.md` (escrever do zero, sem copiar o método do Genesis). Formato de `verification.md`: o de `scripts/gates/validate_verification.py` (T2). Skills existentes como modelo de estrutura: `skills/spock/SKILL.md`, `skills/data/SKILL.md`. Bordões do Q no `src/crew.yaml`.

#### BOUNDARIES
May change: `src/briefs/q-verify.md`, `skills/q/`, `tests/test_q_skill.py`
Do not touch: `dist/`, `skills/engajar/`, `skills/laforge/`, `skills/mccoy/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T6: Skills laforge e mccoy
**Linear**: SC-25
**Depends on**: T3
**Requirements**: R40, R41, R42, R43, R45
**Tests**: unit
**Gate**: quick

#### TASK
Criar `skills/laforge/SKILL.md` (implementa só o ticket do briefing, respeita `**May change**:`, TDD, um commit por tarefa com `Refs: <ID>` validado por `check_commit.py`, para e reporta quando precisa de arquivo fora do escopo, aciona `mccoy` na 2ª falha do mesmo erro, roda `run_gates.py ticket` antes de terminar) e `skills/mccoy/SKILL.md` (teste de regressão antes da correção, só arquivos do escopo, relatório com identificador do erro, causa e teste). Ambas com o relatório de até 5 linhas e a proibição de escrever `STATE.md` e o Handoff. Testes de conteúdo em `tests/test_worker_skills.py`.

#### CONTEXT
Spec: `.specs/features/fase-3-execucao/spec.md` (R40–R43, R45, R38). Checks: C17, C18, C19.
Estágio `ticket` do `run_gates.py` e `check_scope.py` vêm do T3. Regras de commit: `scripts/gates/check_commit.py`. Modos Git: `skills/engajar/references/git-modes.md`. Bordões no `src/crew.yaml`.

#### BOUNDARIES
May change: `skills/laforge/`, `skills/mccoy/`, `tests/test_worker_skills.py`
Do not touch: `dist/`, `skills/engajar/`, `skills/q/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T7: Script dispatch.py (briefings, próximo ticket, família do modelo)
**Linear**: SC-26
**Depends on**: T4, T5, T6
**Requirements**: R9, R10, R19, R21, R38, R45
**Tests**: unit
**Gate**: quick

#### TASK
Criar `scripts/dispatch.py` com: `next <slug>` (primeiro ticket do `tasks.md` cujas dependências estão em `**Last integrated:**`/integradas no Handoff; nenhum quando há despacho aberto), `brief <slug> <ticket> --out <arquivo>` (bloco do ticket + regras fixas do worker: escritor único e relatório de até 5 linhas), `q-brief <slug> --base <B> --head <sha> --out <arquivo>` (preenche `src/briefs/q-verify.md`, sem histórico da sessão) e `family <modelo|cli>` (família pela tabela `families` do `src/crew.yaml`, ou pelo prefixo do CLI quando o modelo é o padrão do CLI; imprime `same`/`different` com `--compare`). Testes em `tests/test_dispatch.py`.

#### CONTEXT
Spec: `.specs/features/fase-3-execucao/spec.md` (R9, R10, R19, R21, R38, R45). Checks: C20, C21, C22, C23.
Handoff lido via `scripts/handoff.py` (campos do T4). Briefing do Q: `src/briefs/q-verify.md` (T5). `src/crew.yaml` lido com `tools/miniyaml.py`. Marcador `<plugin-root>` e caminhos: `scripts/starcode_common.py`.

#### BOUNDARIES
May change: `scripts/dispatch.py`, `scripts/starcode_common.py`, `tests/test_dispatch.py`
Do not touch: `dist/`, `skills/`, `scripts/handoff.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T8: Picard executa: skill engajar e referência execute.md
**Linear**: SC-27
**Depends on**: T7
**Requirements**: R8, R11, R12, R13, R14, R15, R16, R17, R18, R20, R23, R24, R25, R26, R27, R28, R29, R31, R32, R33, R37
**Tests**: unit
**Gate**: quick

#### TASK
Acrescentar à `skills/engajar/SKILL.md` o passo de execução e criar `skills/engajar/references/execute.md` com o roteiro do Picard: ramo de integração, `dispatch.py next/brief`, Handoff antes do `worker-start`, `worktree set --linear-issue`, `check --wait --types worker_done`, falhas e tentativas, `run_gates.py ticket` e `merge --no-ff`, conflito com `merge --abort`, retomada com `worker-show`, `run_gates.py proofs`, despacho do Q com a cascata codex → antigravity → self-verified, descarte de escrita extra do Q, ciclo pós-Q, status e comentários no Linear, modo 1 e paradas. Atualizar `state-format.md` (campos novos), `linear-contract.md` (marcos de execução) e o `src/context/STARCODE.md` onde citar a Fase 3. Testes de conteúdo em `tests/test_skills_exec.py`.

#### CONTEXT
Spec: `.specs/features/fase-3-execucao/spec.md` (R8, R11–R18, R20, R23–R29, R31–R33, R37). Checks: C24, C25, C26, C27, C28, C29.
Fluxo em `PLANO_STARCODE.md` §4, §4.3, §4.6, §4.7; CLI da Orca em `docs/cli-baseline/orca-orchestration-worker-start.txt` e `orca orchestration check --help` (`--wait`, `--types`, `--timeout-ms`). Linear por `orca linear` (D2). Scripts do T3, T4 e T7. A skill atual para em `published` (passo 5 da `skills/engajar/SKILL.md`).

#### BOUNDARIES
May change: `skills/engajar/`, `src/context/STARCODE.md`, `tests/test_skills_exec.py`
Do not touch: `dist/`, `skills/laforge/`, `skills/mccoy/`, `skills/q/`, `scripts/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T9: Build, crew, evals e registros da fase
**Linear**: SC-28
**Depends on**: T8
**Requirements**: R46, R47, R48
**Tests**: unit
**Gate**: build
**Runs alone**: yes

#### TASK
Fazer o `tools/build.py` copiar `src/briefs/` para `dist/claude` e emitir `laforge`, `mccoy` e `q`; completar `src/crew.yaml` (famílias de modelos do Codex e do Antigravity, quando conhecidas); acrescentar em `evals/routing/` casos positivos para `laforge`, `mccoy` e `q` e atualizar `evals/README.md`; registrar F3-* em `DECISIONS.md`, a origem dos gates adaptados em `CREDITS.md` e a revisão 4.7 no `PLANO_STARCODE.md`; regenerar `dist/`. Testes em `tests/test_build.py`.

#### CONTEXT
Spec: `.specs/features/fase-3-execucao/spec.md` (R46, R47, R48). Checks: C30, C31.
`tools/build.py` emite um tripulante só quando `skills/<skill>/SKILL.md` existe; `dist/` nunca é editado à mão. Evals: `evals/README.md` (`--ablation none`). `scripts/check_decisions.py` exige entrada nova em `DECISIONS.md` quando `skills/`, `scripts/` ou `hooks/` mudam (D30).

#### BOUNDARIES
May change: `tools/build.py`, `src/crew.yaml`, `evals/`, `tests/test_build.py`, `DECISIONS.md`, `CREDITS.md`, `PLANO_STARCODE.md`, `dist/`
Do not touch: `skills/`, `scripts/`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T10: Roteiros de aceite no sandbox e evidência
**Linear**: SC-29
**Depends on**: T9
**Requirements**: R48
**Tests**: unit
**Gate**: build

#### TASK
Rodar no sandbox (`F:\Projetos\starcode-sandbox`, time PROJ, feature task-priority, PROJ-7..9) os roteiros de aceite da SC-10: modo 2 (3 tickets por workers, Q em outra família, achado plantado corrigido), modo 1, degradado, disjuntor e escritor único; registrar a evidência de cada um em `docs/aceite/fase-3.md`. Teste em `tests/test_acceptance_doc.py` que confere as cinco seções do roteiro com evidência.

#### CONTEXT
Spec: `.specs/features/fase-3-execucao/spec.md` (R48; aceite da Fase 3 em `PLANO_STARCODE.md` §10). Checks: C32.
Modelo de evidência: `docs/aceite/fase-2.md`. Nunca criar projeto de teste no time SC.

#### BOUNDARIES
May change: `docs/aceite/fase-3.md`, `tests/test_acceptance_doc.py`
Do not touch: `dist/`, `skills/`, `scripts/`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `check_proofs.py` executa Build, cada Run uma vez e cada Proof isolado, e grava `proofs.md` com HEAD, Tree, Result e uma linha por check e Build (R1)
Proof: run unit | test_check_proofs_writes_proofs_md ... ok

**C2** - Uma prova `run` só passa com as palavras depois de `|` em ordem numa mesma linha; filtro que não roda teste reprova (R2)
Proof: run unit | test_run_proof_needs_words_in_order_on_one_line ... ok

**C3** - Árvore suja grava `**Tree**: dirty (modo 1)` e sai com código 1 mesmo com provas verdes (R3)
Proof: run unit | test_dirty_tree_marks_mode1_and_fails ... ok

**C4** - `validate_verification.py` sai com 1 sem `proofs.md`/`verification.md`, com `proofs.md` de outro HEAD ou árvore suja, ou com check sem linha `pass` (R4)
Proof: run unit | test_verification_fails_on_missing_or_stale_proofs ... ok

**C5** - `validate_verification.py` sai com 1 com achado sem commit em `Closed`, check sem teste no `verification.md` ou sem `**Approved**:` em spec/tasks (R4)
Proof: run unit | test_verification_fails_on_open_finding_or_missing_approval ... ok

**C6** - `**Verification:** degraded`/`self-verified` imprime `verificação degradada`, sai 0 sem `--strict` e 1 com `--strict` (R5)
Proof: run unit | test_degraded_warns_and_strict_fails ... ok

**C7** - `check_scope.py` reprova e lista arquivo fora do `**May change**:` (pasta com `/` aceita os filhos) (R6)
Proof: run unit | test_check_scope_flags_outside_may_change ... ok

**C8** - `check_scope.py` reprova alteração em `.specs/STATE.md` ou na seção `## Handoff` (R6, R38)
Proof: run unit | test_check_scope_flags_state_and_handoff ... ok

**C9** - `run_gates.py` aceita `ticket`, `proofs` e `done` e imprime o VEREDITO primeiro (R7)
Proof: run unit | test_run_gates_execution_stages ... ok

**C10** - `handoff.py set` grava e preserva `--dispatched`, `--integration-branch`, `--last-integrated` e `--report` (R39)
Proof: run unit | test_handoff_execution_fields ... ok

**C11** - `--attempt <id>=fail` conta por identificador e `--attempt <id>=ok` zera a contagem daquele identificador (R34)
Proof: run unit | test_attempts_count_and_reset ... ok

**C12** - A 3ª falha do mesmo identificador grava `**Breaker:** open (<id>, attempts 3/3)` (R35)
Proof: run unit | test_third_failure_opens_breaker ... ok

**C13** - O banner mostra `Disjuntor aberto: <slug> (<id>)` quando o Handoff tem o disjuntor aberto (R36)
Proof: run unit | test_banner_shows_open_breaker ... ok

**C14** - O banner mostra `Verificação: degradada (<slug>)` quando o `verification.md` está degraded ou self-verified (R30)
Proof: run unit | test_banner_shows_degraded_verification ... ok

**C15** - `q-verify.md` tem os cinco marcadores, a regra de escrever só `verification.md`, as três tarefas do Q e funciona sem StarCode instalado (R44)
Proof: run unit | test_q_brief_contract ... ok

**C16** - A skill `q` exige CLI, modelo pedido e efetivo (ou `model: unconfirmed`) e HEAD no `verification.md` (R22, R44)
Proof: run unit | test_q_skill_records_model_and_head ... ok

**C17** - A skill `laforge` limita a escrita ao `**May change**:`, exige TDD, um commit por tarefa com `Refs:` e para ao precisar de arquivo fora do escopo (R40, R41)
Proof: run unit | test_laforge_skill_scope_tdd_commit ... ok

**C18** - A skill `laforge` aciona `mccoy` na 2ª falha do mesmo identificador, antes da 3ª tentativa (R42)
Proof: run unit | test_laforge_calls_mccoy_on_second_failure ... ok

**C19** - A skill `mccoy` exige teste de regressão antes da correção e o relatório com identificador, causa e teste; as duas skills têm o relatório de até 5 linhas (R43, R45)
Proof: run unit | test_mccoy_skill_regression_and_report ... ok

**C20** - `dispatch.py next` devolve o primeiro ticket com dependências integradas e nenhum quando há despacho aberto (R9)
Proof: run unit | test_next_ticket_respects_dependencies ... ok

**C21** - `dispatch.py brief` grava o bloco do ticket com as regras de escritor único e de relatório de até 5 linhas (R10, R38, R45)
Proof: run unit | test_ticket_brief_has_block_and_worker_rules ... ok

**C22** - `dispatch.py q-brief` preenche todos os marcadores e não deixa nenhum `{{...}}` nem histórico da sessão (R19)
Proof: run unit | test_q_brief_fills_placeholders ... ok

**C23** - `dispatch.py family --compare` acusa `same` para dois modelos da mesma família e `different` para claude × codex (R21)
Proof: run unit | test_family_compare ... ok

**C24** - `execute.md` manda criar ou reutilizar `feature/<slug>`, gravar o Handoff antes do `worker-start`, usar `worktree set --linear-issue` e `check --wait --types worker_done` com 3600000 ms (R8, R11, R12)
Proof: run unit | test_execute_ref_dispatch_steps ... ok

**C25** - `execute.md` cobre falha/timeout sem integração com tentativa `worker-<ticket>`, `run_gates.py ticket` + `merge --no-ff`, `merge --abort` no conflito, comentário de integração e retomada com `worker-show` (R13, R14, R15, R16, R17)
Proof: run unit | test_execute_ref_integration_and_resume ... ok

**C26** - `execute.md` roda `run_gates.py proofs` após o último ticket, despacha o Q com a cascata codex → antigravity → self-verified e descarta escrita do Q fora do `verification.md` (R18, R20, R23)
Proof: run unit | test_execute_ref_q_dispatch ... ok

**C27** - `execute.md` descreve o ciclo pós-Q: um LaForge com todos os achados, provas e `done` de novo sem segundo Q, parada para mudança de spec e achado aberto ao usuário (R24, R25, R26, R27)
Proof: run unit | test_execute_ref_post_q_cycle ... ok

**C28** - `execute.md` move para started com `crew:laforge`, review ou comentário "pronto para revisão", completed só com confirmação e nunca no modo 1 (R28, R29, R31)
Proof: run unit | test_execute_ref_linear_states ... ok

**C29** - `execute.md` descreve o modo 1 (um worktree, sem commits, `git diff <base>`, achados fechados como degradados) e segue para o próximo ticket sem perguntar (R32, R33, R37)
Proof: run unit | test_execute_ref_mode1_and_no_stop ... ok

**C30** - O build emite `laforge`, `mccoy`, `q` e `briefs/q-verify.md` em `dist/claude` (R46)
Proof: run unit | test_build_emits_execution_skills ... ok

**C31** - `evals/routing/` tem casos positivos de `laforge`, `mccoy` e `q`, e `DECISIONS.md` tem entradas F3 (R47, R48)
Proof: run unit | test_routing_and_decisions_cover_phase3 ... ok

**C32** - `docs/aceite/fase-3.md` tem as cinco seções do roteiro (modo 2, modo 1, degradado, disjuntor, escritor único), cada uma com evidência (R48)
Proof: run unit | test_acceptance_doc_has_all_scripts ... ok

## Handoff

**Phase:** published
**Size:** LARGE
**Git mode:** 2
**Next:** Implementar T1 (SC-20) na sessão (LaForge ainda não existe), depois T4
**Linear:** SC-10 (pai); T1..T10 = SC-20..SC-29 (Todo, crew:data, blocks), publicado em 2026-11-04 após user: "sim"
**Integration branch:** not created
**Last integrated:** none
**Dispatched:** none
**Settled:** none
**Breaker:** closed
