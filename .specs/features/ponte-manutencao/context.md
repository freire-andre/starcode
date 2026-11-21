# Ponte-manutencao: Context

**Size**: MEDIUM
**Risk triggers**: none
**Source request**: "PROXIMO PASSO" (missão 2 do passo 4 da seção 12 da triagem v2: itens C.4, C.8 e C.9; decisão D-k: "Só manutenção. Corrigir C.4 e C.8, congelar a Cena e não acrescentar nada até os testes do painel rodarem no CI (C.9)")

## Problem
- **C.4**: o painel Ponte não mostra o modelo dos workers despachados pelo `dispatch.py start`. O `start` grava a entrada do `**Dispatched:**` como `<Tn> · <issue> · base <sha> · <cli>:<modelo> · <UTC> [· <dispatch id>]`, mas o `ponte.py` procura os campos `dispatch <id>` e `model <m>`, que ninguém grava. Cada script lê a entrada à sua maneira.
- **C.8**: quatro pontas soltas no plugin da Orca:
  - a capacidade `storage:own` é declarada e não é usada;
  - o `issue.url` vindo da Orca é aceito sem conferir o endereço;
  - `agentFor` casa por trecho, então `T1` pega o agente de `T10`;
  - o nome do worktree não separa caminhos com barra invertida (Windows).
- **C.9**: no CI, o passo `orca plugin validate` fica verde sem rodar nada quando não há `orca` no PATH. Quem lê o CI acha que o painel foi conferido.

## Users
- O dono do repositório, que acompanha os workers pelo painel Ponte na Orca.
- Quem lê o resultado do CI.

## Success
- Um worker despachado pelo `start` aparece no painel com `<cli>:<modelo>`.
- O `T1` nunca é ligado ao agente de `T10`.
- Um endereço de issue fora de `https://linear.app/` não é aberto.
- O nome do worktree sai certo com `\` e com `/`.
- O manifesto não declara capacidade sem uso.
- No CI sem `orca`, o passo deixa um aviso visível e uma linha no resumo do job dizendo que foi pulado.

## Constraints
- D-k: só manutenção. A Cena fica congelada; nada novo no painel.
- `dist/` é gerado por `tools/build.py`. O D30 exige entrada no `DECISIONS.md`.
- Os testes TypeScript (`src/orca/src/*.test.ts`) só rodam com `orca plugin test` num worktree no drive C: (`docs/compatibilidade.md:150`).
- O Actions está sem minutos até 2026-12-01: a mudança do `ci.yml` não é exercitada de verdade antes do merge.

## Scope Notes
- Dentro: C.4, C.8 e C.9, como descritos na triagem v2 (linhas 138, 142 e 143).
- Fora:
  - versionar os tipos da Orca, criar `package.json` ou rodar `tsc` no CI (opção recusada no C.9);
  - qualquer recurso novo no painel ou na Cena (D-k).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| C.9: como tratar os testes do painel no CI | pulo visível (aviso + resumo) / versionar os tipos da Orca e rodar tsc | Pulo visível (Recomendado) | 2026-11-20 |
| C.4: formato do modelo exibido | `<cli>:<modelo>` como gravado / só `<modelo>` | `<cli>:<modelo>`, igual ao gravado pelo `start` — default (não perguntado) | 2026-11-20 |
| C.4: entradas antigas (`dispatch <id> · model <m>`) | continuar lendo / ignorar | continuar lendo, para não apagar o modelo das features antigas — default (não perguntado) | 2026-11-20 |
| C.8: `issue.url` fora do padrão | descartar (`null`) / montar o endereço pelo identificador | descartar (`null`); o painel já monta o endereço pela chave do workspace quando ela existe (`worker.ts:271`) — default (não perguntado) | 2026-11-20 |
| C.8: casamento de agente | token inteiro no título / igualdade exata | token inteiro (delimitado por não alfanumérico) — default (não perguntado) | 2026-11-20 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | O leitor do `Dispatched` aceita os dois formatos (o atual do `start` e o antigo), com o último campo `blocked` e sem o dispatch id; campo ausente vira `None`, nunca exceção. O `issue.url` só passa se começar com `https://linear.app/`. |
| Failure and partial failure | Uma entrada malformada não derruba o painel: o worker aparece sem modelo. |
| Observability | O CI sem `orca` emite `::warning::` e escreve no `GITHUB_STEP_SUMMARY`. |
| Demais dimensões | N/A para este escopo. |

## Facts Found
- `scripts/dispatch.py:820-860`: o `start` grava `f"{tid} · {issue} · base {sha} · {cli}:{model} · {stamp}"`, com ` · <dispatch id>` no fim depois do `worker-start`.
- `scripts/dispatch.py:340-350`: `overdue` lê o horário como `parts[4]` e pula as entradas com o último campo `blocked`. `scripts/dispatch.py:908-913`: `settle` lê a base com `_entry_base`. Cada leitor parte a entrada por conta própria.
- `scripts/handoff.py:149-155`: `dispatch_entries` e `entry_ticket` são o único código comum hoje.
- `scripts/ponte.py:138-150`: `parse_dispatched` espera `dispatch <ctx> · model <m>`; a fixture `tests/fixtures/ponte/tasks-ativa.md:17` usa esse formato, que o `start` nunca grava.
- `src/orca/src/panel.tsx:200`: mostra `w.model`. `src/orca/src/panel.tsx:103-106`: `agentFor` usa `title.includes(k)`.
- `src/orca/src/worker.ts:305`: `url: issue.url ?? null`, sem conferir. `src/orca/src/worker.ts:271`: monta `https://linear.app/${key}/issue/${id}`.
- `src/orca/src/worker.ts:371`: `path.split(/[\/]/)` separa só `/`.
- `src/orca/orca-plugin.json:55-61`: declara `storage:own`; nenhum código fora de `worker.test.ts:980` o usa.
- `.github/workflows/ci.yml:53-55`: o passo `orca plugin validate` só faz `echo` quando falta `orca`.
