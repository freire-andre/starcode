# verificacao-1-8-0 verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 222a2cb
**HEAD**: a224ad5
**Verifier**: codex · requested cli-default · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_piloto.py` `test_start_is_idempotent_and_fixed_format` | no - não compara o arquivo antes e depois da segunda chamada. |
| C2 | `tests/test_piloto.py` `test_mandate_numbered_and_locked_after_confirm` | no - não compara os bytes após a recusa nem testa o exit 1. |
| C3 | `tests/test_piloto.py` `test_no_decision_before_confirmed_mandate`, `test_finish_stops_decisions`, `test_registrar_exige_mandato_com_user` | no - os dois primeiros não verificam ausência de escrita ou exit 1. |
| C4 | `tests/test_piloto.py` `test_record_decisions_confidence_and_review` | no - aceita status sem `⚠️ revisar` e não testa baixa com base. |
| C5 | `tests/test_piloto.py` `test_cli_exit_codes` | no - não testa erro de uso 2 nem feature e piloto ausentes. |
| C6 | `tests/test_piloto.py` `test_banner_shows_active_autopilot` | no - não testa exit de `ativo` nem os estados negativos. |
| C7 | `tests/test_piloto.py` `test_aprovacao_com_decisao_registrada_passa_nos_dois_gates`, `test_d07_cita_d7`, `test_uma_linha_valida_basta` | yes |
| C8 | `tests/test_piloto.py` `test_decisao_inexistente_reprova_nos_dois_gates`, `test_sem_piloto_md_reprova_sem_excecao`, `test_mandato_sem_user_nao_vale`, `test_spec_recusa_piloto_com_decisao_registrada` | no - não exercita piloto inativo nos dois gates. |
| C9 | `tests/test_model_info.py` `test_tier_by_output_price` | no - não testa preços exatos 0, 2 e 12, ausência de preço ou sufixo `-free` independente de preço zero. |
| C10 | `tests/test_model_info.py` `test_fit_vetoes_and_warnings` | no - omite contexto em execução, raciocínio em pesado e faixa grátis em pesado; compara fragmentos. |
| C11 | `tests/test_model_info.py` `test_cache_fresh_stale_and_no_fetch`, `test_cli_exit_codes` | no - não testa exit 2, limite de sete dias ou falha de rede sem cache; mocka a falha de download no caso com cache. |
| C12 | `tests/test_model_info.py` `test_opencode_provider_models_get_a_family`, `test_q_cli_accepts_opencode_model_of_other_family`, `test_without_catalog_stays_unknown` | yes |
| C13 | `tests/test_model_info.py` `test_precedence_local_over_user_over_default`, `test_local_schema_only_crew`, `test_banner_and_crew_table_show_local` | no - precedência do usuário é verificada só pela origem, não pelos valores efetivos. |
| C14 | `tests/test_piloto.py` `test_piloto_skill_rules`, `test_troi_grill_mode` | no - não exige a marca de revisão nem vincula os termos de push, PR, merge e deploy à reserva ao usuário. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Status de decisão baixa omite `⚠️ revisar`, exigido por R4. | `python -B -c "import sys,tempfile; from pathlib import Path; sys.path.insert(0,'scripts'); import piloto as p; t=tempfile.TemporaryDirectory(); r=Path(t.name); (r/'.specs/features/exemplo').mkdir(parents=True); p.start('exemplo',r); p.add_mandate('exemplo',r,'limite','limite','Q1'); p.confirm('exemplo',r,'sim'); p.record('exemplo',r,'data','q','a','a','r','M1','baixa'); print(p.status('exemplo',r)[-1])"` → `Revisar: D1` | Incluir a marca no status e testar decisão baixa com e sem base. | |
| Contexto zero é inferior a 200k, mas não gera aviso de R10. | `python -B -c "import sys; sys.path.insert(0,'scripts'); import model_info as m; print(m.fit({'tool_call':True,'reasoning':True,'limit':{'context':1}}, '$$')['execucao']); print(m.fit({'tool_call':True,'reasoning':True,'limit':{'context':0}}, '$$')['execucao'])"` → `aviso: contexto de 0k, abaixo de 200k`<br>`ok` | Distinguir zero de contexto ausente e testar os dois papéis. | |
| A listagem usada pelo banner inclui piloto com mandato pendente, embora a regra implementada para `ativos` exija confirmação. | `python -B -c "import sys,tempfile; from pathlib import Path; sys.path.insert(0,'scripts'); import piloto as p; t=tempfile.TemporaryDirectory(); r=Path(t.name); (r/'.specs/features/exemplo').mkdir(parents=True); p.start('exemplo',r); print('ativo:',p.is_active('exemplo',r)); print('ativos:',p.actives(r))"` → `ativo: False`<br>`ativos: [('exemplo', 0, 0)]` | Filtrar a listagem pela mesma regra de mandato confirmado e cobrir o caso pendente no banner. | |
| C1 não demonstra idempotência do conteúdo. | `tests/test_piloto.py:37` | Comparar bytes antes e depois da segunda chamada. | |
| C2 e C3 não provam ausência de escrita após recusas e não cobrem todos os exits exigidos. | `tests/test_piloto.py:44` | Comparar bytes antes e depois e verificar exit 1 dos casos via CLI. | |
| C4 aceita saída sem a marca exigida e não cobre baixa com base. | `tests/test_piloto.py:62` | Verificar a saída integral e ambas as formas de decisão baixa. | |
| C5 e C6 não cobrem todos os códigos ou estados da CLI. | `tests/test_piloto.py:89` | Exercitar uso inválido, arquivos ausentes e `ativo` antes e depois da confirmação e encerramento. | |
| C8 não prova que ambos os gates recusam piloto encerrado. | `tests/test_piloto.py:199` | Executar ambos os gates com decisão registrada e piloto encerrado. | |
| C9 não verifica os limites nem todas as formas de preço ausente ou gratuito. | `tests/test_model_info.py:45` | Fixar resultados nos limites 0, 2 e 12, preço ausente e cada sufixo gratuito. | |
| C10 omite combinações de papel e condição e usa substrings. | `tests/test_model_info.py:57` | Verificar cada combinação exigida e o veredito completo. | |
| C11 omite exit 2, o limite de sete dias e a falha real sem rede nem cache. | `tests/test_model_info.py:68` | Testar uso inválido, as duas margens do limite e falha de rede com cache ausente. | |
| C13 não verifica os valores herdados da configuração do usuário. | `tests/test_model_info.py:269` | Comparar CLI e modelo efetivos para origem usuário e padrão. | |
| C14 verifica palavras isoladas e não testa a marca de revisão na skill. | `tests/test_piloto.py:308` | Verificar a regra completa de ações reservadas e a marca de decisões sem base. | |

## Limits

Regressão completa no HEAD: `python -m unittest discover -s tests` executou 936 testes em 452,755 s, sem falhas, com 1 ignorado.
