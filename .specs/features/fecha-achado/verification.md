# fecha-achado verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 61d7980
**HEAD**: 7636563
**Verifier**: codex · requested cli-default · effective GPT-6.1 Terra medium (terminal)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_fecha_achado.py` `test_close_finding_grava` | yes |
| C2 | `tests/test_fecha_achado.py` `test_close_finding_recusa` | no - não exercita fallback para spec nem texto de definição dentro de string e só verifica uma linha malformada com células a mais. |
| C3 | `tests/test_fecha_achado.py` `test_close_finding_preserva_bytes` | yes |
| C4 | `tests/test_fecha_achado.py` `test_done_exige_cobertura` | no - não verifica a regra com checks vindos da spec sem tasks nem rejeita definição aparente dentro de string. |
| C5 | `tests/test_fecha_achado.py` `test_done_acusa_celulas` | no - em Checks testa apenas células a mais e filtra os erros, sem provar ausência de erro de commit nem células a menos; não testa linha sem pipe inicial. |
| C6 | `tests/test_fecha_achado.py` `test_textos_close_finding` | yes |
| C7 | `tests/test_fecha_achado.py` `test_decisions_fecha_achado` | no - exige palavras isoladas na Decisão, sem assegurar que descrevam a regra de cobertura e o erro de células. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R2 e R4: uma definição aparente dentro de string é aceita como teste existente, fechando achado sem cobertura real. | `$env:PYTHONDONTWRITEBYTECODE='1'; python -c "import sys; sys.path[:0]=['tests','scripts','scripts/gates']; from test_fecha_achado import FechaAchadoTests,cli,run_git; t=FechaAchadoTests(); t.setUp(); p=t.repo/'tests'/'doc.py'; p.write_text('texto = '+chr(39)*3+chr(10)+'    def test_fantasma():'+chr(10)+chr(39)*3); run_git(t.repo,'add','tests/doc.py'); run_git(t.repo,'commit','-qm','doc'); print('exit:',cli(t.repo,'1','--commit',t.sha,'--cover','test_fantasma')[0]); t.tearDown()"` → `exit: 0` | Identificar definições Python reais no conteúdo do HEAD, excluindo strings e comentários, e testar os dois chamadores. | adb7fad · test_cobertura_le_ast |
| R5: uma linha Markdown sem pipe inicial é ignorada, mesmo com células a mais; o gate não informa o erro exigido. | `$env:PYTHONDONTWRITEBYTECODE='1'; python -c "import sys; sys.path[:0]=['tests','scripts','scripts/gates']; from test_fecha_achado import FechaAchadoTests,HEADER; t=FechaAchadoTests(); t.setUp(); p=chr(124); row=p+' A '+p+' e '+p+' f '+p+' '+t.sha[:7]+' · C1 '+p+chr(10); bad='B '+p+' e '+p+' f '+p+' x '+p+' extra'; r=t.done(HEADER+row+bad+chr(10)); print('erros:',r.errors); t.tearDown()"` → ``erros: ['falta proofs.md: rode `run_gates.py proofs <feature>` (check_proofs.py)']`` | Reconhecer linhas de tabela sem pipe inicial e validar seu número de células em Checks e Findings. | adb7fad · test_done_acusa_celulas |
| C2 e C4 deixam sem prova a seleção de checks da spec quando tasks.md não existe; a mesma validação compartilhada pode falhar silenciosamente nos dois chamadores. | `tests/test_fecha_achado.py:39` | Testar os dois chamadores sem tasks.md, aceitando check da spec e recusando check inexistente. | adb7fad · test_cobertura_sem_tasks |
| C5 não prova células a menos na tabela Checks e filtra erros nessa tabela, permitindo que erros adicionais passem. | `tests/test_fecha_achado.py:152` | Verificar a lista completa de erros para linhas com células a mais e a menos em ambas as tabelas. | adb7fad · test_done_acusa_celulas |
| C7 aceita termos desconexos na Decisão, sem provar o significado da regra de cobertura nem do erro de células. | `tests/test_fecha_achado.py:175` | Verificar os enunciados necessários dos requisitos na seção Decisão. | adb7fad · test_decisions_fecha_achado |

## Limits

Regressão em 7636563: `python -m unittest discover -s tests -v` terminou com 1.003 testes, `OK (skipped=1)`, em 555,234 s.
O nome do teste de C3 está truncado na tabela de `proofs.md`; o teste correspondente foi identificado na spec e inspecionado.
