# piloto-decisao-citada verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 514729d
**HEAD**: b003660
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_piloto.py` `test_gates_leem_piloto_pelo_piloto_py` | yes |
| C2 | `tests/test_piloto.py` `test_aprovacao_com_decisao_registrada_passa_nos_dois_gates` | yes |
| C3 | `tests/test_piloto.py` `test_decisao_inexistente_reprova_nos_dois_gates` | yes |
| C4 | `tests/test_piloto.py` `test_spec_recusa_piloto_com_decisao_registrada` | yes |
| C5 | `tests/test_piloto.py` `test_mandato_sem_user_nao_vale` | yes |
| C6 | `tests/test_piloto.py` `test_sem_piloto_md_reprova_sem_excecao` | yes |
| C7 | `tests/test_piloto.py` `test_d07_cita_d7` | yes |
| C8 | `tests/test_piloto.py` `test_uma_linha_valida_basta` | yes |
| C9 | `tests/test_piloto.py` `test_decisions_piloto_decisao_citada` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Um ID numérico longo aceito pela regex causa exceção não tratada durante `int()`, podendo interromper os gates em vez de produzir uma recusa. | `scripts/gates/gates_common.py:200`; `python -c 'from scripts.gates.gates_common import pilot_cited; s="9"*5000; print(pilot_cited(["**Approved**: 2026-11-14 - piloto: "+chr(34)+"D"+s+" x"+chr(34)]))'` e saída literal: `Traceback (most recent call last):`<br>`  File "<string>", line 1, in <module>`<br>`    from scripts.gates.gates_common import pilot_cited; s="9"*5000; print(pilot_cited(["**Approved**: 2026-11-14 - piloto: "+chr(34)+"D"+s+" x"+chr(34)]))`<br>`                                                                          ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^`<br>`  File "C:\Users\freir\orca\workspaces\StarCode\piloto-decisao-citada\scripts\gates\gates_common.py", line 200, in pilot_cited`<br>`    return [int(m.group(1)) for m in (PILOT_APPROVED_RE.match(ln.strip()) for ln in lines) if m]`<br>`            ~~~^^^^^^^^^^^^`<br>`ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit` | Limitar/rejeitar o comprimento do ID antes da conversão e garantir que a entrada inválida vire erro de aprovação, não traceback. | |
| C3 não verifica igualdade com a mensagem exigida: `assertIn(MSG_D4, errors)` aceita mensagem com texto adicional ou divergente depois do trecho esperado. | `tests/test_piloto.py:204` | Comparar a lista/valor integral esperado em ambos os gates. | |
| C6 verifica apenas o prefixo da mensagem exigida (`startswith(SEM_APPROVED)`), permitindo que o restante da mensagem difira do texto atual especificado. | `tests/test_piloto.py:231` | Comparar a mensagem integral esperada em ambos os gates. | |

## Limits

- A regressão exigida foi executada no HEAD b003660: `python -m unittest discover -s tests -v 2>&1` — `Ran 844 tests in 1052.482s`, `OK (skipped=1)`; não houve testes falhos.
- `proofs.md` registra HEAD 514729d, diferente do HEAD b003660 verificado aqui; reexecutei a suíte completa no HEAD atual conforme exigido, mas não revalidei os comandos de build registrados nas provas.