# restauracao-e-telas verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at bd69d78
**HEAD**: c87c170
**Verifier**: pending

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_restauracao_e_telas.py` `test_restore_le_escopo_do_snapshot` | no - a prova omite o teste do snapshot sem artefato e suas três condições. |
| C2 | `tests/test_restauracao_e_telas.py` `test_capture_so_host_local` | yes |
| C3 | `tests/test_restauracao_e_telas.py` `test_capture_out_restrito` | yes |
| C4 | `tests/test_restauracao_e_telas.py` `test_veredito_nome_inteiro` | yes |
| C5 | `tests/test_restauracao_e_telas.py` `test_png_sem_idat` | yes |
| C6 | `tests/test_restauracao_e_telas.py` `test_decisions_e_changelog` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C1 não comprova a recusa do snapshot sem artefato: o teste citado cobre apenas o escopo ampliado. | `tests/test_restauracao_e_telas.py:82` | Citar também `test_restore_snapshot_sem_artefato_sai_2` na prova de C1. | |
| Um cabeçalho de chunk IDAT truncado, sem dados nem CRC, é aceito como imagem com dados. | `python -B -c "import sys,struct; sys.path.insert(0,'scripts/gates'); import images; data=b'\x89PNG\r\n\x1a\n'+struct.pack('>I',13)+b'IHDR'+struct.pack('>IIBBBBB',4,4,8,2,0,0,0)+b'\0'*4+struct.pack('>I',100)+b'IDAT'; print(images._png(data))"` → `(4, 4)` | Verificar que o chunk IDAT declarado está completo e contém dados antes de aceitá-lo; adicionar teste de truncamento. | |

## Limits

Regressão em HEAD: `python -B -m unittest discover -s tests -v` terminou com código 0; 1074 testes, 1 pulado (`test_restore_yes_devolve_bit_executavel`: bit executável indisponível no Windows).
Sonda adicional de R2 e R3: `python -B -c "import sys; sys.path.insert(0,'scripts'); import screens; print(screens.host_allowed(screens.url_host('http://deep.app.localhost:123/'), [])); print(screens.out_allowed('captures/.running.png'))"` imprimiu `True` e `False`, respectivamente.
