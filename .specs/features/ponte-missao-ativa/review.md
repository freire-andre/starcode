**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
COMMENT. As correções da SC-143 e da SC-142 estão corretas e cobertas por testes. Há um ponto should-fix: com missão de outro worktree, o painel mostra essa missão, mas os botões Abrir spec, Abrir tasks e Abrir Handoff continuam abrindo os arquivos da feature local, que já está done. Há também um nit sobre a origem dos erros lidos do outro worktree.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | `src/orca/src/panel.tsx:127` | Com `elsewhere`, o painel mostra a missão X (`f = el ?? snap.feature`), mas os atalhos Abrir spec/tasks/Handoff usam `snapshot.feature.files` e o `ponte.open` abre os arquivos da feature local done Y no worktree em foco. Sugestão: com `elsewhere`, desabilitar os três botões (o Focar worktree leva até a missão) ou rotulá-los como da feature local. | `src/orca/src/panel.tsx:127`; `src/orca/src/panel.tsx:212`; `src/orca/src/worker.ts:509` | aberto |
| W2 | 🟡 nit | `scripts/ponte.py:290` | `other.errors = snap.errors` faz os erros do outro worktree entrarem com a mesma `source` das fontes locais, e o painel os mostra nas seções locais. Prefixar com o caminho do worktree, ou usar a fonte `worktrees`, deixaria clara a origem. | `scripts/ponte.py:290` | aberto |

## Escada determinística
- `python tools/build.py --check && python scripts/check_decisions.py && python -m unittest discover -s tests`: exit 0, 670 testes OK (worktree no C:, árvore idêntica ao HEAD).
- `orca plugin validate/test/check src/orca`: exit 0, 69 testes do plugin (worktree no C:; no F: o harness da Orca 1.4.257 falha para qualquer plugin).
- `run_gates.py proofs` / `done ponte-missao-ativa`: verde.
- Scan de bypass (`git diff origin/main...HEAD | scan_bypasses.py`): 1 candidato (`worker.test.ts:917`, `as any` num teste), descartado porque só lê o mock.
- CI do PR #31: ubuntu e windows pass, 670 testes OK em cada.

## Pesquisa
- Orca host API (`orca skills get orca-plugin-authoring --reference references/host-api.md`): `workspace.open` exige `workspace:write`, `workspace.list` exige `workspace:read` e `notifications.show` exige capacidade própria.
**Posted**: 2026-11-12 - https://github.com/freire-andre/starcode/pull/31#pullrequestreview-5878785871
