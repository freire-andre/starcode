# Q preserva o Handoff: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "proximo passo" → passo 9 do primeiro corte: item 1.1 ampliado de `starcode-triagem-v2-2026-11-13.md` (seção 4)

## Problem
O Q deve escrever só `verification.md`, mas nenhuma regra do brief cita o `## Handoff`. Na fase 12, o Q (codex) restaurou o `tasks.md` e apagou o Handoff não commitado (retro `fase-12-robustez`, item 2). Hoje o Picard desfaz à mão (`execute.md`, seção 4, passo 7), e o `handoff.py set --phase review` roda depois do commit das provas, então o Handoff está sujo quando o Q começa.

## Users
O Picard (coordenador) e quem retoma uma missão pelo Handoff.

## Success
- O Handoff está commitado quando o Q é despachado; nada do que o Q fizer apaga estado do Picard.
- Logo após o `worker_done` do Q, um comando diz, com saída 1 e a lista, se o Q mexeu em arquivo fora da lista permitida.

## Constraints
- Congelamento D-i (triagem v2, seção 8): nenhuma skill, comando ou perfil novo antes do fim do primeiro corte. O subcomando `q-check` é exceção registrada, porque é o próprio item 1.1 do corte.
- O comando nunca apaga nem restaura arquivo.

## Scope Notes
- Dentro: o Picard commita o Handoff antes de despachar o Q; regra explícita no brief do Q sobre o Handoff e sobre não restaurar ou descartar arquivos; subcomando `dispatch.py q-check` que compara o `git status` com a lista permitida.
- Fora: qualquer outro item da triagem.

## Gray Areas

| Item | Options | User answer | Date |
|---|---|---|---|
| Onde fica a checagem | subcomando `dispatch.py q-check` / regra no gate `done` / só texto | `dispatch.py q-check`, rodado pelo Picard logo após o `worker_done` do Q; exceção registrada ao D-i ("Subcomando dispatch.py q-check") | 2026-11-15 |
| O que acontece com arquivo fora da lista | só relata / desfaz sozinho | só relata: saída 1 com a lista; o Picard desfaz com `git restore`, seguro porque o Handoff já está commitado ("Só relata") | 2026-11-15 |
| Lista permitida | só `verification.md` / também `screens.md` e as fotos | `.specs/features/<slug>/verification.md`, `screens.md` e `captures/*.running.png` da feature (o juiz de telas escreve as fotos, `src/briefs/screens-verify.md:24`). Default (não perguntado) | 2026-11-15 |
| Arquivo novo não rastreado fora da lista | conta / ignora | conta como alteração do Q. Default (não perguntado) | 2026-11-15 |
| Onde roda o `q-check` | worktree do Q / pasta principal | no worktree onde o Q trabalhou (`--root`, padrão a pasta atual). Default (não perguntado) | 2026-11-15 |
| Ordem no `execute.md` | Handoff depois das provas / antes do despacho | `handoff.py set --phase review` e commit do Handoff antes do `worker-start` do Q. Default (não perguntado) | 2026-11-15 |

## Implicit Requirements

| Dimension | Requirement or N/A because ... |
|---|---|
| Failure and partial failure | `git status` que falha (fora de repositório Git) dá saída 2 com mensagem, nunca "limpo" |
| Observability | A saída lista cada arquivo fora da lista, um por linha, com o estado do `git status` |

Demais dimensões: N/A para este escopo.

## Facts Found
- `src/briefs/q-verify.md:22-24`: regra 1, "Write only `{{output}}` ... `git status` must show only `{{output}}` changed"; não cita o Handoff nem proíbe restaurar arquivos.
- `skills/engajar/references/execute.md`, seção 4: passo 2 commita `proofs.md` e depois roda `handoff.py set --phase review` (Handoff fica sujo); passo 4 registra `--dispatched` e despacha; passo 7 manda o Picard descartar as mudanças extras do Q com `git restore`.
- `src/briefs/screens-verify.md:24,32`: o juiz de telas escreve `screens.md` e os `captures/*.running.png`.
- `scripts/dispatch.py`: `q_brief` (`:472`), parser dos subcomandos (`:889-895`) e despacho (`:945-949`).
- Retro `fase-12-robustez`, item 2: o Q restaurou o `tasks.md` e apagou o Handoff não commitado.
