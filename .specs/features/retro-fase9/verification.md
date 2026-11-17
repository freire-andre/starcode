# retro-fase9 verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 65952cc
**HEAD**: f7f08a0
**Verifier**: codex · requested cli-default · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_review_gate.py` `test_require_text_tabela` | no - não verifica os campos condicionais `missing_fact` e `reason` nem a aceitação de valores válidos nesses campos. |
| C2 | `tests/test_review_gate.py` `test_help_sai_com_zero` | yes |
| C3 | `tests/test_review_gate.py` `test_uso_e_codigos_mantidos` | no - compara apenas trechos da saída de erro e não cobre caminhos iniciados por hífen. |
| C4 | `tests/test_review_gate.py` `test_scripts_de_review_respondem_help` | yes |
| C5 | `tests/test_review_gate.py` `test_retro_fase9_estado` | no - aceita qualquer hash igual nas linhas 3 e 7, inclusive um commit alheio à feature. |
| C6 | `tests/test_review_gate.py` `test_decisions_retro_fase9` | no - não exige na Decisão a aplicação do helper em todos os campos nem as issues e linhas específicas de R5. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| R3: um arquivo válido com nome iniciado por hífen é tratado como opção e rejeitado com saída e código diferentes dos anteriores. | `python -B -c "import pathlib,subprocess,sys,tempfile; s=str(pathlib.Path('scripts/review/review_gate.py').resolve()); data=pathlib.Path('tests/fixtures/review/review_clean.json').read_bytes(); t=tempfile.TemporaryDirectory(); pathlib.Path(t.name,'-review.json').write_bytes(data); p=subprocess.run([sys.executable,s,'-review.json'],cwd=t.name,capture_output=True,text=True); print('exit:',p.returncode); print('stdout:',repr(p.stdout)); print('stderr:',repr(p.stderr))"` produziu literalmente: `exit: 2`<br>`stdout: ''`<br>`stderr: 'usage: review_gate.py [-h] review.json\nreview_gate.py: error: the following arguments are required: review.json\n'` | Preservar a leitura de um argumento de caminho iniciado por hífen, exceto as opções de ajuda explicitamente excluídas, e testar esse caso. | |
| C1 não comprova a validação por `require_text` dos campos condicionais `missing_fact` e `reason`, nem o caso válido dos campos. | `tests/test_review_gate.py:174` | Exercitar valores inválidos e válidos em todos os campos que usavam `blank`, inclusive os condicionais, com resultado exato. | |
| C3 não comprova a saída integral preservada para JSON ilegível e violações; mensagens adicionais ou alteradas podem passar. | `tests/test_review_gate.py:208` | Comparar a saída completa e o código em casos representativos, inclusive caminho iniciado por hífen. | |
| C5 aceita qualquer hash hexadecimal igual nas linhas 3 e 7 sem verificar se identifica commit desta feature. | `tests/test_review_gate.py:252` | Exigir o commit concreto desta feature ou comprovar sua presença no intervalo da feature. | |
| C6 permite remover da Decisão o uso do helper em todos os campos e as associações de linhas às issues de R5 sem falhar. | `tests/test_review_gate.py:265` | Afirmar esses termos e valores na seção Decisão. | |

## Limits

Regressão em HEAD: `python -m unittest discover -s tests -v` — 966 testes em 538,054 s, OK, 1 ignorado.
O C4 não cobre a preservação do comportamento normal de `scan_bypasses.py` com diff no stdin ou `--diff`, descrita na decisão; a suíte inclui testes separados para esses caminhos.
Após a suíte, `git status` também mostra `docs/fluxograma-starcode.svg` não rastreado; não foi removido porque o despacho proíbe excluir arquivos.
