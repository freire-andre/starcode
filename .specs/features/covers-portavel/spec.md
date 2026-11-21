# Regra covers igual em Windows e Linux: Spec

**Size**: SMALL
**Linear**: SC-209
**May change**: scripts/gates/gates_common.py, tests/test_coverage_rule.py, DECISIONS.md, CHANGELOG.md, dist/

## Scope
- Item R.9 da triagem v2. Hoje `gates_common.covers` usa `fnmatch.fnmatch`, que ignora maiúsculas no Windows, deixa `*` atravessar `/` e trata `[` como classe de caracteres.
- O casamento de padrão do `covers` passa a ter regra própria, igual em qualquer sistema:
  - diferencia maiúsculas;
  - `*` casa zero ou mais caracteres sem `/`, e `?` casa um caractere que não seja `/`;
  - `**` como segmento inteiro casa zero ou mais segmentos (`a/**/b` cobre `a/b` e `a/x/y/b`; `a/**` cobre tudo abaixo de `a/`);
  - `[` e `]` são literais.
- A regra de pasta (entrada terminada em `/`), a igualdade e a recusa de caminho absoluto ou com `..` ficam como estão.
- Entrada `### SC-209:` no `DECISIONS.md` (**Problema**, **Decisão**, **Motivo**, **Por que não é bug**) e linha no `CHANGELOG.md` `[Unreleased]`.

## Checks
**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Tabela de casos com o resultado esperado de cada um, rodada também com `os.path.normcase` e `fnmatch` forçados ao comportamento do Windows (patch de `os.name`/`ntpath`), dando o mesmo resultado. Os casos incluem: `src/*.py` não cobre `src/deep/x/a.py`; `src/**/*.py` cobre `src/a.py` e `src/deep/x/a.py`; `app/[id]/*.tsx` cobre `app/[id]/page.tsx`; `Tests/test_*.py` não cobre `tests/test_x.py`; `tests/test_?.py` cobre `tests/test_a.py` e não `tests/test_ab.py`; `dist/` cobre `dist/a/b`
Proof: run unit | test_covers_tabela_portavel (test_coverage_rule.CoverageRuleTests.test_covers_tabela_portavel) ... ok

**C2** - Entrada `### SC-209:` com os quatro campos, citando `fnmatchcase` ou a regra própria, `**`, `[` literal e o teste, e a linha no CHANGELOG
Proof: run unit | test_decisions_covers_portavel (test_coverage_rule.CoverageRuleTests.test_decisions_covers_portavel) ... ok

## Handoff

**Phase:** pr-review
**Size:** SMALL
**Git mode:** 3
**Next:** publicar r1, push do review, merge (confirmação)
**Linear:** SC-209
**Integration branch:** feature/covers-portavel
**Last integrated:** T1 (67ef1fa)
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** 2026-11-21: Worf r1 APPROVE (sem achados)
**Breaker:** closed
