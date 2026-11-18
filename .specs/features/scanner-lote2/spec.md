# Scanner de segredos: heredoc, gh e falsos positivos: Spec

**Approved**: 2026-11-18 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: Segurança (o scanner decide o que bloqueia)
**Status**: Approved
**Linear**: SC-195
**May change**: hooks/scripts/secret_scan.py, tests/test_secret_scan.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Esta spec cobre os itens 2.2 (só o scan), 2.4 e 2.6 da triagem v2. O discovery está em `.specs/features/scanner-lote2/context.md`. Todos os casos abaixo foram reproduzidos na `main`, em 647934b:
- **2.2:** um corpo em heredoc passa sem scan, tanto em `gh pr create --body "$(cat <<'EOF' ...)"` quanto em `git commit -m "$(cat <<'EOF' ...)"`.
- **2.4:** `gh issue create|comment|edit` e `gh pr review` não são escaneados.
- **2.6:** quatro textos sem segredo são bloqueados.

## Scope
- Comando que publica texto: o scanner escaneia o texto inteiro do comando.
- `gh issue create|comment|edit` e `gh pr review` passam a ser alvos do scan.
- Os quatro falsos positivos deixam de bloquear.

## Non-Goals
- O bloqueio falso do `git_guard` com heredoc e o 2.5: ficam para a próxima missão.
- Outros comandos `gh` que publicam texto, como `release`, `gist` e `api`.
- Mudar os padrões que hoje encontram as fixtures `FAKE`.

## Decisions
| Item | Options | User answer |
|---|---|---|
| Divisão do lote 2 | por hook (scanner agora, `git_guard` depois) / lote inteiro / um item por missão | approved - user: "Por hook, 2 missões (Recomendado)" |

## Requirements
- **R1** - WHEN o comando tem um segmento que publica texto (`git commit`, `gh pr create|edit|comment|review`, `gh issue create|comment|edit` ou `orca linear` nos casos de hoje) THEN o scanner SHALL escanear o texto inteiro do comando, inclusive o corpo de heredoc. Um token do GitHub no corpo heredoc de `gh pr create` e de `git commit -m` SHALL ser negado.
- **R2** - WHEN o comando é `gh issue create`, `gh issue comment`, `gh issue edit` ou `gh pr review` THEN o scanner SHALL escanear o texto e os arquivos de `--body-file`/`-F`, como já faz com `gh pr create`. Um segredo `FAKE` no `--body` ou no arquivo SHALL ser negado.
- **R3** - IF uma string de conexão tem senha placeholder (`${...}`, `$NOME`, `<...>`) ou host local (`localhost`, `127.0.0.1`, `::1`) THEN o scanner SHALL não acusá-la. `postgresql://postgres:postgres@localhost` e `postgres://user:${DB_PASSWORD}@db` SHALL passar, e a fixture `FAKE["dsn"]` (host `db.internal`) SHALL continuar sendo encontrada.
- **R4** - The system SHALL tratar `AUTH` no nome da chave de atribuição só como parte inteira do nome, separada por `_` ou na borda: `AUTH`, `AUTH_TOKEN`, `OAUTH`, `X_AUTH`. `AUTHOR_EMAIL=dev2024.bot@empresa.com.br` SHALL passar.
- **R5** - IF o valor de uma atribuição é uma URL `http://` ou `https://` sem `usuário:senha@` THEN o scanner SHALL não acusá-lo como alta entropia. `token_url = "https://auth.example.com/oauth2/token"` SHALL passar.
- **R6** - The system SHALL continuar encontrando todas as fixtures `FAKE` e deixando passar todos os `LOOKALIKES` de `tests/test_secret_scan.py`. Os quatro exemplos de R3 a R5 SHALL entrar em `LOOKALIKES`.
- **R7** - The system SHALL ter no `DECISIONS.md` a entrada da issue desta feature (`### SC-195:`) com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**. A **Decisão** SHALL trazer R1 a R6 em frase: texto inteiro do comando, os quatro comandos `gh` novos, placeholder e host local, `AUTH` como parte inteira e URL sem credencial. O **Por que não é bug** SHALL citar os testes. SHALL ter também uma linha em `CHANGELOG.md` `[Unreleased]`.

## Edge Cases
- Comando sem segmento que publica texto (ex.: `cat <<EOF > notas.md`): não é escaneado (R1).
- URL com credencial (`https://user:s3cr3tpass@host`) continua sendo acusada como string de conexão (R5, C5).
- `localhost` com segredo de padrão conhecido (ex.: token do GitHub como senha) continua acusado pelo padrão do token (R3).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Token no corpo heredoc de `gh pr create` e de `git commit -m` é negado; `cat <<EOF > notas.md` com token não é alvo (R1)
Proof: run unit | test_heredoc_de_comando_que_publica_e_escaneado (test_secret_scan.TextTargetsTests.test_heredoc_de_comando_que_publica_e_escaneado) ... ok

**C2** - Os quatro comandos `gh` novos são negados com segredo no `--body` e no `--body-file`; sem segredo, passam (R2)
Proof: run unit | test_gh_issue_e_pr_review_sao_escaneados (test_secret_scan.TextTargetsTests.test_gh_issue_e_pr_review_sao_escaneados) ... ok

**C3** - Strings de conexão com placeholder e com host local passam, e `FAKE["dsn"]` continua encontrada (R3)
Proof: run unit | test_conexao_placeholder_e_local_passam (test_secret_scan.ScanTextTests.test_conexao_placeholder_e_local_passam) ... ok

**C4** - `AUTHOR_EMAIL` passa, e `AUTH_TOKEN`, `OAUTH_SECRET` e `X_AUTH` com valor de alta entropia continuam acusados (R4)
Proof: run unit | test_auth_so_como_parte_inteira (test_secret_scan.ScanTextTests.test_auth_so_como_parte_inteira) ... ok

**C5** - URL sem credencial como valor passa; URL com `usuário:senha@` continua acusada (R5)
Proof: run unit | test_url_sem_credencial_passa (test_secret_scan.ScanTextTests.test_url_sem_credencial_passa) ... ok

**C6** - Fixtures `FAKE` encontradas e `LOOKALIKES` (com os quatro novos) sem achado (R6)
Proof: run unit | test_lookalikes_pass (test_secret_scan.ScanTextTests.test_lookalikes_pass) ... ok
Proof: run unit | test_each_fake_secret_is_found (test_secret_scan.ScanTextTests.test_each_fake_secret_is_found) ... ok

**C7** - Entrada do `DECISIONS.md` com os quatro campos, R1 a R6 em frase na Decisão, testes citados e linha no CHANGELOG (R7)
Proof: run unit | test_decisions_scanner_lote2 (test_secret_scan.ScanTextTests.test_decisions_scanner_lote2) ... ok

## Handoff

**Phase:** execute
**Size:** MÉDIA
**Git mode:** 3
**Next:** LaForge implementa T1 (SC-195)
**Linear:** SC-195
**Integration branch:** feature/scanner-lote2
**Last integrated:** 964728e4ce61b287f7b266b041bd66d8fc03cb28
**Dispatched:** none
**Settled:** 2026-11-18: spec + issue: "sim"
**Attempts:** none
**Reports:** 2026-11-18: T1: 655eb53 (R1–R7); test_secret_scan 51 OK; ticket gate verde; worker não rodou a suíte inteira (as provas rodam)
**Breaker:** closed
