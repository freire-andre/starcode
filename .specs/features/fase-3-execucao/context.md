# Fase 3 — Execução sequencial e verificação: Context

**Size**: LARGE
**Risk triggers**: Concorrência e estado
**Source request**: "Nova missão: Fase 3 do StarCode (SC-10) — Execução sequencial e verificação (LaForge, McCoy, Q) no Claude Code. Escopo e aceite em PLANO_STARCODE.md seção 10 "Fase 3" e na issue SC-10. Usar a issue existente SC-10 no time SC (não criar projeto de teste no SC). Ramo já criado: freireandrem/sc-10-fase-3-execucao-sequencial-e-verificacao-laforge-mccoy-q."

## Problem
O StarCode hoje planeja (Troi → Spock → Data) e publica no Linear, mas para em `published`: não existe quem implemente os tickets, verifique o resultado nem feche o ciclo. A Fase 3 entrega a metade da execução no Claude Code: o Picard cria o ramo de integração e despacha um LaForge por ticket como worker da Orca com contexto limpo, o McCoy entra em gates vermelhos e bugs teimosos, e o Q verifica a feature inteira em outra família de modelo. Inclui o ciclo de correção pós-Q (plano 4.6), o disjuntor e a lista fechada de paradas (4.7, D27, D29) e o escritor único do Handoff (D28).

## Users
- O dono do repositório (usuário do StarCode), que aprova spec e tasks e quer ver os tickets implementados e verificados sem conduzir cada passo.
- O Picard (sessão principal), que coordena e é o único a escrever `STATE.md` e o Handoff.
- Os workers (LaForge, Q), que recebem só o briefing e devolvem um relatório de até 5 linhas.

## Success
- O roteiro de aceite da SC-10 passa no sandbox, com evidência em `docs/aceite/fase-3.md`: modo 2, modo 1, degradado, disjuntor e escritor único.
- Uma feature GRANDE publicada vai de `published` até `review` sem o Picard escrever código, com cada worktree vinculado à sua issue e nascido do ramo de integração.
- `check_proofs` e `validate_verification` verdes no HEAD do ramo de integração; o Q roda em outra família, com o modelo pedido e o efetivo registrados (F0-2).
- Testes unitários, `build --check`, `plugin validate --strict` e evals continuam verdes.

## Constraints
- Só Claude Code nesta fase (D21); paridade com Codex/Antigravity/OpenCode é a Fase 4.
- Picard só coordena (D23): LaForge e Q são workers da Orca via `orca orchestration worker-start`; vínculo com `orca worktree set --linear-issue`.
- Modo sequencial: um ticket por vez. Frota (paralelo) é a Fase 7.
- Q em outra família de modelo (D7): padrão `codex` (crew.yaml); briefing autossuficiente em `src/briefs/q-verify.md` via `--spec-file`; escreve só `verification.md`.
- Gates novos `check_proofs.py` e `validate_verification.py` adaptados do tlc-spec-driven (ADR-0002, D24), escritos sem copiar o método do Genesis.
- Linear: `orca linear` para status, labels e comentários; MCP só para Projeto/Documento (D2).
- Hooks de bloqueio: JSON deny com exit 0 (F0-5). Nunca contornar um hook.
- Skills em inglês, saída em PT-BR; turnos curtos (F2-10).

## Scope Notes
- Dentro (plano, Fase 3): Picard com ramo de integração, despacho do LaForge por ticket, vínculo do worktree, integração no ramo da feature; skills `laforge`, `mccoy`, `q` com `src/briefs/q-verify.md`; ciclo pós-Q; disjuntor e paradas; escritor único.
- Dentro (usuário, 2026-11-04): o Data publica os tickets desta fase como **sub-issues da SC-10** no projeto StarCode existente, sem projeto novo; nada de projeto de teste no time SC.
- Dentro (usuário, 2026-11-04): o aceite usa a feature **task-priority** do sandbox (`F:\Projetos\starcode-sandbox`, time PROJ, PROJ-7..9, 3 tickets em cadeia).
- Fora: Frota (Fase 7), paridade nos outros CLIs (Fase 4), hooks nos outros CLIs (Fase 5), Worf/review de PR (v1.3), verificação de telas (D25), snapshot do modo 1 (Fase 12).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Publicação dos tickets da fase no Linear | sub-issues da SC-10 / projeto novo no SC / não publicar | sub-issues da SC-10 | 2026-11-04 |
| Feature do aceite | task-priority / csv-import-export / feature nova | task-priority | 2026-11-04 |
| CLI do Q | codex / antigravity (Gemini) / opencode | codex; antigravity como alternativa se o codex falhar no despacho — default (não perguntado) | 2026-11-04 |
| Onde roda o McCoy | worker próprio / skill acionada dentro do worker do LaForge / sessão do Picard | skill acionada dentro do worker do LaForge (e pelo usuário); sem worker próprio — default (não perguntado) | 2026-11-04 |
| Aceite do modo 1 | mesma feature num worktree novo a partir do ramo base, sem commits, descartado depois / outra feature | mesma feature (task-priority) num worktree novo a partir do base, sem commits — default (não perguntado) | 2026-11-04 |
| Achado plantado do aceite | o Picard planta uma falha nos checks antes do Q / o usuário planta / um ticket com defeito intencional | o Picard registra no roteiro um defeito plantado (ex.: asserção frouxa num teste) num commit do ramo de integração antes do Q — default (não perguntado) | 2026-11-04 |
| Espera pelo worker | o Picard bloqueia até `worker_done` / o Picard volta e o usuário avisa | o Picard espera o `worker_done` da Orca, com timeout; timeout vira bloqueio no Linear e parada — default (não perguntado) | 2026-11-04 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | O Picard só despacha ticket com briefing de 5 blocos e `May change` válidos (gate `validate_tasks` verde) e com as dependências `blocks` concluídas. |
| Failure and partial failure | Worker que termina com `failed`/timeout: o Picard não integra, comenta no Linear, conta como tentativa do disjuntor e para no 3º erro igual. Integração com conflito no ramo da feature é parada com o diff resumido. |
| Retries, idempotency and duplicates | `**Dispatched:**` gravado antes do envio; ao retomar, um despacho registrado sem `worker_done` é conferido na Orca antes de redespachar (nunca dois workers no mesmo ticket). Integrar o mesmo commit duas vezes é no-op. |
| Authorization boundaries and rate limits | Merge do ticket no ramo da feature não pede autorização (D11); merge no ramo base, push e PR seguem o modo Git. Despacho do Codex exige hooks com trust (F0-1): sem trust é parada por acesso (D29 item 3). |
| Concurrency and ordering | Sequencial: no máximo um LaForge ativo por feature; a ordem segue as relações `blocks`. Workers nunca escrevem `STATE.md` nem o Handoff (D28), conferido pelo diff de cada ticket. |
| Data lifecycle | Worktrees dos tickets ficam após a integração; remoção só com autorização (nunca `branch -D`, bloqueado pelo hook). `verification.md` e `proofs.md` versionados no ramo da feature. |
| Observability | Banner mostra fase, disjuntor aberto e verificação degradada; Linear recebe status e comentários de marco (iniciado, integrado, revisão, degradado). Relatório do worker ≤5 linhas transcrito no Handoff. |
| External dependency failure | Orca ou Linear indisponíveis: para o passo afetado com a linha exata do erro; Linear fora não impede o código local. Modelo recusado pelo CLI: avisa e pergunta, não troca sozinho. |
| State-transition rules | Fases do Handoff: published → execute → review → done. Issue: started (LaForge) → comentário "integrado" (Picard) → review (gates + Q) → completed só com confirmação e nunca no modo 1. `self-verified`/modo 1 marcados como degradados. |

## Facts Found
- Plano: Fase 3 em `PLANO_STARCODE.md` §10; contrato do Q §4.3; ciclo pós-Q §4.6; disjuntor e paradas §4.7; fluxo completo §4; matriz de `--model` §9.2.
- Decisões: D7, D11, D22, D23, D27, D28, D29; F0-1 (trust do Codex), F0-2 (modelo pedido + efetivo), F0-5 (JSON deny) em `DECISIONS.md`.
- Gates existentes: `scripts/gates/{check_commit,run_gates,validate_spec,validate_tasks,tasks_export}.py`; `check_commit.py` já lembra de `check_proofs`/Q/`validate_verification`. Fontes do tlc em `docs/reference/tlc-spec-driven.zip`: `scripts/check_proofs.py`, `scripts/validate_verification.py`, `references/validate.md`.
- Handoff só via `scripts/handoff.py` (F2-10, F2-12); formato em `skills/engajar/references/state-format.md` já prevê `**Dispatched:**`, `**Integration branch:**`, `**Last integrated:**`, `**Breaker:**`.
- `src/crew.yaml`: laforge (claude, Sonnet), mccoy (claude, Opus), q (codex, padrão do CLI). Skills `laforge`, `mccoy`, `q` ainda não existem; o build só as emite quando `skills/<skill>/SKILL.md` existir.
- Fase 0 (`docs/compatibilidade.md`): `worker-start --spec-file --model` passou em Claude, Codex e Antigravity; o resultado traz `model` (pedido). Codex logado (ChatGPT) em 2026-11-04.
- Sandbox: `F:\Projetos\starcode-sandbox`, ramo `chore/starcode-specs`; task-priority com Handoff `published`, projeto P-PROJ-5, issues PROJ-7..9.
