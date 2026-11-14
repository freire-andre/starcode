# setup-grava-config verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 6334872
**HEAD**: ca5f7d8
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_config_skill.py` `test_setup_cita_intervalo_ate_a_gravacao` | yes |
| C2 | `tests/test_config_skill.py` `test_intervalo_do_setup_acompanha_titulo_write` | no - a comparação deixa de localizar `Write` com `AttributeError`, sem a mensagem exigida; também aceita a primeira ocorrência quando há títulos duplicados |
| C3 | `tests/test_config_skill.py` `test_dist_setup_cita_steps_1_6` | yes |
| C4 | `tests/test_config_skill.py` `test_decisions_setup_grava_config` | no - verifica intervalo, cabeçalho final e nome do teste, mas não exige os campos Problema, Decisão e Motivo |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C2 não trata a ausência de `Write` com a mensagem nomeando o título, como exige o edge case de R2; além disso, a busca da primeira ocorrência deixa passar `Write` duplicado quando a primeira numeração coincide. | `tests/test_config_skill.py:134-135`; `python -c "import sys; sys.path.insert(0, 'tests'); from test_config_skill import interval_diff; from pathlib import Path; s=Path('skills/setup/SKILL.md').read_text(encoding='utf-8'); c=Path('skills/config/SKILL.md').read_text(encoding='utf-8'); print(interval_diff(s, c.replace('## 6. Write', '## 6. Gravar')))"` e a saída literal: `AttributeError: 'NoneType' object has no attribute 'group'`; `python -c "import sys; sys.path.insert(0, 'tests'); from test_config_skill import interval_diff; from pathlib import Path; s=Path('skills/setup/SKILL.md').read_text(encoding='utf-8'); c=Path('skills/config/SKILL.md').read_text(encoding='utf-8'); print('duplicated Write:', interval_diff(s, c + '\\n## 7. Write\\n'))"` e a saída literal: `duplicated Write: (6, 6)` | Validar que existe exatamente um título `Write`; falhar com mensagem explícita ao faltar ou duplicar; testar ambos os casos. | |
| O teste de R4 não prova a presença dos campos Problema, Decisão e Motivo: os três poderiam sumir e o teste ainda passaria. | `tests/test_config_skill.py:161-163` | Asserir os quatro nomes de campo na entrada SC-172. | |

## Limits

A suíte inteira solicitada (`python -m unittest discover -s tests -v 2>&1`) terminou: 862 testes, OK (1 skipped), exit 0. A árvore já continha `.specs/features/setup-grava-config/spec.md` modificado antes deste trabalho; foi preservado conforme a instrução de não alterar o Handoff.
