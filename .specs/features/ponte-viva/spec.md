# Ponte viva: Spec

**Size**: LARGE
**Risk triggers**: concorrência e estado; chamadas externas
**Status**: Approved
**Approved**: 2026-11-23 - user: "sim"

A versão anterior foi aprovada em 2026-11-22; esta revisão altera o comportamento de presença.

## Context
O usuário acompanha agentes StarCode em um painel estreito da Orca. A cena identifica os 12 tripulantes e mantém a presença estável, alterando-a quando o trabalho muda ou o usuário solicita outro integrante, sem confundir presença com atividade real.

## Scope
- Cena da Ponte, apresentação dos 12 integrantes e entradas e saídas animadas por mudança de presença.
- Estado de atividade, atualização automática, recuperação e acessibilidade.
- Testes do modelo, atualização e pintura, além de aceite visual na Orca.

## Non-Goals
- Alterar a execução, os papéis ou a configuração dos agentes.
- Publicar ou implantar sem confirmação para cada ação aplicável.
- Reproduzir literalmente a imagem conceitual ou depender dela como sprite de produção.

## Requirements
- **R1** - WHEN a cena é aberta THEN the system SHALL disponibilizar os 12 integrantes de `src/crew.yaml`, cada um com nome completo e aparência própria inspirada em Star Trek.
- **R2** - WHEN a cena apresenta tripulantes na ponte THEN the system SHALL mostrar no máximo seis por vez, com nome legível junto de cada personagem.
- **R3** - WHILE os estados e a seleção manual não mudam THEN the system SHALL manter os mesmos integrantes presentes, sem rodízio por passagem do tempo.
- **R4** - WHEN uma mudança de presença é necessária THEN the system SHALL animar a saída pelo acesso e a entrada até a estação, sem alterar o estado real dos integrantes.
- **R5** - WHEN um integrante está trabalhando THEN the system SHALL apresentar texto ou símbolo de trabalho e animação de operação do console.
- **R6** - WHEN um integrante está ocioso THEN the system SHALL identificá-lo como ocioso e apresentá-lo sem animação de trabalho.
- **R7** - WHEN um integrante está aguardando, bloqueado ou concluído THEN the system SHALL distinguir seu estado por texto ou símbolo próprio.
- **R8** - IF os dados não permitem identificar com segurança o estado de um integrante THEN the system SHALL identificá-lo como desconhecido, sem inferir que trabalha.
- **R9** - WHEN o usuário abre a relação da tripulação THEN the system SHALL apresentar os 12 nomes, estados e indicação de presença na cena.
- **R10** - WHEN o usuário seleciona na relação um integrante fora da cena THEN the system SHALL trazê-lo à cena sem modificar seu estado real.
- **R11** - WHEN a Orca comunica mudança de agente ou worktree THEN the system SHALL atualizar automaticamente a cena para o worktree em foco.
- **R12** - WHILE o painel estiver aberto THEN the system SHALL reconciliar o estado automaticamente em até 30 segundos, inclusive após perda de evento, sem intervenção do usuário.
- **R13** - IF a atualização falha ou os dados são marcados como antigos THEN the system SHALL indicar a indisponibilidade ou os dados desatualizados e o horário da última atualização válida.
- **R14** - WHEN atualizações concorrentes retornam fora de ordem THEN the system SHALL impedir que a resposta mais antiga substitua o estado mais recente ou o worktree em foco.
- **R15** - WHEN a cena é exibida em painéis de 240 e 360 px de largura THEN the system SHALL manter nomes e indicadores legíveis sem sobreposição ou corte.
- **R16** - WHEN o usuário utiliza teclado ou leitor de tela THEN the system SHALL disponibilizar a relação de integrantes e estados em elementos acessíveis.
- **R17** - WHEN a preferência de movimento reduzido estiver ativa THEN the system SHALL dispensar animações de deslocamento, mantendo acesso manual aos integrantes.
- **R18** - WHEN o estado de um agente não muda entre atualizações THEN the system SHALL preservar sua representação sem reiniciar a transição de entrada ou saída.
- **R19** - WHEN há mais de seis integrantes com atividade ou alerta comprovados THEN the system SHALL priorizar bloqueados e aguardando, depois trabalhando, mantendo os já presentes em caso de mesma prioridade e os demais acessíveis na relação.
- **R20** - WHEN um integrante já presente é acionado na relação THEN the system SHALL manter a composição da cena e o estado do integrante.
- **R21** - WHEN uma sessão é associada a um integrante THEN the system SHALL exigir uma identidade verificável da sessão e do worktree em foco para atribuir seu estado a esse integrante.
- **R22** - IF a identidade ou o worktree de uma sessão não puder ser comprovado THEN the system SHALL manter seu estado como desconhecido e não inferir entrada ou saída por essa sessão.

## Data & Contracts
A fonte da tripulação permanece `src/crew.yaml` e o estado da cena deriva do contrato `PonteState` e dos eventos do plugin. A associação entre integrante, sessão e worktree deve usar identificadores verificáveis; títulos e contagens agregadas por repositório não comprovam essa associação. O mecanismo concreto será definido e validado na implementação.

## States
- Carregando: indicar que o estado está sendo obtido.
- Disponível: mostrar última atualização e estados conhecidos.
- Desatualizado ou erro: identificar o problema, preservar o último retrato quando existir e não apresentá-lo como atual.
- Sem worktree ou projeto StarCode: apresentar mensagem explícita.

## Edge Cases
- Mais de seis integrantes ativos: prioridade estável para as seis vagas; lista sempre completa e seleção manual disponível.
- Troca de Q para Worf: Q sai e Worf entra quando os estados e as identidades dos dois forem comprovados; nenhuma troca é inferida de contagem agregada.
- Atualizações repetidas ou dados incertos não provocam trocas periódicas.
- Mudança de foco enquanto uma consulta está em andamento: descartar resposta obsoleta.
- Agente sem correspondência inequívoca: estado desconhecido.
- Painel estreito ou movimento reduzido: manter acesso textual e seleção manual.
- Falha temporária da Orca: tentar novamente na próxima reconciliação sem acumular consultas.

## Decisions
| Item | Options | Status |
|---|---|---|
| Presença visual | rodízio periódico · presença estável e troca conforme o trabalho | adjusted - user: "O efeito que tinha pensado era deixar fixo na tela apenas quem precisa estar lá, não ficar em loop só pra mostrar todos." |
| Seleção na relação | alternar qualquer integrante · trazer quem está fora e manter quem já está | adjusted - user: "somente para quel esta fora de cena que quando clico nele que ele aparece. Acho que deveria ser assim, pois quem já esta na cena nõa faz sentido clicar nele." |
| Identidade | genérica · tripulação inspirada em Star Trek | approved - user: "Lembre de usar star trek como inspiração" |
| Atualização | manual · automática | approved - user: "sem precisar do usuario ficar clicando em atualizar" |

## Open Questions
None.

## Sources
- `context.md` - non-binding, descoberta da missão.
- Prancha de 12 personagens apresentada no chat - non-binding - user: "gostei."

## Differences from the Source
O desenho final será simplificado para o tamanho do painel e gerado segundo as restrições técnicas do projeto; a prancha é inspiração visual.
