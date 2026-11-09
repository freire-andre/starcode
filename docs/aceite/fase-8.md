# Aceite da Fase 8 (SC-100): Uhura, Scotty e Kirk

Executado em 2026-11-08 em `F:/Projetos/starcode-missoes/` (fora do repo do StarCode), com os scripts e os perfis do ramo de integração `feature/fase-8-uhura-scotty-kirk` em `533f0d6` (cenários 3, 4 e 5) e, nos cenários 1 e 2 refeitos, os do ramo da correção em `bb5a320` (`dist/claude`, por caminho absoluto; a instalação do plugin não foi alterada). Nada de `/starcode:setup`, Linear, GitHub ou remoto para esses projetos. As datas `2026-11-09` que o `scaffold.py` imprime ao lado de cada versão são a data da consulta ao registro (UTC); as entradas do cache usam `2026-11-08`.

Os cenários 1 e 2 seguiram os passos de `dist/claude/skills/nova-missao/SKILL.md` na ordem (versões, cache Context7, `new`, gates, commit inicial), com as opções recomendadas. Na primeira execução os dois foram reprovados por código do StarCode (achados 1 e 2); depois da correção (`bb5a320`) foram refeitos do zero e os cinco cenários estão aprovados.

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

**Resultado**: aprovado

Refeito do zero em 2026-11-08, depois da correção do achado 1 (commit `bb5a320`), com `dist/claude/scripts` e `dist/claude/skills/nova-missao` regenerados no worktree da correção, na ordem da skill e sem contorno.

- **Projeto**: `flask-pg-aceite`, pasta-mãe `F:/Projetos/starcode-missoes`, frase "Projeto de aceite da Fase 8.".
- **Versões** (`scaffold.py versions python-flask+postgresql`, 2026-11-08): flask 3.1.3 (pypi), pytest 9.2.0 (pypi), ruff 0.17.4 (pypi), mypy 2.4.1 (pypi), sqlalchemy 2.1.8 (pypi), alembic 1.20.1 (pypi), psycopg 3.3.8 (pypi), postgres 18 (dockerhub). Nenhuma fora da série testada. O `new` imprimiu as mesmas versões com a data de consulta 2026-11-09 (UTC).
- **Cache `.specs/stack/` (Context7 real, `Verified: context7`, Fetched 2026-11-08)**, gravado antes do `new`: `flask.md` (`/pallets/flask`, 3.1.3), `pytest.md` (`/pytest-dev/pytest`, 9.2.0), `sqlalchemy.md` (`/sqlalchemy/sqlalchemy`, 2.1.8), `alembic.md` (`/sqlalchemy/alembic`, 1.20.1), `psycopg.md` (`/psycopg/psycopg`, 3.3.8). `Doc version`: `desconhecida` (achado 3).
- **`new`** com a pasta contendo só `.specs/stack/`: exit 0, `template: python-flask+postgresql`.
- **Gates** (`scaffold.py gates`, exit 0):
  - `PASS uv sync`
  - `PASS uv run ruff check .`
  - `PASS uv run ruff format --check .`
  - `PASS uv run mypy src`
  - `PASS uv run pytest -v`
  - `PASS python scripts/ephemeral_db.py run postgresql -- uv run pytest -v -m integration`
- **Commit inicial**: `9be4937` `chore: projeto inicial (python-flask+postgresql)`, sem remoto; as 5 entradas do cache entram no commit.

## Nova missão: tauri

**Resultado**: aprovado

Refeito do zero em 2026-11-08, depois das correções dos achados 1 e 2 (commit `bb5a320`), pelo mesmo fluxo e sem contorno.

- **Projeto**: `tauri-aceite`, mesma pasta-mãe e mesma frase.
- **Versões** (`scaffold.py versions tauri`, 2026-11-08): tauri 2.12.5 (crates), tauri-build 2.7.4 (crates), @tauri-apps/cli 2.12.4 (npm), @tauri-apps/api 2.12.4 (npm), vite 8.3.6 (npm), typescript 7.0.2 (npm), vitest 5.1.0 (npm), @biomejs/biome 2.6.6 (npm). Nenhuma fora da série testada.
- **Cache `.specs/stack/` (Context7 real, Fetched 2026-11-08)**: `tauri.md` (2.12.5), `tauri-apps-cli.md` (2.12.4), `tauri-apps-api.md` (2.12.4), todas com `/tauri-apps/tauri-docs`; `vite.md` (`/vitejs/vite`, 8.3.6), `typescript.md` (`/microsoft/typescript`, 7.0.2), `vitest.md` (`/vitest-dev/vitest`, 5.1.0). `Doc version`: `desconhecida`.
- **`new`** com a pasta contendo só `.specs/stack/`: exit 0, `template: tauri`.
- **Gates** (`scaffold.py gates`, exit 0):
  - `PASS npm install`
  - `PASS npx biome check .`
  - `PASS cargo fmt --check [src-tauri]`
  - `PASS cargo clippy --all-targets -- -D warnings [src-tauri]`
  - `PASS npx tsc --noEmit`
  - `PASS npx vitest run`
  - `PASS cargo test [src-tauri]`
  - `PASS npm run tauri build -- --debug --no-bundle`
- **Commit inicial**: `5c855b3` `chore: projeto inicial (tauri)`, sem remoto; as 6 entradas do cache entram no commit.

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

- `docker ps -a --format '{{.Names}}'` no fim de todos os cenários (2026-11-08, repetido depois da refação dos cenários 1 e 2): só `orcamento-pg`, que já existia e é de outro projeto; zero contêineres `starcode-eph-*` (`--filter name=starcode-eph` devolveu 0 linhas).
- Os gates de banco (`ephemeral_db.py run postgresql` e `run mysql`) passaram e não deixaram contêiner.

## Achados e pendências

1. **Corrigido (`bb5a320`)**: `scaffold.py new` recusava a pasta com o cache (`pasta não vazia`). Agora aceita a pasta que contém só `.specs/`; qualquer outro conteúdo continua recusado com exit 2, e uma falha do `new` não apaga o `.specs/` que já existia.
2. **Corrigido (`bb5a320`)**: o `biome.json` dos perfis `tauri` e `typescript` agora exclui `.specs`; o gate `npx biome check .` passa com o cache presente.
3. **Corrigido (`9534c36`)**: `Doc version` fica sempre `desconhecida` (os IDs do perfil não têm versão e o Context7 não informa a versão dos docs). `stack_cache.py check` agora julga a entrada só pela idade e pela versão do manifesto e mostra `ok (doc sem versão)` (exit 0) logo após o `write` (R27 emendado).
4. **Corrigido (`cfa0307`)**: o `biome.json` dos perfis `tauri` e `typescript` usava `linter.rules.recommended`, obsoleto no Biome 2.6; agora usa `linter.rules.preset: "recommended"`, mesmo conjunto de regras, e os gates reais passam.
5. **Limpeza**: as pastas em `F:/Projetos/starcode-missoes/` (`flask-pg-aceite`, `tauri-aceite`, `aceite-*`, `serie-fora`, `fixtures`) ficam para o usuário. Só `flask-pg-aceite` e `tauri-aceite` são repositórios git (commit inicial, sem remoto).
