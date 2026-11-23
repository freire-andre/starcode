# Revisão: ponte-viva

**Round**: 1
**Verdict**: COMMENT
**Reviewer**: codex · modelo não confirmado

## TL;DR

Há três falhas reproduzíveis na seleção e na confiabilidade dos estados, além de conversões que contornam tipos sem justificativa. O PR precisa de correções antes de solicitar merge.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | should-fix | `src/orca/src/scene.ts:398` | Acionar alguém já presente substitui a seleção anterior e pode retirar quem foi trazido manualmente. | Selecionar Q e depois Picard, com seis integrantes trabalhando, inicia a saída de Q; `scene-model.ts:283`. | confirmed |
| W2 | should-fix | `src/orca/src/crew-visual.ts:112` | Um `sessions.json` inválido produz contagens zero e pode aparecer como ociosidade, sem aviso. | `scripts/ponte.py:96` e `src/orca/src/worker.ts:489`; com erro de JSON no snapshot e sem agentes, Spock retorna `ocioso`. | confirmed |
| W3 | should-fix | `src/orca/src/crew-visual.ts:121` | Comparar caminhos sem distinguir maiúsculas também em sistemas sensíveis a caixa pode vincular worktrees distintos. | `/repo/Foo` no registro e `/repo/foo` no foco produzem vínculo para Spock. | confirmed |
| W4 | should-fix | `src/orca/src/scene.ts:599` | Conversão dupla de `document` contorna a verificação de tipos sem justificativa vinculada a issue. | `src/orca/src/scene.ts:599`. | confirmed |
| W5 | should-fix | `src/orca/src/scene.test.ts:317` | Dublês de testes contornam tipos sem justificativa vinculada a issue. | `src/orca/src/scene.test.ts:317`, `src/orca/src/worker.test.ts:1051` e `src/orca/src/worker.test.ts:1079`. | confirmed |

## Escada determinística

- `python tools/build.py --check`: passou.
- `python scripts/check_decisions.py`: passou.
- `claude plugin validate dist/claude --strict`: passou.
- `orca plugin test src/orca`: 117 passaram.
- `scan_bypasses.py`: cinco candidatos; um em `dist/` gerado, excluído do review; os quatro restantes estão agrupados em W4 e W5.
- `python -m unittest discover -s tests -v`: não reexecutado nesta rodada; o worker da compatibilidade relatou 1116 testes aprovados, com um ignorado.

## Pesquisa

- https://github.com/stablyai/orca/blob/main/docs/reference/plugin-host-api.md — contrato de `agents.list` e eventos.
- https://github.com/stablyai/orca/blob/main/docs/reference/plugin-authoring.md — superfície e limites da API.

Arquivos gerados em `dist/` foram excluídos da análise de código.
