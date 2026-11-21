# falhas-start-settle verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 6b76534
**HEAD**: 8be67b1
**Verifier**: pending (o coordenador registra CLI e modelos)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_falhas_start_settle.py` `test_recibo_com_texto_antes` | yes |
| C2 | `tests/test_falhas_start_settle.py` `test_start_sem_id_sai_com_3` | no - o caminho JSON substitui o próprio start por mock. |
| C3 | `tests/test_falhas_start_settle.py` `test_merge_falha_sem_conflito` | no - não verifica o fallback para stdout nem todas as combinações de conflito e MERGE_HEAD. |
| C4 | `tests/test_falhas_start_settle.py` `test_handoff_concorrente` | no - a corrida não força a sobreposição do ciclo de leitura e gravação. |
| C5 | `tests/test_falhas_start_settle.py` `test_run_git` | no - não verifica a promessa de nunca lançar exceção. |
| C6 | `tests/test_falhas_start_settle.py` `test_scripts_usam_run_git` | no - não verifica o timeout do diff de HEAD e aceita perda do stderr em outros caminhos. |
| C7 | `tests/test_falhas_start_settle.py` `test_decisions_e_changelog` | no - não associa cada estado ao respectivo caso nem exige a preservação das duas mudanças na Decisão. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| O timeout do diff de HEAD é ignorado e a seleção de regressão pode ser apresentada como válida mesmo sem verificar a árvore de trabalho. | `$env:PYTHONPATH='scripts'; python -c "from unittest.mock import patch; import dispatch; from pathlib import Path; p=patch.object(dispatch.sc,'run_git',return_value=(124,'','git timeout')); q=patch.object(dispatch.impact,'select',return_value={}); r=patch.object(dispatch.impact,'format_text',return_value='OK'); p.start(); q.start(); r.start(); print(dispatch.regression_block(Path('.'),'base','HEAD'))"` → `OK` | Tratar códigos diferentes de 0 e 1 como erro, incluir stderr e exigir seleção indisponível; testar HEAD e timeout do diff. | |
| `run_git` lança exceção para ambiente inválido, apesar da garantia de nunca lançar. | `$env:PYTHONPATH='scripts'; python -c "import starcode_common as s; s.run_git(['status'], '.', env={'BAD': 1})" 2>&1 &#124; Select-Object -Last 1` → `TypeError: environment can only contain strings` | Converter erros de argumentos ou ambiente em retorno de erro e cobrir esse caso. | |
| `_git` descarta stderr e `valid_names` converte timeout em falso, sem transmitir o erro exigido por R6. | `scripts/dispatch.py:138`, `scripts/snapshot.py:64`, `tests/test_falhas_start_settle.py:243` | Propagar o timeout pelo erro apropriado com stderr e testar os chamadores afetados. | |
| O teste JSON injeta um resultado pronto no lugar de executar o start e pode passar com integração incorreta. | `tests/test_falhas_start_settle.py:120` | Exercitar o fluxo completo com runner falso, verificando código e objeto impresso. | |
| O teste do merge não cobre stderr vazio com stdout, nem conflito sem MERGE_HEAD ou falha sem conflito com MERGE_HEAD. | `tests/test_falhas_start_settle.py:132` | Exercitar as combinações com runner controlado e comparar mensagem integral, código e abort. | |
| A prova de concorrência depende do escalonamento: quatro execuções podem serializar mesmo que a trava não cubra todo o ciclo. | `tests/test_falhas_start_settle.py:160` | Sincronizar os processos para forçar a disputa durante leitura e gravação e comprovar falha sem a proteção do ciclo inteiro. | |
| O teste da decisão exige palavras isoladas para estados e omite da seção Decisão a preservação das duas alterações concorrentes de R4. | `tests/test_falhas_start_settle.py:273` | Assegurar o estado de cada caso e todos os termos do requisito R4 na seção correspondente. | |

## Limits

Regressão completa no HEAD: `python -m unittest discover -s tests -v` passou com 1060 testes em 1688,508 s; 1 pulado porque o bit executável não existe no Windows.
O teste de concorrência foi repetido duas vezes e passou nas duas; isso não demonstra que falharia sem a proteção integral.
