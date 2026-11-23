# Ponte viva: Tasks

**Spec**: `.specs/features/ponte-viva/spec.md`
**Status**: Approved
**Approved**: 2026-11-23 - user: "sim"

As tarefas T1–T5 foram aprovadas em 2026-11-22; esta revisão acrescenta T6–T8.
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

### T6: Identidade da sessão no worktree
**Linear**: SC-222
**Depends on**: T5
**Requirements**: R8, R11, R21, R22
**Tests**: integration
**Gate**: full

#### TASK
Associar integrante, sessão e worktree por identificadores comprováveis desde os registros da tripulação até o estado entregue à cena. Testar dois worktrees, sessões sem vínculo, falhas e compatibilidade com registros antigos; não inferir por título ou contagem agregada.

#### CONTEXT
Spec: `.specs/features/ponte-viva/spec.md` (R8, R11, R21, R22). Checks: C8, C11, C21, C22. `crew_live.py` e `crew_hook.py` registram sessões agregadas; `ponte.py`, `worker.ts` e `crew-visual.ts` alimentam a cena, que hoje recebe identidades vazias. Confirme quais identificadores Orca estão disponíveis antes de usar cada vínculo.

#### BOUNDARIES
May change: `scripts/crew_live.py`, `hooks/scripts/crew_hook.py`, `scripts/ponte.py`, `src/orca/src/protocol.ts`, `src/orca/src/worker.ts`, `src/orca/src/crew-visual.ts`, `src/orca/src/scene.ts`, `tests/`, `src/orca/src/worker.test.ts`, `src/orca/src/crew-visual.test.ts`, `src/orca/src/scene.test.ts`, `DECISIONS.md`, `dist/`
Do not touch: modelo de seleção visual e Handoff.

#### RULES
Leia AGENTS.md. TDD; registre decisão e gere dist apenas pelo build. Descarregue a pasta de desenvolvimento antes do build para evitar recarga automática; não instale ou aprove plugin. Modo Git 3; commit convencional com `Refs: <ID-LINEAR>`. Sem push ou deploy.

#### DELIVERY
Commit e relatório de até cinco linhas: vínculo comprovado e limites, testes, gates, pendências e disjuntor.

### T7: Presença estável e troca animada
**Linear**: SC-223
**Depends on**: T6
**Requirements**: R2, R3, R4, R10, R15, R17, R18, R19, R20
**Tests**: integration
**Gate**: full

#### TASK
Substituir rodízio por presença estável: preservar integrantes sem mudança de estado, priorizar alertas e trabalho até seis vagas, e animar apenas entradas e saídas necessárias. A seleção manual traz quem está fora e não altera a composição ao acionar quem já está presente.

#### CONTEXT
Spec: `.specs/features/ponte-viva/spec.md` (R2–R4, R10, R15, R17–R20). Checks: C2–C4, C10, C15, C17–C20. `scene-model.ts` usa relógio de oito segundos; teste Q concluindo e Worf assumindo com identidade comprovada, prioridade, empate, dados incertos, movimento reduzido e atualizações repetidas.

#### BOUNDARIES
May change: `src/orca/src/scene-model.ts`, `src/orca/src/scene-model.test.ts`, `src/orca/src/scene.ts`, `src/orca/src/scene.test.ts`, `DECISIONS.md`, `dist/`
Do not touch: registros de identidade e Handoff.

#### RULES
Leia AGENTS.md. TDD; registre decisão e gere dist apenas pelo build. Não instale ou aprove plugin. Modo Git 3; commit convencional com `Refs: <ID-LINEAR>`. Sem push ou deploy.

#### DELIVERY
Commit e relatório de até cinco linhas: comportamento, testes, gates, pendências e disjuntor.

### T8: Aceite real e distribuição
**Linear**: SC-224
**Depends on**: T7
**Requirements**: R1, R2, R4, R11, R12, R15, R16, R17, R21, R22
**Tests**: integration
**Gate**: build

#### TASK
Gerar dist pelo build, executar os comandos do CI e registrar o aceite real na Orca com capturas de 240 e 360 px, uma troca real comprovada e verificação de teclado e leitor de tela. Distinguir capturas reais de renderizações sintéticas.

#### CONTEXT
Spec: `.specs/features/ponte-viva/spec.md` (R1, R2, R4, R11, R12, R15–R17, R21, R22). Checks: C1, C2, C4, C11, C12, C15–C17, C21, C22. Compare com `.specs/features/ponte-viva/referencias/` e registre o que não puder ser comprovado. Carregar ou substituir plugin requer autorização do usuário aplicável ao conteúdo e às capacidades.

#### BOUNDARIES
May change: `docs/aceite/ponte-viva.md`, `docs/aceite/ponte-viva/`, `dist/`, `DECISIONS.md`
Do not touch: fontes do plugin e Handoff.

#### RULES
Leia AGENTS.md. Nunca edite dist manualmente; execute o gerador. Não instale, carregue ou aprove plugin sem autorização aplicável. Modo Git 3; commit convencional com `Refs: <ID-LINEAR>`. Sem push ou deploy.

#### DELIVERY
Commit e relatório de até cinco linhas: evidências reais, testes, gates, limitações e disjuntor.

## Checks

**Build**: `python tools/build.py --check`; `python scripts/check_decisions.py`; `claude plugin validate dist/claude --strict`
**Run unit**: `orca plugin test src/orca`

**C1** - Os 12 perfis têm nomes e identidades visuais distintos (R1)
Proof: run unit | ponte viva identifica os 12 integrantes
**C2** - A cena apresenta até seis integrantes com nome (R2)
Proof: run unit | ponte viva limita a seis integrantes
**C3** - A presença não muda pela passagem do tempo quando os estados são iguais (R3)
Proof: run unit | ponte viva mantém presença sem rodízio
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
**C10** - Selecionar integrante fora da cena o traz sem alterar seu estado (R10)
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
**C17** - Movimento reduzido suspende deslocamentos e mantém seleção manual (R17)
Proof: run unit | ponte viva respeita movimento reduzido
**C18** - Estado repetido não reinicia transição (R18)
Proof: run unit | ponte viva preserva transição em atualização repetida
**C19** - Mais de seis integrantes comprovados respeitam prioridade e permanência em empate (R19)
Proof: run unit | ponte viva prioriza presença estável
**C20** - Acionar integrante presente preserva a composição e seu estado (R20)
Proof: run unit | ponte viva mantém integrante já presente
**C21** - O vínculo exige sessão e worktree comprovados (R21)
Proof: run unit | ponte viva vincula sessão ao worktree
**C22** - Vínculo incerto não cria estado ou troca de presença (R22)
Proof: run unit | ponte viva não infere troca sem vínculo

## Handoff

**Phase:** pr-review
**Size:** LARGE
**Git mode:** 3
**Plugin:** 1.9.0
**Next:** corrigir achados da revisão Worf rodada 1
**Linear:** SC-216; T1 SC-217; T2 SC-218; T3 SC-219; T4 SC-220; T5 SC-221; T6 SC-222; T7 SC-223; T8 SC-224
**Integration branch:** feature/ponte-viva
**Last integrated:** a22a9a7591e40aa8a2039f67b0aeca7d72a020ad
**Dispatched:** nenhum
**Settled:** 2026-11-22: aprovado; 2026-11-22: sim; 2026-11-23: sim: revisão da spec aprovada; 2026-11-23: sim: tarefas e publicação no Linear aprovadas
**Attempts:** none
**Reports:** 2026-11-22: T1: perfis e estados implementados; 79 testes Orca passaram; commit 0c06273; dist será gerado em T5; 2026-11-22: T2: reconciliação automática, recuperação e concorrência; 84 testes Orca passaram; commit 33d0524; dist pendente de T5; 2026-11-22: T3 revisão: ampliar limites para corrigir estados por sessões ativas e melhorar composição; capturas requeridas; 2026-11-22: T3 revisão: atividade por count corrigida; prévia sintética 360 distante do mockup; devolvida para melhorar composição; 2026-11-22: T3: cena revisada e estados por sessões; 97 testes Orca passaram; prévias sintéticas verificadas; teste de T2 oscilou; commits 84164ec, e225444 e d16ba0c; 2026-11-22: T4: acessibilidade implementada e flakiness corrigida, 103 testes Orca; corrigir escopo e incerteza de atividade antes de integrar; 2026-11-22: T4: acessibilidade, flakiness e ambiguidade de estados corrigidas; 104 testes Orca; commits f3e7522 e 86faf81; 2026-11-22: T5: dist gerado, 104 testes Orca; suíte identificou falha no analisador de impacto; correção despachada; captura real pendente; 2026-11-22: T5: dist gerado e impact corrigido em b2c3edd; 104 testes Orca, 23 impact, build, decisões e validate verdes; captura real pendente; 2026-11-22: Q FAIL: cinco achados; correção em andamento; 2026-11-23: Retomada após desligamento: tentativa anterior interrompida; dois commits e alterações locais preservados; 2026-11-23: Pós-Q: cinco achados associados aos commits 7543e30, a96b4e4, 8afa2c2 e 7e83f4d; provas 21/21 e done automáticos verdes; 106 testes Orca e 1108 Python relatados pelo worker; gate ticket incompatível com escopo pós-Q; aceite real pendente; 2026-11-23: Aceite real: plugin de desenvolvimento autorizado e carregado; capturas Orca em 240 e 360 px revelam legibilidade insuficiente e divergência visual; acessibilidade real e troca de estado ainda pendentes; pasta de desenvolvimento descarregada antes das alterações; 2026-11-23: Tentativa de despacho recusada: consumer_fenced; Run foi vinculada ao coordenador atual; nenhum worker novo iniciado; 2026-11-23: LaForge despachado para corrigir legibilidade e aparência verificadas nas capturas reais 240 e 360; 2026-11-23: LaForge: revisão visual 1d9aa26, 111 testes Orca; capturas reais revisadas 240 e 360; árvore de acessibilidade expõe 12 e seleção traz Picard; teste real de teclado e leitor de tela pendentes; carregamento dev gerou arquivos auxiliares em dist, regenerar pelo build após testes; 2026-11-23: Teste real: Enter abriu relação; árvore acessível lista 12 nomes, estados e presença e seleção semântica funciona; foco não exposto impediu comprovar seleção por teclado; leitor de tela pendente. Suíte 1108: única falha dist auxiliar gerado pelo dev load, um teste ignorado; build regenerou dist e check passou; 2026-11-23: Após descarregar dev e regenerar dist, build check e teste test_repo_dist_is_up_to_date passaram; provas e gate done verdes; suíte completa anterior 1108, uma falha ambiental corrigida e um ignorado; 2026-11-23: Usuário confirmou anúncio de estado e presença e seleção acessível; solicitou presença estável e entradas e saídas por mudanças reais, sem rodízio periódico; 2026-11-23: T6–T8 preparados; gate tasks verde; issue mãe SC-216 e cinco tarefas existentes serão preservadas; 2026-11-23: Linear: descrição de SC-216 atualizada e SC-222 criada para T6; 2026-11-23: Linear: SC-223 criada para T7; 2026-11-23: Linear: SC-224 criada para T8; 2026-11-23: Linear: SC-221 bloqueia SC-222, SC-222 bloqueia SC-223, SC-223 bloqueia SC-224; issue mãe atualizada e reutilizada; 2026-11-23: T6: commit 32113be, 113 testes Orca e 1116 Python, gate ticket verde; identidade real sessão-hook ainda requer validação na Orca; 2026-11-23: T7: commit 437682b, presença estável e transições; 114 testes Orca, suíte Python e gate ticket verdes; aceite real segue T8; 2026-11-23: T8 parcial: commit 74365ce; testes Orca 114 e Python 1116, CI e gate ticket verdes; capturas novas e troca real pendentes de carregamento autorizado; 2026-11-23: T8 integrado em a22a9a7; provas automáticas verdes; aceite real e vínculo de sessão pendentes de captura; 2026-11-23: Q codex CLI padrão, modelo efetivo não confirmado: FAIL, três achados em 9313368; regressões 114 Orca e 1116 Python com um ignorado; 2026-11-23: LaForge despachado para corrigir estado inválido e caminhos vazios; acessibilidade real permanece pendente; 2026-11-23: Pós-Q: achados 1 e 2 corrigidos em b36170d e 7bdf0ec; 116 testes Orca e suíte Python relatados verdes, provas verdes; achado de acessibilidade segue aberto; capturas reais 240 e 360 geradas; 2026-11-23: Aceite real: sessionId e terminal do LaForge coincidem, mas sessions.worktree veio null; enviado diagnóstico somente leitura; seleção por teclado e leitor de tela da nova versão aguardam usuário; 2026-11-23: Diagnóstico real: Claude carrega hook instalado anterior à SC-222, mesma versão 1.9.0, que não grava worktree; payload cwd não observado; avaliar prova pelo agents.list filtrado sem trocar instalação; 2026-11-23: Diagnóstico: sessionId real coincidiu com hook antigo e agents.list limitado ao workspace; contrato e ausência de colisões exigem comprovação antes de aceitar registro sem worktree; 2026-11-23: LaForge avalia compatibilidade com hook anterior em worktree isolado; sem prova suficiente manterá desconhecido; 2026-11-23: Usuário respondeu teste ok ao roteiro real de teclado, leitor de tela, nomes, estados, presença e seleção; registrado em a1e7cbb; Esc e role status não foram confirmados separadamente; 2026-11-23: Compatibilidade do hook anterior integrada; gate T6 verde, commit 3ad479e; dados contraditórios permanecem desconhecidos; 2026-11-23: Aceite real: sessão LaForge vinculada e apresentada como trabalhando nas capturas 240 e 360; após término aparece desconhecido; transição animada entre dois integrantes não observada. Usuário confirmou teste acessível em termos gerais.; 2026-11-23: Usuário confirmou teste ok de presença estável e animação na seleção manual; troca por sessões reais ainda não observada; 2026-11-23: Usuário confirmou estabilidade e animação por seleção manual; validação de evento real iniciada; 2026-11-23: Evento real repetido com LaForge trabalhando e capturas 240/360; observador não viu entrada ou saída nem troca de integrante; usuário aprovou animação manual; 2026-11-23: Guinan: retro e lições L96, L97 e L98 registradas; usuário confirmou teclado e leitor em termos gerais; transição real entre agentes ainda não observada; 2026-11-23: PR 84 criado contra main com limitação de transição real documentada; 2026-11-23: Worf r1 COMMENT: três falhas funcionais e duas categorias de bypass de tipos; revisão local não publicada
**Breaker:** closed
