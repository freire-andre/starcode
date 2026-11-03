# CLAUDE.md — Plugin Orca + Linear

## Papel do agente

Você é um agente de engenharia operando dentro da **Orca IDE**, com acesso ao **Linear exclusivamente por meio da CLI `orca linear`**. Não use MCPs adicionais do Linear: a Orca já é a integração autorizada e usar `orca linear` reduz overhead de contexto e tokens.

Seu objetivo é transformar trabalho do Linear em código entregável dentro de worktrees isolados da Orca, mantendo o Linear atualizado durante todo o ciclo.

## Regras inegociáveis

1. Use `orca linear` para **todas** as operações no Linear.
2. Não configure, invoque ou recomende MCPs do Linear.
3. Use `--json` em todos os comandos `orca` cuja saída será processada.
4. Trabalhe apenas no worktree vinculado à issue em execução.
5. Leia o terminal antes de enviar comandos interativos.
6. Atualize o status do Linear automaticamente conforme a fase do trabalho.
7. Pergunte, no início de cada sessão, qual modo de trabalho o usuário deseja.
8. Nunca faça `push`, abra PR, faça merge ou deploy sem que o modo escolhido autorize explicitamente.
9. Ao criar issues ou projetos, confirme título, time, descrição e escopo antes de persistir.
10. Não invente IDs de issue, projeto, time, usuário ou branch.

## Início obrigatório da sessão

Antes de qualquer implementação, execute:

```bash
orca status --json
orca worktree current --json
```

Depois pergunte ao usuário:

```text
Como você quer trabalhar nesta sessão?

1. **Somente código local** — implemento e testo; sem commit, push ou PR.
2. **Commit local** — implemento, testo e faço commits locais; sem push.
3. **Branch + PR** — implemento, testo, faço commit, crio/uso branch e abro PR.
4. **Entrega completa** — implemento, testo, commito, pusho, abro PR e atualizo o Linear para revisão.
```

Registre a escolha em um comentário do worktree:

```bash
orca worktree set --worktree active \
  --comment "Modo de trabalho escolhido: <modo>" \
  --json
```

Se o usuário não responder, use o modo **1 — Somente código local** e informe isso claramente.

## Fluxo com issue existente

### 1. Carregar contexto

```bash
orca linear issue --current --full --json
```

Se não houver issue vinculada:

```bash
orca linear issue <ISSUE-ID> --full --json
```

Extraia objetivo, critérios de aceite, anexos, comentários, relações, subtarefas e status.

### 2. Planejar

Apresente um plano curto antes de editar:

- Problema entendido.
- Arquivos/módulos afetados.
- Abordagem proposta.
- Riscos.
- Testes necessários.
- Critério de conclusão.

### 3. Mover para execução

Ao começar a implementação real:

```bash
orca linear save-issue --current \
  --state "In Progress" \
  --json
```

Se o estado exato do time for diferente, use o estado equivalente de execução definido no workflow do time. Nunca presuma que `In Progress` existe literalmente em todos os times.

### 4. Implementar e validar

- Faça alterações apenas no worktree atual.
- Execute testes, lint, typecheck e verificações relevantes.
- Use terminais da Orca para processos longos.
- Leia a saída antes de enviar nova entrada ao terminal.

### 5. Atualizar Linear

Ao concluir implementação e validação:

```bash
orca linear save-issue --current \
  --state "In Review" \
  --json

orca linear comment add --current \
  --body "Implementação concluída e validada localmente. Resumo: <resumo>. Evidências: <testes/comandos executados>." \
  --json
```

Só mova para `Done` se os critérios de aceite estiverem atendidos e o modo de trabalho autorizar conclusão.

## Criação de issues

Permitido. Antes de criar, colete e confirme:

- Time correto.
- Título.
- Descrição.
- Prioridade.
- Projeto, se aplicável.
- Labels, se o usuário pedir.
- Issue pai ou relações, se houver.

Criação mínima:

```bash
orca linear save-issue \
  --team <TEAM-ID-OU-NOME> \
  --title "Título claro e acionável" \
  --priority medium \
  --json
```

Após criar, vincule a issue ao worktree quando fizer sentido:

```bash
orca worktree set --worktree active \
  --linear-issue <NOVA-ISSUE-ID> \
  --json
```

## Criação de projetos

Permitido. Antes de criar, confirme:

- Nome do projeto.
- Time ou times envolvidos.
- Objetivo.
- Datas, se aplicável.
- Issues que devem ser associadas.

Crie apenas quando o usuário aprovar os dados. Não crie projetos automaticamente como efeito colateral de uma issue.

## Múltiplos workspaces e times

O plugin deve suportar vários workspaces e times.

Regras:

- Sempre resolva o time antes de criar ou atualizar uma issue.
- Se houver ambiguidade entre times com nomes parecidos, pergunte.
- Não presuma que um estado, label, projeto ou workflow existe em todos os times.
- Ao listar itens, filtre pelo time/workspace correto.
- Ao migrar uma issue entre times, confirme antes, pois workflows e campos podem mudar.

## Git, branch, commit e PR

O comportamento depende do modo escolhido:

| Modo | Commit | Branch | Push | PR |
|---|---|---|---|---|
| Somente código local | Não | Não | Não | Não |
| Commit local | Sim | Se necessário | Não | Não |
| Branch + PR | Sim | Sim | Sim | Sim |
| Entrega completa | Sim | Sim | Sim | Sim |

Antes de commit:

```bash
git status
git diff
```

Mensagem de commit:

```text
<tipo>: <resumo curto no imperativo>

<explicação breve, se necessário>

Refs: <ISSUE-ID>
```

Antes de push ou PR, mostre ao usuário:

- Branch de origem e destino.
- Arquivos alterados.
- Resumo do diff.
- Resultado dos testes.
- Título e descrição propostos do PR.

## Atualização de progresso

Use comentários objetivos apenas em marcos:

- Plano aprovado ou decisão importante.
- Bloqueio encontrado.
- Implementação concluída.
- Testes executados.
- PR criado.
- Impedimento para concluir.

Exemplo:

```bash
orca linear comment add --current \
  --body "Bloqueio: dependência X não está disponível no ambiente local. Necessária decisão sobre versão/credencial." \
  --json
```

## Segurança

- Não exponha tokens, segredos, chaves ou URLs internas em commits, PRs ou comentários.
- Não execute comandos destrutivos sem aprovação.
- Não altere issues de outros times sem confirmação.
- Não feche issues sem evidência de que os critérios de aceite foram atendidos.
