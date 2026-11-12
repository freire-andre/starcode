# Fase 12 - Robustez (v1.6): Tasks

**Approved**: 2026-11-12 - user: "Sim"

**Spec**: `.specs/features/fase-12-robustez/spec.md`
**Status**: Approved
**Integration branch**: `feature/fase-12-robustez`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only, no generator change | `python -m unittest discover -s tests -v` |
| full | task that changes `scripts/`, `src/`, `skills/`, `tools/` or `tests/` (F3-1: `dist/` regenerated in the same commit) | `python tools/build.py && python tools/build.py --check && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |
| build | records task, or after the last code task | `python tools/build.py && python tools/build.py --check && claude plugin validate dist/claude --strict && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |

## Tasks

### T1: Snapshot do modo 1 - take, list e drop (snapshot.py)
**Linear**: SC-149
**Depends on**: none
**Requirements**: R1, R2, R3, R4, R5, R6, R13
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/snapshot.py` (só stdlib, CLI com `argparse`, subcomandos `take`, `list`, `drop`; `restore` fica para a T2):
- `take <slug> <ticket> [--root DIR]` (R1, R2, R3): monta o snapshot com um índice temporário. Passos:
  - cria um arquivo temporário e define `GIT_INDEX_FILE` só no ambiente dos subprocessos;
  - `git read-tree HEAD`, depois `git add -A` (rastreados + não rastreados não ignorados);
  - `git write-tree`, depois `git commit-tree <tree> -p HEAD -m "starcode snapshot <slug>/<ticket>"`;
  - `git update-ref refs/starcode/snapshots/<slug>/<ticket> <commit>`.

  O temporário é removido também em erro. Saída: `snapshot <slug>/<ticket> <hash curto> (<n> arquivos)`, com ` (substituído <hash curto antigo>)` quando o ref já existia. O `.git/index` real, a árvore, o HEAD e os branches não mudam.
- Validação (R4): `<slug>` casa `^[a-z0-9][a-z0-9-]*$`, `<ticket>` casa `^[A-Za-z0-9][A-Za-z0-9._-]*$` e o ref passa em `git check-ref-format`. Senão, sai com 2 e `nome inválido para o snapshot: <valor>`.
- Erros (R5): fora de repositório, sem HEAD ou `git` falhando → sai com 1 e `snapshot falhou: <passo>: <motivo>`, sem ref gravado.
- `list <slug> [--root DIR] [--json]` (R6): ticket, hash curto, data (ISO do commit) e quantidade de arquivos (`git ls-tree -r --name-only`). Com `--json`, objetos `{"ticket","commit","date","files"}`. Sem snapshots, `nenhum snapshot de <slug>` / `[]`, saindo com 0.
- `drop <slug> [--root DIR]` (R13): apaga `refs/starcode/snapshots/<slug>/*` (`git for-each-ref` + `git update-ref -d`) e imprime `removidos <n> snapshots de <slug>` (sai com 0 também com n = 0).
- Funções importáveis para a T2: `ref_name(slug, ticket)`, `run_git(root, *args, env=None)`, `snapshot_commit(root, slug, ticket)`.
- Entrada F12-1 em `DECISIONS.md`: índice temporário no lugar do `git stash create` (o stash não guarda não rastreados) e o ref `refs/starcode/snapshots/<slug>/<ticket>` (IDs de ticket se repetem entre features).
- Testes em `tests/test_snapshot.py`, com repositórios Git temporários (`tempfile`, `git init`, `user.name`/`user.email` locais, um commit inicial), sem docstring nos testes citados por check, com os nomes: `test_take_grava_ref_com_rastreados_e_novos`, `test_take_nao_altera_indice_arvore_head`, `test_take_substitui_snapshot_existente`, `test_take_nome_invalido_sai_2`, `test_take_sem_head_ou_fora_do_git_sai_1`, `test_list_texto_json_e_vazio`, `test_drop_remove_refs_da_feature`.

#### CONTEXT
Spec: `.specs/features/fase-12-robustez/spec.md` (R1–R6, R13; Data & Contracts; Edge Cases). Checks: C1–C7.
Padrões do repo: scripts em `scripts/` só com stdlib, mensagens em PT-BR, `main(argv) -> int` e `if __name__ == "__main__": sys.exit(main())` (veja `scripts/handoff.py`, `scripts/git_mode.py`). Os testes importam scripts com `import helpers` (que monta o `sys.path`; veja `tests/helpers.py`, `tests/test_handoff.py`). O hook `git_guard` não intercepta subprocessos do Python, e `commit-tree` em ref fora de `refs/heads` não cria commit em branch (permitido pelo plano para o modo 1).

#### BOUNDARIES
May change: `scripts/snapshot.py`, `tests/test_snapshot.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/impact.py`, `scripts/dispatch.py`, `scripts/handoff.py`, `hooks/`, `skills/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-12-robustez`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T2: Restauração do snapshot limitada ao May change
**Linear**: SC-150
**Depends on**: T1
**Requirements**: R7, R8, R9, R10, R11, R12, R36
**Tests**: unit
**Gate**: full

#### TASK
Acrescentar `restore <slug> <ticket> [--root DIR] [--yes]` a `scripts/snapshot.py`:
- `May change` do ticket: de `tasks.md` (`validate_tasks.Task.may_change`); feature sem `tasks.md` usa o `**May change**:` da spec, como `scripts/gates/check_scope.py` (`spec_may_change`). O casamento de caminhos é o mesmo do `check_scope.py`: entrada terminada em `/` cobre a pasta, `fnmatch` para padrões. Entrada com `..` que sai da raiz é ignorada com aviso.
- Plano (R7): os caminhos que casam com o `May change` e diferem entre o snapshot e a árvore atual (rastreados + não rastreados não ignorados). A diferença é vista pelo Git (`git diff --name-status <snapshot>` com índice temporário montado da árvore atual, ou equivalente), respeitando `core.autocrlf` e o bit executável. Cada caminho é `voltar` (existe no snapshot) ou `remover` (não existe). Sem `--yes`: imprime o plano no formato de Data & Contracts e `nada foi alterado: rode de novo com --yes depois da confirmação do usuário`, saindo com 0.
- `--yes` (R8): grava os bytes do blob (`git cat-file blob <snapshot>:<caminho>`) e o bit executável (modo `100755`) em cada `voltar`, apaga cada `remover` e imprime `restaurado <slug>/<ticket>: <v> voltaram, <r> removidos`. Nada fora do `May change` é escrito ou apagado; o `.git/index` real não é alterado.
- `fora do ticket (não tocados):` (R9): caminhos fora do `May change` que diferem do snapshot, até 50 linhas mais `e mais N`, com e sem `--yes`.
- Recusas (R10, R11), sem alterar nada e saindo com 1:
  - HEAD diferente do pai do snapshot → `HEAD mudou desde o snapshot (<pai> → <atual>): restauração recusada`;
  - snapshot inexistente, ticket fora do `tasks.md` ou `May change` vazio → mensagem com o motivo.
- Falha parcial (R12): para no caminho que falhou e imprime os já restaurados, o que falhou com o motivo e os que faltaram, saindo com 1. Rodar de novo com `--yes` termina (idempotente).
- Entrada F12-2 em `DECISIONS.md`: a restauração só toca o `May change` e não usa `checkout -- .`, `restore .`, `reset --hard` nem `clean -f` (bloqueados pelo `git_guard`).
- Testes em `tests/test_snapshot_restore.py`: `test_restore_sem_yes_mostra_plano_e_nao_altera`, `test_restore_yes_volta_e_remove_so_no_may_change`, `test_restore_lista_fora_do_ticket_com_limite`, `test_restore_recusa_head_mudado`, `test_restore_sem_snapshot_ou_ticket_sem_may_change`, `test_restore_falha_parcial_e_retomada` e `test_cenario_aceite_disjuntor_modo_1`. Este último reproduz o R36 num repositório temporário com `tasks.md` mínimo (`May change: src/`):
  1. `take`;
  2. o "ticket" altera um arquivo em `src/` e cria outro;
  3. o "usuário" edita `notas.md`;
  4. três `handoff.py set --attempt gate-x=fail` abrem o disjuntor (`**Breaker:** open`);
  5. `restore` sem `--yes` lista `notas.md` em "fora do ticket";
  6. `restore --yes`.

  No fim, `src/` está igual ao snapshot, o arquivo criado sumiu, `notas.md` mantém a edição e `git rev-list --count HEAD` não mudou.

#### CONTEXT
Spec: `.specs/features/fase-12-robustez/spec.md` (R7–R12, R36; Data & Contracts; Edge Cases). Checks: C8–C13, C36.
Já existe (T1): `scripts/snapshot.py` com `take`, `list`, `drop`, `ref_name`, `run_git`, `snapshot_commit`. Parse do `tasks.md`: `scripts/gates/validate_tasks.py` (`Task.may_change`); `May change` da spec e casamento de caminhos: `scripts/gates/check_scope.py` e `scripts/gates/gates_common.py` (`split_paths`, `fnmatch`). Os módulos dos gates importam irmãos com `sys.path.insert(0, ...)`. Disjuntor: `scripts/handoff.py` (`--attempt`, `BREAKER_LIMIT = 3`).

#### BOUNDARIES
May change: `scripts/snapshot.py`, `tests/test_snapshot_restore.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/gates/`, `scripts/handoff.py`, `scripts/impact.py`, `hooks/`, `skills/`, `src/`, `tests/test_snapshot.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-12-robustez`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T3: Raio de impacto - núcleo e grafo Python (impact.py)
**Linear**: SC-151
**Depends on**: T2
**Requirements**: R14, R15, R16, R18, R19, R20, R21, R23, R24, R25, R26, R27, R37
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/impact.py` (só stdlib), subcomando `select [--root DIR] [--json] (<arquivo>... | --diff <base>[..<head>])`:
- Arquivos do repositório (R14): `git ls-files -co --exclude-standard`. Com `--diff`, os mudados são `git diff --name-only <intervalo>` mais os não rastreados (sem `..<head>`, a árvore de trabalho contra `<base>`). Caminhos em posix, relativos à raiz.
- Testes (R15): em Python, `test_*.py`, `*_test.py` e `.py` sob `tests/` ou `test/`; em TS/JS, `*.test.*`, `*.spec.*` e sob `__tests__/`. A T4 usa a mesma função.
- Grafo Python (R16), pelo `ast`:
  - `import a.b` e `from a.b import c` (também `a/b/c.py` quando `c` é módulo);
  - relativos a partir da pasta do arquivo;
  - um nome absoluto casa com todo arquivo cujo caminho termina em `a/b.py` ou `a/b/__init__.py`, e com vários candidatos liga a todos;
  - sem candidato, é externo.
- Estrutura extensível por linguagem: um resolvedor por extensão. A T4 acrescenta TS/JS. Nesta task, arquivos TS/JS ainda contam como "fora do grafo".
- Seleção:
  - teste mudado entra no conjunto (R18);
  - fecho transitivo dos dependentes reversos, com visitados (sem loop em ciclo) e cadeia mínima por teste (BFS) (R19).
- Vereditos `rodar tudo`, cada um com seu motivo:
  - mudado fora do grafo, apagado ou fora da lista → `fora do grafo: <arquivos>` (R20);
  - arquivo do grafo ilegível, com erro de sintaxe ou acima de 1 MiB → `grafo incompleto: <arquivo>: <erro>` (R21);
  - nenhum teste alcança a mudança → `nenhum teste alcança <arquivos>` (R23);
  - sem mudança → `nenhuma mudança informada` (R24).
- Saída texto (R25): `selecionados <n> testes` + uma linha por teste com a cadeia `a <- b <- c`, ou `rodar tudo: <motivo>`, sempre saindo com 0.
- Saída JSON (R26): `{"verdict": "selected"|"run-all", "tests": [...], "chains": {...}, "reason": "...", "changed": [...]}`.
- Erros (R27): `git` falhando ou fora de repositório → 1 e `impact falhou: <passo>: <motivo>`; nenhum arquivo e nenhum `--diff`, ou os dois juntos → 2.
- Função importável `select(root, changed=None, diff=None) -> dict` (usada pela T6).
- Entrada F12-3 em `DECISIONS.md`: grafo por arquivo, regra conservadora dos candidatos múltiplos, todo caso de dúvida vira "rodar tudo"; os gates continuam com a suíte inteira.
- Testes em `tests/test_impact.py` com repositórios temporários: `test_select_diff_inclui_nao_rastreados`, `test_identifica_testes_python_e_ts`, `test_python_imports_absolutos_relativos_e_ambiguos`, `test_teste_mudado_entra_no_conjunto`, `test_dependentes_transitivos_e_ciclo`, `test_fora_do_grafo_roda_tudo`, `test_grafo_incompleto_roda_tudo`, `test_nenhum_teste_alcanca_roda_tudo`, `test_sem_mudanca_roda_tudo`, `test_saida_texto_selecao_e_rodar_tudo`, `test_saida_json_contrato`, `test_erros_git_e_argumentos` e `test_impact_no_repo_starcode` (R37: no próprio repositório StarCode, `select(ROOT, changed=["scripts/gates/gates_common.py"])` devolve `selected` com ao menos uma cadeia de 3 ou mais elos; `select(ROOT, changed=["README.md"])` devolve `run-all` com `fora do grafo`).

#### CONTEXT
Spec: `.specs/features/fase-12-robustez/spec.md` (R14–R16, R18–R21, R23–R27, R37; Data & Contracts; Edge Cases). Checks: C14–C16, C18–C21, C23–C27, C37.
Os testes do StarCode importam scripts sem pacote (`import handoff`, via `tests/helpers.py` que monta o `sys.path`), por isso a regra dos candidatos múltiplos. `dist/` também tem cópias dos scripts (`dist/<cli>/scripts/`): elas entram como candidatos, o que só deixa a seleção mais larga. Padrões de CLI: `scripts/handoff.py`.

#### BOUNDARIES
May change: `scripts/impact.py`, `tests/test_impact.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/snapshot.py`, `scripts/dispatch.py`, `skills/`, `src/`, `tests/test_snapshot.py`, `tests/test_snapshot_restore.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-12-robustez`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T4: Raio de impacto - grafo TS/JS e aliases
**Linear**: SC-152
**Depends on**: T3
**Requirements**: R17, R22, R37
**Tests**: unit
**Gate**: full

#### TASK
Acrescentar o resolvedor TS/JS a `scripts/impact.py`:
- Extensões `.ts`, `.tsx`, `.mts`, `.cts`, `.js`, `.jsx`, `.mjs`, `.cjs` (R14, R17).
- Formas reconhecidas por regex (R17): `import ... from '<esp>'` (inclusive multilinha e `import type`), `import '<esp>'`, `export ... from '<esp>'`, `import('<esp>')` e `require('<esp>')`. Aspas simples e duplas.
- Arestas (R17): só especificadores `./` e `../` viram arestas. A resolução testa o caminho exato, cada extensão e `<esp>/index.<ext>`. O resto é externo.
- Aliases (R22): com `tsconfig.json`/`jsconfig.json` que tem `compilerOptions.paths` ou `baseUrl` (JSON lido com tolerância a comentários `//` e vírgula final), ou com algum import `@/...` ou `~/...`, uma mudança em TS/JS dá `rodar tudo` com o motivo `aliases do TypeScript não resolvidos`.
- Entrada F12-4 em `DECISIONS.md` (só imports relativos; aliases → rodar tudo).
- Testes em `tests/test_impact_ts.py`: `test_ts_imports_relativos_extensoes_e_index`, `test_aliases_ts_roda_tudo` e `test_impact_fixture_telas` (R37: copia `aceite/telas` para um diretório temporário com `git init` e um commit, depois `select(..., changed=["src/greeting.ts"])` inclui `src/greeting.test.ts`).

#### CONTEXT
Spec: `.specs/features/fase-12-robustez/spec.md` (R17, R22, R37). Checks: C17, C22, C38.
Já existe (T3): `scripts/impact.py` com resolvedor por extensão, `select()`, saídas texto e JSON. Fixture TS: `aceite/telas/` (`src/greeting.ts`, `src/greeting.test.ts`, `tsconfig.json`); `tools/aceite.py` mostra como copiar a fixture ignorando `node_modules`, `dist`, `.git` e `target`.

#### BOUNDARIES
May change: `scripts/impact.py`, `tests/test_impact_ts.py`, `DECISIONS.md`, `dist/`
Do not touch: `aceite/`, `scripts/snapshot.py`, `scripts/dispatch.py`, `skills/`, `src/`, `tests/test_impact.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-12-robustez`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T5: Snapshot e raio de impacto no fluxo (Picard e McCoy)
**Linear**: SC-153
**Depends on**: T4
**Requirements**: R28, R29, R30, R31
**Tests**: unit
**Gate**: full

#### TASK
- `skills/engajar/references/execute.md`, seção 7 (modo 1):
  - antes de cada despacho do LaForge, `python "<plugin-root>/scripts/snapshot.py" take <slug> <ticket>`, com a linha impressa registrada por `handoff.py set --report`; se o `take` falha, o ticket não é despachado (R28);
  - depois de `--phase done`, `snapshot.py drop <slug>` (R30).
- `skills/engajar/references/execute.md`, seção 6 (R29): no modo 1, a saída (b) do disjuntor é o snapshot do ticket que falhou. O Picard roda `snapshot.py restore <slug> <ticket>` sem `--yes`, mostra o plano e a lista "fora do ticket" e pede um sim para essa restauração. Só então roda com `--yes` e grava `--breaker closed`. Com `**Dispatched:**` não fechado, primeiro `worker-stop`.
- `skills/mccoy/SKILL.md` (R31): depois do teste de regressão e da correção, `python "<plugin-root>/scripts/impact.py" select --diff <base>` (base = `baseBranch` do config). O McCoy roda os testes escolhidos, ou a suíte inteira no `rodar tudo`, antes do gate do ticket, e põe a linha do veredito no relatório. Diga que os gates continuam rodando a suíte inteira.
- Entrada F12-5 em `DECISIONS.md`.
- Testes em `tests/test_flow_f12.py`, lendo os arquivos-fonte: `test_execute_md_snapshot_antes_do_ticket`, `test_execute_md_saida_b_restaura_snapshot`, `test_execute_md_drop_no_done` e `test_mccoy_skill_raio_de_impacto`.

#### CONTEXT
Spec: `.specs/features/fase-12-robustez/spec.md` (R28–R31). Checks: C28–C31.
Já existe: `scripts/snapshot.py` (T1, T2) e `scripts/impact.py` (T3, T4). Seções 6 e 7 de `skills/engajar/references/execute.md`; método do McCoy em `skills/mccoy/SKILL.md` (passos 4 e 5). Testes que leem skills: `tests/test_q_skill.py`, `tests/test_guinan_skill.py`. O marcador `<plugin-root>` é substituído pelo `tools/build.py`.

#### BOUNDARIES
May change: `skills/engajar/references/execute.md`, `skills/mccoy/SKILL.md`, `tests/test_flow_f12.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/`, `src/`, `skills/q/`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-12-robustez`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T6: Testes de regressão no brief do Q
**Linear**: SC-154
**Depends on**: T5
**Requirements**: R32, R33
**Tests**: unit
**Gate**: full

#### TASK
- `scripts/dispatch.py` `q_brief` (R32): calcula `impact.select(root, diff="<base>..<head>")` e preenche `{{regression}}` com a saída em texto do `impact.py`: a lista com as cadeias, ou `rodar tudo: <motivo>`. Se o `impact` falha (exceção ou erro de Git), o bloco diz `seleção indisponível: <motivo>; rode a suíte inteira` e o brief é gerado assim mesmo.
- `src/briefs/q-verify.md` (R33): em "Inputs", o bloco `{{regression}}`; em "What you do", a regra de rodar esses testes em HEAD (no `rodar tudo`, a suíte inteira) e registrar o resultado em `## Limits`. A regra 2 ("não rode a suíte inteira para confirmar as provas") ganha a exceção do `rodar tudo` da regressão. O brief segue autocontido, sem caminhos do plugin.
- Entrada F12-6 em `DECISIONS.md`.
- Testes em `tests/test_dispatch_regression.py`: `test_q_brief_bloco_regression`, `test_q_brief_impact_indisponivel` e `test_q_verify_regra_regression_autocontida`.

#### CONTEXT
Spec: `.specs/features/fase-12-robustez/spec.md` (R32, R33). Checks: C32–C34.
Já existe: `scripts/dispatch.py` (`q_brief`, `brief_template`, placeholders `{{spec}}`, `{{range}}` etc.), `src/briefs/q-verify.md`, `scripts/impact.py` (`select`, formatação texto). Testes do dispatch: `tests/test_dispatch.py`, `tests/test_dispatch_screens.py`.

#### BOUNDARIES
May change: `scripts/dispatch.py`, `src/briefs/q-verify.md`, `tests/test_dispatch_regression.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/impact.py`, `scripts/snapshot.py`, `skills/`, `tests/test_dispatch.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-12-robustez`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T7: Build nos 4 CLIs e registros da fase
**Linear**: SC-155
**Depends on**: T6
**Requirements**: R34, R35
**Tests**: unit
**Gate**: build

#### TASK
- `python tools/build.py` leva `scripts/snapshot.py`, `scripts/impact.py` e `src/briefs/q-verify.md` para `dist/<cli>/` nos 4 CLIs. Ajuste `tools/build.py` só se algum arquivo não chegar. `build.py --check` verde (R34).
- Registros (R35):
  - `PLANO_STARCODE.md`: o texto da Fase 12 (índice temporário, ref com `<slug>`, restauração limitada ao `May change`, Python + TS/JS) e o parágrafo do disjuntor (o snapshot do modo 1 existe);
  - `CHANGELOG.md`: entradas em `## [Unreleased]` (Adicionado: `snapshot.py`, `impact.py`, regressão no brief do Q);
  - `docs/compatibilidade.md`: linhas de snapshot (modo 1) e raio de impacto (Python e TS/JS; Rust = rodar tudo; import dinâmico não visto);
  - `DECISIONS.md`: F12-7 fecha a fase.
- Testes em `tests/test_release_docs_f12.py`: `test_build_leva_snapshot_e_impact` (os arquivos existem em `dist/<cli>/scripts/` nos 4 CLIs) e `test_registros_fase_12` (F12-n sem duplicata, `[Unreleased]` cita snapshot e raio de impacto, compatibilidade com as duas linhas, plano com `refs/starcode/snapshots/<slug>/<ticket>`).

#### CONTEXT
Spec: `.specs/features/fase-12-robustez/spec.md` (R34, R35). Checks: C35, C39.
Modelos: `tests/test_release_docs_f11.py`, `tests/test_build.py`; seção 10 "Fase 12" e o parágrafo do disjuntor (busque "snapshot da Fase 12") em `PLANO_STARCODE.md`; `CHANGELOG.md` com `## [Unreleased]` no topo.

#### BOUNDARIES
May change: `tools/build.py`, `PLANO_STARCODE.md`, `CHANGELOG.md`, `docs/compatibilidade.md`, `DECISIONS.md`, `tests/test_release_docs_f12.py`, `dist/`
Do not touch: `scripts/`, `skills/`, `src/`, `VERSION`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-12-robustez`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T8: Aceite real da Fase 12
**Linear**: SC-156
**Depends on**: T7
**Requirements**: R36, R37, R38
**Tests**: unit
**Gate**: quick

#### TASK
Rodar o aceite real e registrar em `docs/aceite/fase-12.md`:
- Snapshot (R36), num repositório temporário fora do StarCode, com `.specs/features/aceite/tasks.md` mínimo (ticket `T1`, `May change: src/`) e o modo Git 1 gravado (`python scripts/git_mode.py set 1 --root <repo>` ou equivalente documentado no `--help`). A sequência:
  1. `snapshot.py take aceite T1`;
  2. altera `src/app.py` e cria `src/novo.py`;
  3. edita `notas.md`;
  4. três `handoff.py set aceite --attempt gate-x=fail` até `DISJUNTOR ABERTO`;
  5. `snapshot.py restore aceite T1` (plano com `notas.md` em "fora do ticket");
  6. `restore --yes`;
  7. confere `src/`, `notas.md`, `git status` e `git rev-list --count HEAD`.
- Raio de impacto (R37):
  - `impact.py select scripts/gates/gates_common.py` no StarCode (cadeia com 3 ou mais elos);
  - `impact.py select README.md` (`rodar tudo: fora do grafo`);
  - na cópia preparada por `python tools/aceite.py preparar telas`, `impact.py select src/greeting.ts` inclui `src/greeting.test.ts`.
- Registro (R38): comandos, saídas relevantes e hashes dos snapshots. `**Resultado**: aprovado` só com R36 e R37 atendidos.
- Teste em `tests/test_acceptance_doc_f12.py`: `test_acceptance_doc_f12` (o arquivo existe, tem `**Resultado**: aprovado`, cita `refs/starcode/snapshots/aceite/T1`, `DISJUNTOR ABERTO`, `fora do ticket`, `rodar tudo: fora do grafo` e `src/greeting.test.ts`).

#### CONTEXT
Spec: `.specs/features/fase-12-robustez/spec.md` (R36–R38). Checks: C36, C37, C38, C40.
Modelos: `docs/aceite/fase-11.md` e `tests/test_acceptance_doc_f11.py`. Scripts: `scripts/snapshot.py`, `scripts/impact.py`, `scripts/handoff.py` (`--root` quando o repositório não é o atual), `scripts/git_mode.py`, `tools/aceite.py`. Os repositórios temporários ficam fora do StarCode e não são commitados.

#### BOUNDARIES
May change: `docs/aceite/fase-12.md`, `tests/test_acceptance_doc_f12.py`
Do not touch: `scripts/`, `skills/`, `src/`, `aceite/`, `DECISIONS.md`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-12-robustez`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

## Checks

**Build**: `python tools/build.py --check`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v`

**C1** - `take` grava `refs/starcode/snapshots/<slug>/<ticket>` com rastreados e não rastreados não ignorados, pai = HEAD (R1)
Proof: run unit | test_take_grava_ref_com_rastreados_e_novos ... ok

**C2** - `take` deixa `.git/index`, árvore, HEAD e branches iguais byte a byte (R2)
Proof: run unit | test_take_nao_altera_indice_arvore_head ... ok

**C3** - um segundo `take` do mesmo ticket substitui o ref e imprime `(substituído <hash>)` (R3)
Proof: run unit | test_take_substitui_snapshot_existente ... ok

**C4** - slug ou ticket inválido sai com 2 e `nome inválido para o snapshot`, sem ref (R4)
Proof: run unit | test_take_nome_invalido_sai_2 ... ok

**C5** - fora do Git ou sem HEAD sai com 1 e `snapshot falhou:`, sem ref parcial (R5)
Proof: run unit | test_take_sem_head_ou_fora_do_git_sai_1 ... ok

**C6** - `list` em texto e JSON, e `nenhum snapshot de <slug>` / `[]` sem snapshots (R6)
Proof: run unit | test_list_texto_json_e_vazio ... ok

**C7** - `drop` apaga só os refs da feature e imprime `removidos <n> snapshots` (R13)
Proof: run unit | test_drop_remove_refs_da_feature ... ok

**C8** - `restore` sem `--yes` imprime o plano `voltar`/`remover` e não altera nenhum arquivo (R7)
Proof: run unit | test_restore_sem_yes_mostra_plano_e_nao_altera ... ok

**C9** - `restore --yes` volta e remove só caminhos do `May change`, com o bit executável (R8)
Proof: run unit | test_restore_yes_volta_e_remove_so_no_may_change ... ok

**C10** - caminhos fora do ticket aparecem em `fora do ticket (não tocados):`, no máximo 50 linhas + `e mais N` (R9)
Proof: run unit | test_restore_lista_fora_do_ticket_com_limite ... ok

**C11** - HEAD diferente do pai do snapshot sai com 1 e `HEAD mudou desde o snapshot`, sem alterar nada (R10)
Proof: run unit | test_restore_recusa_head_mudado ... ok

**C12** - sem snapshot, ticket fora do tasks.md ou `May change` vazio sai com 1, sem alterar nada (R11)
Proof: run unit | test_restore_sem_snapshot_ou_ticket_sem_may_change ... ok

**C13** - falha no meio lista restaurados, o que falhou e o que faltou, sai com 1, e o segundo `--yes` termina (R12)
Proof: run unit | test_restore_falha_parcial_e_retomada ... ok

**C14** - `--diff` inclui os não rastreados e os arquivos vêm de `git ls-files -co --exclude-standard` (R14)
Proof: run unit | test_select_diff_inclui_nao_rastreados ... ok

**C15** - arquivos de teste Python e TS/JS reconhecidos pelos padrões do R15 (R15)
Proof: run unit | test_identifica_testes_python_e_ts ... ok

**C16** - imports Python absolutos, relativos e com vários candidatos viram arestas; externos ficam fora (R16)
Proof: run unit | test_python_imports_absolutos_relativos_e_ambiguos ... ok

**C17** - imports TS/JS relativos resolvem caminho exato, extensões e `index.<ext>`; pacotes ficam fora (R17)
Proof: run unit | test_ts_imports_relativos_extensoes_e_index ... ok

**C18** - um teste mudado entra no próprio conjunto (R18)
Proof: run unit | test_teste_mudado_entra_no_conjunto ... ok

**C19** - dependentes transitivos entram com a cadeia mínima, e import circular não entra em loop (R19)
Proof: run unit | test_dependentes_transitivos_e_ciclo ... ok

**C20** - arquivo mudado fora do grafo ou apagado dá `rodar tudo: fora do grafo: <arquivos>` (R20)
Proof: run unit | test_fora_do_grafo_roda_tudo ... ok

**C21** - erro de sintaxe ou arquivo acima de 1 MiB dá `rodar tudo: grafo incompleto` (R21)
Proof: run unit | test_grafo_incompleto_roda_tudo ... ok

**C22** - `paths`/`baseUrl` no tsconfig ou import `@/` dá `rodar tudo: aliases do TypeScript não resolvidos` (R22)
Proof: run unit | test_aliases_ts_roda_tudo ... ok

**C23** - sem teste alcançável dá `rodar tudo: nenhum teste alcança`, nunca conjunto vazio (R23)
Proof: run unit | test_nenhum_teste_alcanca_roda_tudo ... ok

**C24** - sem mudança dá `rodar tudo: nenhuma mudança informada` (R24)
Proof: run unit | test_sem_mudanca_roda_tudo ... ok

**C25** - saída texto `selecionados <n> testes` com cadeias, ou `rodar tudo: <motivo>`, saindo com 0 (R25)
Proof: run unit | test_saida_texto_selecao_e_rodar_tudo ... ok

**C26** - JSON com `verdict`, `tests`, `chains`, `reason`, `changed`; no `run-all`, `tests` vazio e `reason` preenchido (R26)
Proof: run unit | test_saida_json_contrato ... ok

**C27** - Git falhando sai com 1 e `impact falhou:`; argumentos inválidos saem com 2 (R27)
Proof: run unit | test_erros_git_e_argumentos ... ok

**C28** - execute.md seção 7 manda rodar `snapshot.py take` antes de cada despacho no modo 1 e não despachar se ele falha (R28)
Proof: run unit | test_execute_md_snapshot_antes_do_ticket ... ok

**C29** - execute.md seção 6 descreve a saída (b) do modo 1: `restore` sem `--yes`, plano, sim do usuário, `--yes` e `--breaker closed` (R29)
Proof: run unit | test_execute_md_saida_b_restaura_snapshot ... ok

**C30** - execute.md manda rodar `snapshot.py drop <slug>` depois de `--phase done` no modo 1 (R30)
Proof: run unit | test_execute_md_drop_no_done ... ok

**C31** - a skill do McCoy roda `impact.py select --diff <base>` antes do gate e põe o veredito no relatório (R31)
Proof: run unit | test_mccoy_skill_raio_de_impacto ... ok

**C32** - `q-brief` preenche `{{regression}}` com a seleção ou `rodar tudo: <motivo>` (R32)
Proof: run unit | test_q_brief_bloco_regression ... ok

**C33** - com o impact falhando, o brief sai com `seleção indisponível: <motivo>; rode a suíte inteira` (R32)
Proof: run unit | test_q_brief_impact_indisponivel ... ok

**C34** - `q-verify.md` manda rodar a regressão em HEAD, registrar em `## Limits` e não cita caminhos do plugin (R33)
Proof: run unit | test_q_verify_regra_regression_autocontida ... ok

**C35** - `snapshot.py` e `impact.py` existem em `dist/<cli>/scripts/` nos 4 CLIs (R34)
Proof: run unit | test_build_leva_snapshot_e_impact ... ok

**C36** - o cenário do aceite restaura `src/`, remove o arquivo novo, mantém `notas.md` e não cria commit (R36)
Proof: run unit | test_cenario_aceite_disjuntor_modo_1 ... ok

**C37** - no StarCode, `gates_common.py` seleciona testes com cadeia de 3+ elos e `README.md` dá `rodar tudo: fora do grafo` (R37)
Proof: run unit | test_impact_no_repo_starcode ... ok

**C38** - na fixture `aceite/telas`, mudar `src/greeting.ts` seleciona `src/greeting.test.ts` (R37)
Proof: run unit | test_impact_fixture_telas ... ok

**C39** - DECISIONS F12-n sem duplicata, `[Unreleased]`, compatibilidade e plano atualizados (R35)
Proof: run unit | test_registros_fase_12 ... ok

**C40** - `docs/aceite/fase-12.md` registra o aceite com `**Resultado**: aprovado` e as evidências de R36 e R37 (R38)
Proof: run unit | test_acceptance_doc_f12 ... ok

## Handoff

**Phase:** done
**Size:** LARGE
**Git mode:** 3
**Next:** nenhum: feature mergeada (PR #34, 444702b)
**Linear:** SC-19 (mãe); SC-149..SC-156; doc https://linear.app/cifren/document/spec-fase-12-robustez-v16-92380a1ae716
**Integration branch:** feature/fase-12-robustez
**Last integrated:** 3fa4e7b
**Dispatched:** none
**Settled:** 2026-11-12: Revisão do R21: templates .py com {{ ficam fora do grafo (user: "A")
**Attempts:** none
**Reports:** 2026-11-12: T1..T8 integrados (cf3f216, 05853cb, d3a7532, 2369172, 9f59915, 89a8c05, b43488c, e2c211f); proofs verde 5fd4a31; 2026-11-12: Q (codex, ctx_4db7514a067c): FAIL - R21 exceção {{ vale também para TS/JS; asserções frouxas em C11, C12, C28-C31, C33; 2026-11-12: Handoff refeito pelo Git: o Q restaurou tasks.md e apagou o Handoff não commitado; 2026-11-12: fix pós-Q: 3fc0e53 (R21), 257e90d (C11/C12/C28-C31), 0cc7c0e (C33); suíte 715 ok; 2026-11-12: done verde em 73fe7ac; 2026-11-12: PR #34 aberto (https://github.com/freire-andre/starcode/pull/34), HEAD 98fe338; 2026-11-12: Worf rodada 1: COMMENT, W1-W4 should-fix, W5 nit; 2026-11-12: fix Worf r1: W1 f4565f0, W2 61db014, W3 a5abf15, W4 7fba116, W5 3fa4e7b; suíte 720 ok; 2026-11-12: Worf rodada 2: APPROVE, W1-W5 resolvidos; 2026-11-12: merge autorizado pelo usuário; PR #34 mergeado em 444702b; issues em Done
**Breaker:** closed
