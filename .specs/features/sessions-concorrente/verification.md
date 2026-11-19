# sessions-concorrente verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 4e9283c
**HEAD**: 57d81d5
**Verifier**: codex · requested cli-default · effective GPT-6.1 Terra medium (terminal)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_sessions_concorrente.py` `test_locked_e_escrita_atomica` | no - não testa as cinco novas tentativas nem a limpeza após falha definitiva de replace. |
| C2 | `tests/test_sessions_concorrente.py` `test_update_sessions_paralelo` | yes |
| C3 | `tests/test_sessions_concorrente.py` `test_set_progress_paralelo` | yes |
| C4 | `tests/test_sessions_concorrente.py` `test_update_session_paralelo` | no - não confere as 64 chaves após as gravações concorrentes de write_session. |
| C5 | `tests/test_sessions_concorrente.py` `test_trava_esgotada` | yes |
| C6 | `tests/test_sessions_concorrente.py` `test_decisions_sessions_concorrente` | no - verifica 16 e 64, mas não os números de perda e falha da reprodução. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| write_session apaga chaves de leituras concorrentes defasadas; os 16 processos concluíram, mas restaram 4 das 64 chaves. | `python -c "import sys,tempfile,subprocess; sys.path[:0]=['scripts','tests']; import test_sessions_concorrente as t, starcode_common as s; d=tempfile.TemporaryDirectory(); subprocess.run(['git','init','-q',d.name],check=True); codes=t._run_parallel(t._w_write_session,lambda keys:(d.name,keys)); print('exitcodes:',codes); print('keys:',len(s.read_session(d.name)))"`<br>Saída literal: `exitcodes: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`<br>`keys: 4` | Fazer a leitura e a mutação ocorrerem juntas sob a trava e testar as 64 chaves por write_session. | |
| C1 aceita implementação com menos de cinco novas tentativas ou que deixa temporário após falha definitiva de replace. | `tests/test_sessions_concorrente.py:141` | Testar sucesso na sexta tentativa e falha na sexta, incluindo conteúdo anterior e ausência do temporário. | |
| C6 aceita decisão sem os números de perdas e de falhas que integram a reprodução do requisito. | `tests/test_sessions_concorrente.py:250` | Verificar os números da reprodução na seção Problema. | |
| A regra de timeout em authorize-merge e revoke-merge pode falhar sem que C5 detecte: o teste só exercita git_mode set. | `tests/test_sessions_concorrente.py:226` | Exercitar os dois comandos com a trava presa e conferir saída, código e bytes intactos. | |

## Limits

Regressão completa `python -m unittest discover -s tests -v`: 1025 testes em 597,188 s, OK, 1 omitido (`test_restore_yes_devolve_bit_executavel`: bit executável não existe no Windows).

O teste específico `python -m unittest discover -s tests -p test_sessions_concorrente.py -v` passou: 6 testes.

Sonda adicional R2: `python -c "import sys,tempfile,json; from pathlib import Path; sys.path.insert(0,'scripts'); import crew_live as c; d=tempfile.TemporaryDirectory(); p=Path(d.name); (p/'sessions.json').write_text('{',encoding='utf-8'); exec('try:\n c.update_sessions(p, [], lambda x: None, strict=True)\nexcept Exception as e:\n print(type(e).__name__)'); print((p/'sessions.json').read_text(encoding='utf-8'))"` imprimiu `JSONDecodeError` e `{`; o conteúdo inválido foi preservado.

Windows executado com processos reais; POSIX não executado neste ambiente. Na documentação oficial, [msvcrt.locking](https://docs.python.org/3/library/msvcrt.html#msvcrt.locking) bloqueia a partir da posição corrente e LK_NBLCK falha imediatamente; o código posiciona no byte 0 e bloqueia 1 byte. [fcntl.flock](https://docs.python.org/3/library/fcntl.html#fcntl.flock) aceita LOCK_EX e LOCK_NB; o código os combina.
