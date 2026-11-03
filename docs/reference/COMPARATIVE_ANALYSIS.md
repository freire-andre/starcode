# Análise comparativa e decisões adotadas

## Escopo e base da comparação

Foram lidos integralmente `Perplexity_CLAUDE.md` e `Perplexity_PLUGIN_SPEC.md`, anexados ao contexto. A proposta anterior desta conversa tinha guias Orca/Linear e sugeria **Skill + integração Orca + MCP oficial do Linear** como mecanismos complementares; a pessoa usuária depois decidiu explicitamente usar somente `orca linear`. Esta comparação considera a proposta anterior descrita no histórico disponível, os dois anexos e a documentação oficial consultada da Orca, Linear e Claude Code.

## Prós e contras

| Abordagem | Prós | Contras / riscos |
|---|---|---|
| Proposta anterior desta conversa | Boa separação de responsabilidades (Linear como gestão, Orca como ambiente, Claude como executor); valorizava Skills próprias, worktrees, browser, terminal, diff e possível orquestração; reconheceu que a integração nativa Orca reduz implementação duplicada. | Recomendou também MCP do Linear, contrariando decisão posterior do usuário e duplicando superfície de acesso/contexto; descreveu certas capacidades como confirmadas sem separar evidência e sintaxe local; sugeriu workflow padrão que não pode ser presumido em todos os times. |
| Perplexity `CLAUDE.md` | Regras fáceis de seguir; pergunta inicial de modos; confirmações para criação; suporte explícito a múltiplos times; progresso e estados automáticos; preocupação com worktree dedicado. | Trata nomes `In Progress`/`In Review` como padrão apesar da variação por time; diz “se não responder, use modo 1”, quando a escolha é obrigatória; modo 1 diz “não branch”, mas exige worktree Git; a matriz autoriza push/PR no modo 3/4 sem confirmação imediatamente antes; exemplos de comandos/flags são apresentados como válidos sem prova local; cria projeto como requisito sem confirmar suporte CLI; associa issue/worktree por sintaxe não demonstrada; comportamento de labels pode substituir labels existentes. |
| Perplexity `PLUGIN_SPEC.md` | Arquitetura simples; evita MCP duplicado; define responsabilidades; inclui estados semânticos, suporte multi-time, confirmação de issue e critérios de aceite. | Repete comandos específicos sem controle de versão; não trata criação de projeto com precisão; não distingue o que a CLI oficial realmente documenta; sugere registrar estado equivalente sem regra de ambiguidade; escopo de Git confunde autorização por modo e confirmação de ação. |
| Pacote consolidado | Mantém a clareza e os requisitos úteis dos anexos; usa só `orca linear`; separa guia operacional, regras principais, especificação e comparação; diferencia comandos documentados de itens dependentes da versão; usa estados semânticos por time; explicita confirmação de push/PR e a contradição do modo 1. | A criação de projeto por CLI e algumas associações issue/worktree ficam deliberadamente condicionadas ao `--help` e Skill locais. Os arquivos são pacote de instruções Markdown; não são, sem validação adicional, um pacote instalável completo de Claude Code com manifesto/hooks. |

## Verificação técnica

Fontes consultadas:

- Orca: [CLI overview](https://www.onorca.dev/docs/cli/overview), [CLI reference](https://www.onorca.dev/docs/cli/reference), [Skills registry](https://www.onorca.dev/docs/cli/skills), [worktrees](https://www.onorca.dev/docs/model/worktrees), [Linear na Orca](https://www.onorca.dev/docs/review/linear), [browser por worktree](https://www.onorca.dev/docs/browser/overview).
- Linear: [modelo conceitual](https://linear.app/docs/conceptual-model), [times](https://linear.app/docs/teams), [criação de issues](https://linear.app/docs/creating-issues), [projetos](https://linear.app/docs/projects).
- Claude Code: [documentação oficial](https://docs.anthropic.com/en/docs/claude-code/getting-started) consultada para reconhecer que o formato de distribuição do plugin não deve ser presumido a partir de um `CLAUDE.md` isolado.

### Confirmado pela documentação oficial

- Orca oferece CLI e recomenda `--json` para automação; runtime/CLI têm verificação documentada.
- Orca documenta worktrees reais de Git, terminais, comandos de arquivo/diff, navegador por worktree e Skills versionadas.
- Orca documenta `orca linear`, leitura/busca/listagem, consulta de times/estados/labels, `save-issue`, comentários, relações e consulta de projetos; orienta `orca linear --help` e `orca skills get orca-linear` para a lista/sintaxe correspondente à versão.
- A sincronização que move issue para “In Progress” ao criar worktree é opt-in por time.
- No Linear, issue pertence a um time/workflow; workflows são configuráveis por time. Projetos podem envolver vários times e status de projeto depende do time líder.

### Exemplos dos anexos que não foram confirmados como universais

- `orca status --json` e alguns comandos de worktree do anexo coincidem com documentação, mas cada flag deve ser confirmada na CLI instalada.
- `orca linear issue --current --full --json`, busca, estados/labels e `save-issue` têm formas documentadas pela Orca. Campos específicos de criação/atualização e sintaxe devem ser validados localmente.
- `orca worktree set --linear-issue ...`, `orca linear save-issue --current`, criação de projeto por CLI e algumas formas de associação não foram estabelecidos como universalmente disponíveis pelas páginas consultadas. Não são comandos garantidos neste pacote.
- O Linear documenta criação de projetos na interface; a referência CLI da Orca consultada confirma listagem/consulta, mas não expõe criação de projeto. A ausência na página não prova impossibilidade em toda versão: exige `--help`/Skill local. Até confirmação, o agente não deve contornar a regra de integração com API, MCP ou UI.
- Worktree é um checkout Git real. Assim, a instrução “não criar branch” do modo 1 conflita com “worktree isolado” quando a Orca cria/seleciona branch para ele. A interpretação adotada permite somente a branch necessária ao worktree e proíbe branch adicional manual, commit, push e PR.

## Decisões adotadas

1. **Uma única via Linear:** `orca linear`, seguindo a decisão direta do usuário, ainda que a proposta anterior aconselhasse MCP complementar.
2. **Confirmação de criação:** título, escopo, workspace/time e propriedades relevantes são revisados com a pessoa usuária antes da mutação.
3. **Workflows por equipe:** consultar estados do time e mapear por semântica; não fixar `In Progress`, `In Review` ou `Done` como nomes universais.
4. **Autonomia de status com evidência:** o agente atualiza status em marcos, mas não fecha issue sem critérios atendidos; se equivalência for ambígua, não adivinha.
5. **Modos de trabalho:** pergunta obrigatória; sem resposta não há implementação sob modo presumido. Push/PR sempre recebem confirmação imediatamente antes, e merge/deploy precisam de autorização separada.
6. **Worktree por issue:** preferir isolamento, conferir worktree existente e validar o mecanismo de associação na versão instalada.
7. **Navegador, terminal, diff e Skills:** mantidos porque a documentação Orca os confirma. Orquestração só quando a tarefa for multiagente e após carregar a Skill atual.
8. **Comandos versionados:** antes de operar, consultar `orca --help`, `orca linear --help` e Skills instaladas; exemplos deste pacote são classificados pela documentação, não por suposição.
9. **Pacote versus plugin binário:** entregar os cinco Markdown solicitados. A estrutura completa de distribuição de plugin Claude Code permanece um item de validação, não um manifesto inventado.

## Dúvidas bloqueantes

Não há dúvida bloqueante para usar os documentos como instruções Markdown do projeto. A única validação necessária antes de automatizar criação de projetos é confirmar se a versão instalada do `orca linear` oferece esse comando e quais campos aceita. Se não oferecer, o agente deve reportar a limitação sem recorrer a outra integração do Linear.
