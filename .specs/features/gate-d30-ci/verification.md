# Gate D30 no CI e decisões da 1.8.0 verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 8e1547f
**HEAD**: 8266cab
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_ci_workflow.py` `test_ci_checkout_historico_completo` | yes |
| C2 | `tests/test_check_decisions.py` `test_clone_raso_sai_2` | yes |
| C3 | `tests/test_check_decisions.py` `test_raso_indeterminado_sai_2` | no - a saída inválida ` false ` é aceita como `false` após `strip()` |
| C4 | `tests/test_check_decisions.py` `test_flow` | no - verifica códigos e apenas a substring `FALHOU`, não preserva as mesmas mensagens exigidas por R4 |
| C5 | `tests/test_check_decisions.py` `test_decisions_v18_1_piloto` | no - não exige a lista completa de itens nunca delegados da seção 5 |
| C6 | `tests/test_check_decisions.py` `test_decisions_v18_2_aprovacao_piloto` | no - os termos podem aparecer sem impor piloto ativo, mandato confirmado do usuário ou aprovação de spec só pelo usuário |
| C7 | `tests/test_check_decisions.py` `test_decisions_v18_3_config_model_info` | no - não verifica a fonte, os limites das faixas nem os papéis associados a cada faixa |
| C8 | `tests/test_check_decisions.py` `test_decisions_v18_4_config_local` | no - `config.local.json` não fixa o caminho `.starcode/config.local.json` requerido |
| C9 | `tests/test_check_decisions.py` `test_decisions_v18_5_menu` | no - não exige que a entrada diga que o menu não roda ferramentas nem que todas as skills estejam cobertas |
| C10 | `tests/test_check_decisions.py` `test_decisions_gate_raso` | no - não exige a citação do teste para R3, nem que os testes citados falhem sem cada comportamento de R1 a R3 |
| C11 | `python scripts/check_decisions.py` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| A saída de `rev-parse` com espaços extras em torno de `false` é aceita como confirmação de clone completo; R3 exige código 2 para qualquer saída que não seja exatamente `true` ou `false`. | `python -c "import sys; from pathlib import Path; from unittest.mock import patch; sys.path.insert(0,'scripts'); import check_decisions as cd; real=cd.git; fake=lambda p,*a: (0,' false ') if a[:2]==('rev-parse','--is-shallow-repository') else real(p,*a); ctx=patch.object(cd,'git',fake); ctx.start(); print(cd.check(Path('.').resolve())); ctx.stop()"` imprimiu `(0, 'check_decisions: OK (DECISIONS.md atualizado no mesmo commit 7d7fd99c)')` | Validar a saída bruta `true`/`false` sem aceitar espaços laterais adicionais e cobrir esse caso com teste. || 7c24202 |
| C4 não detecta mudança nas mensagens de sucesso ou de falha, embora R4 exija os mesmos códigos e mensagens. | `tests/test_check_decisions.py:17` | Afirmar tuplas de código e mensagem completas para todos os casos cobertos antes da mudança. || 6369977 |
| C5 pode passar sem registrar a lista de decisões não delegáveis exigida por R5. | `tests/test_check_decisions.py:93` | Verificar cada item aplicável da seção 5 no corpo da entrada. || 6369977 |
| C6 não fixa as condições e o formato de autorização de R6: os quatro termos podem existir em texto sem relação entre si. | `tests/test_check_decisions.py:98` | Exigir as condições de status ativo e mandato confirmado, o formato da linha `piloto:` e a regra de aprovação de `spec.md`. || 6369977 |
| C7 não testa os limites de custo nem as faixas por papel requeridos em R7. | `tests/test_check_decisions.py:103` | Verificar limites `$`/`$$`/`$$$`, papéis e catálogo models.dev como fonte. || 6369977 |
| C8 pode passar com outro caminho contendo `config.local.json`, sem o diretório `.starcode` exigido por R8. | `tests/test_check_decisions.py:108` | Afirmar a ocorrência literal de `.starcode/config.local.json`. || 6369977 |
| C9 pode passar sem afirmar que o menu não executa ferramentas e sem garantir que o teste referido cobre todas as skills, como requer R9. | `tests/test_check_decisions.py:113` | Exigir explicitamente a regra de não executar ferramentas e conferir a cobertura completa. || 6369977 |
| C10 pode passar sem citar nem vincular um teste que proteja R3 e sem garantir que os testes cobrem cada regra de R1 a R3. | `tests/test_check_decisions.py:118` | Verificar a referência ao teste de R3 e que cada comportamento descrito tenha teste que falha quando ele falta. || 6369977 |

## Limits

Suíte completa em HEAD: `python -m unittest discover -s tests -v 2>&1` — `Ran 820 tests in 393.706s`; `OK (skipped=1)`.

Probes: clone completo contendo só `DECISIONS.md`, sem commits monitorados, retornou `(0, 'check_decisions: OK (nenhuma mudança em skills/, scripts/ ou hooks/)')`; saída `maybe` retornou código 2 com a mensagem de indeterminado. A saída inválida ` false ` foi registrada como finding acima.

O `HEAD` 8266cab difere do commit de provas 8e1547f apenas por uma alteração de 2 linhas em `spec.md`; os proofs afirmam execução em 8e1547f, enquanto a suíte completa foi executada em 8266cab. A saída integral da suíte foi resumida pelo runner; o código de saída foi 0.
