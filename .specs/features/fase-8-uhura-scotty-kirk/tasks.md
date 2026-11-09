# Fase 8: Uhura, Scotty e Kirk (v1.2): Tasks

**Approved**: 2026-11-08 - user: "SIM"

**Spec**: `.specs/features/fase-8-uhura-scotty-kirk/spec.md`
**Status**: Approved
**Integration branch**: `feature/fase-8-uhura-scotty-kirk`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only, no generator change | `python -m unittest discover -s tests -v` |
| full | task that changes `skills/`, `scripts/`, `hooks/`, `src/`, `schemas/`, `evals/` or `tools/build.py` (F3-1: `dist/` regenerated in the same commit) | `python tools/build.py && python tools/build.py --check && python -m unittest discover -s tests -v` |
| slow | template task: real toolchain, real registry and Docker on the machine | `python -m unittest discover -s tests -v && python -m unittest discover -s tests_slow -v` |
| build | records task, or after the last code task | `python tools/build.py && python tools/build.py --check && claude plugin validate dist/claude --strict && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |

## Tasks

### T1: Leitura de versões estáveis nos registros (registry.py)
**Linear**: SC-88
**Depends on**: none
**Requirements**: R7, R8, R10, R11
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/registry.py` (só stdlib) com uma função `latest_stable(registry, package, *, series=None) -> str` e uma CLI `python registry.py <registry> <package> [--series S] [--json]`:
- `npm`: `https://registry.npmjs.org/<pkg>` → dist-tag `latest`; com `series`, a maior versão de `versions` dentro da série, sem pré-release.
- `pypi`: `https://pypi.org/pypi/<pkg>/json` → maior versão de `releases` sem pré-release (`a`, `b`, `rc`, `.dev`) e sem arquivo `yanked` em todos os arquivos.
- `crates`: `https://crates.io/api/v1/crates/<crate>` (com `User-Agent: starcode-registry`) → `max_stable_version`; com `series`, a maior de `versions[].num` não-yanked e sem pré-release.
- `dockerhub`: `https://hub.docker.com/v2/repositories/library/<image>/tags?page_size=100` → maior tag só numérica de major (`17`, `9`), ignorando `-rc`, `-alpine` etc.
- `series` é o major (`"3"`) para versões ≥ 1 ou major.minor (`"0.2"`) para 0.x; função `in_series(version, series)` exportada.
- Pré-release nunca é devolvida (`-alpha`, `-beta`, `-rc`, `a1`, `b2`, `rc1`, `.dev0`).
- Timeout de 15 s; erro HTTP, timeout, JSON inválido ou pacote inexistente levantam `RegistryError` com a mensagem `registro <nome> indisponível para <pacote>: <motivo>`; a CLI imprime essa mensagem e sai com 2.
- Com `STARCODE_REGISTRY_FIXTURE=<arquivo.json>` no ambiente, nenhuma rede: as respostas vêm do arquivo (formato em Data & Contracts da spec) e `source()` devolve `fixture` (senão `registry`).

Testes em `tests/test_registry.py` com fixtures em `tests/fixtures/registry/` (nunca rede). Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R7, R8, R10, R11; fixture em Data & Contracts). Checks: C7, C8, C10, C11.
Os scripts do repo são stdlib puro e testados com `unittest` (veja `tests/test_dispatch.py` e `tests/helpers.py`). Fato de 2026-11-08: `npm view @tauri-apps/cli dist-tags` → `latest 2.12.4`, `next 3.0.0-alpha.6`; `cargo info tauri` mostra `3.0.0-alpha.6`, por isso `max_stable_version`.

#### BOUNDARIES
May change: `scripts/registry.py`, `tests/test_registry.py`, `tests/fixtures/registry/`, `dist/`
Do not touch: `scripts/scaffold.py`, `scripts/ephemeral_db.py`, `profiles/`, `skills/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T2: Banco efêmero local em Docker (ephemeral_db.py)
**Linear**: SC-89
**Depends on**: T1
**Requirements**: R20, R21, R22, R23, R24, R25
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/ephemeral_db.py` (só stdlib, autossuficiente: será copiado para os projetos gerados) com:
- `run <postgresql|mysql> [--image IMG] [--reuse-env] -- <comando...>`: imagem de `--image` ou de `.starcode/stack.json` (`image.<engine>`) na pasta atual; container `starcode-eph-<engine>-<8 hex>`; `-p 127.0.0.1:<porta livre>:<porta do banco>`; usuário, senha e banco fictícios gerados na hora (`secrets.token_hex`); espera pronto até 60 s (`pg_isready` / `mysqladmin ping` via `docker exec`); roda o comando com `DATABASE_URL` (`postgresql+psycopg://...` ou `mysql+pymysql://...` em `127.0.0.1`); `docker rm -f -v` no `finally` (também em erro e Ctrl+C); exit = o do comando.
- Docker ausente ou daemon parado (`docker info` falha) → exit 3 e `gate de integração não executado: Docker indisponível (<motivo>)`, sem rodar o comando.
- Não pronto em 60 s → remove o container, exit 4, `banco efêmero não ficou pronto em 60 s`. Porta ocupada no `docker run` → até 3 tentativas com outra porta; depois exit 4.
- Sem `--reuse-env`, o `DATABASE_URL` do ambiente é sempre substituído; com `--reuse-env`, um `DATABASE_URL` que não aponte para `127.0.0.1`/`localhost` é recusado com exit 2.
- `list [--json]`: containers `starcode-eph-*` (nome, idade em minutos); `down <nome>`: remove um (recusa nome fora do prefixo, exit 2).
- Nomes e portas únicos por execução (duas execuções simultâneas não colidem).

Testes em `tests/test_ephemeral_db.py` com um `docker` falso (script Python num PATH temporário que registra as chamadas e simula `info`, `run`, `exec`, `rm`, `ps`), nunca o Docker real. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R20–R25, exit codes em Data & Contracts). Checks: C20–C25.
A máquina de aceite tem Docker 29.7.2; o teste real com Docker fica na T10 (`tests_slow`). Windows: localize o executável com `shutil.which("docker")`; o docker falso precisa de um `docker.cmd`/`docker.bat` que chame o Python no Windows.

#### BOUNDARIES
May change: `scripts/ephemeral_db.py`, `tests/test_ephemeral_db.py`, `dist/`
Do not touch: `scripts/registry.py`, `scripts/scaffold.py`, `profiles/`, `skills/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T3: Scaffold: versions, new, checks, gates e série testada (scaffold.py)
**Linear**: SC-90
**Depends on**: T2
**Requirements**: R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R40, R41, R45
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/scaffold.py` (usa `registry.py` e `tools/miniyaml.py` ou um leitor equivalente já presente em `scripts/`) com:
- Pasta de perfis: `<script>/../profiles` (funciona no repo e em `dist/<cli>/`); `STARCODE_PROFILES_DIR` substitui (testes).
- `list`: perfis e combinações válidas (`combinesWith`).
- `versions <app>[+<db>] [--json]`: versão estável de cada dependência (R7); série `tested` de cada dependência principal: fora dela → marca `fora da série testada (<série>)` com a mais nova da série ao lado; grupo `alignMajor` do perfil (ex.: `{from: "@tauri-apps/cli", deps: [tauri, tauri-build, "@tauri-apps/api"]}`) usa o major do `from` para os outros; sem estável nesse major → exit 2 e `<from>: crate sem versão estável no major <N>` (para o tauri: `tauri: crate sem versão estável no major <N>`).
- `new <pasta> --profile <app> [--db <db>] [--name N] [--description "<frase>"] [--pin-tested | --allow-new-series]`:
  - valida nome `^[a-z][a-z0-9-]{0,62}$` (exit 2, `nome inválido: use minúsculas, dígitos e hífen, começando por letra`), descrição (uma linha, ≤200; exit 2, `descrição inválida: uma linha, até 200 caracteres`; padrão `Projeto <nome>.`), pasta (não vazia → exit 2, `pasta não vazia: <caminho>`), perfil/combinação (exit 2 com a lista válida);
  - resolve todas as versões **antes** de escrever qualquer arquivo (registro indisponível → exit 2, nada escrito);
  - série fora da testada sem flag → exit 5 e `<pacote> <versão> fora da série testada <série>: use --pin-tested ou --allow-new-series`; `--pin-tested` usa a maior da série; `--allow-new-series` usa a nova e grava `"outsideTested": true`;
  - copia `template/` do app e do banco, troca `{{name}}`, `{{module}}` (nome com `_`), `{{description}}`, `{{version:<pacote>}}`; aplica `inject` do perfil de banco (linhas inseridas no marcador declarado num arquivo do app); com perfil `db`, copia `scripts/ephemeral_db.py` para `<pasta>/scripts/ephemeral_db.py`;
  - grava `.starcode/stack.json` (formato da spec; `source` = `registry` ou `fixture`; `image.<engine>` com `<imagem>:<major>`);
  - falha depois de criar a pasta → remove o que foi criado nesta execução (pasta vazia pré-existente volta vazia), exit 1;
  - imprime o relatório (`<pacote> <versão> (<registro>, <data>)`, `template: ...`, `pasta: ...`).
- `checks <pasta> [--json]`: linhas `**Build**:`, `**Run unit**:` e, com banco, `**Run integration**:` a partir do `stack.json` e dos `gates` dos perfis; sem `stack.json` → exit 1, `perfil não registrado: rode o Scotty`.
- `gates <pasta> [--json] [--timeout-min 30]`: roda `install` e cada gate em ordem (`cwd` do gate quando o perfil declara, ex.: `src-tauri`), imprime `PASS <cmd>` / `FAIL <cmd>` (`FAIL <cmd>: timeout 30 min` no estouro) / `SKIP <cmd>: <ferramenta> ausente` (ferramenta de `tools` fora do PATH); exit 0 sem FAIL nem SKIP, 1 com FAIL, 3 com SKIP sem FAIL. Exit 3 do `ephemeral_db.py` vira `SKIP <cmd>: Docker indisponível`.

Testes em `tests/test_scaffold.py` com perfis falsos em `tests/fixtures/profiles/` (comandos de gate em Python, sem uv/npm/cargo) e o registro por fixture. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R9–R19, R40, R41, R45; contratos de `profile.yaml`, `stack.json` e relatório em Data & Contracts). Checks: C9–C19, C40, C41, C45.
`tools/miniyaml.py` é o parser YAML do repo (subconjunto, sem âncoras); os scripts em `dist/` não enxergam `tools/`, então leia como `scripts/dispatch.py` resolve imports e, se preciso, copie o mínimo para `scripts/` (sem duplicar lógica além do necessário). Os perfis reais chegam nas T9–T12; esta tarefa só usa perfis falsos.

#### BOUNDARIES
May change: `scripts/scaffold.py`, `scripts/registry.py`, `tests/test_scaffold.py`, `tests/fixtures/profiles/`, `dist/`
Do not touch: `scripts/ephemeral_db.py`, `profiles/`, `skills/`, `tools/build.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T4: Cache do Context7 em .specs/stack (stack_cache.py)
**Linear**: SC-91
**Depends on**: T3
**Requirements**: R26, R27
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/stack_cache.py` (stdlib):
- `write <repo> <lib> --id <context7-id> --project-version <v> --doc-version <v|desconhecida> --summary-file <arq> [--verified context7|"não verificada (<url>)"] [--date AAAA-MM-DD]`: grava `.specs/stack/<lib>.md` no formato da spec, substituindo a entrada da mesma lib (nome do arquivo normalizado: `@tauri-apps/api` → `tauri-apps-api.md`); resumo com no máximo 30 linhas (corta e avisa).
- `check <repo> [--json] [--today AAAA-MM-DD]`: para cada entrada, `ok`, `velha` (> 30 dias), `versão mudou` (versão no `.starcode/stack.json` ou no manifesto ≠ `Project version`) ou `outra versão` (`Doc version` ≠ `Project version` no major.minor; `desconhecida` conta como `outra versão`); exit 0 com todas `ok`, 1 caso contrário, 2 em erro de uso.

Testes em `tests/test_stack_cache.py`. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R26, R27; formato de `.specs/stack/<lib>.md` em Data & Contracts). Checks: C26, C27.
As versões do projeto vêm de `.starcode/stack.json` (T3) e, sem ele, de `pyproject.toml`/`package.json`/`Cargo.toml`.

#### BOUNDARIES
May change: `scripts/stack_cache.py`, `tests/test_stack_cache.py`, `dist/`
Do not touch: `scripts/scaffold.py`, `scripts/registry.py`, `profiles/`, `skills/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T5: Skill da Uhura e textos de PR e Linear
**Linear**: SC-92
**Depends on**: T4
**Requirements**: R28, R29, R30
**Tests**: unit
**Gate**: full

#### TASK
- `skills/uhura/SKILL.md` (EN, saída PT-BR, persona só no chat, cabeçalho como as outras skills): protocolo do Context7 (bootstrap só das dependências `main` do perfil; sob demanda antes de afirmar comportamento de lib; atualização quando `stack_cache.py check` não dá `ok`; sem Context7 → doc oficial e `--verified "não verificada (<url>)"`); versões nunca do Context7; grava sempre via `stack_cache.py write`; redige o corpo do PR e os comentários do Linear a partir dos templates.
- `skills/uhura/references/pr-body.md`: seções Resumo, Issue, Mudanças, Gates (com resultado), Verificação do Q, Riscos; neutro, PT-BR.
- `skills/uhura/references/linear-comments.md`: modelos de início, integrado, bloqueado, cancelado e concluído.
- `skills/engajar/references/execute.md`: onde o Picard abre o PR e comenta no Linear, mandar redigir pela Uhura (no Claude, subagente com o modelo da Uhura; nos outros CLIs, a própria sessão segue a skill); o Picard continua confirmando e executando `gh pr create` e `orca linear comment`.
- `src/context/STARCODE.md`: a seção do Context7 aponta para a skill `uhura`.

Testes em `tests/test_uhura_skill.py` (texto das skills fonte e de `dist/<cli>/`). Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R28–R30). Checks: C28, C29, C30.
`src/crew.yaml` já declara `uhura` (skill `uhura`, `subagent: true`, Haiku 5.5). Veja `skills/troi/SKILL.md` e `skills/spock/SKILL.md` para o formato (frontmatter `name`/`description`, `<plugin-root>`, linha do cabeçalho por hook) e `tests/test_data_skill.py` para testes de texto de skill.

#### BOUNDARIES
May change: `skills/uhura/`, `skills/engajar/references/execute.md`, `src/context/STARCODE.md`, `tests/test_uhura_skill.py`, `dist/`, `tests/test_build.py`, `tests/test_crew_hook.py`, `tests/test_ephemeral_db.py`, `tests/test_registry.py` (ampliado pelo Picard em 2026-11-08: testes que assumiam Uhura ausente e encoding)
Do not touch: `skills/scotty/`, `skills/nova-missao/`, `skills/data/`, `scripts/`, `profiles/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T6: Skill do Scotty, detecção de perfil e gates do Data a partir do perfil
**Linear**: SC-93
**Depends on**: T5
**Requirements**: R24, R31, R32
**Tests**: unit
**Gate**: full

#### TASK
- `scripts/scaffold.py`: subcomando `detect <repo> [--json]` (manifestos → perfis, como R31) e `record <repo> --profiles a[,b] [--yes]` que grava `.starcode/stack.json` com versões lidas do manifesto/lockfile (`source: manifest`), sem copiar template; sem `--yes` só mostra o que gravaria.
- `skills/scotty/SKILL.md`: aplicar perfil em repo existente (detect → mostrar → confirmar → record); scaffold em pasta vazia (`scaffold.py new`); listar órfãos `starcode-eph-*` com mais de 60 min (`ephemeral_db.py list`) e remover só com confirmação (`down`); deploy fora (Non-Goal); Context7 pela Uhura.
- `skills/data/SKILL.md` e `skills/data/references/tasks-template.md`: com `.starcode/stack.json` no repo, `**Build**`/`**Run <nome>**` vêm de `scaffold.py checks`; sem ele, como hoje.

Testes em `tests/test_scaffold_detect.py` e `tests/test_scotty_skill.py`. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R24, R31, R32). Checks: C24 (parte do Scotty), C31, C32.
`scripts/scaffold.py` vem da T3; `ephemeral_db.py list/down` da T2. `src/crew.yaml` já declara `scotty` (Sonnet 5.5, subagente).

#### BOUNDARIES
May change: `scripts/scaffold.py`, `skills/scotty/`, `skills/data/SKILL.md`, `skills/data/references/tasks-template.md`, `tests/test_scaffold_detect.py`, `tests/test_scotty_skill.py`, `dist/`, `tests/test_build.py`, `tests/test_crew_live.py`, `tests/test_skills_cli.py` (só se um teste antigo assumir que a skill nova não existe; ampliado pelo Picard em 2026-11-08)
Do not touch: `skills/uhura/`, `skills/nova-missao/`, `scripts/ephemeral_db.py`, `profiles/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T7: Skill nova-missao (Kirk) e evals de roteamento
**Linear**: SC-94
**Depends on**: T6
**Requirements**: R33, R34, R35, R43, R44
**Tests**: unit
**Gate**: full

#### TASK
- `skills/nova-missao/SKILL.md` (invocação só do usuário): uma mensagem com nome, pasta-mãe, perfil de app, banco opcional e uma frase do projeto (cada um com recomendação; `gpui` com o aviso `experimental: API 0.x muda entre versões`); depois, em ordem: `scaffold.py versions`; série fora da testada → resumo do Context7 da versão nova + escolha (a) `--pin-tested` (recomendado) / (b) `--allow-new-series`; criar a pasta vazia e a Uhura grava o cache das dependências `main` antes de gerar o projeto (sem Context7: aviso em uma linha, `não verificada`, segue); `scaffold.py new --description`; `scaffold.py gates`; com FAIL: mostra o gate e as últimas 20 linhas, sem commit, oferece McCoy / manter / remover (com confirmação); sem FAIL: `git init` + commit `chore: projeto inicial (<perfis>)`; relatório; oferta numa só mensagem de `/starcode:setup` e de engajar a primeira missão, sem rodar nenhum; nunca remoto, push ou deploy.
- `evals/routing/`: casos para `uhura`, `scotty` e `nova-missao` (frases que devem e não devem rotear), no formato dos existentes.

Testes em `tests/test_nova_missao_skill.py`. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R33–R35, R43, R44; estados do Kirk em States). Checks: C33, C34, C35, C43, C44.
`src/crew.yaml` declara `kirk` com skill `nova-missao`, `invocation: user`, sem subagente. Veja `evals/README.md` e os casos em `evals/routing/`; graders `tool_used` com max 0 precisam de `min: 0` (lição da Fase 1).

#### BOUNDARIES
May change: `skills/nova-missao/`, `evals/routing/`, `tests/test_nova_missao_skill.py`, `dist/`, `tests/test_build.py`, `tests/test_crew_live.py`, `tests/test_skills_cli.py` (só se um teste antigo assumir que a skill nova não existe; ampliado pelo Picard em 2026-11-08)
Do not touch: `skills/uhura/`, `skills/scotty/`, `scripts/`, `profiles/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T8: Perfil python-flask
**Linear**: SC-95
**Depends on**: T3
**Requirements**: R1, R2, R3, R4, R6, R39, R42, R45
**Tests**: integration
**Gate**: slow

#### TASK
Criar `profiles/python-flask/profile.yaml` e `profiles/python-flask/template/`:
- gates exatos de R2 (`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, `uv run pytest -v`), `tools: [uv]`, `install: ["uv sync"]`, `combinesWith: [postgresql, mysql]`;
- deps `main` (flask, pytest) e dev (ruff, mypy) com `tested` e `docs` (Context7 ID + data da consulta que você fizer agora para a versão resolvida);
- template: `pyproject.toml` com `{{version:...}}` e o marcador de injeção para o banco, `src/{{module}}/` com app factory, blueprint `GET /health` → 200 `{"status": "ok"}`, config por ambiente, `tests/` com o teste do cliente Flask; testes de integração (marcador `integration`) não rodam no gate unit; `README.md` (`# {{name}}`, `{{description}}`, `## Gates`), `.gitignore`, `.github/workflows/ci.yml` rodando os gates;
- nenhum número de versão de dependência escrito no template.

Antes de escrever código de Flask, consulte o Context7 da versão resolvida pelo registro (protocolo do `STARCODE.md`).

Testes: `tests/test_profile_python_flask.py` (renderiza com fixture do registro em pasta temporária: arquivos esperados, sem versões no template, marcadores trocados) e `tests_slow/test_slow_python_flask.py` (`scaffold.py new` com registro real em pasta temporária + `scaffold.py gates` → todos PASS).

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R1–R4, R6, R39, R42, R45; `profile.yaml` em Data & Contracts). Checks: C4.
`scripts/scaffold.py` (T3) faz a renderização e os gates; use `STARCODE_PROFILES_DIR` só nos testes rápidos se precisar. Máquina: uv 0.9.3, Python 3.14.8. Os testes globais de perfis (R1, R2, R3, R6, R39, R42) ficam na T12.

#### BOUNDARIES
May change: `profiles/python-flask/`, `tests/test_profile_python_flask.py`, `tests_slow/test_slow_python_flask.py`
Do not touch: `profiles/postgresql/`, `profiles/mysql/`, `profiles/rust/`, `profiles/gpui/`, `profiles/typescript/`, `profiles/tauri/`, `scripts/`, `skills/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T9: Perfis postgresql e mysql
**Linear**: SC-96
**Depends on**: T8
**Requirements**: R5, R20
**Tests**: integration
**Gate**: slow

#### TASK
Criar `profiles/postgresql/` e `profiles/mysql/` (`kind: db`):
- `image: {name: postgres|mysql, registry: dockerhub}`, `gates.integration` exato de R2 (`python scripts/ephemeral_db.py run <engine> -- uv run pytest -v -m integration`), `tools: [uv, docker]`;
- deps `main` (sqlalchemy, alembic, `psycopg[binary]` ou `pymysql`) com `tested` e `docs`, injetadas no `pyproject.toml` do flask pelo `inject`;
- template: `alembic.ini`, `migrations/` com a migração inicial reversível (tabela fictícia), `src/{{module}}/db.py` lendo `DATABASE_URL`, `tests/integration/` com o teste que roda `upgrade head`, grava e lê uma linha fictícia e roda `downgrade base`; CI do flask com o passo do banco efêmero.

Consulte o Context7 de SQLAlchemy e Alembic nas versões resolvidas antes de escrever o código.

Testes: `tests/test_profile_db.py` (renderização com fixture) e `tests_slow/test_slow_db.py` (flask+postgresql e flask+mysql com registro real e Docker real: `scaffold.py gates` todo PASS e nenhum `starcode-eph-*` restante em `docker ps -a`).

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R5, R20; `stack.json` e `image` em Data & Contracts). Checks: C5, C50, C20 (Docker real).
`ephemeral_db.py` (T2) é copiado pelo `scaffold.py new` (T3) quando há perfil de banco. Docker 29.7.2 com daemon ativo na máquina.

#### BOUNDARIES
May change: `profiles/postgresql/`, `profiles/mysql/`, `tests/test_profile_db.py`, `tests_slow/test_slow_db.py`
Do not touch: `profiles/python-flask/`, `profiles/rust/`, `profiles/gpui/`, `profiles/typescript/`, `profiles/tauri/`, `scripts/`, `skills/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T10: Perfis rust e gpui
**Linear**: SC-97
**Depends on**: T3
**Requirements**: R4
**Tests**: integration
**Gate**: slow

#### TASK
- `profiles/rust/`: lib + binário com um teste de unidade; gates exatos de R2; `tools: [cargo]`; `Cargo.toml` com `{{name}}`; `README.md`, `.gitignore`, CI.
- `profiles/gpui/` (`experimental: true`, `combinesWith: []`): binário que abre uma janela com uma view de contador e teste de unidade da lógica do contador (sem abrir janela); gates `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`, `cargo build`; dep `gpui` com `tested: "0.2"` e `docs`; `README.md`, `.gitignore`, CI.

Consulte o Context7 do GPUI na versão resolvida (ex.: `/websites/rs_gpui`) antes de escrever o código. Se o `cargo build` do GPUI falhar no Windows por pré-requisito do sistema (SDK, toolchain), não contorne: relate o erro exato nas pendências.

Testes: `tests/test_profile_rust_gpui.py` (renderização com fixture) e `tests_slow/test_slow_rust_gpui.py` (registro real + `scaffold.py gates` todo PASS nos dois perfis).

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R2, R4; edge case "GPUI 0.x"). Checks: C46, C47.
cargo/rustc 1.99.1 na máquina; `gpui` 0.2.2 é a estável no crates.io em 2026-11-08 (existe também o crate `gpui-pre`, que não é usado).

#### BOUNDARIES
May change: `profiles/rust/`, `profiles/gpui/`, `tests/test_profile_rust_gpui.py`, `tests_slow/test_slow_rust_gpui.py`
Do not touch: `profiles/python-flask/`, `profiles/postgresql/`, `profiles/mysql/`, `profiles/typescript/`, `profiles/tauri/`, `scripts/`, `skills/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T11: Perfis typescript e tauri
**Linear**: SC-98
**Depends on**: T3
**Requirements**: R4, R9
**Tests**: integration
**Gate**: slow

#### TASK
- `profiles/typescript/`: lib com um teste do vitest; gates exatos de R2 (`npx tsc --noEmit`, `npx biome check .`, `npx vitest run`); `tools: [node, npm]`; `install: ["npm install"]`; `package.json` e `tsconfig.json` com `{{version:...}}`; `README.md`, `.gitignore`, CI.
- `profiles/tauri/`: frontend vanilla TS + Vite com um teste do vitest; `src-tauri/` com o comando `greet` e teste Rust; gates: os 3 do typescript, os 3 do rust com `cwd: src-tauri`, e `npm run tauri build -- --debug --no-bundle`; `alignMajor` com `from: "@tauri-apps/cli"` e `deps: [tauri, tauri-build, "@tauri-apps/api"]`; ícones mínimos exigidos pelo `tauri-build`; `README.md`, `.gitignore`, CI.

Consulte o Context7 do Tauri v2 (`/tauri-apps/tauri-docs`) e do Vite/vitest nas versões resolvidas antes de escrever o código.

Testes: `tests/test_profile_ts_tauri.py` (renderização com fixture, incluindo o alinhamento de major) e `tests_slow/test_slow_ts_tauri.py` (registro real + `scaffold.py gates` todo PASS nos dois perfis).

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R2, R4, R9; Sources: `tauri build --debug --no-bundle`). Checks: C48, C49.
Node 24.22.1 e npm 12.2.0 na máquina; `@tauri-apps/cli` `latest` 2.12.4 e crate `tauri` com 3.0.0-alpha.6 como última versão em 2026-11-08.

#### BOUNDARIES
May change: `profiles/typescript/`, `profiles/tauri/`, `tests/test_profile_ts_tauri.py`, `tests_slow/test_slow_ts_tauri.py`
Do not touch: `profiles/python-flask/`, `profiles/postgresql/`, `profiles/mysql/`, `profiles/rust/`, `profiles/gpui/`, `scripts/`, `skills/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T12: Perfis no build dos 4 CLIs, testes globais dos perfis e registros
**Linear**: SC-99
**Depends on**: T7, T9, T10, T11
**Requirements**: R1, R2, R3, R6, R36, R38, R39, R42
**Tests**: unit
**Gate**: build

#### TASK
- `tools/build.py`: copiar `profiles/` para `dist/<cli>/profiles/` nos 4 CLIs; `--check` acusa perfil desatualizado; confirmar que `uhura`, `scotty` e `nova-missao` saem nos 4 CLIs.
- `tests/test_profiles.py`: os 7 perfis existem com os campos obrigatórios (R1), gates exatos de R2, nenhum número de versão nos templates (R3), apps com CI e `.gitignore` (R6), dependências `main` com `tested` (R39) e `docs` com ID e data (R42).
- `tests/test_build.py`: perfis e as 3 skills nos 4 CLIs.
- `DECISIONS.md`: decisões F8-n (templates fixos + script, versões pelas APIs dos registros, série testada e Context7 antes do scaffold, `.starcode/stack.json`, banco efêmero só Docker, biome, GPUI experimental, Kirk sem grill-me e sem remoto); `CHANGELOG.md`: `## [1.2.0] - não lançada`; `docs/compatibilidade.md`: linha dos perfis e ferramentas por CLI.
- `tests/test_release_docs_f8.py`: as F8-n e a seção do CHANGELOG existem.

Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R1–R3, R6, R36, R38, R39, R42). Checks: C1, C2, C3, C6, C36, C38, C39, C42.
`tools/build.py` hoje gera skills, hooks, scripts, crew.json e capabilities por CLI; `scripts/check_decisions.py` é o gate da CI para o `DECISIONS.md` (D30).

#### BOUNDARIES
May change: `tools/build.py`, `tests/test_build.py`, `tests/test_profiles.py`, `tests/test_release_docs_f8.py`, `DECISIONS.md`, `CHANGELOG.md`, `docs/compatibilidade.md`, `dist/`, `evals/README.md` (ampliado pelo Picard em 2026-11-08: o T7 editou só a cópia gerada), `profiles/tauri/profile.yaml`, `profiles/typescript/profile.yaml` (só o campo `docs` das deps main; ampliado pelo Picard em 2026-11-08)
Do not touch: `profiles/`, `scripts/`, `skills/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T13: Aceite real da nova-missao em F:\Projetos\starcode-missoes
**Linear**: SC-100
**Depends on**: T12
**Requirements**: R37
**Tests**: unit
**Gate**: build

#### TASK
Com o StarCode deste ramo de integração (scripts de `dist/claude`), executar em `F:/Projetos/starcode-missoes/` (fora do repo do StarCode; crie a pasta se não existir):
1. `nova-missao` com `python-flask` + `postgresql` (registro real, Context7 real);
2. `nova-missao` com `tauri`;
3. `scaffold.py new` + `gates` para `rust`, `typescript`, `gpui` e `python-flask` + `mysql`;
4. um caso de série fora da testada com a fixture do registro: `new` sai com 5 e segue com `--pin-tested`;
5. `docker ps -a` sem nenhum `starcode-eph-*` no fim.

Não rode `/starcode:setup` nem crie nada no Linear ou no GitHub para esses projetos. Registre cada cenário em `docs/aceite/fase-8.md` com `**Resultado**: aprovado` ou `reprovado`, as versões com fonte e data, as entradas do cache e as linhas PASS/FAIL. Achados que pedem código viram pendência, não correção aqui.

Testes: `tests/test_acceptance_doc_f8.py` com `test_fase8_acceptance_all_scenarios_approved` (5 seções com `**Resultado**: aprovado` e versões preenchidas).

#### CONTEXT
Spec: `.specs/features/fase-8-uhura-scotty-kirk/spec.md` (R37). Checks: C37.
Aceites anteriores: `docs/aceite/fase-7.md` (formato). O time PROJ do sandbox não é usado nesta fase.

#### BOUNDARIES
May change: `docs/aceite/fase-8.md`, `tests/test_acceptance_doc_f8.py`, `scripts/scaffold.py`, `tests/test_scaffold.py`, `profiles/tauri/template/biome.json`, `profiles/typescript/template/biome.json`, `tests/test_profile_ts_tauri.py`, `dist/` (ampliado pelo Picard em 2026-11-08: correção dos achados 1 e 2 do aceite; `DECISIONS.md` para registrar a correção)
Do not touch: `scripts/`, `skills/`, `profiles/`, `dist/`

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
**Run slow**: `python -m unittest discover -s tests_slow -v 2>&1`

**C1** - Os 7 perfis existem com `name`, `kind`, `tools`, `gates`, `deps` e `combinesWith` (apps) (R1)
Proof: run unit | test_profiles_all_seven_with_required_fields ... ok

**C2** - Os gates de cada perfil são exatamente os comandos de R2 (R2)
Proof: run unit | test_profiles_gate_commands_exact ... ok

**C3** - Nenhum template contém número de versão de dependência; só marcadores `{{version:...}}` (R3)
Proof: run unit | test_templates_have_no_hardcoded_versions ... ok

**C4** - Projeto python-flask gerado com registro real passa em todos os gates na primeira execução (R4)
Proof: run slow | test_flask_template_gates_pass ... ok

**C5** - Projeto python-flask + postgresql passa no teste de integração com upgrade/downgrade no banco efêmero (R5)
Proof: run slow | test_flask_postgresql_gates_pass ... ok

**C6** - Templates de app têm `.github/workflows/ci.yml` com os gates e `.gitignore` (R6)
Proof: run unit | test_app_templates_have_ci_and_gitignore ... ok

**C7** - `latest_stable` devolve a maior estável em npm, PyPI, crates.io e Docker Hub (R7)
Proof: run unit | test_registry_stable_latest_per_registry ... ok

**C8** - Pré-releases (`-alpha`, `rc1`, `.dev0`, `18-rc`) nunca são devolvidas (R8)
Proof: run unit | test_registry_rejects_prereleases ... ok

**C9** - Grupo `alignMajor` usa o major do `@tauri-apps/cli` e para sem estável nesse major (R9)
Proof: run unit | test_scaffold_aligns_major_group ... ok

**C10** - Registro indisponível sai com 2 e a mensagem de R10, sem nenhum arquivo escrito (R10)
Proof: run unit | test_scaffold_registry_error_writes_nothing ... ok

**C11** - Com `STARCODE_REGISTRY_FIXTURE`, nenhuma rede e `source: fixture` no `stack.json` (R11)
Proof: run unit | test_registry_fixture_marks_source ... ok

**C12** - `new` renderiza os marcadores e grava `.starcode/stack.json` com versões, fonte e data (R12)
Proof: run unit | test_scaffold_new_renders_and_writes_stack_json ... ok

**C13** - Nome inválido sai com 2 e a mensagem de R13 (R13)
Proof: run unit | test_scaffold_rejects_invalid_name ... ok

**C14** - Pasta não vazia sai com 2 e `pasta não vazia: <caminho>`, nada escrito (R14)
Proof: run unit | test_scaffold_rejects_non_empty_dir ... ok

**C15** - Perfil ou combinação inexistente sai com 2 e a lista válida (R15)
Proof: run unit | test_scaffold_rejects_unknown_combo ... ok

**C16** - Falha no meio da geração remove o que foi criado e sai com 1 (R16)
Proof: run unit | test_scaffold_cleans_up_on_failure ... ok

**C17** - `checks` imprime `**Build**`, `**Run unit**` e, com banco, `**Run integration**`; sem `stack.json` sai com 1 (R17)
Proof: run unit | test_scaffold_checks_lines ... ok

**C18** - `gates` imprime `PASS`/`FAIL` por comando e sai com 0 só sem FAIL (R18)
Proof: run unit | test_scaffold_gates_pass_fail_lines ... ok

**C19** - Ferramenta ausente vira `SKIP <cmd>: <ferramenta> ausente` e exit 3 (R19)
Proof: run unit | test_scaffold_gates_skip_missing_tool ... ok

**C20** - `run` sobe em 127.0.0.1 com porta livre, passa `DATABASE_URL`, devolve o exit do comando e remove o container também em falha (R20)
Proof: run unit | test_ephemeral_run_lifecycle_with_fake_docker ... ok

**C21** - Docker indisponível sai com 3 sem rodar o comando (R21)
Proof: run unit | test_ephemeral_docker_unavailable_exit_3 ... ok

**C22** - Banco não pronto em 60 s remove o container e sai com 4 (R22)
Proof: run unit | test_ephemeral_not_ready_exit_4 ... ok

**C23** - Com `--reuse-env`, `DATABASE_URL` remota é recusada com 2; sem ela, é substituída (R23)
Proof: run unit | test_ephemeral_reuse_env_rejects_remote_url ... ok

**C24** - `list` mostra os `starcode-eph-*` com idade e `down` remove só nomes do prefixo (R24)
Proof: run unit | test_ephemeral_list_and_down ... ok

**C25** - Duas execuções simultâneas usam nomes e portas diferentes (R25)
Proof: run unit | test_ephemeral_unique_names_and_ports ... ok

**C26** - `stack_cache.py write` substitui a entrada da mesma lib, sem duplicar (R26)
Proof: run unit | test_stack_cache_write_replaces_entry ... ok

**C27** - `check` classifica `ok`, `velha`, `versão mudou` e `outra versão` e sai com 1 se alguma não for `ok`; `Doc version` desconhecida recém-gravada sai `ok (doc sem versão)` com exit 0, e velha com mais de 30 dias (R27, emenda de 2026-11-09)
Proof: run unit | test_stack_cache_check_states ... ok

**C28** - A skill `uhura` traz o protocolo do Context7 (bootstrap só `main`, sob demanda, atualização, `não verificada`) nos 4 CLIs (R28)
Proof: run unit | test_uhura_skill_context7_protocol ... ok

**C29** - `pr-body.md` tem as 6 seções e `linear-comments.md` os 5 modelos (R29)
Proof: run unit | test_uhura_pr_and_comment_templates ... ok

**C30** - `execute.md` manda redigir PR e comentários pela Uhura e mantém o Picard confirmando e executando (R30)
Proof: run unit | test_execute_uses_uhura_for_pr_and_comments ... ok

**C31** - `detect` reconhece os perfis pelos manifestos e `record` grava `stack.json` com `source: manifest` só com `--yes` (R31)
Proof: run unit | test_scaffold_detect_and_record_profiles ... ok

**C32** - A skill do Data usa `scaffold.py checks` quando há `.starcode/stack.json` (R32)
Proof: run unit | test_data_skill_uses_stack_checks ... ok

**C33** - A skill `nova-missao` segue a ordem perguntas → versões → Context7 → new → gates → commit (R33)
Proof: run unit | test_nova_missao_skill_order ... ok

**C34** - Com gate vermelho, a `nova-missao` não faz commit e oferece McCoy, manter ou remover (R34)
Proof: run unit | test_nova_missao_gates_fail_no_commit ... ok

**C35** - A `nova-missao` oferece setup e primeira missão sem rodar nenhum, e nunca remoto/push/deploy (R35)
Proof: run unit | test_nova_missao_offers_setup_and_first_mission ... ok

**C36** - O build copia `profiles/` e gera `uhura`, `scotty` e `nova-missao` nos 4 CLIs (R36)
Proof: run unit | test_build_copies_profiles_and_new_skills ... ok

**C37** - `docs/aceite/fase-8.md` tem os 5 cenários aprovados com versões e fonte (R37)
Proof: run unit | test_fase8_acceptance_all_scenarios_approved ... ok

**C38** - `DECISIONS.md` tem as F8-n e o CHANGELOG a seção `## [1.2.0] - não lançada` (R38)
Proof: run unit | test_decisions_f8_and_changelog_1_2_0 ... ok

**C39** - Toda dependência `main` dos perfis declara `tested` (R39)
Proof: run unit | test_profiles_main_deps_have_tested_series ... ok

**C40** - Versão fora da série testada: `versions` marca e `new` sai com 5, sem escrever nada (R40)
Proof: run unit | test_scaffold_outside_tested_series_exits_5 ... ok

**C41** - `--pin-tested` usa a maior da série; `--allow-new-series` usa a nova e grava `outsideTested` (R41)
Proof: run unit | test_scaffold_pin_tested_and_allow_new_series ... ok

**C42** - Toda dependência `main` dos perfis declara `docs` com Context7 ID e data (R42)
Proof: run unit | test_profiles_main_deps_have_docs_id ... ok

**C43** - A `nova-missao` mostra o resumo do Context7 da versão nova e as opções `--pin-tested`/`--allow-new-series` (R43)
Proof: run unit | test_nova_missao_series_choice ... ok

**C44** - Sem Context7, a `nova-missao` avisa, marca `não verificada` e segue (R44)
Proof: run unit | test_nova_missao_without_context7 ... ok

**C45** - `--description` vai para o README; quebra de linha ou mais de 200 caracteres sai com 2 (R45)
Proof: run unit | test_scaffold_description_validation_and_readme ... ok

**C46** - Projeto rust gerado com registro real passa em todos os gates (R4)
Proof: run slow | test_rust_template_gates_pass ... ok

**C47** - Projeto gpui gerado com registro real passa em todos os gates (R4)
Proof: run slow | test_gpui_template_gates_pass ... ok

**C48** - Projeto typescript gerado com registro real passa em todos os gates (R4)
Proof: run slow | test_typescript_template_gates_pass ... ok

**C49** - Projeto tauri gerado com registro real passa em todos os gates, incluindo `tauri build --debug --no-bundle` (R4, R9)
Proof: run slow | test_tauri_template_gates_pass ... ok

**C50** - Projeto python-flask + mysql passa no teste de integração no banco efêmero (R5)
Proof: run slow | test_flask_mysql_gates_pass ... ok

## Handoff

**Phase:** done
**Size:** GRANDE
**Git mode:** 3
**Next:** nenhum: fase encerrada
**Linear:** PR #19 https://github.com/freire-andre/starcode/pull/19
**Integration branch:** feature/fase-8-uhura-scotty-kirk
**Last integrated:** 68e12f5
**Dispatched:** none
**Settled:** 2026-11-09: R27 emendado: user "a" (2026-11-09); 2026-11-09: achado do Q2: user "a" (despacho curto, sem terceiro Q)
**Attempts:** gate-T1=1, aceite-T13=1
**Reports:** 2026-11-08: T1: registry.py + testes + dist; 435 testes verdes; commit 9e1038a; 2026-11-08: T1 correção: HTTPError fechado; ae6e32f; suíte 435, 1 falha intermitente em 3 execuções (não reproduzida); 2026-11-08: T2: ephemeral_db.py + 6 testes; 52b97d5; suíte 441 OK sem PYTHONIOENCODING; com PYTHONIOENCODING=utf-8 3 testes novos (T1/T2) falham por decodificação: pendência para o ciclo pós-Q; 2026-11-08: T3: scaffold.py (leitor YAML embutido; chaves run/cwd nos gates) + testes; 9ff1fab; suíte 457 OK; 2026-11-08: T8: perfil python-flask; e252029; slow flask PASS com registro real; 2026-11-08: T4: stack_cache.py; 2c2209a; suíte 468 OK; 2026-11-08: T10: perfis rust e gpui; 5ab71ee; slow rust e gpui PASS (gpui 0.2.2, build Windows ok); 2026-11-08: T9: perfis postgresql/mysql; CI do banco em ci-db.yml separado; ruff.toml exclui scripts/; slow pg/mysql PASS com Docker real; 2026-11-08: T5: skill uhura e47add1; complemento despachado para test_build/test_crew_hook (assumiam uhura ausente) e encoding de T1/T2; 2026-11-08: T11: perfis typescript e tauri; d0b0c59; slow ts e tauri PASS (inclui tauri build --debug --no-bundle); 2026-11-08: T5: skill uhura e47add1 + complemento cf60350 (May change ampliado: 4 testes); suíte verde com e sem PYTHONIOENCODING; 2026-11-08: T6: scotty + detect/record + Data via checks; 8cdbc3a; suíte 501 OK; 2026-11-08: T7: nova-missao + 6 evals de roteamento; fa54664; suíte 507 OK; evals/README.md com contagem antiga (vai na T12); 2026-11-08: T7 integrado com dist/claude/evals/README.md editado à mão (fonte evals/README.md desatualizada): build --check vermelho em b7f54ed; correção no T12; 2026-11-08: 2026-11-08: T12: build com profiles nos 4 CLIs, testes de perfis e registros F8 (DECISIONS F8-1..10, CHANGELOG 1.2.0); be7fdf3 integrado em 533f0d6; build --check OK; suíte 517 OK com e sem PYTHONIOENCODING; 2026-11-08: 2026-11-08: T13: aceite 1e6a686; cenários 3-5 aprovados; 1 e 2 reprovados: scaffold new recusa pasta só com o cache .specs/ (ordem da skill) e biome check do tauri falha nos .md do cache; correção despachada no próprio T13 (May change ampliado); 2026-11-08: 2026-11-08: T13 correção: bb5a320 (scaffold new aceita pasta só com .specs; biome ignora .specs) + 61f93c7 (aceite com 5 cenários aprovados); integrado em dd1196a; suíte 523 OK nos dois modos; pendências do aceite para o Q: Doc version sempre desconhecida (check acusa outra versão logo após write) e recommended obsoleto no Biome 2.6; 2026-11-09: 2026-11-09: queda de energia interrompeu o worker da F8-11 (entrada já escrita, sem commit); redespachado no mesmo worktree; 2026-11-09: 2026-11-09: F8-11 integrada em f01208a (merge anterior ebd95fc desfeito localmente: check_commit vermelho por mensagem com maiúscula prescrita no brief; mensagem corrigida, gate verde); 2026-11-09: 2026-11-09: Q (codex · GPT-6-Luna medium) FAIL: 44/50 checks se sustentam; achados: Doc version desconhecida vira outra versão logo após write (R27 não cobre o caso); C37 só valida o texto do aceite; asserts fracos em C10, C13, C15; Biome recommended obsoleto (limite); 2026-11-09: 2026-11-09: pós-Q integrado em 3c7a412 (9534c36 R27, 902ac26 C10, 630ba58 C13/C15, cfa0307 Biome preset, 99b98a0 C37, bdd5335 dist, b990c6f F8-12/F8-13); suíte 525 OK nos dois modos; 2026-11-09: 2026-11-09: Q2 restrito (codex · GPT-6-Luna) FAIL: C10, C13, C15, C27, C37 agora sustentam e os 2 achados confirmados fechados; achado novo: doc-version sem dígitos (ex.: abc) é tratada como desconhecida (stack_cache.py:195); 2026-11-09: 2026-11-09: achado do Q2 corrigido em b58bfd6 (+ F8-12 emendada), merge 68e12f5; probe do Picard ok; suíte 525 OK nos dois modos; 2026-11-09: 2026-11-09: proofs e done verdes em 68e12f5; achado do Q2 fechado; 2026-11-09: 2026-11-09: push e PR #19 com confirmação do usuário ("sim"); comentário 'pronto para revisão' em SC-88..SC-100 e SC-15; 2026-11-09: 2026-11-09: CI do PR #19 verde (ubuntu e windows, 525 testes); merge na main autorizado pelo usuário ("Autorizado"); 2026-11-09: 2026-11-09: PR #19 integrado na main (06a4921); SC-88..SC-100 e SC-15 em Done com confirmação do usuário ("sim")
**Breaker:** closed
