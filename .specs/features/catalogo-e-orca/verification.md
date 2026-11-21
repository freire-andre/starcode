# catalogo-e-orca verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 49a8163
**HEAD**: 1d9c3e8
**Verifier**: pending

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_catalogo_e_orca.py` `test_download_confere_forma` | yes |
| C2 | `tests/test_catalogo_e_orca.py` `test_texto_do_catalogo_limpo` | yes |
| C3 | `tests/test_catalogo_e_orca.py` `test_catalogo_lido_uma_vez` | yes |
| C4 | `tests/test_catalogo_e_orca.py` `test_orca_cli_run_e_env` | yes |
| C5 | `tests/test_catalogo_e_orca.py` `test_um_adaptador_da_orca` | no - procura texto e não detecta todas as chamadas proibidas ou referências inativas ao adaptador |
| C6 | `tests/test_catalogo_e_orca.py` `test_stack_orca_documentada` | no - palavras isoladas não comprovam os cinco comportamentos documentados |
| C7 | `tests/test_catalogo_e_orca.py` `test_decisions_e_changelog` | no - termos isolados não comprovam que a decisão descreve cada requisito |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R3: um arquivo JSON inválido é interpretado duas vezes para a mesma origem. | `python -c "import sys,tempfile,os; from unittest.mock import patch; sys.path.insert(0,'scripts'); import model_info as m; f=tempfile.NamedTemporaryFile(mode='w',encoding='utf-8'); f.write('{invalido'); f.flush(); os.environ['STARCODE_MODELS_DEV_FILE']=f.name; m._CATALOG.clear(); s=patch.object(m,'_read',wraps=m._read); spy=s.start(); print(m.load_catalog(False),m.load_catalog(False),'leituras=',spy.call_count); s.stop(); f.close()"` → `None None leituras= 2` | Memorizar também o resultado inválido por origem e testar leituras repetidas; preservar a atualização por download. | |
| R5: a saída real 127, 124 ou 126 da Orca é confundida com executável ausente, timeout ou erro do sistema, mudando o diagnóstico anterior. | `scripts/screens.py:45` | Distinguir falha de execução do código de saída do processo e testar os três códigos vindos do executável. | |
| C5: o padrão textual não encontra `which ("orca")` e referências ao adaptador dentro de código inativo satisfazem a asserção. | `tests/test_catalogo_e_orca.py:245` | Inspecionar chamadas efetivas e exercitar os três consumidores com espionagem do adaptador. | |
| C6: a presença de palavras em qualquer parte do documento passa mesmo que as relações exigidas estejam invertidas ou ausentes. | `tests/test_catalogo_e_orca.py:297` | Conferir o conteúdo concreto de cada um dos cinco temas e o resultado do check. | |
| C7: a decisão pode negar ou omitir relações dos requisitos mantendo os termos exigidos. | `tests/test_catalogo_e_orca.py:320` | Comparar afirmações completas de cada requisito na seção Decisão. | |

## Limits

Regressão em HEAD: `python -m unittest discover -s tests -v`, 1.082 testes, OK, 1 ignorado: `test_restore_yes_devolve_bit_executavel`, pois o Windows não oferece bit executável.
O comando `stack_cache.py write` usado para criar o documento não pôde ser comprovado somente pelo conteúdo versionado.
