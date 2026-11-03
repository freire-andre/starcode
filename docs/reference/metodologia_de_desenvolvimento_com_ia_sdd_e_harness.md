# Manual Operacional: Desenvolvimento Profissional de Software com IA (SDD & AI Harness)

> **Fonte de Referência:** *How I Code with AI: The Full Process in 1.5 Hours* — Breno Vieira (LionLab).  
> **Objetivo:** Estabelecer a arquitetura de processos, templates e regras comportamentais para que agentes de IA e engenheiros executem desenvolvimento de software sem alucinações, sem degradação de contexto e com qualidade de nível de produção.

---

## 1. Visão Geral e Filosofia Fundamental

O erro mais comum ao programar com modelos de linguagem (LLMs) é o **"Vibe Coding" não estruturado**: abrir um chat, solicitar funcionalidades complexas em linguagem natural informal e aplicar os patches de código diretamente. Essa abordagem causa:
1. **Quebra de contexto / Degradação do modelo:** A perda de coerência do projeto à medida que o histórico de chat cresce.
2. **Desperdício de Tokens:** Retrabalho constante e loops de depuração infinitos.
3. **Dívida Técnica Oculta:** Código sem padronização arquitetural e regressões de bugs não detectadas.

### Os Pilares da Metodologia SDD (Spec-Driven Development)
* **O Código é o Último Passo:** Nenhuma linha de código é digitada antes que o escopo, arquitetura, dependências e critérios de aceite estejam validados e documentados.
* **A Especificação (SPEC) é o Contrato:** A IA não toma decisões de negócio implícitas. Toda ambiguidade deve ser resolvida antes do gatilho de implementação.
* **AI Harness & Sub-agentes Especializados:** O desenvolvimento não é feito por um único agente generalista ("faz-tudo"), mas por um pipeline de sub-agentes com escopos isolados (Discovery $\rightarrow$ SPEC $\rightarrow$ Planner $\rightarrow$ Coder $\rightarrow$ Evaluator).
* **Artefatos Intermediários Tangíveis:** Uso de documentos Markdown (SPEC, Sprints, Decision Logs) e interfaces de validação rápida (Approval HTML e Test Plan HTML) para interação humana na tomada de decisão.

---

## 2. O Pipeline dos 5 Estágios e Matriz de Agentes

O ciclo de vida de uma feature divide-se em 5 macro-estágios, orquestrados por agentes com papéis bem delimitados:

```
[ BACKLOG / KANBAN ]
         │
         ▼
[ 1. DESCOBERTA & REQUISITOS ] ──► (Discovery Agent + PRD Generator & Validator)
         │
         ▼
[ 2. ARQUITETURA & SPEC ]      ──► (Tech Decisions + Spec Gen + Spec Enricher + Decision Map)
         │
         ▼
[ 3. DECOMPOSIÇÃO EM SPRINTS ] ──► (Planner Agent + Sprint Validator)
         │
         ▼
[ 4. IMPLEMENTAÇÃO EM LOOP ]   ──► (Coder Agent ◄──► Evaluator Agent) [Por Sprint]
         │
         ▼
[ 5. VALIDAÇÃO & COMMIT ]      ──► (Test Plan HTML + Acceptance Reviewer ──► Git Commit)
```

### Matriz de Responsabilidades dos Agentes

| Agente | Entrada (Input) | Função Principal | Saída (Output) |
| :--- | :--- | :--- | :--- |
| **Discovery Agent** | Demanda do card Kanban / Ideia bruta | Realizar entrevista estruturada para extrair requisitos essenciais e regras de negócio. | `discovery_notes.md` |
| **PRD Generator & Validator** | Notas de descoberta | Escrever User Stories, cenários de uso e refinar requisitos em diálogo com o usuário. | `prd_completo.md` |
| **Tech Decisions Agent** | PRD | Definir stack, banco de dados, padrões de concorrência, autenticação e contratos de API. | `tech_decisions.md` |
| **Spec Generation & Enricher** | PRD + Decisões Técnicas | Gerar a especificação formal e enriquecê-la com edge cases, estados de UI/erro e caminhos alternativos. | `spec_tecnica.md` + `decision_map.html` |
| **Planner & Sprint Validator** | SPEC validada | Decompor a SPEC em sprints sequenciais, atômicos e com dependências mapeadas. | `sprints_plan.md` |
| **Coder Agent** | Sprint ativa individual + Trecho da SPEC | Codificar unicamente a sprint atual, sem alterar arquivos fora do escopo definido. | Alterações nos arquivos de código |
| **Evaluator / Reviewer** | Código gerado + Critérios de aceite | Executar testes, checar tipagem, validar padrões e aprovar ou reprovar a sprint. | Feedback de ajuste ou `APPROVED` |
| **Acceptance Reviewer** | Projeto completo compilado | Gerar o plano de validação funcional manual para homologação humana. | `test_plan.html` |

---

## 3. Anatomia dos Artefatos de Controle

Para evitar ambiguidades, o agente deve exigir e ler os seguintes artefatos padronizados:

### 3.1. A SPEC Técnica (`spec_tecnica.md`)
A SPEC é a "planta baixa" da funcionalidade. Deve conter:
1. **Contexto e Motivação:** Por que esta feature existe.
2. **Escopo vs. Fora de Escopo (Non-Goals):** Limite estrito do que não deve ser tocado ou implementado.
3. **Modelagem de Dados e Contratos:** Esquema SQL, interfaces TypeScript, payloads JSON de entrada/saída.
4. **Casos de Borda (Edge Cases):** Falha de conexão, concorrência, timeouts, validações de payloads inválidos.
5. **Critérios de Aceite Mensuráveis:** Condições binárias (passou/não passou) para cada sub-tarefa.

### 3.2. Mapa de Decisão (`decision_map.html` ou Markdown)
Sempre que o agente encontrar mais de uma abordagem viável (ex: Polling vs. WebSocket; persistir em tabela relacional vs. Redis), ele **não assume** uma escolha. Ele gera um artefato de decisão contendo:
* **Item:** Descrição da encruzilhada técnica.
* **Opção A:** Prós, contras e impacto de tokens/complexidade.
* **Opção B:** Prós, contras e impacto de tokens/complexidade.
* **Status:** `[APROVADO / AJUSTADO / REJEITADO]`.

### 3.3. Plano de Sprints Atômicas (`sprints_plan.md`)
O agente quebra a SPEC em micro-tarefas contidas. Cada sprint deve ser autocontida:
* **Sprint N:**
  * **Objetivo:** Uma entrega verificável em código.
  * **Arquivos Modificados/Criados:** Lista restrita de paths autorizados para alteração.
  * **Dependências:** O que precisa estar pronto antes desta etapa.
  * **Critérios de Verificação:** Como checar o funcionamento isolado (ex: rodar `npm test`, validar endpoint).

---

## 4. O Fluxo de Execução Passo a Passo (Runtime Guide)

Qualquer agente de IA configurado para executar este método deve seguir as instruções deste protocolo operacional:

### Fase 1: Recepção e Isolamento do Card
1. Leia o card do Kanban ou a solicitação do usuário.
2. Crie uma branch de trabalho isolada: `git checkout -b feature/<nome-da-demanda>`.
3. Inicie o arquivo de notas (`discovery_notes.md`) destacando o que é claro e listando perguntas para os pontos abertos.

### Fase 2: Geração e Discussão da SPEC
1. Produza o rascunho da SPEC técnica com base no PRD e decisões de arquitetura.
2. **Loop de Enriquecimento:** Adicione uma seção dedicada exclusivamente a:
   * Estados de carregamento (Loading, Error, Empty State, Success).
   * Tratamento de falhas parciais (ex: falha de 1 das pipelines em execução concorrente).
3. Apresente os pontos de escolha ao desenvolvedor. Registre as decisões no log permanente.

### Fase 3: Divisão e Execução em Sprints (Loop Coder-Evaluator)
Para cada Sprint $k \in \{1, 2, \dots, N\}$ definida no `sprints_plan.md`:
1. **Carregamento de Contexto Mínimo:** Carregue apenas o arquivo `spec_tecnica.md` (seção relevante), o `sprints_plan.md` e os arquivos de código explicitamente listados na Sprint $k$.
2. **Implementação (Coder):** Aplique as alterações no código estritamente necessárias para a Sprint $k$. Nunca implemente código adiantado pertencente à Sprint $k+1$.
3. **Avaliação (Evaluator):**
   * Execute os testes automatizados ou lint/build de tipagem (`tsc`, `eslint`, `pytest`).
   * Se houver falha, analise o traceback sem resetar o arquivo inteiro; aplique o patch mínimo de correção.
   * Se os critérios forem satisfeitos, marque a sprint como `[COMPLETED]` no `sprints_plan.md`.

### Fase 4: Validação Funcional com Test Plan HTML
1. Gere um arquivo executável local `test_plan.html` contendo:
   * Checklist interativo de validação funcional para o operador humano.
   * Botões de teste e formulários pontuais para disparar requisições diretamente na API local, exibindo o status de resposta em tempo real.
2. O usuário valida o comportamento interativo no browser (ex: execução simultânea dos dois pipelines).

### Fase 5: Conclusão, Documentação e Git Commit
1. Valide se nenhum arquivo residual temporário permaneceu no repositório (`.gitstatus`).
2. Garanta que o `decision_log` e as especificações finais fiquem versionados na pasta `docs/` do projeto.
3. Elabore uma mensagem de commit semântica e contextualizada vinculada ao card:
   ```bash
   git add .
   git commit -m "feat(lionclaw): enable parallel execution of dual pipelines

   - Implement worker pool concurrency control
   - Add state synchronization and conflict resolution
   - Include HTML test harness for verification
   Refs: CARD-104"
   ```

---

## 5. System Prompt / Instrução Operacional para Agentes de IA

Copie e configure o prompt abaixo no agente (ex: Claude Code, Cursor, Windsurf, Aider ou agentes customizados) para forçá-lo a operar sob este protocolo:

```markdown
Você é um Engenheiro de Software Sênior operando sob a Metodologia SDD (Spec-Driven Development) e AI Harness.

REGRAS DE CONDUTA OBRIGATÓRIAS:
1. NÃO ESCREVA CÓDIGO ANTES DA SPEC: Se o usuário solicitar uma nova funcionalidade, seu primeiro passo é gerar ou validar a SPEC técnica e o plano de sprints. Não implemente código imediatamente.
2. ELIMINAÇÃO DE AMBIGUIDADE: Se houver mais de uma alternativa técnica ou regra de negócio indeterminada, pare, gere um Decision Map com as opções, prós/contras e aguarde a decisão humana.
3. CONTEXTO MÍNIMO E ATÔMICO: Trabalhe estritamente sprint por sprint. Só modifique os arquivos descritos no escopo da sprint atual.
4. NUNCA DEIXE DEPENDÊNCIAS OCULTAS: Toda biblioteca adicionada, variável de ambiente ou migração de banco deve ser explicitada na SPEC e na respectiva sprint.
5. AUTO-AVALIAÇÃO E QUALIDADE: Após codificar, execute checagens sintáticas, de tipagem e de testes unitários. Se houver erro, corrija no ponto cirúrgico, sem refatorar código alheio ao escopo.
6. PLANO DE TESTE TANGÍVEL: Finalize a entrega com um artefato de validação claro (checklist ou Test Plan interativo em HTML/script) antes de autorizar o commit.
```

---

## 6. Síntese dos Ganhos de Eficiência

| Métrica | Vibe Coding Convencional | Metodologia SDD com Harness |
| :--- | :--- | :--- |
| **Previsibilidade** | Baixa (cada rodada produz um resultado diferente) | Determinística (controlada pela SPEC e Sprints) |
| **Gasto de Tokens** | Alto (loops de correções e re-escritas completas) | Otimizado (contexto isolado e cirúrgico por sprint) |
| **Rastreabilidade** | Nula (decisões esquecidas no histórico do chat) | Permanente (arquivos Markdown e Decision Logs no Git) |
| **Manutenibilidade** | Frágil (código fragmentado e não padronizado) | Pronta para Produção (arquitetura validada a priori) |