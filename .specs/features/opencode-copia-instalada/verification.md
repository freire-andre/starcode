# opencode-copia-instalada verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 9865108
**HEAD**: 811c28c
**Verifier**: codex · requested padrão do CLI · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_install_local.py` `test_opencode_uses_installed_copy_not_the_clone` | no - confirma que a cópia não aponta para o clone, mas não compara os caminhos de skills nem o conteúdo do plugin com o caminho instalado exigido. |
| C2 | `tests/test_install_local.py` `test_opencode_reinstall_replaces_stale_installed_copy` | yes |
| C3 | `tests/test_install_local.py` `test_opencode_install_keeps_foreign_skill_paths_in_order` | yes |
| C4 | `tests/test_install_local.py` `test_opencode_install_twice_from_two_clones_no_duplicates` | yes |
| C5 | `tests/test_install_local.py` `test_opencode_dry_run_reports_removed_and_written` | yes - check acrescentado após o Q (achado 2) e reforçado em d157d4a; prova verde no proofs.md; não julgado pelo Q |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C1 não verifica que cada caminho em `opencode.json` e o plugin apontam exatamente para a cópia instalada; uma configuração errada fora do clone ainda passa. | `tests/test_install_local.py:279-291` | Asserir igualdade dos caminhos de skills esperados e do conteúdo integral do plugin com a raiz instalada. | d157d4a |
| R3 inclui o relatório de dry-run, mas nenhum check citado o verifica; C3 só testa a ordem dos caminhos alheios. | `tests/test_install_local.py:230-241` | Incluir `test_opencode_dry_run_reports_removed_and_written` como prova e verificar todos os valores exigidos no relatório sem escrita. | d157d4a |
| A cópia ignora todos os arquivos `*.pyc`, mas o teste só verifica a remoção de `__pycache__`; a regra para `.pyc` fora dessa pasta pode regredir silenciosamente. | `tools/install_local.py:201`; `tests/test_install_local.py:280-286` | Acrescentar um `.pyc` fora de `__pycache__` na fixture e verificar que não foi copiado. | d157d4a |

## Limits

`python -m unittest discover -s tests -v`: 924 testes, OK (1 ignorado). Duas sondas em `--home` temporário passaram: configuração inicialmente sem caminhos e reinstalação com arquivo obsoleto; nenhuma sondagem chamou Orca ou escreveu no home real. Provas registradas em 9865108; o HEAD analisado é 811c28c.
