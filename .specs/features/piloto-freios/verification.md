# piloto-freios verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at b6cc208
**HEAD**: 6d251b4
**Verifier**: codex · requested cli-default · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_piloto.py` `test_aprovacao_vale_depois_de_encerrar` | yes |
| C2 | `tests/test_piloto.py` `test_decisao_depois_do_encerramento_reprova` | yes |
| C3 | `tests/test_piloto.py` `test_mandato_sem_user_reprova_ativo_e_encerrado` | yes |
| C4 | `tests/test_piloto.py` `test_freio_na_terceira_revisar` | yes |
| C5 | `tests/test_piloto.py` `test_segunda_revisar_segue` | yes |
| C6 | `tests/test_piloto.py` `test_freio_fica_e_alta_segue` | no - não verifica a gravação das decisões alta e média. |
| C7 | `tests/test_piloto.py` `test_devolvido_ao_usuario_fora_do_freio` | no - após o freio, não verifica que D4 foi gravada. |
| C8 | `tests/test_piloto.py` `test_categoria_exige_mandato` | no - não testa a decisão devolvida com categoria sem mandato, que é aceita. |
| C9 | `tests/test_piloto.py` `test_categoria_invalida_sai_2` | yes |
| C10 | `tests/test_piloto.py` `test_skill_descreve_freio_e_categoria` | yes |
| C11 | `tests/test_piloto.py` `test_decisions_piloto_freios` | no - verifica nomes de seções e marcadores, sem exigir os termos de R10 na Decisão. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R8 é violado: decisão devolvida com categoria e sem item de mandato é gravada com exit 0; a exceção para `returned` não tem cobertura. | `$env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONIOENCODING='utf-8'; python -c "import sys; sys.path.insert(0,'tests'); from test_piloto import PilotFreiosTests; t=PilotFreiosTests(); t.setUp(); t.confirmed(); r=t.reg('devolvido ao usuário','','--categoria','esquema'); print('exit:',r.returncode); print('stdout:',r.stdout.strip()); print('stderr:',r.stderr.strip()); t.tearDown()"` → `exit: 0`<br>`stdout: D1 registrada (confiança baixa)`<br>`stderr:` | Aplicar R8 também a essa combinação e testá-la, ou resolver explicitamente o conflito de requisitos. | |
| C6 aceita sucesso impresso sem persistência das decisões alta e média. | `tests/test_piloto.py:529` | Conferir no arquivo as entradas D3 e D4, com confiança e conteúdo. | |
| C7 aceita sucesso impresso sem gravar a devolução após o freio. | `tests/test_piloto.py:548` | Conferir a entrada D4 completa no arquivo e a ausência da marca. | |
| C11 aceita uma Decisão que mencione seções 4, 5 e 7 e R10 sem descrever o conteúdo exigido de R10. | `tests/test_piloto.py:619` | Exigir na seção Decisão os elementos concretos de R10, inclusive freio, categoria e critério do gate. | |

## Limits

Regressão completa em HEAD: `python -m unittest discover -s tests -v`, exit 0; 949 testes em 468,752 s, OK, 1 ignorado.
Exemplo adicional de R6: `$env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONIOENCODING='utf-8'; python -c "import sys; sys.path.insert(0,'tests'); from test_piloto import PilotFreiosTests; t=PilotFreiosTests(); t.setUp(); t.confirmed(); [t.reg() for _ in range(2)]; r=t.reg('outra','Q77','--confidence','media'); print('exit:',r.returncode); print('stdout:',r.stdout.strip()); print('stderr:',r.stderr.strip()); t.tearDown()"` imprimiu `exit: 0`, `stdout: D3 registrada (confiança média)` e `stderr:`.
