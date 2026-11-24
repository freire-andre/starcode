# Pasta temporária dos testes resolvida: Spec

**Size**: SMALL
**Linear**: SC-226
**May change**: tests/helpers.py, tests/test_helpers_tmp.py

## Scope
- `TempRepoCase.setUp` guarda a pasta temporária já resolvida (`Path(...).resolve()`), para que os caminhos que os testes montam batam com os que o código devolve quando o sistema entrega a forma curta (`RUNNER~1`) no Windows do CI.

## Checks
**Build**: `python tools/build.py --check`
**C1** - Num `TempRepoCase`, `self.tmp == self.tmp.resolve()` e `self.repo == self.repo.resolve()`, e o teste falha se `setUp` voltar a guardar `Path(self._tmp.name)` sem resolver (o teste troca `tempfile.TemporaryDirectory` por um diretório cujo `name` não é canônico, como um caminho com `..`, e confere que `self.tmp` sai canônico).
Proof: `python -m unittest discover -s tests -p "test_helpers_tmp.py"`

## Handoff

**Phase:** spec-approved
**Size:** SMALL
**Git mode:** 3
**Plugin:** none yet
**Next:** LaForge corrige o TempRepoCase
**Linear:** SC-226
**Integration branch:** feature/ci-windows
**Last integrated:** none
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
