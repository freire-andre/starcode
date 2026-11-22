# versao-1-9-0 verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at af0da98
**HEAD**: a34f8d5
**Verifier**: codex · requested padrão do CLI (worker-start sem campo model) · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_build.py` `test_version_is_1_2_0_in_all_manifests` | yes |
| C2 | `tests/test_versao_1_9_0.py` `test_versao_1_9_0_em_todos_os_manifestos` | no - aceita versão ausente no marketplace de agentes e não exige cada crew específico |
| C3 | `tests/test_versao_1_9_0.py` `test_changelog_fecha_1_9_0` | no - não compara os itens e suas seções com o conteúdo anterior |
| C4 | `tests/test_versao_1_9_0.py` `test_readme_estado_1_9_0` | yes |
| C5 | `tests/test_versao_1_9_0.py` `test_changelog_recent` | no - a amostra tem duas versões, e a busca exclui arquivos e depende do texto literal |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| O marketplace de agentes não contém a versão 1.9.0 exigida; o teste substitui a chave ausente pelo valor esperado. | `.agents/plugins/marketplace.json:7`; `tests/test_versao_1_9_0.py:30`; `tools/build.py:455` | Gerar a versão exigida e afirmar a chave explicitamente no teste. | |
| C2 aceita a falta de um `crew.json` específico se houver cinco arquivos, sem exigir os destinos previstos. | `tests/test_versao_1_9_0.py:31` | Comparar os caminhos esperados e suas versões explicitamente. | |
| C3 aceita alterações ou perda de conteúdo dos itens e troca entre seções se contagem e issues forem preservadas. | `tests/test_versao_1_9_0.py:43` | Comparar os itens e suas seções com o conteúdo anterior. | |
| C5 usa somente duas versões e exclui arquivos da inspeção; uma busca de issue só em Unreleased pode passar nesses arquivos ou sem a grafia literal. | `tests/test_versao_1_9_0.py:57`; `tests/test_versao_1_9_0.py:83` | Testar três versões e verificar semanticamente todos os testes que pesquisam issues. | |

## Limits

Regressão em HEAD: 118 arquivos com `python -m unittest discover -s tests -p <arquivo>`; 118 passaram e nenhum falhou.

Sondas adicionais: a comparação com `main` confirmou os itens do changelog intactos; um changelog com Unreleased vazio e três versões retornou somente Unreleased e a versão mais recente.

As provas registram af0da98; o HEAD analisado é a34f8d5. A diferença posterior a e3951c9 altera apenas a spec.
