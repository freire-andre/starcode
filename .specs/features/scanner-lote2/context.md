# Scanner de segredos: heredoc, gh e falsos positivos: Context

**Size**: MEDIUM
**Risk triggers**: Segurança (o scanner decide o que bloqueia)
**Source request**: "proximo passo" (lote 2 da triagem v2; divisão escolhida: "Por hook, 2 missões (Recomendado)"; esta é a do scanner: 2.4, 2.6 e a parte do 2.2 que deixa heredoc sem scan)

## Problem
Reproduzido em `main` (647934b):
- **2.2:** `tokenize` (de `hooks/scripts/git_guard.py`) quebra o heredoc em segmentos soltos. Com isso, `gh pr create --body "$(cat <<'EOF' ... EOF)"` com um token do GitHub no corpo passa sem achado. O mesmo vale para `git commit -m "$(cat <<'EOF' ...)"`.
- **2.4:** `gh issue create|comment|edit` e `gh pr review` com segredo no `--body` passam (`hooks/scripts/secret_scan.py:328` só cobre `gh pr create|edit|comment`).
- **2.6:** quatro falsos positivos:
  - `postgresql://postgres:postgres@localhost` → string de conexão;
  - `postgres://user:${DB_PASSWORD}@db` → string de conexão;
  - `AUTHOR_EMAIL=dev2024.bot@empresa.com.br` → alta entropia, porque `AUTH` casa dentro de `AUTHOR`;
  - `token_url = "https://auth.example.com/oauth2/token"` → alta entropia.

## Scope Notes
- Entra: 2.2 (só o scan), 2.4 e 2.6.
- Fica para a missão do `git_guard`: a parte do 2.2 sobre o bloqueio falso de heredoc com `git reset --hard`, e o 2.5.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Divisão do lote 2 | por hook / lote inteiro / um por missão | "Por hook, 2 missões (Recomendado)" | 2026-11-18 |
| Como escanear o heredoc | quando o comando tem um segmento que publica texto (`git commit`, `gh` coberto, `orca linear` coberto), o texto **inteiro** do comando é escaneado, não só os argumentos do segmento | default (não perguntado) |  |
| Comandos `gh` novos | `gh issue create`, `gh issue comment`, `gh issue edit`, `gh pr review`, com os mesmos `--body-file`/`-F` | default (não perguntado) |  |
| String de conexão aceita | senha que é placeholder (`${...}`, `$VAR`, `<...>`) ou host local (`localhost`, `127.0.0.1`, `::1`) | default (não perguntado) |  |
| `AUTH` na chave | casa `AUTH` só como parte inteira do nome (`AUTH`, `AUTH_TOKEN`, `OAUTH`, `X_AUTH`), não `AUTHOR` | default (não perguntado) |  |
| URL como valor | valor que é URL `http(s)://` sem `usuário:senha@` não é segredo de alta entropia | default (não perguntado) |  |

## Facts Found
- `hooks/scripts/secret_scan.py:297-331`: `evaluate`, com os ramos `git commit`, `orca linear` e `gh pr`; `:334-352`: `_body_files`.
- `:37-53`: `PATTERNS`, `ASSIGNMENT` e `PLACEHOLDER`.
- `tests/test_secret_scan.py`: `FAKE` (`:14`), `LOOKALIKES` (`:25`) e as classes `ScanTextTests` (`:40`) e `TextTargetsTests` (`:398`).
