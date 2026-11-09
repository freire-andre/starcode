# Fase 8: Uhura, Scotty e Kirk (v1.2): Spec

**Approved**: 2026-11-08 - user: "sim"
**Amended**: 2026-11-09 - user: "a" (R27: `Doc version` desconhecida, achado do Q)

**Size**: LARGE
**Risk triggers**: Chamadas externas (registro de pacotes, Context7), Irreversibilidade (containers locais e criação de projeto)
**Status**: Approved

## Context

Até a v1.1 o StarCode só trabalha em repositórios que já existem. Não há como começar um projeto novo dentro do fluxo; o Data escreve as linhas `**Build**`/`**Run**` dos tickets à mão a cada feature; e as regras do Context7 e do corpo do PR existem só como texto no `STARCODE.md`, sem tripulante responsável nem cache padronizado em `.specs/stack/`. A Fase 8 do plano (seções 3, 3.2, 6, 7 e 10) entrega três tripulantes:
- **Uhura** (`uhura`): cache do Context7 em `.specs/stack/`, corpo do PR e comentários do Linear;
- **Scotty** (`scotty`): perfis das stacks (5 do plano + `gpui` experimental), scaffolding, gates padrão e banco efêmero local;
- **Kirk** (`nova-missao`): criação de um projeto novo do zero.

Sucesso: `nova-missao` cria um projeto Flask+PostgreSQL e um Tauri+TS com versões do registro de pacotes, cache do Context7 só das dependências principais e gates verdes na primeira execução.

Discovery: `.specs/features/fase-8-uhura-scotty-kirk/context.md`. Issue: SC-15.

## Scope

- `profiles/<perfil>/` (novo, fonte na raiz): `profile.yaml` e `template/` para `python-flask`, `rust`, `tauri`, `typescript`, `gpui` (experimental), `postgresql` e `mysql`.
- `scripts/scaffold.py` (novo): `list`, `versions`, `new`, `checks`, `gates`.
- `scripts/registry.py` (novo): leitura de versões estáveis no npm, PyPI, crates.io e Docker Hub.
- `scripts/ephemeral_db.py` (novo, só stdlib; também copiado para os projetos com banco): `up`, `down`, `run`, `list`.
- `scripts/stack_cache.py` (novo): `write`, `check` do cache `.specs/stack/`.
- Skills novas: `skills/uhura/` (com `references/pr-body.md` e `references/linear-comments.md`), `skills/scotty/`, `skills/nova-missao/`.
- Ajustes: `skills/engajar/references/execute.md` (PR e comentários pela Uhura), `skills/data/SKILL.md` e `references/tasks-template.md` (gates a partir do perfil), `src/context/STARCODE.md` (aponta o protocolo do Context7 para a Uhura).
- `tools/build.py`: copia `profiles/` para cada `dist/<cli>/` e gera as 3 skills nos 4 CLIs.
- Evals de roteamento para as 3 skills novas.
- Testes `unittest` dos itens acima (registro falso, sem rede).
- `DECISIONS.md` (F8-n), `CHANGELOG.md` (seção `## [1.2.0] - não lançada`), `docs/compatibilidade.md` (linha dos perfis), `dist/` regenerado.
- Aceite real em `docs/aceite/fase-8.md`.

## Non-Goals

- Worf, Guinan e diagnóstico (Fase 9), painel Ponte (Fase 10), verificação de telas (Fase 11), robustez (Fase 12).
- Criar repositório no GitHub, push, deploy ou qualquer recurso remoto pela `nova-missao` ou pelo Scotty.
- Frontends do Tauri além de vanilla TS + Vite; perfis de banco combinados com `rust`, `tauri`, `typescript` ou `gpui`; componentes de terceiros para GPUI.
- Banco efêmero por instalação local (só Docker); apontar para qualquer banco que não seja o efêmero.
- Mudar o schema do config do usuário ou do repositório; mudar o fluxo do Q, da Frota ou dos gates existentes.
- Tag/release da v1.2.0 (fica para depois do aceite, com confirmação própria).

## Requirements

### Perfis

- **R1** - The system SHALL ter um `profiles/<perfil>/profile.yaml` para cada um destes perfis: `python-flask`, `rust`, `tauri`, `typescript`, `gpui` (tipo `app`; `gpui` com `experimental: true`) e `postgresql`, `mysql` (tipo `db`), com os campos de Data & Contracts.
- **R2** - The system SHALL declarar nos gates de cada perfil exatamente estes comandos:
  - `python-flask`: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, `uv run pytest -v`;
  - `rust`: `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`;
  - `typescript`: `npx tsc --noEmit`, `npx biome check .`, `npx vitest run`;
  - `tauri`: os três do `typescript`, mais os três do `rust` rodados em `src-tauri/`, mais `npm run tauri build -- --debug --no-bundle`;
  - `gpui`: `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`, `cargo build`;
  - `postgresql`/`mysql`: `python scripts/ephemeral_db.py run <engine> -- uv run pytest -v -m integration` (sobe e remove o banco, R20).
- **R3** - The system SHALL ter em cada `template/` só estrutura e convenções, com marcadores `{{name}}` (nome do projeto), `{{description}}` (R45) e `{{version:<pacote>}}`. Nenhum número de versão de dependência fica escrito no template.
- **R4** - The system SHALL ter em cada template de app pelo menos um teste que passa na primeira execução:
  - `python-flask`: app factory, um blueprint com `GET /health` → 200 `{"status": "ok"}`, config por ambiente e teste com o cliente do Flask;
  - `rust`: lib + binário com um teste de unidade;
  - `typescript`: lib com um teste do vitest;
  - `tauri`: frontend vanilla TS + Vite com um teste do vitest e um comando Rust `greet` com teste em `src-tauri/`;
  - `gpui`: binário que abre uma janela com uma view de contador e um teste de unidade da lógica do contador (o teste não abre janela).
- **R5** - The system SHALL ter nos templates de banco (combinados com `python-flask`): SQLAlchemy, Alembic com uma migração inicial reversível, driver `psycopg` (PostgreSQL) ou `PyMySQL` (MySQL), configuração por `DATABASE_URL` e um teste `integration` que roda `upgrade head`, grava e lê uma linha fictícia e roda `downgrade base`.
- **R6** - The system SHALL ter em cada template de app um `.github/workflows/ci.yml` que roda os gates do perfil (com o banco efêmero quando houver perfil de banco) e um `.gitignore` adequado à stack.

### Versões

- **R7** - WHEN `python scaffold.py versions <perfil>[+<perfil-db>] [--json]` roda THEN the system SHALL consultar o registro de cada dependência do perfil e devolver a maior versão estável:
  - npm: dist-tag `latest`;
  - PyPI: maior versão sem pré-release nem yank;
  - crates.io: `max_stable_version`;
  - Docker Hub (imagens `postgres`, `mysql`): maior tag só numérica de major (`17`, `9`).
- **R8** - The system SHALL nunca aceitar versão de pré-release (`-alpha`, `-beta`, `-rc`, `a`, `b`, `rc`, `.dev`) nem tirar versão do Context7.
- **R9** - IF o perfil é `tauri` THEN the system SHALL usar o mesmo major para o crate `tauri`, `tauri-build` e os pacotes npm `@tauri-apps/cli` e `@tauri-apps/api`, tomando o major do `@tauri-apps/cli` `latest`; IF o crate não tem versão estável nesse major THEN the system SHALL parar com `tauri: crate sem versão estável no major <N>`.
- **R10** - IF um registro não responde em 15 s, devolve erro HTTP ou um pacote não existe THEN the system SHALL sair com 2 e a mensagem `registro <nome> indisponível para <pacote>: <motivo>`, sem gerar nenhum arquivo e sem versão inventada.
- **R11** - The system SHALL aceitar a variável `STARCODE_REGISTRY_FIXTURE=<arquivo.json>` que substitui todas as consultas por respostas do arquivo (usada nos testes, nunca no fluxo normal), e marcar a fonte como `fixture` no `.starcode/stack.json`.

- **R39** - The system SHALL declarar em cada dependência principal do `profile.yaml` o campo `tested` com a série em que o template foi escrito e testado: o major para versões ≥ 1 (`"3"`), major.minor para 0.x (`"0.2"`).
- **R40** - IF a maior versão estável de uma dependência principal está fora da série `tested` THEN `scaffold.py versions` SHALL marcá-la `fora da série testada (<série>)` com a versão mais nova da série ao lado, e `scaffold.py new` SHALL sair com 5 e `<pacote> <versão> fora da série testada <série>: use --pin-tested ou --allow-new-series`, sem escrever nada.
- **R41** - WHEN `scaffold.py new` recebe `--pin-tested` THEN the system SHALL usar a maior versão estável dentro da série `tested`; WHEN recebe `--allow-new-series` THEN the system SHALL usar a versão mais nova e gravar `"outsideTested": true` na entrada da dependência em `.starcode/stack.json`.
- **R42** - The system SHALL ter em cada dependência principal do `profile.yaml` o campo `docs` com o Context7 ID e a data da consulta usada para escrever o template.

### Scaffold

- **R12** - WHEN `python scaffold.py new <pasta> --profile <app> [--db <db>] [--name <nome>]` roda THEN the system SHALL resolver as versões (R7), copiar o template do app e o do banco, trocar os marcadores, gravar `.starcode/stack.json` e imprimir o relatório de Data & Contracts. O nome padrão é o nome da pasta.
- **R13** - IF o nome não casa com `^[a-z][a-z0-9-]{0,62}$` THEN the system SHALL sair com 2 e `nome inválido: use minúsculas, dígitos e hífen, começando por letra`.
- **R14** - IF a pasta existe e não está vazia THEN the system SHALL sair com 2 e `pasta não vazia: <caminho>`, sem escrever nada.
- **R15** - IF o perfil ou a combinação não existe (ex.: `--db postgresql` com `--profile rust`) THEN the system SHALL sair com 2 e listar os perfis e combinações válidos.
- **R16** - IF a geração falha depois de criar a pasta THEN the system SHALL remover a pasta criada nesta execução e sair com 1 e o motivo; uma pasta vazia que já existia volta a ficar vazia.
- **R17** - WHEN `python scaffold.py checks <pasta> [--json]` roda THEN the system SHALL ler o `.starcode/stack.json` e imprimir as linhas prontas para o `tasks.md`: `**Build**:` com build, type check e lint, `**Run unit**:` e, com perfil de banco, `**Run integration**:`. Sem `.starcode/stack.json` sai com 1 e `perfil não registrado: rode o Scotty`.
- **R18** - WHEN `python scaffold.py gates <pasta> [--json]` roda THEN the system SHALL instalar as dependências (`uv sync`, `npm install`, `cargo fetch` conforme o perfil) e rodar cada gate do perfil em ordem, imprimindo `PASS <comando>`, `FAIL <comando>` ou `SKIP <comando>: <motivo>`, e sair com 0 só se nenhum gate for `FAIL`.
- **R19** - IF uma ferramenta exigida pelo perfil não está no PATH (`uv`, `node`/`npm`, `cargo`, `docker`) THEN the system SHALL marcar os gates que dependem dela como `SKIP <comando>: <ferramenta> ausente` e sair com 3 quando houver `SKIP` sem `FAIL`.

### Banco efêmero

- **R20** - WHEN `python ephemeral_db.py run <postgresql|mysql> -- <comando>` roda THEN the system SHALL subir um container `starcode-eph-<engine>-<8 hex>` com a imagem do `.starcode/stack.json`, publicado só em `127.0.0.1` numa porta livre escolhida na hora, com usuário, senha e banco fictícios gerados na hora; esperar o banco aceitar conexões (até 60 s); rodar o comando com `DATABASE_URL` no ambiente; e remover o container e o volume (`docker rm -f -v`) ao fim, também quando o comando falha ou é interrompido. O exit code é o do comando.
- **R21** - IF o Docker não está instalado ou o daemon não responde THEN the system SHALL sair com 3 e `gate de integração não executado: Docker indisponível (<motivo>)`, sem rodar o comando.
- **R22** - IF o banco não aceita conexões em 60 s THEN the system SHALL remover o container e sair com 4 e `banco efêmero não ficou pronto em 60 s`.
- **R23** - The system SHALL recusar com exit 2 qualquer `DATABASE_URL` já presente no ambiente que não aponte para `127.0.0.1` ou `localhost` quando `run` é chamado com `--reuse-env`; sem `--reuse-env`, a variável do ambiente é sempre substituída pela do banco efêmero.
- **R24** - WHEN `python ephemeral_db.py list` roda THEN the system SHALL listar os containers `starcode-eph-*` existentes (nome, idade); `down <nome>` remove um deles. O Scotty mostra os órfãos com mais de 60 min e só os remove com confirmação.
- **R25** - WHILE dois `run` acontecem ao mesmo tempo (Frota, Q), the system SHALL usar nomes e portas diferentes em cada um.

### Uhura

- **R26** - WHEN `python stack_cache.py write <repo> <lib> --id <context7-id> --project-version <v> --doc-version <v|desconhecida> --summary-file <arq>` roda THEN the system SHALL gravar `.specs/stack/<lib>.md` no formato de Data & Contracts, substituindo a entrada da mesma lib, nunca duplicando.
- **R27** - WHEN `python stack_cache.py check <repo> [--json]` roda THEN the system SHALL listar cada entrada como `ok`, `velha` (mais de 30 dias), `versão mudou` (versão do manifesto ≠ `project-version`) ou `outra versão` (`doc-version` ≠ `project-version` no major.minor), e sair com 0 quando todas estão `ok` e 1 caso contrário. IF `doc-version` é `desconhecida` (o Context7 não informa a versão dos docs) THEN the system SHALL pular só a comparação de `outra versão`, julgar a entrada pela idade e pela versão do manifesto, e listá-la como `ok (doc sem versão)` quando passar nas duas, contando como `ok` no código de saída.
- **R28** - The system SHALL ter na skill `uhura` o protocolo do Context7 (bootstrap só das dependências principais do perfil, sob demanda, atualização por R27, sem Context7 → doc oficial e `**Verified**: não verificada` na entrada).
- **R29** - The system SHALL ter em `uhura/references/pr-body.md` o template do corpo do PR (Resumo, Issue, Mudanças, Gates com resultado, Verificação do Q, Riscos) e em `references/linear-comments.md` os modelos de comentário (início, integrado, bloqueado, cancelado, concluído), todos neutros e em PT-BR.
- **R30** - WHEN o Picard vai abrir o PR ou comentar no Linear THEN `execute.md` SHALL mandar redigir o texto pela Uhura: no Claude como subagente com o modelo da Uhura; nos outros CLIs pela própria sessão seguindo a skill. O Picard continua sendo quem confirma e executa o `gh pr create` e o `orca linear comment`.

### Scotty

- **R31** - WHEN o Scotty é chamado num repositório existente THEN the system SHALL detectar o perfil pelos manifestos (`pyproject.toml` com flask → `python-flask`; `src-tauri/tauri.conf.json` → `tauri`; `Cargo.toml` → `rust`; `package.json` com typescript → `typescript`; dependência `psycopg`/`PyMySQL` → banco), mostrar o resultado e, com a confirmação do usuário, gravar `.starcode/stack.json` com as versões lidas do manifesto/lockfile (fonte `manifest`), sem copiar template.
- **R32** - WHEN o Data monta o `## Checks` de um repo com `.starcode/stack.json` THEN the system SHALL usar as linhas de `scaffold.py checks` em `**Build**` e `**Run <nome>**`; sem esse arquivo, o Data segue como hoje (comandos lidos dos manifestos e da CI).

### Kirk

- **R33** - WHEN o usuário invoca `nova-missao` THEN the system SHALL perguntar numa só mensagem: nome, pasta-mãe, perfil de app, perfil de banco opcional e uma frase sobre o que o projeto faz (cada um com recomendação; `gpui` aparece com o aviso `experimental: API 0.x muda entre versões`), e depois rodar, em ordem: `scaffold.py versions`; consulta ao Context7 pela Uhura das dependências principais nas versões resolvidas, gravando o cache `.specs/stack/` **antes** de gerar qualquer arquivo do projeto (o cache é escrito na pasta nova, criada vazia); `scaffold.py new`; `scaffold.py gates`; `git init` com o commit `chore: projeto inicial (<perfis>)`; o relatório final.
- **R43** - IF `scaffold.py versions` marca alguma dependência `fora da série testada` THEN o Kirk SHALL mostrar, junto com o resumo do Context7 da versão nova, duas opções numa só mensagem: (a) usar a última da série testada (`--pin-tested`, recomendado), (b) seguir na versão nova assumindo o risco (`--allow-new-series`).
- **R44** - IF o Context7 não está disponível na sessão THEN o Kirk SHALL avisar numa linha, gravar as entradas do cache com `**Verified**: não verificada (<url oficial>)` e seguir; isso não bloqueia o scaffold.
- **R34** - IF `scaffold.py gates` sai com `FAIL` THEN the system SHALL mostrar o gate e as últimas 20 linhas da saída, não fazer o commit inicial e oferecer: (a) chamar o McCoy, (b) manter a pasta para investigar, (c) remover a pasta (com confirmação).
- **R35** - WHEN o commit inicial existe THEN the system SHALL oferecer numa só mensagem, sem rodar nenhum sozinho: (a) o `/starcode:setup` (Linear) e (b) engajar a primeira missão (`engajar`, que dimensiona e leva à Troi), e nunca criar repositório remoto, push ou deploy.
- **R45** - The system SHALL ter em cada template de app um `README.md` com `# {{name}}`, a linha `{{description}}` e a seção `## Gates` com os comandos do perfil; o `scaffold.py new` SHALL aceitar `--description "<frase>"` (até 200 caracteres, uma linha) e, sem ela, gravar `Projeto {{name}}.`; IF a frase tem quebra de linha ou passa de 200 caracteres THEN the system SHALL sair com 2 e `descrição inválida: uma linha, até 200 caracteres`.

### Build, aceite e registros

- **R36** - The system SHALL fazer o `tools/build.py` copiar `profiles/` para `dist/<cli>/profiles/` nos 4 CLIs e gerar `uhura`, `scotty` e `nova-missao`, com `build.py --check` verde.
- **R37** - The system SHALL registrar em `docs/aceite/fase-8.md` um aceite real, fora do repo do StarCode (pasta `F:\Projetos\starcode-missoes\`), cobrindo:
  - `nova-missao` com `python-flask` + `postgresql` e com `tauri`, cada um com as versões e a fonte `registry` + data, as entradas do cache só das dependências principais e `scaffold.py gates` com todos os gates `PASS` na primeira execução;
  - nenhum container `starcode-eph-*` depois dos gates (`docker ps -a`);
  - `scaffold.py gates` dos perfis `rust`, `typescript`, `gpui` e `python-flask` + `mysql` com `PASS`;
  - um caso de série fora da testada (fixture do registro) parando com exit 5 e seguindo com `--pin-tested`.
- **R38** - The system SHALL registrar em `DECISIONS.md` as decisões F8-n desta fase e no `CHANGELOG.md` a seção `## [1.2.0] - não lançada`.

## Data & Contracts

- **`profile.yaml`** (miniyaml do repo):
  ```yaml
  name: python-flask
  kind: app            # app | db
  combinesWith: [postgresql, mysql]   # só em app; [] quando não combina
  tools: [uv]
  install: ["uv sync"]
  gates:
    lint: ["uv run ruff check .", "uv run ruff format --check ."]
    typecheck: ["uv run mypy src"]
    unit: ["uv run pytest -v"]
    build: []
  deps:                # dependências principais: versão + bootstrap do Context7
    - {name: flask, registry: pypi, main: true, tested: "3", docs: {id: /pallets/flask, at: 2026-11-08}}
    - {name: pytest, registry: pypi, main: true, dev: true, tested: "9", docs: {id: /pytest-dev/pytest, at: 2026-11-08}}
    - {name: ruff, registry: pypi, main: false, dev: true}
  ```
  `experimental: true` só no `gpui`. Os IDs e séries acima são ilustrativos; os reais vêm da consulta feita ao escrever cada template (R42).
  Perfis `db` têm `gates.integration` e `image: {name: postgres, registry: dockerhub}`.
- **`.starcode/stack.json`** (versionado no projeto):
  ```json
  {"schemaVersion": 1, "profiles": ["python-flask", "postgresql"],
   "versions": {"flask": {"version": "3.1.3", "registry": "pypi", "source": "registry", "at": "2026-11-08"}},
   "image": {"postgresql": "postgres:17"}}
  ```
  `source` é `registry`, `manifest` (Scotty em repo existente) ou `fixture` (R11).
- **`.specs/stack/<lib>.md`**:
  ```markdown
  # <lib>
  **Context7 ID**: /org/proj[/versão]
  **Project version**: 3.1.3
  **Doc version**: 3.1.x | desconhecida
  **Fetched**: 2026-11-08
  **Verified**: context7 | não verificada (<url oficial>)
  ## Summary
  <resumo prático, até 30 linhas>
  ```
- **Relatório do `scaffold.py new`**: uma linha por dependência `<pacote> <versão> (<registro>, <data>)`, depois `template: <perfis>`, `pasta: <caminho>`. Exit: 0 ok, 1 falha de geração, 2 uso/entrada inválida ou registro indisponível, 5 fora da série testada (R40).
- **Exit codes do `ephemeral_db.py run`**: o do comando; 2 uso; 3 Docker indisponível; 4 banco não ficou pronto.
- **Fixture do registro** (R11): `{"pypi": {"flask": ["3.1.3", "3.2.0rc1"]}, "npm": {"vite": {"latest": "8.3.6"}}, "crates": {"tauri": {"max_stable_version": "2.12.4"}}, "dockerhub": {"postgres": ["17", "17.2", "18-rc"]}}`.

## States

- **Scaffold:** resolvendo versões → gerando → gerado | falhou (pasta removida, R16) | recusado (R13–R15, nada escrito).
- **Gates:** todos `PASS` (exit 0) | algum `FAIL` (exit 1) | `SKIP` sem `FAIL` (exit 3, ferramenta ausente).
- **Banco efêmero:** subindo → pronto → comando rodando → removido; Docker indisponível (3); não ficou pronto (4, removido).
- **Cache:** `ok` | `velha` | `versão mudou` | `outra versão`.
- **Kirk:** perguntas → versões → Context7 + cache → (fora da série testada → escolha, R43) → scaffold → gates → commit → oferta do setup e da primeira missão; gates vermelhos param antes do commit (R34).

## Edge Cases

- **Registro devolve só pré-release** (ex.: `tauri` 3.0.0-alpha.6 em `cargo search`): R8/R9 escolhem a estável do major do CLI; nunca a alpha.
- **Sem rede no meio da resolução:** R10; nenhum arquivo escrito porque as versões são resolvidas antes da cópia.
- **Ctrl+C durante `ephemeral_db.py run`:** o container é removido no `finally`; se o processo morrer sem `finally`, o container aparece no `list` como órfão (R24).
- **Porta escolhida ocupada entre a escolha e o `docker run`:** uma nova tentativa com outra porta, no máximo 3; depois exit 4.
- **Windows:** comandos em PowerShell e Git Bash; `npx`/`npm` resolvidos via `shutil.which` (`.cmd`); caminhos com espaço citados.
- **Primeira compilação do Tauri demora:** cada gate tem timeout de 30 min no `scaffold.py gates`; estouro = `FAIL <comando>: timeout 30 min`.
- **GPUI 0.x:** uma 0.3 estável no registro já fica fora da série `0.2` e cai em R40/R43; a linha `gpui-pre` (outro crate) não é usada.
- **Context7 sem a versão exata:** a entrada grava `Doc version` real consultada e `check` aponta `outra versão`.
- **Repo existente com perfis misturados (ex.: Flask + pacote TS solto):** o Scotty mostra o que detectou e pede a escolha; nada é gravado sem confirmação.

## Decisions

| Item | Options | Status |
|---|---|---|
| Divisão da fase | uma feature GRANDE · três features em sequência | approved - user: "Uma feature GRANDE (Recomendado)" |
| Geração dos templates | arquivos fixos + script (determinístico, testável) · modelo gera os arquivos | approved - user: "Arquivos fixos + script (Recomendado)" |
| Perfil GPUI | incluir como 7º perfil experimental, série 0.2, sem banco (escolhido) · deixar para depois | approved - user: "pode incluir também o app GPUI" |
| Context7 antes do scaffold | versões → Context7 → scaffold, com série testada por dependência (escolhido) · Context7 só depois, como registro | approved - user: "Eles não consultam o MCP Context7 para garantir a documentação mais recente antes de iniciar o processo?" |
| `Doc version` desconhecida no `check` (R27) | julgar só por idade e manifesto, listada como `ok (doc sem versão)` (escolhido) · gravar a versão do projeto como versão dos docs · manter e o `check` sempre falha | approved - user: "a" |
| Grill-me no Kirk | não incluir; frase do projeto no README + oferta de engajar a primeira missão, que leva à Troi (já baseada em grilling) (escolhido) · interrogatório dentro do Kirk | approved - user: "sim, inclua os dois e reapresente" |
| Frontend do Tauri | vanilla TS + Vite · + React · + React e Svelte | approved - user: "Vanilla TS + Vite (Recomendado)" |
| Alcance do Kirk | pasta + git init + oferta do setup · + repo no GitHub · só scaffold | approved - user: "Pasta + git init + setup (Recomendado)" |
| Ferramentas Python/Node | uv + npm · pip/venv + npm · uv + pnpm | approved - user: "uv + npm (Recomendado)" |
| Perfis com template | os 5 com template, aceite real nos 2 combos + gates dos outros (escolhido) · só os 2 do aceite | approved - default da Troi, confirmado pela aprovação da spec |
| Banco efêmero | só Docker (escolhido) · Docker ou instalação local | approved - default da Troi, confirmado pela aprovação da spec |
| Combinação de perfis | app + banco opcional, banco só com `python-flask` nesta versão (escolhido) · banco com qualquer app | approved - default da Troi, confirmado pela aprovação da spec |
| Onde fica o perfil do projeto | `.starcode/stack.json` próprio (escolhido; não exige setup do Linear) · chave nova no config do repo (exige `linear.workspace`) | approved - default do Spock, confirmado pela aprovação da spec |
| Lint do TypeScript | biome (um pacote, sem config extra) (escolhido) · eslint (vários pacotes e config flat) | approved - default do Spock, confirmado pela aprovação da spec |
| Consulta ao registro | APIs JSON dos registros via stdlib, com fixture para teste (escolhido) · `npm view`/`pip index`/`cargo search` (o `cargo search` mostra pré-release, sem modo offline) | approved - default do Spock, confirmado pela aprovação da spec |

## Open Questions
None.

## Sources

- PLANO_STARCODE.md, seções 3, 3.2, 6, 7 e Fase 8: binding.
- Tauri v2 CLI (`/tauri-apps/tauri-docs`, Context7, 2026-11-08): `tauri build --debug --no-bundle` existe; via npm, `npm run tauri build -- --debug --no-bundle`: binding para o gate do perfil `tauri`.
- Registros consultados em 2026-11-08: `npm view @tauri-apps/cli dist-tags` → `latest 2.12.4`, `next 3.0.0-alpha.6`; `cargo info tauri` → `3.0.0-alpha.6`: motivo de R8/R9.

## Differences from the Source

- **Comandos de versão:** o plano cita `npm view`, `pip index versions` e `cargo search`. A spec usa as APIs JSON dos mesmos registros, porque o `cargo search` devolve pré-release e os comandos não têm modo offline para teste. A fonte continua sendo o registro de pacotes (R7, R11).
- **Gate do Tauri:** o plano diz "`tauri build` em modo debug"; a spec acrescenta `--no-bundle` para não gerar instaladores na verificação (R2).
- **Lint do TypeScript:** o plano diz "eslint/biome"; a spec fixa biome.
