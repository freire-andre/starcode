# scanner-lote2 verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 964728e
**HEAD**: 44b7704
**Verifier**: codex · requested cli-default · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_secret_scan.py` `test_heredoc_de_comando_que_publica_e_escaneado` | yes |
| C2 | `tests/test_secret_scan.py` `test_gh_issue_e_pr_review_sao_escaneados` | no - aceita qualquer achado, inclusive aviso de arquivo grande, como prova de detecção. |
| C3 | `tests/test_secret_scan.py` `test_conexao_placeholder_e_local_passam` | yes |
| C4 | `tests/test_secret_scan.py` `test_auth_so_como_parte_inteira` | yes |
| C5 | `tests/test_secret_scan.py` `test_url_sem_credencial_passa` | no - aceita qualquer achado na URL com credencial, sem exigir string de conexão. |
| C6 | `tests/test_secret_scan.py` `test_lookalikes_pass`, `test_each_fake_secret_is_found` | no - não exige que os quatro exemplos permaneçam em LOOKALIKES. |
| C7 | `tests/test_secret_scan.py` `test_decisions_scanner_lote2` | no - termos isolados não asseguram as afirmações de R1 a R6 na Decisão. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| String de conexão com host remoto é tratada como local e sua senha deixa de ser detectada quando o usuário inclui `@localhost:5432` na senha. | `@'`<br>`import sys`<br>`from urllib.parse import urlsplit`<br>`sys.path.insert(0, 'hooks/scripts')`<br>`import secret_scan as s`<br>`value = 'postgres://u:hunter22@localhost:5432@evil.com/db'`<br>`print('host:', urlsplit(value).hostname)`<br>`print('findings:', [item[1] for item in s.scan_text(value, s.Allowlist(None))])`<br>`'@ \| python -`<br>Saída literal: `host: evil.com`<br>`findings: []` | Identificar corretamente a autoridade e comparar o host completo antes de dispensar a string. | |
| URL com usuário mas sem par usuário:senha é acusada como alta entropia, contrariando R5. | `@'`<br>`import sys`<br>`sys.path.insert(0, 'hooks/scripts')`<br>`import secret_scan as s`<br>`a = s.Allowlist(None)`<br>`for value in ['postgres://u:hunter22@::1evil.example/db', 'TOKEN_URL=https://alice@auth.example.com/oauth2/token']:`<br>`    print(value, [item[1] for item in s.scan_text(value, a)])`<br>`'@ \| python -`<br>Saída literal: `TOKEN_URL=https://alice@auth.example.com/oauth2/token ['valor de alta entropia em TOKEN_URL']` | Reconhecer somente um par usuário:senha na autoridade como credencial para essa exceção. | |
| C2 aceita qualquer lista não vazia como detecção, inclusive aviso de arquivo grande; não comprova o segredo nem sua origem. | `tests/test_secret_scan.py:469` | Comparar os achados esperados, com tipo e origem, para cada comando e opção. | |
| C5 aceita alta entropia ou outro achado em vez da string de conexão exigida para URL com credencial. | `tests/test_secret_scan.py:78` | Exigir o tipo exato `string de conexão com senha`. | |
| C6 passa se os quatro exemplos forem removidos de LOOKALIKES. | `tests/test_secret_scan.py:53` | Exigir explicitamente a presença dos quatro exemplos e seu resultado vazio. | |
| C7 aceita termos soltos sem afirmar o comportamento dos requisitos, e não exige os termos das fixtures FAKE e LOOKALIKES na Decisão. | `tests/test_secret_scan.py:85` | Verificar na seção Decisão cada afirmação concreta de R1 a R6 e os testes citados. | |

## Limits

Regressão em `44b7704`: `python -m unittest discover -s tests -v` terminou com exit 0, 972 testes em 980,313 s e um ignorado: `test_restore_yes_devolve_bit_executavel` (bit executável indisponível no Windows).
