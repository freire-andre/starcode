# Fase 7: Modo Frota (v1.1): Context

**Size**: LARGE
**Risk triggers**: Concorrência e estado (workers em paralelo, timeout, falha parcial, dono de arquivo)
**Source request**: "vamos seguir com a fase 7, lembre de atualizar o linear". Aqui, Fase 7 = Fase 7 do PLANO_STARCODE.md, issue SC-14: "Despacho paralelo com todos os limites da seção 4.4. Aceite: 3 tickets em paralelo em CLIs/modelos diferentes, todos a partir do ramo de integração, sem arquivo alterado fora da lista; ticket com lockfile recusado no lote; worker parado vira bloqueio no Linear pelo timeout; um ticket com falha não afeta os outros."

## Problem
Hoje o Picard despacha os tickets de uma feature GRANDE **um por vez** (`references/execute.md`, seção 2: "one at a time per feature"). O `dispatch.py next` devolve só o primeiro ticket liberado e sai com código 3 se o Handoff tiver um despacho aberto. O campo `**Dispatched:**` guarda um único ticket, e o `crew.json` ao vivo marca o LaForge como 0/1. Numa feature com tickets independentes, o tempo total é a soma de todos os tickets, mesmo quando eles não tocam nos mesmos arquivos.

A seção 4.4 do plano define o Modo Frota: despachar em paralelo os tickets independentes, com limites de segurança (fronteira, arquivos sensíveis, lote máximo com custo e confirmação, timeout, cancelamento e falha parcial).

## Users
- O dono do repositório, que roda features GRANDE/COMPLEXA com o Picard e quer reduzir o tempo de execução sem perder o controle (confirmação por lote, nada de merge automático em `main`).
- O Picard, que precisa de um cálculo determinístico do lote (scripts) em vez de julgar a fronteira na conversa.

## Success
- Com 2 ou mais tickets elegíveis, o Picard propõe um lote. Para cada ticket, mostra o ticket, o CLI, o modelo e a faixa de custo, e no fim a faixa total do lote. Ele pede uma confirmação. Depois despacha os workers em paralelo, todos a partir de `feature/<slug>`.
- A fronteira do lote é calculada por script. Um ticket entra no lote só se não tiver `blocks` pendente, não tiver arquivo do `May change` em comum com um ticket ativo ou com outro do lote, e não tocar em arquivo sensível. Ticket com arquivo sensível (lockfile, por exemplo) fica fora do lote e roda sozinho.
- Cada worker termina e é integrado assim que chega: gates do ticket, depois `merge --no-ff` em `feature/<slug>`. Os outros continuam rodando.
- Worker que passa do timeout vira bloqueio no Linear (estado `blocked` se o time tiver, senão um comentário) e o Picard avisa. Não há relançamento automático.
- Um ticket que falha volta para a fila com o motivo, os dependentes dele continuam bloqueados e os outros tickets do lote seguem normalmente.
- Aceite real no `starcode-sandbox` (time PROJ), com evidência em `docs/aceite/fase-7.md`:
  - 3 tickets em paralelo, em CLIs/modelos diferentes, sem arquivo alterado fora do `May change`;
  - um ticket com lockfile recusado no lote;
  - um worker parado que vira bloqueio pelo timeout;
  - uma falha isolada.

## Constraints
- Base no fluxo da Fase 3 (D22 ramo de integração, D23 Picard só coordena, D28 escritor único). O caminho sequencial continua igual quando o lote tem 1 ticket.
- Merge nunca automático em `main`. A integração em `feature/<slug>` dispensa autorização extra (D11).
- `worker-abandon`/`worker-stop` e a remoção de worktree só com confirmação. O worktree de um ticket cancelado é preservado.
- Nada de preço inventado (STARCODE.md "Facts, never guesses"). O custo é uma faixa relativa declarada.
- Python só com stdlib. `dist/` gerado pelo `build.py` no mesmo commit da fonte (F3-1). Decisões novas registradas no `DECISIONS.md` (D30).
- OpenCode no aceite só com modelos gratuitos. Codex exige o trust dos hooks dado pelo usuário (F0-1).
- Limite de aninhamento da Orca ≥ 2 para o Picard despachar (já está em 3).
- Testes do Linear só no time PROJ do sandbox, nunca no time SC.

## Scope Notes
- Dentro (plano 4.4): despacho paralelo com `--deps` (das relações `blocks`), `--timeout-ms`, `--spec-file` e `--base-branch feature/<slug>`; `orca worktree set --linear-issue`; ticket ativo segundo o Handoff + Linear; fronteira; arquivos sensíveis (padrão + `sensitiveFiles` do repo); lote máximo N (`fleet.maxBatch`, padrão 3) com custo e confirmação; timeout → bloqueio; cancelamento preserva o worktree; falha parcial isolada.
- Dentro (usuário, 2026-11-07): pool `fleet.workers` no config do usuário com troca na confirmação; custo em faixa relativa; integração assim que cada worker termina; oferta do lote a cada rodada.
- Dentro (default): `crew.json` ao vivo passa de 0/1 para a contagem de workers ativos do LaForge (alimenta a Fase 10).
- Fora: painel "Ponte" (Fase 10); Uhura/Worf (Fases 8–9); relançamento automático; merge automático em `main`; paralelismo entre features diferentes; paralelismo no modo Git 1 (um único worktree, sem commits).
- "lembre de atualizar o linear": a SC-14 recebe status e comentários de progresso a cada etapa (Picard).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| CLI/modelo por ticket | pool `fleet.workers` no config + troca na confirmação / campo `Agent:` no ticket / só na confirmação | Pool no config + troca | 2026-11-07 |
| Estimativa de custo | faixa relativa por modelo (grátis/$/$$/$$$) / tokens estimados / preço em US$ | Faixa relativa | 2026-11-07 |
| Momento da integração | assim que cada worker termina / no fim do lote | Assim que termina | 2026-11-07 |
| Ativação | oferta a cada lote com ≥2 elegíveis / opt-in por feature / sempre que elegível | Oferta a cada lote | 2026-11-07 |
| Q com LaForges de famílias diferentes | Q numa família diferente de todas as usadas no lote; se não houver, verificação degradada | default (não perguntado) | 2026-11-07 |
| Timeout do worker | `fleet.timeoutMinutes` (padrão 30) / 60 min do sequencial | `fleet.timeoutMinutes`, padrão 30 — default (não perguntado) | 2026-11-07 |
| Pool vazio ou ausente | todos usam o LaForge efetivo (crew) | default (não perguntado) | 2026-11-07 |
| Conflito de merge com o lote em andamento | aborta o merge daquele ticket, ticket volta à fila com os arquivos, os outros seguem | default (não perguntado) | 2026-11-07 |
| Modo Git 1 | Frota indisponível, segue sequencial com aviso de uma linha | default (não perguntado) | 2026-11-07 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | `fleet.maxBatch` 1–10 e `fleet.timeoutMinutes` 1–1440 já validados; `fleet.workers` validado (lista única de `cli:model`, CLI conhecido); faixa de custo só de valores declarados; ticket sem `May change` nunca entra em lote. |
| Failure and partial failure | Falha de um worker não interrompe os outros; o ticket volta à fila com o motivo; o disjuntor (D27) conta tentativas por ticket; dependentes continuam bloqueados. |
| Retries, idempotency and duplicates | Sem relançamento automático; redespacho só pelo fluxo existente (nova tentativa conta no disjuntor); `next`/lote nunca devolve um ticket já ativo ou integrado (evidência do Git + Handoff), então reexecutar o cálculo não duplica despacho. |
| Authorization boundaries and rate limits | Confirmação por lote (D29 item 6); `worker-stop`/`abandon` e remoção de worktree só com confirmação; N máximo limita a carga concorrente nos CLIs. |
| Concurrency and ordering | Dono de arquivo: nenhum arquivo em comum entre tickets ativos; arquivos sensíveis rodam sozinhos; integração serializada pelo Picard (um merge por vez em `feature/<slug>`) na ordem de chegada; Handoff com escritor único. |
| Data lifecycle | Worktrees de tickets cancelados preservados até confirmação; `crew.json`/`progress.json` ao vivo continuam fora do Git. |
| Observability | Handoff registra todos os despachos ativos (ticket, issue, base, dispatch id, modelo pedido); `crew.json` mostra a contagem de LaForges ativos; comentário no Linear por despacho, integração, falha e timeout. |
| External dependency failure | Falha no `worker-start` de um ticket (trust do Codex, aninhamento, CLI indisponível) não cancela os já iniciados; é relatada por ticket com as mesmas paradas do sequencial. |
| State-transition rules | Ticket: na fila → ativo (despacho gravado antes do envio) → integrado / falhou (volta à fila) / bloqueado (timeout) / cancelado (worktree preservado). Linear: `started` no despacho, `blocked` ou comentário no timeout, `completed` só no fim com evidência. |

## Facts Found
- Despacho sequencial e regras: `src/skills/engajar/references/execute.md` (seção 2 "one at a time per feature"; timeout padrão 3600000 ms).
- `scripts/dispatch.py next` devolve o 1º ticket liberado e sai 3 com despacho aberto (`handoff_values(...)["dispatched"]`, um só valor); a integração vem do Git (`Refs:` ou `integra T<n>`).
- Configs: `schemas/config.md` e `scripts/config/validate_config.py` já têm `fleet.maxBatch` (1–10, padrão 3), `fleet.timeoutMinutes` (1–1440, padrão 30) e `sensitiveFiles` no repo; ainda sem `fleet.workers`.
- Linear sem estado bloqueado: `linear-contract.md` linha 41 ("`blocked` if it exists; otherwise a comment"). SC e PROJ têm `blocked: null`.
- `scripts/crew_live.py set <member> 0|1` (F6-7) e `progress` (F6-8).
- Orca 1.4.251: `worker-start` aceita `--deps <json_array>`, `--timeout-ms <ms>` ("Maximum wait time before timing out"), `--base-branch`, `--spec-file`, `--model`; OpenCode precisa de worktree existente. Ainda não conferido se `--timeout-ms` limita a duração do worker ou só a espera do início.
- Famílias de modelo e escolha do CLI do Q: `dispatch.py family` / `q-cli`.
