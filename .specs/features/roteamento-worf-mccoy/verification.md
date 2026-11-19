# roteamento-worf-mccoy verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at c3e9e2f
**HEAD**: df53c9e
**Verifier**: codex · requested cli-default · effective GPT-6.1 Terra medium (terminal)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_roteamento_worf_mccoy.py` `test_descricao_worf` | no - não garante que todos os gatilhos tenham contexto StarCode. |
| C2 | `tests/test_roteamento_worf_mccoy.py` `test_descricao_mccoy` | no - não garante que todos os gatilhos tenham contexto StarCode. |
| C3 | `tests/test_roteamento_worf_mccoy.py` `test_casos_novos` | no - verifica linhas isoladas sem garantir a estrutura YAML e o vínculo de cada grader. |
| C4 | `tests/test_roteamento_worf_mccoy.py` `test_readme_e_contagem` | no - não verifica a preservação das verificações de `test_evals_f9.py`. |
| C5 | `tests/test_roteamento_worf_mccoy.py` `test_decisions_roteamento` | no - verifica palavras isoladas, sem garantir o conteúdo das decisões. |
| C6 | `tests/test_roteamento_worf_mccoy.py` `test_descricao_piloto` | no - na ausência de `main`, aceita a descrição como substring, não a descrição integral. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Os testes das descrições aceitam um novo gatilho genérico, pois procuram apenas duas frases exatas e termos de contexto em qualquer ponto. | `tests/test_roteamento_worf_mccoy.py:37` e `tests/test_roteamento_worf_mccoy.py:46` | Verificar cada gatilho e sua associação ao contexto exigido. | d5e81b1 · test_descricao_worf, test_descricao_mccoy |
| O teste dos casos aceita linhas sob a seção errada e não associa `type: tool_used` ao grader correspondente; um YAML malformado pode passar. | `tests/test_roteamento_worf_mccoy.py:68` | Analisar o YAML e comparar a estrutura e cada grader completo. | d5e81b1 · test_casos_novos |
| A prova de C4 não examina as verificações de `test_evals_f9.py`, que poderiam ser removidas sem falhar o teste citado. | `tests/test_roteamento_worf_mccoy.py:86` | Acrescentar prova que verifique a preservação efetiva dos casos e das asserções anteriores. | d5e81b1 · test_readme_e_contagem |
| O teste da decisão aceita termos mesmo se o texto disser o oposto, inclusive que o piloto não é exclusivo do usuário. | `tests/test_roteamento_worf_mccoy.py:102` | Verificar as afirmações concretas da decisão, incluindo a exclusividade do piloto. | 89c1491 · test_decisions_roteamento |
| Sem o ramo `main`, o fallback aceita uma descrição com texto extra, embora C6 exija igualdade. A regra `invocation: user` e o frontmatter gerado também não são cobertos pelo check C6. | `tests/test_roteamento_worf_mccoy.py:53` | Comparar a descrição completa com a versão de referência e verificar a invocação na fonte e no artefato gerado. | d5e81b1 · test_descricao_piloto |
| O README afirma que 15 casos negativos não devem disparar nenhuma skill, mas os dois novos só impedem, respectivamente, Worf e McCoy; outra skill pode ser chamada sem reprovar o caso. | `evals/README.md:9` e `evals/routing/neg-worf-generic-pr/case.yaml:11` | Descrever o alcance real dos graders ou verificar todas as skills se essa for a intenção. | d5e81b1 · test_readme_e_contagem |

## Limits

Regressão em HEAD: `python -m unittest discover -s tests -v` passou: 1031 testes em 611,009 s, 1 ignorado.
Sondas em HEAD: R1, `python -c "from pathlib import Path; import re; d=re.search(r'^description: (.*)$',Path('skills/worf/SKILL.md').read_text(encoding='utf-8'),re.M).group(1); print('gatilho Worf para intervalo base...head:', 'StarCode or Worf for a review of a pull request or of a base...head range' in d)"` imprimiu `gatilho Worf para intervalo base...head: True`; R2, `python -c "from pathlib import Path; import re; d=re.search(r'^description: (.*)$',Path('skills/mccoy/SKILL.md').read_text(encoding='utf-8'),re.M).group(1); print('gatilho ticket com bug resistente:', 'bug in a StarCode ticket resists a fix' in d)"` imprimiu `gatilho ticket com bug resistente: True`.
Eval de roteamento não executado, conforme instrução; o Handoff registra 12/12 nos casos novos e vizinhos.
