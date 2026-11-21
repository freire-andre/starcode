# Falhas do start e do settle: Spec

**Approved**: 2026-11-21 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-208
**May change**: .gitignore, scripts/starcode_common.py, scripts/dispatch.py, scripts/handoff.py, scripts/snapshot.py, scripts/impact.py, tests/test_falhas_start_settle.py, tests/test_dispatch_start.py, tests/test_dispatch.py, tests/test_handoff.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Itens R.8 e N.6 da triagem v2 (seção 10), missão 3 do passo 4. Discovery em `.specs/features/falhas-start-settle/context.md`. O caso "`orca` fora do PATH" do R.8 já foi resolvido em `dcadac4`. Seguem abertos: recibo sem id que sai com 0, toda falha de merge chamada de `conflito` e o Handoff gravado sem trava. O N.6 pede um helper de `git` com tempo limite.

## Scope
- `start`: recibo do `worker-start` com texto antes do JSON, e recibo sem id de despacho.
- `settle`: mensagem de falha de merge com o erro real.
- `handoff.py set` com trava por feature.
- Helper único de `git` com tempo limite, adotado por `snapshot.py`, `impact.py` e `dispatch.py`.

## Non-Goals
- Migrar `check_decisions.py`, `check_proofs.py`, `check_scope.py`, `run_gates.py` e `validate_verification.py` (N.6: só quando forem tocados).
- Mudar o `starcode_common.git()` do banner (5 s, devolve stdout ou `None`).
- Tempo limite nas chamadas da Orca e no `git merge` do `settle`, que passam pelo `runner` injetável.

## Decisions
| Item | Options | Status |
|---|---|---|
| Recibo com texto antes do JSON | ler a partir do primeiro `{` · só sair com 3 | approved - user: "você decide" (ler a partir do primeiro `{`, e sem id sair com 3; default registrado no context.md) |
| Tempo limite do helper | 5 s · 30 s com parâmetro · configurável | approved - user: "você decide" (30 s com parâmetro; default registrado no context.md) |
| Trava do Handoff | por artefato · por feature | approved - user: "você decide" (por feature; default registrado no context.md) |

## Requirements
- **R1** - The `_receipt` (`scripts/dispatch.py`) SHALL ler o recibo do `worker-start` também quando há texto antes do JSON, decodificando o objeto a partir do primeiro `{` da saída.
- **R2** - WHEN o `worker-start` sai com 0 AND o recibo não traz id de despacho THEN o `start` SHALL manter a entrada do `Dispatched` sem o id, imprimir `worker ativo sem id de despacho: <T> · <worktree ou ->: confira com orca orchestration list` e sair com 3. With `--json`, SHALL imprimir o mesmo objeto de recibo de hoje.
- **R3** - WHEN o `git merge` do `settle` falha com arquivos em conflito (`git diff --name-only --diff-filter=U` não vazio) THEN SHALL imprimir `conflito no merge de <T>: <arquivos>`, como hoje. WHEN falha sem arquivo em conflito THEN SHALL imprimir `merge de <T> falhou: <primeira linha do stderr, ou do stdout, do git merge>`. Nos dois casos, SHALL rodar `git merge --abort` só quando houver merge em andamento e sair com 1.
- **R4** - The `set_handoff` (`scripts/handoff.py`) SHALL ler, mudar e gravar os artefatos dentro de `starcode_common.locked(<pasta da feature>/.handoff)`. WHEN dois `set` rodam ao mesmo tempo com mudanças diferentes THEN as duas mudanças SHALL estar no artefato no fim. IF a trava não sair em 5 s THEN o `handoff.py set` SHALL sair com 2 e `handoff ocupado: <pasta da feature>`. The arquivo `.handoff.lock` SHALL estar no `.gitignore`.
- **R5** - The `scripts/starcode_common.py` SHALL ter `run_git(args, cwd, timeout=30, binary=False, env=None)`, que devolve `(código, stdout, stderr)`. Com `binary=True`, a saída vem em bytes. IF o `git` não termina no tempo THEN SHALL devolver código 124 com stderr `git excedeu <n> s: git <args>`. IF o `git` não é encontrado THEN SHALL devolver 127 com stderr `git não encontrado`. SHALL nunca levantar exceção.
- **R6** - The scripts `snapshot.py` (`run_git`, `valid_names`, `_write_blob`), `impact.py` (`run_git`) e `dispatch.py` (`_git`, o `git diff --quiet` da seleção de impacto e o `git status` do `q_check`) SHALL chamar o `git` só por `starcode_common.run_git`. As mensagens e os códigos de saída de hoje SHALL ser mantidos, e o tempo esgotado SHALL sair pelo caminho de erro de cada um (`GitError`, `ImpactError`, `ValueError`) com o texto do stderr.
- **R7** - The `DECISIONS.md` SHALL ter a entrada `### SC-<n>:` com **Problema** (com os quatro casos do R.8 e o estado de cada um), **Decisão**, **Motivo** e **Por que não é bug** (com os testes), e o `CHANGELOG.md` uma linha em `[Unreleased]`.

## Edge Cases
- Recibo só com texto, sem `{`: recibo vazio, R2 vale (código 3).
- Merge que falha por árvore suja: sem arquivo `U`, mensagem com o erro real (R3).
- `run_git` com `binary=True` e erro: stderr também em bytes, decodificado pelo chamador (R5).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Recibo com texto antes do JSON é lido; recibo sem `{` fica vazio (R1)
Proof: run unit | test_recibo_com_texto_antes (test_falhas_start_settle.FalhasStartSettleTests.test_recibo_com_texto_antes) ... ok

**C2** - `worker-start` com 0 e sem id: entrada mantida, linha exata e código 3; com `--json`, o objeto de recibo (R2)
Proof: run unit | test_start_sem_id_sai_com_3 (test_falhas_start_settle.FalhasStartSettleTests.test_start_sem_id_sai_com_3) ... ok

**C3** - Merge com conflito mantém a linha de conflito; merge que falha sem conflito imprime a linha exata com o erro do git; o abort só roda com merge em andamento; código 1 nos dois (R3)
Proof: run unit | test_merge_falha_sem_conflito (test_falhas_start_settle.FalhasStartSettleTests.test_merge_falha_sem_conflito) ... ok

**C4** - Dois `handoff.py set` em processos simultâneos com campos diferentes: os dois valores no fim; trava ocupada dá código 2 e a mensagem exata; `.handoff.lock` ignorado pelo git (R4)
Proof: run unit | test_handoff_concorrente (test_falhas_start_settle.FalhasStartSettleTests.test_handoff_concorrente) ... ok

**C5** - `run_git`: sucesso, falha com código e stderr, tempo esgotado (124 e a mensagem exata), git ausente (127), modo binário (R5)
Proof: run unit | test_run_git (test_falhas_start_settle.FalhasStartSettleTests.test_run_git) ... ok

**C6** - Nenhuma chamada de `subprocess` com `git` em `snapshot.py`, `impact.py` e `dispatch.py` fora do `run_git`; tempo esgotado em cada um sai pelo erro próprio com o texto do stderr (R6)
Proof: run unit | test_scripts_usam_run_git (test_falhas_start_settle.FalhasStartSettleTests.test_scripts_usam_run_git) ... ok

**C7** - Entrada do SC no `DECISIONS.md` com as quatro partes e os termos de cada requisito, e linha no `CHANGELOG.md` (R7)
Proof: run unit | test_decisions_e_changelog (test_falhas_start_settle.FalhasStartSettleTests.test_decisions_e_changelog) ... ok

## Handoff

**Phase:** review
**Size:** MEDIUM
**Git mode:** 3
**Next:** Q verifica
**Linear:** SC-208
**Integration branch:** feature/falhas-start-settle
**Last integrated:** T1 (247cd98)
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
