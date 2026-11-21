# versao-e-retro verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 00a4f91
**HEAD**: e71628b
**Verifier**: pending (o coordenador registra CLI e modelos)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_versao_e_retro.py` `test_brief_traz_versao_do_plugin` | no - encontra um título em qualquer posição, sem exigir que o brief comece por ele. |
| C2 | `tests/test_versao_e_retro.py` `test_start_grava_plugin_no_handoff` | yes |
| C3 | `tests/test_versao_e_retro.py` `test_aviso_de_versao_diferente` | no - o caso de start é recusado antes de registrar o despacho; não verifica sucesso com runner falso. |
| C4 | `tests/test_versao_e_retro.py` `test_retro_da_guinan_tem_estado` | yes |
| C5 | `tests/test_versao_e_retro.py` `test_retros_abertas` | no - não cobre retro sem tabela e, portanto, sem coluna Estado. |
| C6 | `tests/test_versao_e_retro.py` `test_retros_estado` | no - não verifica preservação de espaços após o delimitador final da linha. |
| C7 | `tests/test_versao_e_retro.py` `test_decisions_e_changelog` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| O teste de C1 aceita texto anterior ao título dos quatro briefs. | `tests/test_versao_e_retro.py:117` | Exigir título na primeira linha em cada brief. | 6cdcca3 · test_brief_traz_versao_do_plugin |
| Os briefs de Q e telas começam por `Repositório:`, antes do título exigido em C1. | `scripts/dispatch.py:537` e `scripts/dispatch.py:587` | Colocar o título na primeira linha e preservar o repositório em seguida. | a318913 · test_q_brief_fills_placeholders |
| O teste de C3 só exercita start recusado e não prova o aviso sem alterar a saída de um despacho bem-sucedido. | `tests/test_versao_e_retro.py:186` | Exercitar start bem-sucedido com runner falso e comparar código, saída e stderr. | 2e3139e · test_aviso_nao_altera_start_bem_sucedido |
| A atualização remove espaços fora da célula Estado, violando a preservação dos demais bytes. | `python -B -c "import sys,tempfile,pathlib; sys.path.insert(0,'scripts'); import retros; t=tempfile.TemporaryDirectory(); r=pathlib.Path(t.name); p=r/'.specs/features/x/retro.md'; p.parent.mkdir(parents=True); p.write_bytes('&#124; # &#124; Estado &#124; Ação proposta &#124;\n&#124;---&#124;---&#124;---&#124;\n&#124; 1 &#124; aberto &#124; y &#124;   \n'.encode()); before=p.read_bytes(); retros.set_estado('x','1','feito em abc',r); print(repr(before.splitlines()[2])); print(repr(p.read_bytes().splitlines()[2]))"` produziu `b'&#124; 1 &#124; aberto &#124; y &#124;   '` e `b'&#124; 1 &#124; feito em abc &#124; y &#124;'`. | Substituir apenas o intervalo da célula e testar espaços após o delimitador final. | 1fae449 · test_retros_estado |
| Uma retro sem tabela não é contada como retro sem coluna Estado. | `python -B -c "import sys,tempfile,pathlib; sys.path.insert(0,'scripts'); import retros; t=tempfile.TemporaryDirectory(); r=pathlib.Path(t.name); p=r/'.specs/features/x/retro.md'; p.parent.mkdir(parents=True); p.write_text('# Retro sem tabela',encoding='utf-8'); print(retros.main(['abertas','--root',str(r)]))"` produziu `0 retro(s) sem coluna Estado` e `0`. | Contar arquivos sem coluna mesmo quando não há tabela de ações; incluir esse caso no teste. | a2be644 · test_retros_abertas |

## Limits

Regressão em HEAD: `python -m unittest discover -s tests -v` passou: 1090 testes em 708,674 s, 1 ignorado.
`test_restore_yes_devolve_bit_executavel` ignorado porque o bit executável não existe no Windows.
