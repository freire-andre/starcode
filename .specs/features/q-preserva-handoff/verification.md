# q-preserva-handoff verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 62a1af9
**HEAD**: 781e86c
**Verifier**: pending (o coordenador registra CLI e modelos)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_dispatch.py` `test_q_brief_proibe_tocar_no_handoff` | yes |
| C2 | `tests/test_dispatch_qcheck.py` `test_q_check_so_permitidos_sai_0` | yes |
| C3 | `tests/test_dispatch_qcheck.py` `test_q_check_fora_da_lista_sai_1_sem_tocar` | yes |
| C4 | `tests/test_dispatch_qcheck.py` `test_q_check_fora_de_repositorio_sai_2` | no - confere somente o prefixo do stderr; não verifica a mensagem completa nem o motivo informado por `git status`. |
| C5 | `tests/test_dispatch_qcheck.py` `test_execute_commita_handoff_antes_do_q` | no - não verifica que `handoff.py set ... --phase review` seja seguido pelo commit, nem que `q-check` venha logo após `worker_done`. |
| C6 | `tests/test_dispatch_qcheck.py` `test_decisions_q_preserva_handoff` | no - verifica apenas presença dos termos; passaria sem demonstrar que `q-check` é a exceção ao D-i ou que os campos descrevem a decisão. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Renomeação staged entre dois caminhos permitidos é reportada como fora da lista: a saída porcelain `R old -> new` é comparada como se fosse um único caminho. | `scripts/dispatch.py:507`; `python "$env:TEMP\qcheck_rename_probe_sc181.py"` imprimiu literalmente: <br>`porcelain: 'R  .specs/features/demo/verification.md -> .specs/features/demo/screens.md\n'` <br>`q_check: (1, ['fora da lista:  R  .specs/features/demo/verification.md -> .specs/features/demo/screens.md', 'q-check: 1 arquivo(s) fora da lista; desfaça com git restore (rastreados) ou apague (novos)'])` | Interpretar os campos de renomeação do porcelain e permitir quando origem e destino forem ambos caminhos autorizados; cobrir também uma origem ou destino fora da lista. | |
| C4 não fixa a mensagem de erro exigida por R6. | `tests/test_dispatch_qcheck.py:81` | Asserir o stderr completo, incluindo pasta e motivo, além do código 2. | |
| C5 não prova a ordem integral exigida por R7: a busca por `--phase review` e por `commit the Handoff` permite texto intermediário arbitrário, e não compara `q-check` com `worker_done`. | `tests/test_dispatch_qcheck.py:90` | Asserir a sequência concreta do comando de handoff, commit, dispatch e `worker_done` seguido imediatamente pelo único `q-check`. | |
| C6 pode passar sem provar os vínculos semânticos de R8. | `tests/test_dispatch_qcheck.py:104` | Asserir cada campo dentro da entrada e o texto que liga a exceção ao D-i e a decisão a `q-check`/`Handoff`. | |

## Limits

A suíte completa `python -m unittest discover -s tests -v` passou: 910 testes, 0 falhas, 1 ignorado (bit executável indisponível no Windows). Sondas adicionais de `--root` em subdiretório e slug `demo+` passaram; não foi sondada renomeação com um dos caminhos fora da lista.
