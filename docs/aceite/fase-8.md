# Aceite da Fase 8 (SC-100): Uhura, Scotty e Kirk

Executado em 2026-11-08 em `F:/Projetos/starcode-missoes/` (fora do repo do StarCode), com os scripts e os perfis do ramo de integração `feature/fase-8-uhura-scotty-kirk` em `533f0d6` (`dist/claude`, por caminho absoluto; a instalação do plugin não foi alterada). Nada de `/starcode:setup`, Linear, GitHub ou remoto para esses projetos. As datas `2026-11-09` que o `scaffold.py` imprime ao lado de cada versão são a data da consulta ao registro (UTC); as entradas do cache usam `2026-11-08`.

Os cenários 1 e 2 seguiram os passos de `dist/claude/skills/nova-missao/SKILL.md` na ordem (versões, cache Context7, `new`, gates), com as opções recomendadas. Os dois ficaram **reprovados** por código do StarCode (achados 1 e 2); os cenários 3, 4 e 5 passaram.

## Versões

| Item | Versão |
| --- | --- |
| StarCode | 1.1.0 (arquivo `VERSION`), ramo `feature/fase-8-uhura-scotty-kirk` em `533f0d6` |
| Python | 3.14.8 |
| uv | 0.9.3 |
| cargo | 1.99.1 |
| Node / npm | v24.22.1 / 12.2.0 |
| Docker | 29.7.2 |
| Claude Code | 2.1.319 |
| Context7 | ferramentas `resolve`/`query-docs` do conector claude.ai, usadas em 2026-11-08 |

## Nova missão: python-flask + postgresql

**Resultado**: reprovado

- **Projeto**: `flask-pg-aceite`, pasta-mãe `F:/Projetos/starcode-missoes`, frase "Projeto de aceite da Fase 8.".
- **Versões** (`scaffold.py versions python-flask+postgresql`, 2026-11-08): flask 3.1.3 (pypi), pytest 9.2.0 (pypi), ruff 0.17.4 (pypi), mypy 2.4.1 (pypi), sqlalchemy 2.1.8 (pypi), alembic 1.20.1 (pypi), psycopg 3.3.8 (pypi), postgres 18 (dockerhub). Nenhuma fora da série testada.
- **Cache `.specs/stack/` (Context7 real, `Verified: context7`, Fetched 2026-11-08)**: `flask.md` (`/pallets/flask`, 3.1.3), `pytest.md` (`/pytest-dev/pytest`, 9.2.0), `sqlalchemy.md` (`/sqlalchemy/sqlalchemy`, 2.1.8), `alembic.md` (`/sqlalchemy/alembic`, 1.20.1), `psycopg.md` (`/psycopg/psycopg`, 3.3.8). Os IDs usados são os do perfil, sem versão: `Doc version` ficou `desconhecida`, e por isso `stack_cache.py check` mostra as cinco como `outra versão` (esperado para esse valor).
- **Motivo da reprovação**: com o cache criado antes do `new`, como manda a skill (passos 3 e 4), `scaffold.py new` terminou com exit 2: `pasta não vazia: ...\flask-pg-aceite` (achado 1). Para seguir, tirei `.specs/` da pasta, rodei o `new` (exit 0, `template: python-flask+postgresql`) e devolvi o cache; isso não faz parte do fluxo da skill.
- **Gates** (`scaffold.py gates`, exit 0):
  - `PASS uv sync`
  - `PASS uv run ruff check .`
  - `PASS uv run ruff format --check .`
  - `PASS uv run mypy src`
  - `PASS uv run pytest -v`
  - `PASS python scripts/ephemeral_db.py run postgresql -- uv run pytest -v -m integration`
- **Commit inicial**: não feito, porque o fluxo da skill parou no `new`.

## Nova missão: tauri

**Resultado**: reprovado

- **Projeto**: `tauri-aceite`, mesma pasta-mãe e mesma frase.
- **Versões** (`scaffold.py versions tauri`, 2026-11-08): tauri 2.12.5 (crates), tauri-build 2.7.4 (crates), @tauri-apps/cli 2.12.4 (npm), @tauri-apps/api 2.12.4 (npm), vite 8.3.6 (npm), typescript 7.0.2 (npm), vitest 5.1.0 (npm), @biomejs/biome 2.6.6 (npm). Nenhuma fora da série testada.
- **Cache `.specs/stack/` (Context7 real, Fetched 2026-11-08)**: `tauri.md` (2.12.5), `tauri-apps-cli.md` (2.12.4), `tauri-apps-api.md` (2.12.4), todas com `/tauri-apps/tauri-docs`; `vite.md` (`/vitejs/vite`, 8.3.6), `typescript.md` (`/microsoft/typescript`, 7.0.2), `vitest.md` (`/vitest-dev/vitest`, 5.1.0). `Doc version`: `desconhecida`.
- **Motivo da reprovação 1**: o mesmo exit 2 `pasta não vazia` do `new` com o cache presente (achado 1); mesmo contorno.
- **Motivo da reprovação 2**: `npx biome check .` falhou com 6 erros, todos de formatação nos 6 arquivos de `.specs/stack/*.md` (o Biome formata Markdown e o `biome.json` do perfil não exclui `.specs`; as entradas não têm linha em branco depois do título e saem com CRLF no Windows). Mesmo com LF o erro continua (achado 2).
- **Gates** (`scaffold.py gates`, exit 1):
  - `PASS npm install`
  - `FAIL npx biome check .`
  - `PASS cargo fmt --check [src-tauri]`
  - `PASS cargo clippy --all-targets -- -D warnings [src-tauri]`
  - `PASS npx tsc --noEmit`
  - `PASS npx vitest run`
  - `PASS cargo test [src-tauri]`
  - `PASS npm run tauri build -- --debug --no-bundle`
- **Commit inicial**: não feito (há `FAIL`, R34).

## Scaffold e gates por perfil

**Resultado**: aprovado

Pastas vazias, sem cache (o cenário pede só `new` + `gates`); `new` saiu com 0 nos quatro.

- **rust** (`aceite-rust`; sem dependências resolvidas pelo registro): `PASS cargo fetch`, `PASS cargo fmt --check`, `PASS cargo clippy --all-targets -- -D warnings`, `PASS cargo test` (exit 0).
- **typescript** (`aceite-typescript`): typescript 7.0.2 (npm, 2026-11-09), vitest 5.1.0 (npm, 2026-11-09), @biomejs/biome 2.6.6 (npm, 2026-11-09). `PASS npm install`, `PASS npx biome check .`, `PASS npx tsc --noEmit`, `PASS npx vitest run` (exit 0).
- **gpui** (`aceite-gpui`, experimental): gpui 0.2.2 (crates, 2026-11-09). `PASS cargo fetch`, `PASS cargo fmt --check`, `PASS cargo clippy --all-targets -- -D warnings`, `PASS cargo test`, `PASS cargo build` (exit 0).
- **python-flask + mysql** (`aceite-flask-mysql`): flask 3.1.3 (pypi, 2026-11-09), pytest 9.2.0 (pypi), ruff 0.17.4 (pypi), mypy 2.4.1 (pypi), sqlalchemy 2.1.8 (pypi), alembic 1.20.1 (pypi), pymysql 1.2.3 (pypi), cryptography 50.0.2 (pypi), mysql 26 (dockerhub). `PASS uv sync`, `PASS uv run ruff check .`, `PASS uv run ruff format --check .`, `PASS uv run mypy src`, `PASS uv run pytest -v`, `PASS python scripts/ephemeral_db.py run mysql -- uv run pytest -v -m integration` (exit 0).
- **Cache**: nenhuma entrada (sem `.specs/stack/`), como pede o cenário.

## Série fora da testada

**Resultado**: aprovado

- **Fixture** (fora do repo): `F:/Projetos/starcode-missoes/fixtures/flask-serie-nova.json`, com `STARCODE_REGISTRY_FIXTURE` apontando para ele: flask `4.0.1` (série 4; a testada do perfil é `3`), `3.1.3`, `3.0.9`, `2.9.9`; pytest 9.2.0, ruff 0.17.4, mypy 2.4.1.
- **`versions python-flask`**: `flask 4.0.1 (pypi) — fora da série testada (3); mais nova da série: 3.1.3` (exit 0).
- **`new` sem opção**: `flask 4.0.1 fora da série testada 3: use --pin-tested ou --allow-new-series`, exit 5, nenhuma pasta criada.
- **`new --pin-tested`**: exit 0 com flask 3.1.3 (pypi, 2026-11-09), pytest 9.2.0, ruff 0.17.4, mypy 2.4.1; `pyproject.toml` com `flask==3.1.3`.
- **Gates** do projeto `serie-fora`: `PASS uv sync`, `PASS uv run ruff check .`, `PASS uv run ruff format --check .`, `PASS uv run mypy src`, `PASS uv run pytest -v`.
- **Cache**: nenhuma entrada.

## Contêineres efêmeros

**Resultado**: aprovado

- `docker ps -a --format '{{.Names}}'` no fim de todos os cenários (2026-11-08): só `orcamento-pg`, que já existia e é de outro projeto; zero contêineres `starcode-eph-*` (`--filter name=starcode-eph` devolveu 0 linhas).
- Os gates de banco (`ephemeral_db.py run postgresql` e `run mysql`) passaram e não deixaram contêiner.

## Achados e pendências

Cada item pede código ou ajuste de perfil e vira ticket próprio; nada foi corrigido neste ticket (fora do `May change`).

1. **`scaffold.py new` recusa a pasta com o cache** (`validate_inputs`, `scaffold.py`): a skill `nova-missao` manda gravar `.specs/stack/` antes do `new` e diz que o `new` aceita essa pasta, mas o script falha com exit 2 `pasta não vazia` assim que existe qualquer arquivo. Ou o script tolera uma pasta só com `.specs/stack/`, ou a skill muda a ordem (e o R43/R44 junto).
2. **Cache de `.specs/stack/` quebra o `biome check` do perfil tauri**: o `biome.json` não exclui `.specs` e o formato das entradas (sem linha em branco após o título; CRLF no Windows) não passa no formatador Markdown do Biome 2.6. O gate falha em qualquer projeto tauri/typescript que tenha cache. Excluir `!.specs` no `biome.json` dos perfis ou gerar as entradas já formatadas.
3. **`Doc version` sempre `desconhecida`**: os IDs do perfil não têm versão e o Context7 não informa a versão dos docs; `stack_cache.py check` então mostra `outra versão` logo após o `write`. Ajustar a regra do `check` para esse valor ou definir como obter a versão dos docs.
4. **Aviso do Biome**: o `biome.json` do perfil usa `linter.rules.recommended`, que o Biome 2.6 marca como obsoleto (só informativo, não falha).
5. **Reexecução dos cenários 1 e 2**: depois das correções 1 e 2, refazer `nova-missao` para `python-flask + postgresql` e `tauri` (inclusive o commit inicial, que não foi feito aqui) e então marcar `aprovado`.
6. **Limpeza**: as pastas em `F:/Projetos/starcode-missoes/` (`flask-pg-aceite`, `tauri-aceite`, `aceite-*`, `serie-fora`, `fixtures`) ficam para o usuário; nenhuma é repositório git.
