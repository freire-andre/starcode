# Review: fase-10-ponte (PR #24)

**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR

APPROVE. O PR entrega o painel Ponte (`ponte.py` somente leitura, worker e painel da Orca) e a Cena da Ponte. A escada está verde e o CI passa no Ubuntu e no Windows. Há um nit: a mensagem "worktree inválido" do `ponte.py` não chega ao painel. O desempate por mtime igual em `choose_feature` usa a ordem alfabética, como o Q já anotou; a spec não define esse caso. `dist/orca` e as capturas de `docs/aceite/fase-10/` ficam fora do review (arquivos mecânicos e imagens).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟡 nit | `src/orca/src/worker.ts:82` | A mensagem "worktree inválido" do `ponte.py` (stdout, exit 2) não chega ao painel: o `realExec` rejeita a saída diferente de 0 usando só o stderr, e o ramo `snap.error` nunca roda | `src/orca/src/worker.ts:28`; `scripts/ponte.py:265`; https://nodejs.org/api/child_process.html | aberto |

## Escada determinística

- `python tools/build.py --check`: exit 0
- `orca plugin validate src/orca --json`: ok, válido
- `python scripts/check_decisions.py`: exit 0
- `python -m unittest discover -s tests` (Windows): OK, 599 testes
- `gh pr checks 24`: checks ubuntu-latest e windows-latest passaram
- `git diff main...HEAD -- . ':!dist' | scan_bypasses.py`: 17 candidatos, todos aceitos:
  - `noqa: E402` de import após `sys.path` (padrão do repo);
  - `BLE001`, `SLF001` e `E731` com justificativa na linha;
  - `type: ignore` do `reconfigure`;
  - casts `as any` e `as unknown as` em testes e na fronteira do canvas.

## Pesquisa

- https://nodejs.org/api/child_process.html: com `execFile`, um exit diferente de 0 vira `error` no callback.
**Posted**: 2026-11-11 - https://github.com/freire-andre/starcode/pull/24#pullrequestreview-5864187846
