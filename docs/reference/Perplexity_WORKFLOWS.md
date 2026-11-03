# Modos de trabalho e políticas de entrega

## Pergunta inicial

No início de cada sessão, o agente deve perguntar:

```text
Como você quer trabalhar nesta sessão?

1. Somente código local
2. Commit local
3. Branch + PR
4. Entrega completa
```

A resposta define exatamente até onde o agente pode avançar.

## Modo 1 — Somente código local

**Permitido:**

- Ler issue.
- Criar/atualizar worktree.
- Editar arquivos.
- Rodar testes.
- Comentar progresso no Linear.
- Mover issue para `In Progress` e `In Review`.

**Proibido:**

- `git commit`
- `git push`
- Criação de PR
- Merge
- Deploy

## Modo 2 — Commit local

**Permitido:**

- Tudo do modo 1.
- Criar commits locais.
- Criar branch local, se necessário.

**Proibido:**

- `git push`
- Criação de PR
- Merge
- Deploy

## Modo 3 — Branch + PR

**Permitido:**

- Tudo do modo 2.
- Criar/atualizar branch remoto.
- Fazer push.
- Abrir PR.
- Vincular PR à issue.

**Regra:** antes de push e PR, apresentar resumo do diff, testes e proposta de PR.

## Modo 4 — Entrega completa

**Permitido:**

- Tudo do modo 3.
- Atualizar Linear para revisão.
- Marcar como concluída apenas se os critérios de aceite forem atendidos e não houver revisão humana pendente obrigatória.

**Proibido sem aprovação adicional:**

- Merge automático.
- Deploy.
- Alteração de produção.
- Exclusão de branches, issues ou projetos.

## Política de status

| Evento | Ação no Linear |
|---|---|
| Implementação iniciada | Mover para estado de execução |
| Implementação concluída e testada | Mover para estado de revisão |
| PR aberto | Comentar link/evidência e manter em revisão |
| Bloqueio encontrado | Mover para estado de bloqueio, se existir, e comentar |
| Critérios atendidos e entrega autorizada | Mover para estado final |

## Confirmações obrigatórias

O agente deve confirmar antes de:

- Criar issue ou projeto.
- Alterar time, projeto ou responsável de uma issue.
- Criar relações entre issues.
- Fazer push.
- Abrir PR.
- Fechar issue.
- Executar comando destrutivo.
