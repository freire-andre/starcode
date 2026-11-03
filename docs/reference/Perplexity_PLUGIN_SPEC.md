# Especificação do Plugin — Orca + Linear para Claude Code

## Decisões de produto

| Decisão | Escolha |
|---|---|
| Integração com Linear | Exclusivamente `orca linear`, sem MCP adicional do Linear |
| Criação de issues | Permitida |
| Criação de projetos | Permitida |
| Transição de status | Automática pelo agente |
| Git/PR | Definido por pergunta no início da sessão |
| Workspaces e times | Suporte a múltiplos |
| Worktree | Um worktree por tarefa/issue, sempre que possível |

## Arquitetura

```text
Claude Code
   ↓ lê CLAUDE.md / skills
Orca CLI (`orca`)
   ├── worktrees, terminais, arquivos, navegador
   └── `orca linear`
          ↓ API/token já configurado na Orca
       Linear (múltiplos workspaces/times)
```

A Orca já mantém a conexão autenticada com o Linear por meio de **Settings → Integrations → Linear**. O plugin não deve duplicar credenciais nem criar outra camada de integração. [web:12]

## Responsabilidades

### Claude Code

- Interpretar a issue.
- Planejar e implementar código.
- Rodar validações.
- Controlar terminal e worktree via `orca`.
- Atualizar issue, comentários, status e relações via `orca linear`.
- Perguntar o modo de trabalho antes de operações Git externas.

### Orca

- Fornecer runtime, worktrees, terminais, arquivos e navegador.
- Resolver a issue vinculada ao worktree atual.
- Encaminhar chamadas `orca linear` ao Linear.
- Fornecer contexto de issue, comentários, anexos, relações e subtarefas. [web:9][web:12]

### Linear

- Ser a fonte de verdade de trabalho, prioridade, responsável, status, projeto e histórico.
- Receber atualizações automáticas de progresso.
- Armazenar evidências de execução em comentários.

## Estados e transições

O agente deve mapear estados semanticamente, porque cada time pode ter workflow próprio.

| Fase | Estado alvo | Ação do agente |
|---|---|---|
| Issue lida e planejamento iniciado | Estado de backlog/triagem, se aplicável | Nenhuma mudança automática obrigatória |
| Implementação iniciada | Estado de execução, normalmente `In Progress` | Mover automaticamente |
| Implementação e testes concluídos | Estado de revisão, normalmente `In Review` | Mover automaticamente |
| Critérios de aceite atendidos e entrega autorizada | Estado final, normalmente `Done` | Mover automaticamente |
| Bloqueio real | Estado apropriado de bloqueio, se existir | Mover e comentar o bloqueio |

Se o estado exato não existir, o agente deve escolher o equivalente mais próximo do workflow do time e registrar a decisão.

## Comandos centrais

```bash
# Runtime e worktree
orca status --json
orca worktree current --json
orca worktree list --repo id:<repoId> --json

# Issue vinculada
orca linear issue --current --full --json

# Issue específica
orca linear issue <ISSUE-ID> --full --json

# Busca
orca linear search "<termo>" --workspace all --json
orca linear list-issues --team <TEAM> --state started --assignee me --json

# Criar issue
orca linear save-issue --team <TEAM> --title "..." --priority medium --json

# Atualizar issue
orca linear save-issue --current --state "In Progress" --json

# Comentário
orca linear comment add --current --body "..." --json

# Relações
orca linear relation add <ISSUE-A> --related <ISSUE-B> --type blocks --json
```

## Critérios de aceite do plugin

- [ ] O agente nunca usa MCP do Linear.
- [ ] O agente pergunta o modo de trabalho no início.
- [ ] O agente move status automaticamente conforme a fase.
- [ ] O agente cria issues e projetos somente após confirmação dos dados.
- [ ] O agente suporta múltiplos times/workspaces.
- [ ] O agente trabalha em worktree isolado.
- [ ] O agente não executa push/PR sem autorização do modo escolhido.
- [ ] O agente registra progresso técnico no Linear.
- [ ] O agente não inventa identificadores nem estados inexistentes.
