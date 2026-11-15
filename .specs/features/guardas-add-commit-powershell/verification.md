# guardas-add-commit-powershell verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 613d5a9
**HEAD**: 39e7c66
**Verifier**: pending (o coordenador registra CLI e modelos)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_secret_scan.py` `test_add_antes_do_commit_escaneia_novo_e_modificado` | yes |
| C2 | `tests/test_secret_scan.py` `test_add_antes_do_commit_sem_segredo_passa` | yes |
| C3 | `tests/test_secret_scan.py` `test_add_update_ignora_nao_rastreados` | yes |
| C4 | `tests/test_secret_scan.py` `test_add_so_escaneia_caminhos_passados` | yes |
| C5 | `tests/test_secret_scan.py` `test_add_arquivo_novo_env_e_allowlist` | yes |
| C6 | `tests/test_secret_scan.py` `test_add_com_dash_c` | yes |
| C7 | `tests/test_build.py` `test_claude_hooks_cobrem_powershell` | yes |
| C8 | `tests/test_git_guard.py` `test_git_guard_nega_push_force_pelo_powershell` | yes |
| C9 | `tests/test_secret_scan.py` `test_secret_scan_nega_commit_pelo_powershell` | yes |
| C10 | `tests/test_secret_scan.py` `test_decisions_guardas_add_commit_powershell` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C1, C3, C4 e C6 não verificam o formato completo do achado de segredo para arquivo novo; aceitam apenas prefixo de caminho e, em C1, substring do tipo. Assim, saída sem o separador e sem o valor mascarado ainda passaria, embora R5 fixe `<caminho>:<linha>: <tipo> (<mascarado>)`. | `tests/test_secret_scan.py:158` | Comparar cada achado integralmente com o formato e valor mascarado esperados, incluindo todos os casos de arquivo novo desses checks. | 49fab08 |
| A regra que nega arquivo não rastreado acima de `MAX_DIFF_BYTES` não tem check dedicado; a suíte prova o limite para diff rastreado, mas não para o caminho `untracked_findings`. | `hooks/scripts/secret_scan.py:196` | Adicionar check de arquivo novo grande que confirme a negação e o limite informado. | 49fab08 (`test_add_arquivo_novo_grande_nega`) |

## Limits

Sondas em repositórios temporários para `git add .` no subdiretório, `git add -A <caminho>` e arquivo ignorado tiveram resultados previstos; nenhuma falha adicional foi observada. A regressão `python -m unittest discover -s tests -v` em HEAD 39e7c66 passou: 893 testes, 0 falhas, 1 skip. As provas registram 613d5a9, anterior ao HEAD atual; a suíte completa foi rodada no HEAD atual.
