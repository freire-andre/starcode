# Retro: gate-d30-ci

Lições registradas: L27 (nova), L20 (recorrência; promovida a `confirmed`), L28 (nova).

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | Handoff: `proofs-C11=fail`; `spec.md` C11 com `Proof: python scripts/check_decisions.py \| check_decisions: OK` deu exit 127 no `check_proofs` | `validate_spec.py` recusa prova isolada que não esteja entre crases ou que traga ` \| ` fora de `run <nome>`, com a mensagem do formato certo. |
| 2 | alta | instructions without effect | Relatório do worker pós-Q (`ctx_93c60e58477b`): usou `git checkout HEAD --` em arquivo do worktree de integração, que o brief proibia | Bloquear `git checkout -- <arquivo>`, `git restore` e `git stash` no `git_guard` quando o cwd é o worktree de `feature/<slug>`, ou tirar a regra do brief e confiar no Handoff commitado antes do despacho. |
| 3 | média | instructions without effect | `verification.md` achados 2 a 8 (C4-C10); L20 recorrente em duas features | Na spec, o check de uma entrada do `DECISIONS.md` lista os trechos literais que o teste deve exigir (caminho, ordem, condições), e um helper de teste confere a entrada inteira por ID contra essa lista. |
| 4 | média | tool economy | Commit `25ea5e4`: a coluna `Closed` preenchida por script ficou com `\|\|` e o gate `done` deu 8 erros | Subcomando que preenche `Closed` pelo índice do achado e roda o `validate_verification` em seguida (item 3.7 da triagem). |
| 5 | média | tool economy | Handoff: entradas `Dispatched` gravadas à mão para o LaForge e para o Q, porque `dispatch.py start` não aceita feature MÉDIA | Fazer `dispatch.py start` e `settle` aceitarem a spec com `**May change**:` (item R.6 da triagem). |
| 6 | baixa | information access | `verification.md`, seção Limits: provas em `8e1547f` e suíte do Q em `8266cab` | Rodar `run_gates.py proofs` só depois de commitar toda mudança da spec, para o `proofs.md` e o Q verem o mesmo HEAD. |
