# Ponte viva: Context

**Size**: LARGE
**Risk triggers**: concorrência e estado; chamadas externas
**Source request**: "pode seguir o proximo passo para desenhar os 12 visuais a partir dos nomes e papéis reais da tripulação. Lembre de usar star trek como inspiração, já que o nome dos agentes remete a tripulação de startrek."; "Pode montar o plano para implementar essa nova ponte? Vc vai montar o plano e executar ele. Mas antes uma duvida a ponte vai ser atualizada automaticamente sem precisar do usuario ficar clicando em atualizar."

## Problem
A cena precisa comunicar com clareza a atividade dos 12 agentes em um painel estreito, mantendo-se atualizada sem exigir uma ação manual.

## Users
Pessoas que acompanham missões StarCode no painel da Orca.

## Success
A tripulação tem visuais e nomes distinguíveis; o painel mostra trabalho, espera e ociosidade com base no estado disponível, atualiza-se automaticamente e torna visível quando os dados não são confiáveis.

## Constraints
- Preservar a identidade de ponte espacial em pixel art inspirada em Star Trek e os nomes e papéis em `src/crew.yaml`.
- Respeitar as convenções de geração de `dist/` e registro de decisões do repositório.
- Não confundir a presença na cena com o estado real do agente.

## Scope Notes
- Até seis personagens na ponte, com rodízio e transições de entrada e saída.
- Os 12 agentes devem ser identificáveis por nome e visual; apresentar quem está trabalhando ou ocioso, inclusive fora da cena.
- Atualização automática, sem depender do botão Atualizar.
- A prancha aprovada é referência conceitual, não uma captura obrigatória nem um sprite de produção.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Capacidade e rodízio | mostrar todos · rodízio | "Não precisa mostrar todos de uma vez, pode ter uma animação de um saindo da ponte para outro entrar" | 2026-11-22 |
| Referência visual | visuais genéricos · tripulação inspirada em Star Trek | "Lembre de usar star trek como inspiração"; "gostei." | 2026-11-22 |
| Priorização | ativos primeiro · rodízio igual | ativos e alertas primeiro, com lista completa; default (não perguntado) | 2026-11-22 |
| Dados incertos | inferir atividade · indicar desconhecido | indicar desconhecido; default (não perguntado) | 2026-11-22 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | Tolerar campos ausentes e não atribuir estado sem evidência; até seis personagens visíveis. |
| Failure and partial failure | Exibir erro ou dados desatualizados sem representar o último estado como atual. |
| Retries, idempotency and duplicates | Reconciliar periodicamente e após eventos, sem sobrepor requisições nem animar estados repetidos como eventos novos. |
| Authorization boundaries and rate limits | Preservar capabilities existentes; limitar frequência de atualização. |
| Concurrency and ordering | Ignorar respostas mais antigas e preservar foco no worktree atual. |
| Data lifecycle | N/A: sem novo estado persistido previsto. |
| Observability | Mostrar última atualização e erros relevantes. |
| External dependency failure | Orca indisponível produz indicação de indisponibilidade ou dados antigos. |
| State-transition rules | Animar mudanças de apresentação sem alterar o estado real do agente. |

## Facts Found
- `src/crew.yaml` define os 12 integrantes e seus papéis.
- `src/orca/src/scene-model.ts` define a cena e usa a contagem de sessões da tripulação.
- `src/orca/src/worker.ts` escuta eventos `agent.status.changed` e `workspace.changed`.
- `src/orca/src/protocol.ts` inclui `stale`, `updatedAt` e estados dos agentes; a correspondência com workers pode ser ambígua.
