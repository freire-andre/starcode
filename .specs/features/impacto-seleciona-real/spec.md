# Raio de impacto que seleciona de verdade: Spec

**Approved**: 2026-11-14 - user: "Sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-176
**May change**: scripts/impact.py, tests/test_impact.py, DECISIONS.md, dist/

## Context
Itens R.1 e R.2 de `starcode-triagem-v2-2026-11-13.md` (fora do Git). Discovery em `context.md`. Todo intervalo de feature inclui `.specs/`, que fica fora do grafo, e por isso `select` (`scripts/impact.py:334-382`) sempre manda rodar tudo. Quando seleciona, ignora o mudado que não alcança nenhum teste, conta qualquer `.py` de `tests/` como teste e não vê testes que rodam um script por subprocesso. Sucesso: num intervalo de feature com código + `.specs/`, a seleção sai com os testes certos; nenhum mudado sem teste real passa sem "rodar tudo"; testes que citam o script por nome entram.

## Scope
- `.specs/` sai da lista de mudados.
- Teste real em Python passa a ser `test_*.py` ou `*_test.py`; o resto de `tests/` é apoio.
- Referência textual: teste real que cita o nome do arquivo mudado entra na seleção.
- Rodar tudo quando algum mudado não alcança teste real.

## Non-Goals
- Regras de imports e aliases de TS/JS, padrões de teste TS/JS, gates, McCoy e `dispatch.py` (os chamadores não mudam).
- Qualquer opção ou comando novo (congelamento D-i).

## Requirements
- **R1** - WHEN a lista de mudados (do `--diff` ou de `changed`) contém caminhos sob `.specs/` THEN the system SHALL removê-los antes de qualquer outra regra, de modo que nenhum deles apareça em `changed` nem no motivo `fora do grafo`.
- **R2** - IF todos os mudados estão sob `.specs/` THEN the system SHALL devolver `run-all` com o motivo exato `nenhuma mudança fora de .specs/`.
- **R3** - The system SHALL considerar teste real em Python só o arquivo `.py` cujo nome começa com `test_` ou termina com `_test.py`, em qualquer pasta; `tests/helpers.py`, `tests/conftest.py`, `tests/__init__.py` e `test/x/y.py` SHALL não ser testes. Os padrões de TS/JS ficam como estão.
- **R4** - The system SHALL manter os arquivos de apoio (`.py` que não são teste real) como nós do grafo, de modo que um teste real que importa `tests/helpers.py` seja selecionado quando `helpers.py` muda.
- **R5** - WHEN um teste real tem no texto o nome de arquivo (basename, ex.: `scaffold.py`) de um mudado THEN the system SHALL incluir esse teste na seleção, com a cadeia `<mudado> <- <teste>`, mesmo sem import.
- **R6** - IF ao menos um mudado não alcança nenhum teste real (nem por import, nem por referência textual) THEN the system SHALL devolver `run-all` com o motivo `nenhum teste alcança <mudados sem teste, separados por ", ", em ordem>`, mesmo que outros mudados alcancem testes.
- **R7** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-176:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**, citando que ela muda o padrão de teste do F12 (R15).

## Decisions

| Decisão | Opções | Resposta |
|---|---|---|
| Testes que rodam o script por subprocesso | referência textual / só a regra da triagem | approved - user: "Referência textual" |
| O que conta como teste real em Python | `test_*.py` ou `*_test.py` / qualquer `.py` em `tests/` menos 3 nomes | approved - user: "test_*.py ou *_test.py" |

## Edge Cases
- Intervalo só com `.specs/`: R2 (C2).
- Mudado de apoio importado por teste: R4 (C4).
- Dois mudados, um com teste e outro sem: R6 (C6).
- Colisão de basename: a seleção só fica mais larga (R5, C5).
- Intervalo real de feature (código + `.specs/` num repositório temporário): R1 e R5 (C1).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Repositório temporário com `src/mod.py`, `tests/test_mod.py` (importa `mod`) e um commit de base; um segundo commit muda `src/mod.py`, `.specs/features/x/proofs.md` e `.specs/features/x/spec.md`; `select(repo, diff="<base>..HEAD")` dá `verdict == "selected"`, `tests == ["tests/test_mod.py"]` e `changed == ["src/mod.py"]` (R1)
Proof: run unit | test_intervalo_de_feature_ignora_specs ... ok

**C2** - Só `.specs/features/x/spec.md` mudado: `assertEqual(res["reason"], "nenhuma mudança fora de .specs/")` e `verdict == "run-all"` (R2)
Proof: run unit | test_so_specs_roda_tudo ... ok

**C3** - `is_test_file` verdadeiro para `test_a.py`, `a_test.py`, `tests/test_x.py`, `src/foo.test.ts`, `src/foo.spec.js`, `src/__tests__/foo.ts`, `a/b.test.tsx`; falso para `tests/helpers.py`, `tests/conftest.py`, `tests/__init__.py`, `test/x/y.py`, `a.py`, `src/testing.py`, `latest.py`, `README.md`, `src/contest/x.ts` (R3)
Proof: run unit | test_identifica_testes_python_e_ts ... ok

**C4** - `tests/helpers.py` mudado e importado por `tests/test_a.py`: `tests == ["tests/test_a.py"]` e a cadeia é `["tests/helpers.py", "tests/test_a.py"]`; `tests/helpers.py` não aparece em `tests` (R4)
Proof: run unit | test_apoio_propaga_mas_nao_e_teste ... ok

**C5** - `scripts/tool.py` mudado; `tests/test_cli.py` não importa `tool` mas contém `ROOT / "scripts" / "tool.py"`; `tests/test_outro.py` não cita: `tests == ["tests/test_cli.py"]` e a cadeia é `["scripts/tool.py", "tests/test_cli.py"]` (R5)
Proof: run unit | test_referencia_textual_seleciona_teste ... ok

**C6** - Mudados `a.py` (alcançado por `tests/test_a.py`) e `lonely.py` e `zeta.py` (sem teste): `verdict == "run-all"` e `assertEqual(res["reason"], "nenhum teste alcança lonely.py, zeta.py")` (R6)
Proof: run unit | test_mudado_sem_teste_roda_tudo_mesmo_com_outros ... ok

**C7** - `test_impact_no_repo_starcode` continua passando no repositório real (seleção para `scripts/gates/gates_common.py`, "rodar tudo" com `fora do grafo` para `README.md`), e `test_nenhum_teste_alcanca_roda_tudo` mantém o motivo `nenhum teste alcança lonely.py` (R3, R6)
Proof: run unit | test_impact_no_repo_starcode ... ok

**C8** - A entrada `### SC-176:` do `DECISIONS.md` contém `**Problema**`, `**Decisão**`, `**Motivo**` e `**Por que não é bug**`, cada um asserido dentro da entrada, mais `.specs/`, `test_*.py` e `F12` (R7)
Proof: run unit | test_decisions_impacto_seleciona_real ... ok

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** LaForge corrige os 2 achados do Q
**Linear:** SC-176
**Integration branch:** feature/impacto-seleciona-real
**Last integrated:** 72d7301
**Dispatched:** none
**Settled:** 2026-11-14: aprovação da spec e issue: "Sim"
**Attempts:** none
**Reports:** 2026-11-14: T1: .specs fora, teste real test_*/_test, referência textual, run-all por mudado sem teste; 882 OK; commit 7c10436; 2026-11-14: Q: codex · gpt-6-luna · FAIL, 2 achados em testes (C7 motivo parcial; C8 sem R15); 882 OK
**Breaker:** closed
