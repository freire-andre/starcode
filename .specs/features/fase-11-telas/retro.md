# Retro: fase-11-telas

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | informação acessível | commit c9b8a63 (segunda rodada da correção pós-Q só para a entrada F11-10) | Quando o brief de correção ou de ticket tem arquivos de `scripts/` no May change, o `dispatch.py` acrescenta `DECISIONS.md` automaticamente, porque o `check_decisions` exige a entrada. |
| 2 | alta | checagens automáticas | aviso de CRLF no `proofs.md` nos commits 22b2a1b e e640bea | O `run_gates.py proofs` grava o `proofs.md` com `newline="\n"`, e um teste confere que não há CR no arquivo gerado no Windows. |
| 3 | média | economia de ferramentas | Handoff `**Dispatched:** T10 · SC-145 ...` registrado com o T9 ainda ativo | Um comando `dispatch.py start` que faz `--dispatch-add`, move a issue no Linear, põe a label e chama `worker-start`, e um `dispatch.py settle` que faz o merge e o `--dispatch-remove`, para que tickets paralelos não sobrescrevam o `Dispatched`. |
| 4 | média | regras do revisor | verification.md achado 2 × commit cf601b4 (o exemplo `junkhttps://` já era recusado; o furo real era o fim da URL) | O brief do Q exige que cada sondagem traga o comando e a saída literal na coluna Evidence. |
| 5 | baixa | checagens automáticas | Handoff `**Reports:** 2026-11-12: 2026-11-12: ...` | O `handoff.py set --report` não prefixa a data quando o texto já começa com uma data ISO. |
| 6 | baixa | checagens automáticas | issue SC-143 (linha Build do scaffold com `cd src-tauri` duplicado) | Um teste do perfil tauri executa a linha Build do `checks` gerado num diretório de exemplo e falha com `cd` repetido. |
