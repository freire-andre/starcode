# fase-10-ponte verification

**Verdict**: PASS
**Proofs**: `proofs.md` at 72586cf
**HEAD**: 72586cf
**Verifier**: codex · requested padrão do CLI · effective GPT-6-Luna medium

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_ponte.py` `test_snapshot_keys` | yes |
| C2 | `tests/test_ponte.py` `test_snapshot_crew_ttl` | yes |
| C3 | `tests/test_ponte.py` `test_snapshot_git_mode` | yes |
| C4 | `tests/test_ponte.py` `test_snapshot_feature_choice` | yes |
| C5 | `tests/test_ponte.py` `test_snapshot_feature_fields` | yes |
| C6 | `tests/test_ponte.py` `test_snapshot_workers` | yes |
| C7 | `tests/test_ponte.py` `test_snapshot_sem_starcode` | yes |
| C8 | `tests/test_ponte.py` `test_snapshot_fonte_invalida`, `test_snapshot_handoff_grande_vira_erro` | yes |
| C9 | `tests/test_ponte.py` `test_snapshot_worktree_invalido` | yes |
| C10 | `tests/test_ponte.py` `test_snapshot_somente_leitura` | yes |
| C11 | `src/orca/src/worker.test.ts` `worker acha o worktree em foco pelo ramo` | yes |
| C12 | `src/orca/src/worker.test.ts` `worker sem worktree em foco` | yes |
| C13 | `src/orca/src/worker.test.ts` `worker publica o estado após agent.status.changed` | yes |
| C14 | `src/orca/src/worker.test.ts` `worker agrupa eventos em 300 ms` | yes |
| C15 | `src/orca/src/worker.test.ts` `worker descarta snapshot de foco antigo` | yes |
| C16 | `src/orca/src/worker.test.ts` `worker consulta a issue vinculada e guarda em cache por 60 s` | yes |
| C17 | `src/orca/src/worker.test.ts` `worker sem Linear mostra o ID do Handoff` | yes |
| C18 | `src/orca/src/worker.test.ts` `worker com snapshot falho marca desatualizado` | yes |
| C19 | `src/orca/src/worker.test.ts` `worker atualiza a barra de status` | yes |
| C20 | `tests/test_orca_manifest.py` `test_manifest_toggle_da_barra` | yes |
| C21 | `src/orca/src/panel.test.tsx` `painel pede o estado ao abrir` | yes |
| C22 | `src/orca/src/panel.test.tsx` `painel redesenha com ponte.state` | yes |
| C23 | `src/orca/src/panel.test.tsx` `painel mostra só tripulantes ativos` | yes |
| C24 | `src/orca/src/panel.test.tsx` `painel mostra fase e progresso` | yes |
| C25 | `src/orca/src/panel.test.tsx` `painel casa worker com agente` | yes |
| C26 | `src/orca/src/panel.test.tsx` `painel sem StarCode` | yes |
| C27 | `src/orca/src/panel.test.tsx` `painel com seção indisponível` | yes |
| C28 | `src/orca/src/worker.test.ts` `atalho abre spec tasks e handoff` | yes |
| C29 | `src/orca/src/panel.test.tsx` `atalho abre a issue no navegador` | yes |
| C30 | `src/orca/src/worker.test.ts` `atalho inicia o Picard uma vez` | yes |
| C31 | `src/orca/src/worker.test.ts` `atalho recusa agente que a Orca não lança` | yes |
| C32 | `src/orca/src/worker.test.ts` `atualizar agora ignora o cache` | yes |
| C33 | `tests/test_build.py` `test_build_check_cobre_dist_orca` | yes |
| C34 | `tests/test_install_local.py` `test_install_orca_aprovacao_nunca_automatica` | yes |
| C35 | `tests/test_orca_manifest.py` `test_manifest_capabilities_e_engines` | yes |
| C36 | `tests/test_release_docs_f10.py` `test_release_docs_f10` | yes |
| C37 | `tests/test_acceptance_doc_f10.py` `test_fase10_acceptance_sections` | yes |
| C38 | `src/orca/src/scene-model.test.ts` `cena tem uma estação por tripulante e a engenharia` | yes |
| C39 | `src/orca/src/scene-model.test.ts` `cena senta tripulante ativo e anima a cada 250 ms` | yes |
| C40 | `src/orca/src/scene-model.test.ts` `cena põe o balão no personagem do agente bloqueado` | yes |
| C41 | `src/orca/src/scene-model.test.ts` `cena desenha até 6 workers e +N` | yes |
| C42 | `src/orca/src/scene-model.test.ts` `cena vazia mostra a frase do estado` | yes |
| C43 | `src/orca/src/scene.test.ts` `pintura da cena só lê o modelo e não usa imagem` | yes |
| C44 | `src/orca/src/worker.test.ts` + `src/orca/src/panel.test.tsx` `diário guarda 20 entradas e o painel mostra 10` | yes |
| C45 | `src/orca/src/scene.test.ts` `cena cria o canvas e importa com caminho servido` | yes |
| C46 | `src/orca/src/panel.test.tsx` `painel mostra a nota da issue do Handoff` | yes |
| C47 | `src/orca/src/panel.test.tsx` `painel estreito quebra os atalhos` | yes |
| C48 | `src/orca/src/worker.test.ts` `worker desempata ramo igual pelo nome` | yes |
| C49 | `src/orca/src/worker.test.ts` `worker registra falhas no log` | yes |
| C50 | `src/orca/src/scene-model.test.ts` `cena sem rótulos sobrepostos` | yes |
| C51 | `tests/test_acceptance_doc_f10.py` `test_fase10_limitacoes_registradas` | yes |
| C52 | `src/orca/src/scene-model.test.ts` `cena mostra o telão com fase e progresso` | yes |
| C53 | `src/orca/src/scene-model.test.ts` `cena compacta a engenharia sem workers` | yes |
| C54 | `src/orca/src/scene.test.ts` `cena acende o ativo e conta os ativos no telão` | yes |
| C55 | `src/orca/src/scene-model.test.ts` `cena desenha a ponte em arco com bonecos` | yes |
| C56 | `src/orca/src/scene.test.ts` `cena mostra agora para atividade recente` | yes |
| C57 | `src/orca/src/scene.test.ts` `cena estica o anel e aumenta os bonecos`; `cena cabe no palco sem rolagem` | yes |

## Findings

None.

## Limits

Os exemplos adicionais foram comandos diretos: `linear_ids('')` → `[]`; `linear_ids('SC-1; SC-1; sc-2; SC-3x; SC-4')` → `['SC-1', 'SC-4']`; o limite configurado de fonte é 1.048.576 bytes. Os casos integrados de tamanho acima de 1 MiB, duplicatas, limites de dimensões 240 px e alturas variadas constam nos testes citados; não repeti a suíte conforme instruído.
A regra de seleção em empate de `mtime` em `choose_feature` usa a ordem alfabética dos diretórios, sem check que fixe esse desempate; pode alterar silenciosamente a feature escolhida em empate.
O aceite visual com Orca instalada não foi reproduzido independentemente; usei as provas e os testes disponíveis.
