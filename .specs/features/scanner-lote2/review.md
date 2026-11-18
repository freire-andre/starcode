**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
O PR cobre o corpo em heredoc e os comandos `gh` novos, como pede a spec. As isenções de host local resistem aos contornos testados.

Mas três isenções deixam passar segredos que a `main` bloqueava:
- **W1:** uma senha que começa com `$` é tratada como placeholder. Isso vai além da spec, que pede só `$NOME`.
- **W2:** qualquer URL sem `usuário:senha@` fica isenta, inclusive um webhook com token no caminho.
- **W3:** `AUTHORIZATION` deixou de ser chave de segredo.

W2 e W3 seguem o texto aprovado de R5 e R4, mas esse efeito não foi previsto. Estreitar as duas regras é decisão do usuário.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | `hooks/scripts/secret_scan.py:54` | `CONN_PLACEHOLDER` aceita qualquer `$` seguido de caractere de palavra, minúsculo inclusive. uma string de conexão com host `db.internal` e senha `$ecretPassw0rd9` passa neste ramo e é acusada na `main`. A spec pede `$NOME`, e o `PLACEHOLDER` que já existe usa `$[A-Z_]+`. Sugestão: `$[A-Z_][A-Z0-9_]*`, sem `re.I`, e um teste com essa senha acusada. | `hooks/scripts/secret_scan.py:54` | open |
| W2 | 🟠 should-fix | `hooks/scripts/secret_scan.py:128` | A isenção de R5 pula qualquer `https://` sem `usuário:senha@`, mesmo quando o próprio caminho é o segredo. `SLACK_WEBHOOK_TOKEN=` com uma URL `hooks.slack.com/services/...` cujo último segmento é um token de 24 caracteres passa neste ramo e é acusada na `main`; o mesmo vale para webhook do Discord. Sugestão (decisão do usuário): isentar só quando nenhum segmento do caminho ou da query passa sozinho na regra de alta entropia. Assim `oauth2/token` continua passando. | `hooks/scripts/secret_scan.py:128` | open |
| W3 | 🟡 nit | `hooks/scripts/secret_scan.py:51` | Com `AUTH` só como parte inteira, `AUTHOR_EMAIL` passa, mas `AUTHORIZATION=eyJhbGciOi...` também deixou de ser acusada, e a `main` acusava. Isso foi intencional? Se não, basta acrescentar `AUTHORIZATION` à lista de chaves. | `hooks/scripts/secret_scan.py:51` | open |

## Escada determinística
- `python tools/build.py --check`: OK, `dist/` em dia.
- `python scripts/check_decisions.py`: OK.
- `claude plugin validate dist/claude --strict`: Validation passed.
- Suíte inteira nas provas: 972 OK.
- `scan_bypasses.py`: 0 candidatos.
- Sondagem manual:
  - 10 contornos de host local foram acusados;
  - 4 entradas que a `main` bloqueava passam neste ramo (W1, W2, W3).

## Pesquisa
Nenhuma superfície externa: o código usa só a biblioteca padrão (`re`, `urllib`) e o próprio hook.
