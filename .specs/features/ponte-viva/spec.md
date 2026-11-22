# Ponte viva: Spec

**Size**: LARGE
**Risk triggers**: concorrência e estado; chamadas externas
**Status**: Approved
**Approved**: 2026-11-22 - user: "aprovado"

## Context
O usuário acompanha agentes StarCode em um painel estreito da Orca. A cena precisa ser animada, identificar os 12 tripulantes e refletir o estado disponível automaticamente, sem confundir rodízio visual com atividade real.

## Scope
- Cena da Ponte, apresentação dos 12 integrantes e rodízio animado.
- Estado de atividade, atualização automática, recuperação e acessibilidade.
- Testes do modelo, atualização e pintura, além de aceite visual na Orca.

## Non-Goals
- Alterar a execução, os papéis ou a configuração dos agentes.
- Publicar ou implantar sem confirmação para cada ação aplicável.
- Reproduzir literalmente a imagem conceitual ou depender dela como sprite de produção.

## Requirements
- **R1** - WHEN a cena é aberta THEN the system SHALL disponibilizar os 12 integrantes de `src/crew.yaml`, cada um com nome completo e aparência própria inspirada em Star Trek.
- **R2** - WHEN a cena apresenta tripulantes na ponte THEN the system SHALL mostrar no máximo seis por vez, com nome legível junto de cada personagem.
- **R3** - WHEN há mais integrantes elegíveis do que posições disponíveis THEN the system SHALL executar rodízio automático que permita ver todos, priorizando alertas e integrantes trabalhando.
- **R4** - WHEN um integrante entra ou sai da seleção visual THEN the system SHALL animar sua passagem pelo acesso à ponte sem alterar seu estado real.
- **R5** - WHEN um integrante está trabalhando THEN the system SHALL apresentar texto ou símbolo de trabalho e animação de operação do console.
- **R6** - WHEN um integrante está ocioso THEN the system SHALL identificá-lo como ocioso e apresentá-lo sem animação de trabalho.
- **R7** - WHEN um integrante está aguardando, bloqueado ou concluído THEN the system SHALL distinguir seu estado por texto ou símbolo próprio.
- **R8** - IF os dados não permitem identificar com segurança o estado de um integrante THEN the system SHALL identificá-lo como desconhecido, sem inferir que trabalha.
- **R9** - WHEN o usuário abre a relação da tripulação THEN the system SHALL apresentar os 12 nomes, estados e indicação de presença na cena.
- **R10** - WHEN o usuário seleciona um integrante na relação THEN the system SHALL trazê-lo à cena sem modificar seu estado real.
- **R11** - WHEN a Orca comunica mudança de agente ou worktree THEN the system SHALL atualizar automaticamente a cena para o worktree em foco.
- **R12** - WHILE o painel estiver aberto THEN the system SHALL reconciliar o estado automaticamente em até 30 segundos, inclusive após perda de evento, sem intervenção do usuário.
- **R13** - IF a atualização falha ou os dados são marcados como antigos THEN the system SHALL indicar a indisponibilidade ou os dados desatualizados e o horário da última atualização válida.
- **R14** - WHEN atualizações concorrentes retornam fora de ordem THEN the system SHALL impedir que a resposta mais antiga substitua o estado mais recente ou o worktree em foco.
- **R15** - WHEN a cena é exibida em painéis de 240 e 360 px de largura THEN the system SHALL manter nomes e indicadores legíveis sem sobreposição ou corte.
- **R16** - WHEN o usuário utiliza teclado ou leitor de tela THEN the system SHALL disponibilizar a relação de integrantes e estados em elementos acessíveis.
- **R17** - WHEN a preferência de movimento reduzido estiver ativa THEN the system SHALL dispensar animações de deslocamento e rodízio automático, mantendo acesso manual aos integrantes.
- **R18** - WHEN o estado de um agente não muda entre atualizações THEN the system SHALL preservar sua representação sem reiniciar a transição de entrada ou saída.

## Data & Contracts
A fonte da tripulação permanece `src/crew.yaml` e o estado da cena deriva do contrato `PonteState` e dos eventos do plugin. Qualquer correspondência entre agente, membro e worker deve ser fundamentada em identificador confiável; quando não for possível, usar estado desconhecido.

## States
- Carregando: indicar que o estado está sendo obtido.
- Disponível: mostrar última atualização e estados conhecidos.
- Desatualizado ou erro: identificar o problema, preservar o último retrato quando existir e não apresentá-lo como atual.
- Sem worktree ou projeto StarCode: apresentar mensagem explícita.

## Edge Cases
- Mais de seis integrantes ativos: rodízio entre ativos; lista sempre completa.
- Mudança de foco enquanto uma consulta está em andamento: descartar resposta obsoleta.
- Agente sem correspondência inequívoca: estado desconhecido.
- Painel estreito ou movimento reduzido: manter acesso textual e seleção manual.
- Falha temporária da Orca: tentar novamente na próxima reconciliação sem acumular consultas.

## Decisions
| Item | Options | Status |
|---|---|---|
| Presença visual | todos simultaneamente · rodízio | adjusted - user: "Não precisa mostrar todos de uma vez, pode ter uma animação de um saindo da ponte para outro entrar" |
| Identidade | genérica · tripulação inspirada em Star Trek | approved - user: "Lembre de usar star trek como inspiração" |
| Atualização | manual · automática | approved - user: "sem precisar do usuario ficar clicando em atualizar" |

## Open Questions
None.

## Sources
- `context.md` - non-binding, descoberta da missão.
- Prancha de 12 personagens apresentada no chat - non-binding - user: "gostei."

## Differences from the Source
O desenho final será simplificado para o tamanho do painel e gerado segundo as restrições técnicas do projeto; a prancha é inspiração visual.
