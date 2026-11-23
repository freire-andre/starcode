# Revisão: ponte-viva

**Round**: 2
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR

Os cinco achados da rodada 1 (W1 a W5) estão resolvidos no HEAD `f51f55f`. Cada um tem teste ou justificativa vinculada a SC-216. A rodada 2 não encontrou blocker novo.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | should-fix | `src/orca/src/scene.ts:400` | Acionar quem já está na cena trocava a seleção. Agora o clique passa por `alternaSelecao` com os presentes do último desenho e mantém a seleção. | `src/orca/src/scene.ts:439`, `src/orca/src/scene-model.ts:304`; teste `scene-model.test.ts:768` (Q e depois Picard mantém Q). | resolvido |
| W2 | should-fix | `scripts/ponte.py:98` | `sessions.json` inválido virava contagem zero e ocioso. Agora vira `count: null`, o integrante fica `desconhecido` e o aviso aparece mesmo com status `ok`. | `scripts/ponte.py:118`, `src/orca/src/crew-visual.ts:113`, `src/orca/src/scene-model.ts:808`; teste `scene-model.test.ts:795` e `tests/test_ponte.py`. | resolvido |
| W3 | should-fix | `src/orca/src/crew-visual.ts:125` | A comparação de caminhos ignorava a caixa em POSIX. Agora a caixa só é ignorada com letra de unidade ou UNC. | `src/orca/src/crew-visual.ts:127`; teste `crew-visual.test.ts:220` (`/repo/Foo` x `/repo/foo` nos dois sentidos, sem vínculo; `C:/wt` x `c:\WT` vincula). | resolvido |
| W4 | should-fix | `src/orca/src/scene.ts:603` | Conversão dupla de `document` para `Pagina`. Removida: `criaRelacao(document)`. | `src/orca/src/scene.ts:448`: `Document` satisfaz cada membro de `Pagina`. Typecheck não executado (sem `.orca/types` nem `tsc` local). | resolvido |
| W5 | should-fix | `src/orca/src/scene.test.ts:317` | Dublês contornavam tipos sem justificativa. `filhos` passou a `unknown[]`; as duas conversões restantes têm justificativa SC-216 na linha anterior. | `src/orca/src/worker.test.ts:1051` e `src/orca/src/worker.test.ts:1080`. | resolvido |

Fora do escopo desta rodada: as conversões `as unknown as` em `src/orca/src/scene.ts:385` e `:406` já existiam em `main` e não são candidatas do diff.

## Escada determinística

Executada pelo coordenador no HEAD `f51f55f`; não reexecutada nesta rodada:

- `python tools/build.py --check`: passou.
- `python -m unittest discover -s tests -v`: passou, 1116 testes, 1 ignorado.
- `python scripts/check_decisions.py`: passou.
- `claude plugin validate dist/claude --strict`: passou.
- `orca plugin test src/orca`: 118 de 118.
- `run_gates.py proofs ponte-viva` e `done --strict`: verde.

Executado nesta rodada:

- `git diff main...HEAD | scan_bypasses.py`: 2 candidatos (`src/orca/src/worker.test.ts:1052` e `:1081`), ambos com justificativa e a issue SC-216 na linha anterior; aceitos, sem achado. Na rodada 1 eram 5.
- `review_gate.py review.json`: saída 0.

## Pesquisa

nenhuma superfície externa: as correções não tocam dependência nem API externa.

Arquivos gerados em `dist/` foram excluídos da análise de código.
