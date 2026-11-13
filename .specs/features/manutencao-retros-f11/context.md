# Manutenção das retros da Fase 11 e do patch v1.5.1: Context

**Size**: LARGE
**Risk triggers**: concorrência e estado (item 3: despachos paralelos e o campo `Dispatched`)
**Source request**: "vamos seguir com issue sc-148"

## Problem
As retros da Guinan da Fase 11 (`.specs/features/fase-11-telas/retro.md`) e do patch v1.5.1 (`.specs/features/ponte-missao-ativa/retro.md`) apontaram atritos que custaram rodadas extras: `DECISIONS.md` faltando no May change, `proofs.md` com CRLF no Windows, `Dispatched` sobrescrito com tickets em paralelo, evidência do Q sem comando, arquivos citados no TASK fora do May change, data duplicada no `--report`, `orca plugin test` falhando fora do drive da Orca, mock da Ponte permissivo demais e um exemplo errado no `execute.md`. A SC-148 junta as 9 sugestões aprovadas pelo usuário em 2026-11-12.

## Users
O Picard (coordenador) e os workers (LaForge, Q) que seguem os briefs; o mantenedor do StarCode que lê os registros.

## Success
Cada um dos 9 itens da SC-148 entregue com teste ou doc verificável, sem regressão na suíte.

## Constraints
- Stdlib Python, como o resto de `scripts/`.
- `scripts/` alterado exige entrada F<n> em `DECISIONS.md` (`check_decisions.py`).
- `dist/` regenerado (`tools/build.py --check`).
- Nada de Linear ou Orca nos testes: chamadas externas por injeção (`runner`), como em `tools/install_local.py`.

## Scope Notes
Dentro (texto da SC-148):
1. O `dispatch.py` acrescenta `DECISIONS.md` ao May change quando o ticket tem arquivos de `scripts/`.
2. O `run_gates.py proofs` grava o `proofs.md` em LF (`newline="\n"`); um teste confere que o arquivo gerado no Windows não tem CR.
3. Novos comandos `dispatch.py start` (faz `--dispatch-add`, move a issue, põe a label e chama `worker-start`) e `dispatch.py settle` (faz o merge e o `--dispatch-remove`); tickets em paralelo não sobrescrevem o `Dispatched`.
4. O brief do Q exige que cada sondagem traga o comando e a saída literal na coluna Evidence.
5. O brief de ticket lista no May change todo arquivo citado no TASK e repete a regra de não desligar a assinatura de commits em código de produto.
6. O `handoff.py set --report` não prefixa a data quando o texto já começa com uma data ISO.
7. Documentar que `orca plugin test` e `orca plugin check` (Orca 1.4.257) só rodam com o plugin no mesmo drive da instalação da Orca, e reportar o defeito à Orca.
8. O mock dos testes do painel da Ponte recusa chamadas `host.call` cuja capacidade não está em `orca-plugin.json`.
9. Corrigir o exemplo do `execute.md` para `orca orchestration worker-read --dispatch <id>` e dizer onde ler o modelo efetivo do worker.

Fora (texto da SC-148): o teste da linha Build do tauri (já entregue pela SC-143); um comando para fechar achados no `verification.md`.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Item 5: arquivo citado no TASK fora do May change | gate das tasks recusa e lista / brief acrescenta sozinho | gate das tasks recusa (`run_gates.py tasks` vermelho com a lista; o Data corrige o `tasks.md`) | 2026-11-13 |
| Item 3: `dispatch.py settle` roda o gate do ticket | sim, gate antes do merge / não, só merge | sim: `settle` roda `run_gates.py ticket`; vermelho recusa o merge e mantém a entrada em `Dispatched` | 2026-11-13 |
| Item 7: relato do defeito à Orca | rascunho para o usuário / issue via gh / só documentar | rascunho em `docs/` que o usuário envia; nada sai em nome dele | 2026-11-13 |
| Item 1: onde entra o `DECISIONS.md` | no brief (`dispatch.py brief`) / no gate das tasks | no brief, como diz a SC-148: o `dispatch.py brief` acrescenta e não duplica - default (não perguntado) | 2026-11-13 |
| Item 3: falha no Linear durante o `start` | parar / avisar e seguir | avisar e seguir (o despacho não depende do Linear) - default (não perguntado) | 2026-11-13 |
| Item 3: tipo de merge do `settle` | `--no-ff` no ramo de integração / squash | `git merge --no-ff` no ramo de integração, como o `execute.md` já faz - default (não perguntado) | 2026-11-13 |
| Item 4: como o brief do Q exige a evidência | só texto do brief / texto + gate | só texto do brief (sem gate novo) - default (não perguntado) | 2026-11-13 |
| Item 6: o que conta como data ISO | `AAAA-MM-DD` no início / qualquer data no texto | `AAAA-MM-DD` no início do texto (com ou sem hora) - default (não perguntado) | 2026-11-13 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | `dispatch.py start/settle` recusam ticket inexistente, sem `**Linear**` ou já despachado, com mensagem e exit 2. `--report` reconhece data ISO só no início (`AAAA-MM-DD`). |
| Failure and partial failure | `start`: se o `worker-start` falhar depois do `--dispatch-add`, remove a entrada que acabou de gravar e devolve o erro; falha no Linear não impede o despacho, mas é relatada. `settle`: merge com conflito aborta o merge e mantém a entrada em `Dispatched`. |
| Retries, idempotency and duplicates | `start` de um ticket já em `Dispatched` recusa; `settle` de um ticket sem entrada recusa sem tocar no Git. `--dispatch-add` já substitui a entrada do mesmo `<Tn>` (`scripts/handoff.py:141`). |
| Authorization boundaries and rate limits | N/A because os comandos rodam localmente com as credenciais do usuário; não há novo limite. |
| Concurrency and ordering | Dois `start` seguidos para tickets diferentes deixam as duas entradas em `Dispatched`; um `settle` remove só a do seu ticket. |
| Data lifecycle | N/A because nada novo é guardado além das entradas do Handoff que já existem. |
| Observability | `start` e `settle` imprimem uma linha por passo (Handoff, Linear, worker, merge) e o resultado final. |
| External dependency failure | Orca ou Linear indisponível: `start` para antes do `worker-start` se a Orca faltar; Linear indisponível vira aviso. |
| State-transition rules | A issue vai para o estado "started" do repo config no `start`; o `settle` não move a issue (o Done continua no fim da feature, pelo fluxo atual). |

## Facts Found
- `scripts/handoff.py` já tem `--dispatch-add` e `--dispatch-remove` por ticket (linhas 10-12, 141, 223-226); o problema da retro foi o Picard gravar à mão, não a falta da operação.
- `scripts/handoff.py:123`: `stamp = f"{today or dt.date.today().isoformat()}: {text}"` prefixa sempre.
- `scripts/gates/check_proofs.py:203` grava `proofs.md` com `write_text` sem `newline`, o que no Windows vira CRLF.
- `scripts/dispatch.py:329-330` monta o May change do brief a partir de `tasks.md`; subcomandos atuais: next, batch, brief, q-brief, screens-brief, family, q-cli, overdue.
- `skills/engajar/references/execute.md:108` e `:204` citam `worker-show <dispatch>`; `:149` cita `worker-read <dispatch> --source auto` (sem `--dispatch`).
- O mock do `host.call` da Ponte está em `src/orca/src/worker.test.ts`; o manifesto em `src/orca/orca-plugin.json`.
- O brief do Q é `src/briefs/q-verify.md`.
- Memória do projeto: `orca plugin test` falha no F: porque o harness não acha o `orca-runtime.mjs` fora do drive C:.
