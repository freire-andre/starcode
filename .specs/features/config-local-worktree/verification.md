# config-local-worktree verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 7a64808
**HEAD**: 502a19c
**Verifier**: codex · requested cli-default · effective GPT-6.1 Terra medium (terminal)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_config_local_worktree.py` `test_local_no_worktree_ligado` | no - não exercita dispatch nem setup no worktree ligado. |
| C2 | `tests/test_config_local_worktree.py` `test_entrada_local_inteira` | no - não verifica a mensagem para entrada vazia. |
| C3 | `tests/test_config_local_worktree.py` `test_modelo_valido` | no - a tabela não testa modelos na configuração de repositório. |
| C4 | `tests/test_config_local_worktree.py` `test_aviso_local_versionado` | yes |
| C5 | `tests/test_config_local_worktree.py` `test_suggest_mantem_configurado` | no - no CLI, confere apenas a linha de nomes, sem conferir as propostas e os valores preservados. |
| C6 | `tests/test_config_local_worktree.py` `test_skill_e_decisions` | no - não exige todos os termos de cada requisito na seção Decisão. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Entrada local vazia é recusada com mensagem diferente da exigida por R2. | `python -c "import sys; sys.path[:0]=['scripts','scripts/config']; import validate_config as v; print(v.validate('local', {'schemaVersion':1,'crew':{'q':{}}}))"` → `['crew.q: objeto vazio (remova a chave ou defina cli/model)']` | Emitir a mensagem de R2 também para entrada vazia e verificar a saída exata. | |
| C1 não comprova o resultado dos consumidores dispatch e setup nem o banner com config principal inválida no worktree ligado. | `tests/test_config_local_worktree.py:57` | Exercitar os três consumidores em repositórios temporários e comparar os resultados concretos no principal e no ligado, inclusive o banner inválido. | |
| C3 não comprova a validação de modelos nas três configs exigidas: o teste só aplica a tabela às configs user e local, pois o schema repo não possui campo model. | `tests/test_config_local_worktree.py:141` | Resolver a divergência do requisito com o schema e testar a tabela em todas as fontes de model previstas. | |
| C5 aceita que o CLI liste nomes corretos mas apresente valores ou propostas incorretos. | `tests/test_config_local_worktree.py:233` | Verificar os valores completos retornados pelo CLI para configurados e demais membros, inclusive config local e CLI indisponível. | |
| C6 permite que a seção Decisão omita condições dos requisitos, como a recusa de model vazio ou com espaço e a condição de CLI disponível em R5. | `tests/test_config_local_worktree.py:257` | Exigir na seção Decisão os termos de cada condição dos seis requisitos. | |

## Limits

Regressão em HEAD: `python -m unittest discover -s tests -v` passou com 1.045 testes; um teste foi omitido porque o bit executável não existe no Windows.
Sonda adicional de R3: `python -c "import sys; sys.path[:0]=['scripts','scripts/config']; import setup_helpers as s; print(s.parse_model_arg('codex=modelo@desconhecido'))"` retornou `('codex', 'modelo@desconhecido', None)`, preservando o sufixo no identificador.
