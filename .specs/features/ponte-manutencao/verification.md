# ponte-manutencao verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 2b75935
**HEAD**: 48c7320
**Verifier**: pending (o coordenador registra CLI e modelos)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_ponte_manutencao.py` `test_parse_dispatch_entry` | yes |
| C2 | `tests/test_ponte_manutencao.py` `test_ponte_modelo_do_start`, `test_dispatch_usa_leitor_unico` | no - não verifica a preservação da saída com múltiplas issues nem a saída integral do settle bem-sucedido. |
| C3 | `tests/test_ponte_manutencao.py` `test_manifesto_sem_storage` | yes |
| C4 | `src/orca/src/worker.test.ts` `issue.url fora do linear vira null` | yes |
| C5 | `src/orca/src/panel.test.tsx` `agentFor casa por token inteiro` | no - omite letras alfanuméricas fora de ASCII na delimitação. |
| C6 | `src/orca/src/worker.test.ts` `nome do worktree com barra invertida` | yes |
| C7 | `tests/test_ponte_manutencao.py` `test_ci_pulo_visivel` | no - falha na regressão sob Windows com o bash encontrado no PATH. |
| C8 | `tests/test_ponte_manutencao.py` `test_decisions_e_changelog` | no - a decisão pode omitir condições dos requisitos apesar dos termos isolados. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R2: `overdue` normaliza o campo de issues, alterando a saída anterior para uma entrada válida com duas issues sem espaço após a vírgula. | `python -B -c "import sys; sys.path.insert(0,'scripts'); import dispatch; from pathlib import Path; from unittest.mock import patch; e='T8 \u00b7 SC-2,SC-3 \u00b7 base abc \u00b7 cli:model \u00b7 2026-11-20T00:00:00Z \u00b7 ctx'; a=patch.object(dispatch,'load_tasks',return_value=(Path('.'),None)); b=patch.object(dispatch.gc,'project_root',return_value=Path('.')); c=patch.object(dispatch,'integrated',return_value=set()); d=patch.object(dispatch,'handoff_values',return_value={'dispatched':e}); a.start(); b.start(); c.start(); d.start(); print(ascii(dispatch.overdue('x',Path('.'),30,'2026-11-20T01:00:00Z',base='main')))` → `(0, ['T8 \xb7 SC-2, SC-3 \xb7 60 min \xb7 ctx'])`; antes o campo era `SC-2,SC-3`. | Preservar o campo original de issues na saída e testar o texto e o código completos. | |
| R5: letra acentuada é alfanumérica, mas o delimitador ASCII casa `T1` dentro de `T1é`. | `python -B -c "import pathlib,subprocess; s=pathlib.Path('src/orca/src/panel.tsx').read_text(encoding='utf-8'); f=s[s.index('function hasToken'):s.index('function agentFor')].replace(': string','').replace(': boolean',''); print(subprocess.check_output(['node','-e',f+'console.log(hasToken('+repr('LaForge T1\u00e9')+','+repr('T1')+'))'],text=True).strip())"` → `true` | Tratar letras e números Unicode como alfanuméricos e testar ambos os limites. | |
| C2: o teste confere apenas o prefixo da mensagem de erro e apenas a primeira linha do gate vermelho; não prova a saída e o código do settle bem-sucedido. | `tests/test_ponte_manutencao.py:127` e `tests/test_ponte_manutencao.py:143` | Comparar mensagens completas e testar saída e código do caminho de sucesso usando runner falso. | |
| C8: termos isolados permitem que a seção Decisão omita, por exemplo, `at`, `dispatch` e a leitura do formato antigo de R1; ainda assim o teste passa. | `tests/test_ponte_manutencao.py:200` | Exigir na seção Decisão cada condição e campo de cada requisito, além das quatro partes e da linha do changelog. | |
| A regressão falha em `test_ci_pulo_visivel` neste ambiente Windows: `shutil.which("bash")` encontra o bash do sistema e a execução do passo retorna erro ao abrir o resumo. | `tests/test_ponte_manutencao.py:158` e `tests/test_ponte_manutencao.py:175` | Tornar o teste compatível com o bash escolhido e o caminho do resumo ou selecionar explicitamente um bash compatível. | |

## Limits

`python -m unittest discover -s tests -v`: 1052 testes em 629,203 s; 1 falha (`test_ci_pulo_visivel`), 1 ignorado. Erro: `AssertionError: 1 != 0 : /bin/bash: line 1: : No such file or directory`; `shutil.which('bash')` encontrou `C:\WINDOWS\system32\bash.EXE`.

`orca plugin test src/orca` no worktree indicado, confirmado em 48c7320: 74 passaram, 0 falharam.

`proofs.md` registra 2b75935, não o HEAD 48c7320; a prova original do plugin falhou por erro de shell, e a execução independente acima passou.

R7 não proíbe a linha antiga adicional; o aviso e o resumo exigidos constam no passo do CI.
