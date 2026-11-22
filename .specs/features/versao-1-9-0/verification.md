# versao-1-9-0 verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 7277a80
**HEAD**: 80de62f
**Verifier**: codex · requested padrão do CLI (worker-start sem campo model) · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_build.py` `test_version_is_1_2_0_in_all_manifests` | yes |
| C2 | `tests/test_versao_1_9_0.py` `test_versao_1_9_0_em_todos_os_manifestos` | yes |
| C3 | `tests/test_versao_1_9_0.py` `test_changelog_fecha_1_9_0` | no - admite extração parcial e pula as últimas verificações sem o commit histórico |
| C4 | `tests/test_versao_1_9_0.py` `test_readme_estado_1_9_0` | yes |
| C5 | `tests/test_versao_1_9_0.py` `test_changelog_recent`, `test_nenhum_teste_le_unreleased_nem_busca_issue_fora_do_helper` | no - a varredura ignora acessos indiretos e arquivos excluídos |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| O marketplace de agentes não contém a versão 1.9.0 exigida; o teste substitui a chave ausente pelo valor esperado. | `.agents/plugins/marketplace.json:7`; `tests/test_versao_1_9_0.py:30`; `tools/build.py:455` | Gerar a versão exigida e afirmar a chave explicitamente no teste. | f1c0746 · test_versao_1_9_0_em_todos_os_manifestos |
| C2 aceita a falta de um `crew.json` específico se houver cinco arquivos, sem exigir os destinos previstos. | `tests/test_versao_1_9_0.py:31` | Comparar os caminhos esperados e suas versões explicitamente. | 12b718a · test_versao_1_9_0_em_todos_os_manifestos |
| C3 aceita alterações ou perda de conteúdo dos itens e troca entre seções se contagem e issues forem preservadas. | `tests/test_versao_1_9_0.py:43` | Comparar os itens e suas seções com o conteúdo anterior. | 8f39b7c · test_changelog_fecha_1_9_0 |
| C5 usa somente duas versões e exclui arquivos da inspeção; uma busca de issue só em Unreleased pode passar nesses arquivos ou sem a grafia literal. | `tests/test_versao_1_9_0.py:57`; `tests/test_versao_1_9_0.py:83` | Testar três versões e verificar semanticamente todos os testes que pesquisam issues. | 39a0efd · test_nenhum_teste_le_unreleased_nem_busca_issue_fora_do_helper |
| C3 aceita `_notes` devolvendo somente o fragmento `SC-213`, sem provar que encontrou a seção completa de 1.9.0. | `tests/test_versao_1_9_0.py:74` | Comparar as notas retornadas com a seção integral esperada. | |
| C3 pula a comparação histórica e a chamada de `_notes` quando o commit de referência falta; nessas condições a suíte não prova essas partes. | `tests/test_versao_1_9_0.py:66` | Usar uma referência disponível no teste e executar a verificação de notas independentemente do histórico. | |
| C5 ignora buscas em funções que usam um caminho ou número de issue definido fora delas e exclui arquivos inteiros, permitindo uma busca fora do helper passar despercebida. | `tests/test_versao_1_9_0.py:115`; `tests/test_versao_1_9_0.py:123`; `tests/test_versao_1_9_0.py:133` | Verificar os usos efetivos do changelog em todos os testes, incluindo nomes ligados fora da função e exceções restritas a casos de formato. | |

## Limits

Regressão em HEAD: 118 arquivos com `python -m unittest discover -s tests -p <arquivo>`; 118 passaram e nenhum falhou.

Sonda R6: um changelog com Unreleased vazio e versões 4.5.6 e 4.5.5 retornou somente Unreleased e 4.5.6.

Sonda R4: `_notes(Path('.'), '9.9.9')` retornou `None` para uma versão inexistente.

As provas registram 7277a80; entre bf19eae e o HEAD 80de62f só mudou o Handoff da spec.
