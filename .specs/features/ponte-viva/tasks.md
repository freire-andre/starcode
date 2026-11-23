# Ponte viva: Tasks

**Spec**: `.specs/features/ponte-viva/spec.md`
**Status**: Approved
**Approved**: 2026-11-22 - user: "sim"
**Integration branch**: `feature/ponte-viva`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | testes do plugin | `orca plugin test src/orca` |
| full | integração do plugin | `orca plugin test src/orca` |
| build | entrega integrada | `python tools/build.py --check` |

## Tasks

### T1: Estado confiável da tripulação
**Linear**: SC-217
**Depends on**: none
**Requirements**: R1, R5, R6, R7, R8
**Tests**: unit
**Gate**: quick

#### TASK
Definir os 12 perfis visuais e um modelo de estados que diferencie trabalhando, ocioso, aguardando, bloqueado, concluído e desconhecido sem associações ambíguas. Adicionar testes dos casos comprovados e incertos.

#### CONTEXT
Spec: `.specs/features/ponte-viva/spec.md` (R1, R5–R8). Checks: C1, C5, C6, C7, C8. `src/crew.yaml` é a fonte de integrantes; `src/orca/src/protocol.ts` define os dados disponíveis. Não tratar título contendo texto como identidade inequivocamente confiável.

#### BOUNDARIES
May change: `src/orca/src/crew-visual.ts`, `src/orca/src/crew-visual.test.ts`, `DECISIONS.md`
Do not touch: renderização, worker e arquivos de outras tarefas.

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3. Commit convencional em PT-BR com `Refs SC-<n>` no corpo; use a issue vinculada (modelo do gate: Refs: <ID-LINEAR>). Sem segredos, deploy ou push.

#### DELIVERY
Commit na branch do worktree. Relatório de até cinco linhas com alteração, testes, commit, pendências e tentativas do disjuntor.

### T2: Sincronização automática e recuperação
**Linear**: SC-218
**Depends on**: T1
**Requirements**: R11, R12, R13, R14, R18
**Tests**: unit
**Gate**: quick

#### TASK
Implementar reconciliação automática em até 30 segundos, tratamento de falhas, concorrência e descarte de respostas obsoletas, preservando o comportamento existente do worker e evitando requisições acumuladas.

#### CONTEXT
Spec: `.specs/features/ponte-viva/spec.md` (R11–R14, R18). Checks: C11–C14, C18. `src/orca/src/worker.ts` recebe eventos; `protocol.ts` contém timestamp e indicador de dados antigos. Cubra troca de foco, eventos perdidos, falha e recuperação com relógio controlado.

#### BOUNDARIES
May change: `src/orca/src/worker.ts`, `src/orca/src/worker.test.ts`, `src/orca/src/protocol.ts`, `DECISIONS.md`
Do not touch: arquivos de cena e de perfis visuais.

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3. Commit convencional em PT-BR com `Refs SC-<n>` no corpo; use a issue vinculada (modelo do gate: Refs: <ID-LINEAR>). Sem segredos, deploy ou push.

#### DELIVERY
Commit na branch do worktree. Relatório de até cinco linhas com alteração, testes, commit, pendências e tentativas do disjuntor.

### T3: Cena animada e rodízio
**Linear**: SC-219
**Depends on**: T2
**Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R15, R18
**Tests**: unit
**Gate**: quick

#### TASK
Criar a cena com até seis personagens identificáveis, seus estados, rodízio justo e priorização, entrada e saída animadas e nomes legíveis a 240 e 360 px. Usar pixel art gerada por código, mantendo separação entre modelo e pintura.

#### CONTEXT
Spec: `.specs/features/ponte-viva/spec.md` (R1–R8, R15, R18). Checks: C1–C8, C15, C18. Aproveitar os perfis de T1 e os dados de T2; os nomes visíveis devem corresponder aos nomes da tripulação em `src/crew.yaml` e na prancha, como Picard, LaForge e Scotty. Compare com `.specs/features/ponte-viva/referencias/ponte-conceito.png` e `tripulacao-conceito.png`: ponte espacial escura vista de cima, estações em arco, capitão ao centro, engenharia, contrastes luminosos e silhuetas e acessórios individuais reconhecíveis. São referências conceituais, adaptadas ao espaço reduzido; não exigem cópia pixel a pixel. Presença em cena não implica trabalho. Produza capturas reais em 240 e 360 px e relate diferenças visuais e legibilidade para revisão.

#### BOUNDARIES
May change: `src/orca/src/scene-model.ts`, `src/orca/src/scene-model.test.ts`, `src/orca/src/scene.ts`, `src/orca/src/scene.test.ts`, `src/orca/src/crew-visual.ts`, `src/orca/src/crew-visual.test.ts`, `DECISIONS.md`
Do not touch: worker ou arquivos de outras tarefas.

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3. Commit convencional em PT-BR com `Refs SC-<n>` no corpo; use a issue vinculada (modelo do gate: Refs: <ID-LINEAR>). Sem segredos, deploy ou push.

#### DELIVERY
Commit na branch do worktree. Relatório de até cinco linhas com alteração, testes, commit, pendências e tentativas do disjuntor.

### T4: Lista acessível e movimento reduzido
**Linear**: SC-220
**Depends on**: T3
**Requirements**: R9, R10, R13, R14, R16, R17
**Tests**: integration
**Gate**: full

#### TASK
Adicionar relação acessível dos 12 membros e estados, seleção manual, aviso de dados antigos e suporte a movimento reduzido, com navegação por teclado e testes de integração e comportamento. Investigar a oscilação do teste `ponte viva descarta resposta obsoleta`: reproduzir, identificar a causa e corrigir teste ou sincronização conforme a evidência, preservando uma prova real de descarte fora de ordem.

#### CONTEXT
Spec: `.specs/features/ponte-viva/spec.md` (R9, R10, R13, R16, R17). Checks: C9, C10, C13, C16, C17. `scene.ts` cria a página e o canvas; preservar nomes e estado real mesmo quando fora da cena.

#### BOUNDARIES
May change: `src/orca/src/scene.ts`, `src/orca/src/scene.test.ts`, `src/orca/src/scene-model.ts`, `src/orca/src/scene-model.test.ts`, `src/orca/src/worker.ts`, `src/orca/src/worker.test.ts`, `src/orca/src/crew-visual.ts`, `src/orca/src/crew-visual.test.ts`, `DECISIONS.md`
Do not touch: arquivos de outras tarefas.

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3. Commit convencional em PT-BR com `Refs SC-<n>` no corpo; use a issue vinculada (modelo do gate: Refs: <ID-LINEAR>). Sem segredos, deploy ou push.

#### DELIVERY
Commit na branch do worktree. Relatório de até cinco linhas com alteração, testes, commit, pendências e tentativas do disjuntor.

### T5: Distribuição e aceite da ponte
**Linear**: SC-221
**Depends on**: T4
**Requirements**: R1, R2, R11, R12, R15, R16, R17
**Tests**: integration
**Gate**: build

#### TASK
Gerar `dist/` com o build, registrar decisões, executar os comandos do CI e validar a cena na Orca com capturas e troca real de estado; registrar resultado e limitações verificadas.

#### CONTEXT
Spec: `.specs/features/ponte-viva/spec.md` (R1, R2, R11, R12, R15–R17). Checks: C1, C2, C11, C12, C15–C17. O gate Orca precisa de worktree no drive da instalação conforme AGENTS.md; preservar alterações de terceiros.

#### BOUNDARIES
May change: `dist/`, `DECISIONS.md`, `docs/aceite/ponte-viva.md`, `docs/aceite/ponte-viva/`, `src/orca/src/scene.test.ts`, `scripts/impact.py`, `tests/test_impact.py`
Do not touch: demais fontes do plugin e arquivos de outras features.

#### RULES
Leia AGENTS.md. Nunca edite dist manualmente; execute o gerador. Modo Git: 3. Commit convencional em PT-BR com `Refs SC-<n>` no corpo; use a issue vinculada (modelo do gate: Refs: <ID-LINEAR>). Sem segredos, deploy ou push.

#### DELIVERY
Commit na branch do worktree. Relatório de até cinco linhas com alteração, gates, evidências, commit, pendências e tentativas do disjuntor.

## Checks

**Build**: `python tools/build.py --check`; `python scripts/check_decisions.py`; `claude plugin validate dist/claude --strict`
**Run unit**: `orca plugin test src/orca`

**C1** - Os 12 perfis têm nomes e identidades visuais distintos (R1)
Proof: run unit | ponte viva identifica os 12 integrantes
**C2** - A cena apresenta até seis integrantes com nome (R2)
Proof: run unit | ponte viva limita a seis integrantes
**C3** - O rodízio alcança os elegíveis e prioriza alertas e atividade (R3)
Proof: run unit | ponte viva alterna integrantes elegíveis
**C4** - A entrada e saída são transições visuais sem alterar o estado (R4)
Proof: run unit | ponte viva anima sem alterar estado
**C5** - Agente trabalhando mostra indicador e operação do console (R5)
Proof: run unit | ponte viva representa trabalho
**C6** - Agente ocioso não executa animação de trabalho (R6)
Proof: run unit | ponte viva representa ociosidade
**C7** - Espera, bloqueio e conclusão têm indicadores diferentes (R7)
Proof: run unit | ponte viva distingue estados
**C8** - Identidade ou estado incerto é desconhecido (R8)
Proof: run unit | ponte viva não inventa atividade
**C9** - A lista contém os 12 nomes, estados e presença (R9)
Proof: run unit | ponte viva lista os 12 integrantes
**C10** - Selecionar integrante o traz à cena sem alterar seu estado (R10)
Proof: run unit | ponte viva permite selecionar integrante
**C11** - Eventos atualizam o estado do worktree em foco (R11)
Proof: run unit | ponte viva atualiza por evento
**C12** - Sem evento, reconciliação ocorre em até 30 segundos (R12)
Proof: run unit | ponte viva reconcilia automaticamente
**C13** - Falha e dados antigos aparecem com última atualização válida (R13)
Proof: run unit | ponte viva informa dados desatualizados
**C14** - Resposta antiga não substitui atualização mais recente ou outro foco (R14)
Proof: run unit | ponte viva descarta resposta obsoleta
**C15** - A cena mantém nomes e indicadores sem colisão a 240 e 360 px (R15)
Proof: run unit | ponte viva mantém rótulos legíveis
**C16** - Lista e estados são acessíveis por teclado e leitor de tela (R16)
Proof: run unit | ponte viva expõe lista acessível
**C17** - Movimento reduzido suspende deslocamentos e rodízio automático (R17)
Proof: run unit | ponte viva respeita movimento reduzido
**C18** - Estado repetido não reinicia transição (R18)
Proof: run unit | ponte viva preserva transição em atualização repetida

## Handoff

**Phase:** execute
**Size:** LARGE
**Git mode:** 3
**Plugin:** 1.9.0
**Next:** integrar T5 e verificar aceite na Orca
**Linear:** SC-216; T1 SC-217; T2 SC-218; T3 SC-219; T4 SC-220; T5 SC-221
**Integration branch:** feature/ponte-viva
**Last integrated:** efbe0e6d1a903b69dc5c973a4cb4e3060aa1d0e2
**Dispatched:** none
**Settled:** 2026-11-22: aprovado; 2026-11-22: sim
**Attempts:** none
**Reports:** 2026-11-22: T1: perfis e estados implementados; 79 testes Orca passaram; commit 0c06273; dist será gerado em T5; 2026-11-22: T2: reconciliação automática, recuperação e concorrência; 84 testes Orca passaram; commit 33d0524; dist pendente de T5; 2026-11-22: T3 revisão: ampliar limites para corrigir estados por sessões ativas e melhorar composição; capturas requeridas; 2026-11-22: T3 revisão: atividade por count corrigida; prévia sintética 360 distante do mockup; devolvida para melhorar composição; 2026-11-22: T3: cena revisada e estados por sessões; 97 testes Orca passaram; prévias sintéticas verificadas; teste de T2 oscilou; commits 84164ec, e225444 e d16ba0c; 2026-11-22: T4: acessibilidade implementada e flakiness corrigida, 103 testes Orca; corrigir escopo e incerteza de atividade antes de integrar; 2026-11-22: T4: acessibilidade, flakiness e ambiguidade de estados corrigidas; 104 testes Orca; commits f3e7522 e 86faf81; 2026-11-22: T5: dist gerado, 104 testes Orca; suíte identificou falha no analisador de impacto; correção despachada; captura real pendente; 2026-11-22: T5: dist gerado e impact corrigido em b2c3edd; 104 testes Orca, 23 impact, build, decisões e validate verdes; captura real pendente
**Breaker:** closed
