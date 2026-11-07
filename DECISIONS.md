# Registro de decisões

Formato de cada entrada: **problema → decisão → motivo → por que não é bug**. O texto completo das decisões D1–D32 está na seção 1 do `PLANO_STARCODE.md`.

## Protocolo para revisores

1. Antes de apontar um problema, procure aqui. Se o assunto está registrado, ele só é reaberto com **evidência nova** (versão de CLI, teste, documentação atual), citada na revisão.
2. "Eu faria diferente" não é evidência nova.
3. Uma decisão alterada ganha nova entrada que cita a anterior; a antiga não é apagada.
4. O gate da CI (`scripts/check_decisions.py`, Fase 1) bloqueia o release quando `skills/`, `scripts/` ou `hooks/` mudaram depois da última entrada deste arquivo.

## Decisões do plano (D1–D32)

| ID | Tema | Decisão (resumo) | Por que não é bug |
|---|---|---|---|
| D1 | Nome | StarCode. Comandos `/starcode:<skill>` (no OpenCode, `/sc-<skill>`) | — |
| D2 | Acesso ao Linear | `orca linear` para tudo o que ele cobre. MCP do Linear só para: criar Projetos, criar Documentos e criar as labels `crew:*` no setup, porque o `orca linear` 1.4.246 não faz nenhuma das três. Sempre com confirmação.… | O MCP parece mais completo, mas o `orca linear` mantém worktree e ticket ligados. O MCP fica só para o que o Orca não faz. |
| D3 | Tripulação | Mista TOS+TNG, 12 papéis, entregue em etapas (seção 3) | — |
| D4 | Persona | Só no chat. Commits, PRs, specs e comentários no Linear ficam neutros | Persona em artefatos poluiria histórico e revisão. Fica só na conversa. |
| D5 | Metodologia | Híbrido com tamanho automático por risco: fluxo do mattpocock + dimensionamento do tlc-spec-driven (4.1) + gates Python (formato na D24) + verificador independente | — |
| D6 | Artefatos | Fonte da verdade em `.specs/` no repositório. O Linear recebe a spec como Documento do Projeto e comentários de marco | — |
| D7 | Verificador (Q) | Outra família de modelo, com o contrato da seção 4.3. A ordem depende do CLI de onde se parte: no OpenCode, subagente com outro modelo; nos demais, worker de outro CLI via Orca (Codex ou OpenCode, nunca Gemini, que… | Usar o mesmo modelo para verificar repete os pontos cegos de quem implementou. Outra família é o objetivo, não um exagero. |
| D8 | Distribuição | Uma fonte só + gerador que escreve uma pasta por CLI em `dist/` (seção 9). Promessa do v1: núcleo comum nos 4 CLIs + extras onde o CLI suporta (9.1) | — |
| D9 | Context7 | Fonte de documentação, nunca de versão. Bootstrap só das dependências principais do perfil de stack; o resto sob demanda (seção 6) | — |
| D10 | Stacks | Perfis + scaffolding para Python/Flask, Rust/Tauri, TypeScript, PostgreSQL e MySQL. Versões do registro de pacotes ou da página oficial de releases | — |
| D11 | Git | 4 modos, perguntados a cada sessão. Modo 1 = verificação degradada (sem commit, gates em árvore suja, nunca "concluído"). Push e PR confirmados na hora. Merge do ticket no ramo de integração da feature não pede… | Perguntar o modo Git a cada sessão é intencional: o risco muda entre sessões. |
| D12 | Hooks | Bloquear Git perigoso + banner + scanner de segredos. No Claude, já na Fase 1 | — |
| D13 | Linear | Projeto por feature, issues por fatia com relações `blocks`, labels `crew:<tripulante>` | — |
| D14 | Extras | Auditoria do harness, review de PR (the-judge), retro/lições, painel Orca "Ponte" (todos depois do v1.0) | — |
| D15 | Publicação | Repo privado no GitHub com marketplace próprio. Atribuições em `CREDITS.md` | — |
| D16 | Idioma | Skills em inglês, saída em PT-BR. Nos artefatos, cabeçalhos e marcadores lidos pelos gates ficam em inglês; o texto corrido fica em PT-BR (D24) | Skills em inglês e saída em PT-BR não é inconsistência: os gates leem marcadores em inglês. |
| D17 | Modelos por tripulante | Padrões definidos na seção 3.2 (em `src/crew.yaml`), que o config do usuário pode sobrescrever. Precedência: pedido da sessão > config do usuário > padrão do `crew.yaml`. Aplicado de fato conforme a matriz da seção… | — |
| D18 | Modo Frota | Despacho paralelo via `orca orchestration worker-start` (`--deps` vindo das relações `blocks`, `--timeout-ms`, `--spec-file` com o briefing, `--base-branch` = ramo de integração), seguido de `orca worktree set… | — |
| D19 | Briefing e dono de arquivo | Cada ticket leva um briefing em 5 blocos e a lista de arquivos que pode alterar, dentro do `tasks.md` (D24). Dois tickets ativos nunca compartilham um arquivo | — |
| D20 | Configuração | Dois níveis (usuário e repositório) com `schemaVersion: 1`, validados por um validador próprio só com a stdlib do Python. Chave desconhecida = erro. Migração entre versões só quando existir a v2 (seção 5.2) | — |
| D21 | Ordem de entrega | Cada capacidade é construída e aceita primeiro no Claude Code; Codex, Antigravity e OpenCode ganham paridade numa fase própria | Codex, Gemini e OpenCode ficam atrás do Claude de propósito, até a fase de paridade. |
| D22 | Ramo de integração | Cada feature (GRANDE/COMPLEXA, modos 2–4) tem um ramo de integração `feature/<slug>` criado a partir do ramo base. Os worktrees dos tickets nascem dele, e o resultado de cada ticket é integrado nele. Gates finais, Q… | — |
| D23 | Execução por worker | O Picard só coordena. Cada ticket é implementado por um LaForge com contexto limpo, iniciado no worktree do ticket via `orca orchestration worker-start --worktree <ticket>`, mesmo no modo sequencial. O resultado… | O Picard não implementar nada, nem tarefas pequenas no modo sequencial, é intencional: contexto limpo por ticket. |
| D24 | Formato dos gates | Base: tlc-spec-driven (`spec.md` + `tasks.md`, duas aprovações). Os checks ficam só em `tasks.md ## Checks` (ou em `spec.md ## Checks` na tarefa MÉDIA). O briefing de 5 blocos fica sob cada tarefa no `tasks.md`.… | — |
| D25 | Verificação de telas | Fora do v1.0. Na adaptação dos gates, as regras de captura de tela são removidas e as skills avisam que mockups não são verificados automaticamente. Volta numa fase posterior (Fase 11), usando o navegador da Orca | Mockups não verificados no v1.0 é corte de escopo, não falha. |
| D26 | Corte de release | v1.0 = Fases 0–6 (fundação, núcleo, planejamento, execução sequencial com Q, paridade, hooks nos outros CLIs, distribuição). Depois: v1.1 Frota, v1.2 Uhura/Scotty/Kirk, v1.3 Worf/Guinan/diagnóstico, v1.4 painel, v1.5… | — |
| D27 | Disjuntor | 3 tentativas sem sucesso no mesmo erro = parar. Vale para qualquer loop de correção (gate vermelho, teste, build). O tripulante devolve ao usuário o resumo das 3 tentativas e duas saídas: repensar a abordagem ou… | Parar após 3 tentativas é intencional, mesmo quando a 4ª poderia dar certo. |
| D28 | Escritor único | Só o Picard escreve em `.specs/STATE.md` e em `tasks.md ## Handoff`. Workers e subagentes devolvem um relatório curto e nunca tocam nesses arquivos (evita sobrescrita entre workers paralelos) | Workers não atualizarem STATE/Handoff é intencional (evita sobrescrita em paralelo). |
| D29 | Paradas | Lista fechada de motivos para parar e lista do que nunca é motivo (seção 4.7). Toda parada traz as opções com a recomendação, e todas as decisões pendentes vão numa mensagem só | — |
| D30 | Registro de decisões | `DECISIONS.md` no repo do StarCode: problema → decisão → motivo → "por que não é bug". Revisores só reabrem um assunto registrado com evidência nova. Gate na CI bloqueia o release quando `skills/`, `scripts/` ou… | — |
| D31 | Skills concorrentes | O setup e o banner detectam skills e plugins instalados que competem com a tripulação (mattpocock, tlc, superpowers e similares) e mostram o comando para desativá-los. Nunca desativam sozinhos | O setup nunca desativa as skills concorrentes sozinho; só mostra o comando. |
| D32 | 4º CLI | Antigravity CLI (`agy`) no lugar do Gemini CLI. Adaptador nativo em `dist/antigravity`; também é agente de despacho da Orca. | Não há adaptador do Gemini de propósito: decisão do usuário, não esquecimento. |

## Decisões da Fase 0 (2026-11-03, CIF-7)

### F0-1: Hooks do Codex vêm do plugin e exigem trust
- **Problema:** o plano (rev 4) supunha que o Codex 0.166 não lia hooks de plugin.
- **Decisão:** gerar os hooks em `dist/codex/hooks/` e orientar o usuário a aprová-los em `/hooks`. O despacho de worker do Codex verifica antes se há hooks pendentes.
- **Motivo:** teste da Fase 0 (`docs/compatibilidade.md`, nota 5).
- **Por que não é bug:** o StarCode nunca usa `--dangerously-bypass-hook-trust`. O trust é decisão do usuário.

### F0-2: Modelo registrado (revisa a D17)
- **Problema:** a D17 mandava registrar o modelo do recibo da Orca, que não traz o modelo.
- **Decisão:** registrar o modelo pedido (campo `model` do resultado do `worker-start`) e o modelo efetivo lido do terminal ou do transcript. Se não houver confirmação, marcar `model: unconfirmed`.
- **Motivo:** teste da Fase 0 (nota 8).
- **Por que não é bug:** `unconfirmed` é um estado honesto, não falha do worker.

### F0-3: OpenCode instala o plugin na pasta global
- **Problema:** o plugin carregado por `OPENCODE_CONFIG_DIR` ou caminho absoluto não dispara o hook.
- **Decisão:** o setup copia o plugin para `~/.config/opencode/plugins/` e registra as skills com caminho absoluto no `opencode.json`.
- **Motivo:** teste da Fase 0 (nota 2).
- **Por que não é bug:** escrever na pasta global do usuário é intencional e acontece só com confirmação no setup.

### F0-4: Gemini distribuído por ramo próprio (**substituída pela D32**: o Gemini CLI saiu do projeto)
- **Problema:** o Gemini não instala extensão de subpasta de repo Git.
- **Decisão:** publicar `dist/gemini` na raiz de um ramo próprio e instalar com `--ref`.
- **Motivo:** teste da Fase 0 (nota 1).
- **Por que não é bug:** o ramo é gerado pelo build e nunca editado à mão.

### F0-5: Hooks de bloqueio usam JSON deny, não exit 2
- **Problema:** no Windows, o Codex roda hooks via `pwsh -Command`, que transforma exit 2 em 1. O hook aparece como falho e o comando passa (fail-open).
- **Decisão:** os hooks de bloqueio do Claude e do Codex imprimem `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":...}}` e saem com 0. O Antigravity responde `{"decision":"deny"}` (`--agy`).
- **Motivo:** teste da Fase 0 e código do Codex (`hooks/src/events/pre_tool_use.rs`, `hook_environment_executor.rs`).
- **Por que não é bug:** um hook de bloqueio sair com 0 é intencional. Quem bloqueia é o JSON.

### F0-6: Adaptador nativo do Antigravity, sem conversão automática
- **Problema:** `agy plugin install` converte um plugin do Claude, mas copia o `hooks.json` do Claude sem mudar nada. Com o matcher `Bash` e o campo `tool_input.command`, o hook nunca dispara no Antigravity, que usa `run_command` e `toolCall.args.CommandLine`.
- **Decisão:** o gerador escreve `dist/antigravity` no formato nativo: `plugin.json` na raiz, `hooks.json` com hooks nomeados, `--agy` nos scripts de hook e banner por `injectSteps` com `ephemeralMessage`.
- **Motivo:** teste da Fase 0 e documentação oficial (antigravity.google/docs/hooks).
- **Por que não é bug:** o caminho dos scripts no `hooks.json` é absoluto para a cópia instalada (`~/.gemini/config/plugins/<nome>`) até haver uma variável de raiz confirmada.

## Decisões da Fase 1 (2026-11-03, SC-8)

### F1-1: Modo Git gravado por worktree, dentro do diretório Git
- **Problema:** o `git_guard` precisa saber o modo da sessão, e cada worker roda no próprio worktree.
- **Decisão:** o Picard grava o modo com `scripts/git_mode.py set N` em `<git-dir>/starcode/session.json`. O hook aplica o último modo gravado naquele worktree. O SessionStart não apaga o modo.
- **Motivo:** o arquivo fica fora do Git (nunca é commitado) e é separado por worktree. Na Fase 3, o Picard grava o modo no worktree do ticket antes do despacho.
- **Por que não é bug:** o modo continua sendo perguntado a cada sessão pelo `engajar` (D11). Manter o último modo no hook até a nova resposta é o lado seguro, e o banner mostra quando ele foi gravado.

### F1-2: Fora de um repo com StarCode ativo, o hook só barra o que é sempre perigoso
- **Problema:** o plugin é instalado no nível do usuário e roda em qualquer repositório.
- **Decisão:** as regras de modo e de ramo base valem só quando há modo gravado ou `.starcode/config.json`. A lista "sempre bloqueado" (push forçado, exclusão de branch remota, `reset --hard`, `branch -D`, `clean -f`, `checkout -- .`/`restore .`) vale em qualquer repo.
- **Motivo:** não mudar o comportamento do Git em projetos que não usam o StarCode.
- **Por que não é bug:** `git push origin main` passar num repo sem StarCode é intencional.

### F1-3: Autorização de merge no ramo base registrada com validade
- **Problema:** o hook precisa distinguir merge/push no ramo base autorizado do acidental.
- **Decisão:** depois da autorização explícita do usuário, o Picard roda `git_mode.py authorize-merge <ramo>` (vale 10 minutos; trocar o modo revoga).
- **Motivo:** a autorização fica registrada e expira sozinha.
- **Por que não é bug:** o hook é uma rede contra acidente, não contra um agente mal-intencionado. Registrar uma autorização que o usuário não deu é proibido pelas skills.

### F1-4: `engajar` e `setup` podem ser acionadas pelo modelo
- **Problema:** a tabela da seção 3 marca o Picard como "usuário", mas a Fase 1 exige evals de roteamento por frase.
- **Decisão:** as duas skills ficam com `invocation: both`, com descrições estreitas (só disparam quando a frase cita o StarCode ou a tripulação). Os evals negativos garantem que pedidos comuns não disparam nada.
- **Motivo:** `disable-model-invocation` impediria "StarCode, vamos começar..." de funcionar.
- **Por que não é bug:** as escritas continuam com confirmação. Roteamento: 10/10 (5 positivos e 5 negativos).

### F1-5: `crew.yaml` lido por um parser YAML mínimo
- **Problema:** o gerador usa só a stdlib, que não lê YAML.
- **Decisão:** `tools/miniyaml.py` lê um subconjunto (mapas, listas, listas e mapas em linha, comentários). O build grava `crew.json` em cada pasta de `dist/`, e os scripts em tempo de execução nunca leem YAML.
- **Por que não é bug:** sintaxe fora do subconjunto (âncoras, `|`, tabs) gera erro com o número da linha, nunca uma leitura errada em silêncio.

### F1-6: Caminhos das skills com o marcador `<plugin-root>`
- **Problema:** as skills chamam scripts do plugin, e cada CLI expõe o caminho de um jeito.
- **Decisão:** a fonte usa o texto literal `<plugin-root>` e uma linha de declaração em cada SKILL.md, preenchida pelo build: no Claude, `${CLAUDE_SKILL_DIR}/../..` (substituído pelo Claude Code ao carregar a skill); nos outros CLIs, "duas pastas acima da pasta da skill".
- **Por que não é bug:** as referências (`references/*.md`) não recebem substituição em nenhum CLI. Por isso usam o marcador, e o build recusa `{{PLUGIN_ROOT}}` fora do SKILL.md.

### F1-7: Hooks só registrados no adaptador do Claude; plugin renomeado
- **Decisão:** em `dist/codex`, `dist/antigravity` e `dist/opencode`, os scripts vão junto, mas sem registro de hook (Fase 5). O plugin de teste `starcode-hello` saiu, e o plugin agora se chama `starcode` (instalação: `starcode@starcode`).
- **Por que não é bug:** ausência de `hooks.json` nos outros CLIs é a ordem de entrega (D21), não esquecimento. Quem instalou o `starcode-hello` precisa desinstalá-lo e instalar o `starcode`.

### F1-8: Labels `crew:*` dos 12 tripulantes criadas de uma vez
- **Decisão:** o setup cria as labels de toda a tripulação, inclusive dos que entram depois da v1.0.
- **Por que não é bug:** evita rodar o setup de novo a cada release. Label sem uso não tem custo.

### F1-9: Banner leve no SessionStart, completo no `engajar`
- **Decisão:** no SessionStart, sem rede além do `orca status` (com tempo-limite). A checagem do Linear (`team list`/`team states`) só roda com `--full`, chamado pelo `engajar`. Em repo sem StarCode, uma linha de contexto e nenhuma mensagem na tela.
- **Por que não é bug:** o início da sessão não pode travar por causa da rede, e repositórios sem StarCode não devem ganhar ruído.

### F1-10: Evals dentro de `dist/claude/evals`
- **Problema:** o `claude plugin eval` procura os casos abaixo da pasta do plugin.
- **Decisão:** a fonte fica em `evals/`, e o build copia para `dist/claude/evals/`. Os resultados ficam fora do Git e do `build --check`.
- **Por que não é bug:** são arquivos pequenos de texto, sem efeito no uso do plugin.

### F1-11: A missão é perguntada em texto livre (ajuste após a sessão real de aceite)
- **Problema:** na sessão real, o `engajar` ofereceu "Descrever em Other" como opção de múltipla escolha, e a descrição da tarefa se perdeu. O banner também dizia que o setup cria o config do usuário, mas o setup não grava nada quando o usuário mantém os padrões.
- **Decisão:** as escolhas (modo Git, retomada, preflight) continuam juntas numa pergunta. A missão, quando ainda não foi dada, é pedida em texto livre no mesmo turno, nunca como opção de menu. O banner passa a dizer "ausente (valem os padrões do crew.yaml; só é criado se algo diferir)".
- **Por que não é bug:** config do usuário ausente é o estado normal de quem usa os padrões (a D17 guarda só as diferenças).

### F1-12: O setup sempre cria o config do usuário (revisa a F1-11, parte do banner)
- **Problema:** a F1-11 tratou "config do usuário ausente" como o estado normal de quem mantém os padrões. A seção 5.2 do plano diz que a primeira execução do setup **cria** o config do usuário, e o critério de aceite pede "grava os dois configs". A sessão real de aceite expôs a contradição.
- **Decisão:** sem diferenças, o setup grava `{"schemaVersion": 1}` pelo validador. O banner volta a mandar rodar o `/starcode:setup` quando o arquivo falta. A parte da F1-11 sobre a missão em texto livre continua valendo.
- **Motivo:** o arquivo marca a máquina como configurada e fixa a versão do schema. A D17 continua valendo: `crew` guarda só o que difere do `crew.yaml`.
- **Por que não é bug:** um config com só `schemaVersion` é válido e não muda nenhum padrão.

## Decisões da Fase 2 (2026-11-03, SC-9)

### F2-1: Gates adaptados do tlc com marcador de tamanho
- **Problema:** o tlc não marca o tamanho na spec, então o gate não sabe se cobra o template completo ou o breve.
- **Decisão:** a spec traz `**Size**: MEDIUM | LARGE | COMPLEX`. MEDIUM usa o template breve com `## Checks`; LARGE/COMPLEX, o completo, e os checks ficam só no `tasks.md` (D24). Detalhes no ADR-0002.
- **Por que não é bug:** `**Size**: SMALL` é recusado de propósito: a tarefa PEQUENA não tem spec.

### F2-2: Diagrama de execução do tlc removido
- **Decisão:** dependências só pelo `**Depends on**`. Ciclo e dependência inexistente são erro. Tarefas sem caminho de dependência entre si não podem compartilhar caminho em `May change`.
- **Por que não é bug:** o diagrama repetia o `Depends on` e as relações `blocks` do Linear saem dele. A regra de arquivo vale mesmo no modo sequencial, porque a Frota (v1.1) vai despachar essas tarefas juntas.

### F2-3: Handoff no artefato mais avançado
- **Problema:** o plano põe o Handoff em `tasks.md`, mas a feature MÉDIA não tem `tasks.md`, e a GRANDE só ganha um depois da spec. Sem Handoff nessas fases, uma interrupção não tem de onde retomar.
- **Decisão:** o Handoff fica em `tasks.md`, ou `spec.md`, ou `context.md`, o que estiver mais adiante. O Picard o move quando nasce um artefato novo. O banner lê os três, nessa ordem. Formato e tabela de retomada em `skills/engajar/references/state-format.md`.
- **Por que não é bug:** continua um escritor só (D28) e um Handoff só por feature.

### F2-4: Data acionável pelo modelo
- **Problema:** o `crew.yaml` marcava o Data como `invocation: user`, que vira `disable-model-invocation` no Claude. O Picard não conseguiria chamar o Data depois da aprovação da spec.
- **Decisão:** `invocation: both`, como Troi e Spock.
- **Por que não é bug:** as escritas no Linear continuam atrás de uma confirmação explícita, e o gate `validate_spec --approved` impede o Data de começar sem a aprovação 1.

### F2-5: `tasks_export.py` não chama o Linear
- **Decisão:** o script só gera o corpo das issues, as relações e grava os IDs de volta (`record`). Quem roda `orca linear create`/`relation add` e o MCP é o Data, depois da confirmação.
- **Por que não é bug:** escrita no Linear exige confirmação na conversa e leitura do `--help` (seção 5.0); um script que escreve sozinho pularia as duas.

### F2-6: Requisitos aceitam SHALL ou DEVE
- **Decisão:** o template usa as palavras-chave EARS em inglês (`WHEN … THEN the system SHALL …`) com o resto em PT-BR, e o gate também aceita `DEVE`/`QUANDO`/`SE`.
- **Por que não é bug:** a D16 deixa a prosa em PT-BR. Aceitar as duas formas evita que uma spec correta fique vermelha só pela língua do verbo.

### F2-7: Commit dos artefatos de planejamento nos marcos aprovados
- **Problema:** na sessão real de aceite, no modo 2, o `.specs/` ficou primeiro sem commit; depois, o Picard fez commits no ramo base por conta própria, sem `Refs:` e deixando de fora uma revisão aprovada.
- **Decisão:** nos modos 2–4, o Picard faz commit só de `.specs/` (e `.starcode/` quando mudou) em cada marco aprovado: MÉDIA depois da aprovação da spec e do vínculo da issue; GRANDE/COMPLEXA depois da publicação no Linear; cada reaprovação de revisão ganha um commit próprio. Mensagem `docs(specs): … (<slug>)` com `Refs:` das issues da feature, conferida pelo `check_commit.py`. Modo 1: sem commit.
- **Motivo:** a D6 faz do `.specs/` a fonte da verdade no repositório, e a retomada usa o Git como evidência (4.2).
- **Por que não é bug:** o commit vai para o ramo atual, que antes do ramo de integração é o ramo base. É commit local e permitido no modo 2. Push continua só nos modos 3/4, com confirmação.

### F2-8: Gatilhos "contrato público" e "ambiguidade" contados com rigor
- **Problema:** na sessão real de aceite, uma CLI que só o dono usa contou como "contrato público", e "ambiguidade" contou mesmo depois que as perguntas resolveram tudo. Com dois gatilhos, quase toda feature virava GRANDE e a MÉDIA nunca aparecia.
- **Decisão:** "contrato público" só quando alguém fora do repositório consome o formato ou a interface. "Ambiguidade" só quando sobra depois de uma rodada de perguntas (no máximo 4), feita antes de classificar. Regra em `skills/engajar/references/risk-sizing.md`.
- **Por que não é bug:** os outros gatilhos não mudam, e a regra "na dúvida, a classe mais alta" continua valendo depois da rodada de perguntas.

### F2-9: Uma pergunta só para aprovar e publicar
- **Problema:** a aprovação 2 e a confirmação da publicação no Linear eram duas paradas seguidas sobre a mesma coisa. Na MÉDIA, a aprovação da spec e a criação da issue também.
- **Decisão:** o Data monta o plano de publicação e confere duplicatas antes de perguntar, e faz uma pergunta só: "Aprovo as tasks e publico no Linear? (sim / só aprovar / ajustes)". Na MÉDIA, o Spock pergunta "Aprovo a spec e crio a issue no Linear?". Um "sim" vale pelas duas coisas.
- **Por que não é bug:** a escrita no Linear continua atrás de uma confirmação explícita na conversa (seção 5.0). A pergunta mostra tudo o que será criado e tem a opção "só aprovar".

### F2-10: Turnos curtos, Handoff por script e bordão fora das perguntas
- **Problema:** cada atualização do Handoff despejava o diff no chat, as apresentações traziam tabelas inteiras e o bordão vinha depois da pergunta de aprovação. Numa sessão real, a aprovação foi respondida com o próprio bordão do Picard.
- **Decisão:** o Handoff é gravado só pelo `scripts/handoff.py set`, que move a seção para o artefato mais avançado e imprime uma linha. Turnos de até ~15 linhas, com resumo e caminho do arquivo, sem relatório de gate, diff ou Handoff no chat. Bordão só quando um passo começa e quando devolve, nunca num turno que termina em pergunta. O commit da F2-7 é feito sem perguntar, porque a aprovação já é a autorização.
- **Por que não é bug:** o Picard continua sendo o único escritor do Handoff (D28); o script é a ferramenta dele. O formato da seção não muda, e o banner lê o que o script grava (teste em `tests/test_handoff.py`).

### F2-11: Troi com limite de rodadas
- **Problema:** em GRANDE, a Troi não tinha limite de rodadas e perguntava coisas que não mudam o comportamento (14 rodadas de áreas cinzentas na sessão de aceite).
- **Decisão:** no máximo 1 rodada em MÉDIA, 2 em GRANDE e 3 em COMPLEXA. Só se pergunta o que muda comportamento visível e não tem padrão seguro. O resto vira padrão registrado (`default (não perguntado)`), listado numa linha do resumo para o usuário poder mudar na aprovação da spec.
- **Por que não é bug:** a varredura de requisitos implícitos continua completa em GRANDE; só deixa de virar pergunta. A aprovação da spec é onde o usuário confere esses padrões.

### F2-12: Handoff só pelo script, Settled só depois da aprovação e retomada sem perguntas
- **Problema:** na sessão de aceite da MÉDIA, mesmo com a F2-10, o Handoff foi gravado com `cat >>` e scripts inline, e o diff apareceu no chat. O `**Settled:**` recebeu respostas de antes da aprovação (modo Git, retomada). O Picard também perguntou sobre features paradas esperando o LaForge e sobre um commit de artefato já aprovado.
- **Decisão:** a Troi, o Spock e o Data trazem o comando exato do `handoff.py` no fechamento do passo. Editar o Handoff à mão fica proibido de forma explícita. `**Settled:**` só recebe respostas depois da aprovação da spec. Na retomada, a feature que espera um tripulante ainda não instalado vira uma linha no relatório, sem pergunta. Um artefato aprovado sem commit é commitado (F2-7) e informado numa linha.
- **Por que não é bug:** breaker aberto e conflito entre Git e anotações continuam sendo perguntas (4.2, D29). O commit automático vale só para `.specs/` sem outras mudanças misturadas.

## Decisões da Fase 3 (2026-11-04, SC-10)

### F3-1: `dist/` regenerado em todo commit que muda a fonte
- **Problema:** o `tasks.md` da fase deixava a regeneração do `dist/` só para a T9, mas `test_repo_dist_is_up_to_date` exige o `dist/` atualizado em todo commit que muda `skills/`, `scripts/` ou `hooks/`.
- **Decisão:** cada commit de código regenera o `dist/` (`python tools/build.py`) e o inclui. No StarCode, `dist/` é saída gerada, não arquivo de ticket.
- **Motivo:** o primeiro commit da T1 deixou a suíte vermelha até o `dist/` ser regenerado (`43e387e`).
- **Por que não é bug:** com a Frota (v1.1), dois tickets do próprio StarCode tocariam `dist/` ao mesmo tempo; o Data deve tratar `dist/` como arquivo sensível (`Runs alone`) nesse caso.

### F3-2: Integração e próximo ticket lidos do Git
- **Problema:** o Handoff guarda só o último commit integrado; uma retomada precisa saber quais tickets já entraram no ramo da feature.
- **Decisão:** `dispatch.py next` considera integrado o ticket cujo ID do Linear aparece num rodapé `Refs:` de `<base>..feature/<slug>`, ou cujo merge diz `integra T<n>`. Um `**Dispatched:**` sem integração bloqueia novo despacho (saída 3).
- **Motivo:** a evidência do Git vence a anotação (plano 4.2).
- **Por que não é bug:** um commit de outro ticket que cite o ID por engano marcaria o ticket como integrado; o `check_scope` e o `Refs` esperado da etapa `ticket` reduzem esse risco.

### F3-3: Provas continuam válidas após commits só em `.specs/`
- **Problema:** commitar o `proofs.md` e o `verification.md` muda o HEAD, e o gate do tlc reprova provas de outro commit.
- **Decisão:** `validate_verification.py` aceita provas de um commit anterior quando todos os commits depois dele só mudam `.specs/`.
- **Motivo:** sem isso, a feature nunca fecha no modo 2.
- **Por que não é bug:** qualquer mudança de código depois das provas continua reprovando.

### F3-4: Modo 1 fecha só como verificação degradada
- **Problema:** no modo 1 não há commits, então as provas rodam em árvore suja e os achados não têm commit de fechamento.
- **Decisão:** `check_proofs.py` grava `**Tree**: dirty (modo 1)` e sai com 1; `validate_verification.py` aceita a árvore suja e o `Closed` com `degradada (modo 1)` só quando o `verification.md` tem `**Verification:** degraded`, e mesmo assim avisa (vermelho com `--strict`).
- **Motivo:** D11 e plano 4.3: modo 1 é sempre verificação degradada.
- **Por que não é bug:** a issue nunca vai para concluído no modo 1; o gate só deixa o resultado visível.

### F3-5: Escritor único conferido por `check_scope.py`
- **Problema:** a regra de que só o Picard escreve `STATE.md` e o Handoff (D28) dependia só do briefing.
- **Decisão:** antes de integrar, `run_gates.py ticket` roda `check_scope.py`, que reprova arquivo fora do `May change`, mudança em `.specs/STATE.md` ou na seção `## Handoff`, e intervalo sem commit. Um padrão com `*` em `May change` também cobre subpastas (`fnmatch`).
- **Motivo:** aceite da Fase 3 ("conferido pelo diff de cada ticket").
- **Por que não é bug:** o Q não passa pelo `check_scope`; a escrita extra dele é descartada pelo Picard (R23).

### F3-6: McCoy dentro do worker do LaForge e Q com cascata de CLIs
- **Problema:** o plano não dizia onde o McCoy roda, nem o que fazer quando o Codex não sobe.
- **Decisão:** o McCoy é uma skill acionada pelo LaForge na 2ª falha do mesmo erro, na mesma sessão do worker. O Q tenta `codex`, depois `antigravity` com modelo Gemini, e por fim um subagente de contexto limpo marcado `self-verified`.
- **Motivo:** padrões aprovados com a spec da fase (2026-11-04, user: "sim").
- **Por que não é bug:** o subagente `self-verified` aparece como degradado no Linear e no banner (D7).

### F3-7: Sub-issues de fase do StarCode concluídas ao terminar
- **Problema:** a regra de "concluído só com confirmação" (R31) vale para as features que o StarCode executa; as sub-issues da própria fase (SC-20 a SC-29) são tarefas de desenvolvimento do plugin.
- **Decisão:** cada sub-issue da fase vai para Done quando seu commit passa na suíte completa, com comentário do commit e dos checks. A SC-10 só fecha depois do aceite e do merge.
- **Motivo:** o usuário pediu o Linear sempre atualizado.
- **Por que não é bug:** o aceite da fase (T10) continua sendo a evidência que fecha a SC-10.

### F3-8: Fechar o disjuntor dá tentativas novas ao erro
- **Problema:** no aceite (roteiro 4), depois de o usuário escolher uma saída e o Picard gravar `--breaker closed`, a primeira falha do mesmo erro reabria o disjuntor (`attempts 4/3`), porque o contador ficava em 3.
- **Decisão:** `handoff.py set --breaker closed` sobre um disjuntor aberto zera o contador do identificador que o abriu; os outros identificadores ficam como estavam.
- **Motivo:** a escolha do usuário (repensar ou voltar ao último commit integrado) é um recomeço daquele erro; sem o zero, a saída escolhida não teria nenhuma tentativa.
- **Por que não é bug:** as 3 falhas seguidas continuam abrindo o disjuntor; só o recomeço depois da decisão do usuário passa a contar do zero.

### F3-9: `check_proofs` roda todo `Run` declarado
- **Problema:** o Q da fase 3 achou que um `**Run <nome>**:` que nenhum `Proof:` cita era ignorado, e o `proofs.md` não registrava a saída dele, contra o R1.
- **Decisão:** cada `Run` declarado em `## Checks` roda uma vez, citado ou não, e a saída vai para `## Output`; um `Run` não citado que falha deixa as provas vermelhas.
- **Motivo:** um comando declarado nos checks faz parte da evidência; ignorá-lo esconderia uma suíte vermelha.
- **Por que não é bug:** as provas citadas continuam julgadas pela linha esperada; só deixou de existir o comando declarado e não executado.

## Decisões da Fase 4 (2026-11-05, SC-30)

### F4-1: Matriz de recursos por CLI com `fallback` obrigatório
- **Problema:** hooks, banner por hook, MCP do Linear, modelo de subagente e worker da Orca existem de forma diferente em cada CLI, e o Claude era o único caso tratado.
- **Decisão:** `src/capabilities.yaml` lista cada extra por CLI com `status` (`ok` ou `unavailable`); `tools/build.py` grava `capabilities.json` por `dist/<cli>` e falha com `BuildError` se um extra `unavailable` não tiver `fallback`. O banner imprime `Indisponível neste CLI: <extra> → <fallback>`.
- **Motivo:** o núcleo comum roda em todo CLI; o que falta vira aviso com caminho alternativo, não falha silenciosa.
- **Por que não é bug:** um passo do núcleo que falha reprova o CLI no aceite (R29); ele nunca é marcado como extra indisponível.

### F4-2: Issue-mãe quando o CLI não tem o MCP do Linear
- **Problema:** o Data publicava com Projeto e Documento pelo MCP, que nem todo CLI tem.
- **Decisão:** com `linear_mcp` `unavailable`, o Data cria com `orca linear create` uma issue-mãe (título da feature, spec na descrição) e cada ticket como sub-issue (`--parent`), com as relações `blocks` e os IDs gravados por `tasks_export.py record`; `run_gates.py publish` aceita a issue-mãe no lugar do Projeto.
- **Motivo:** mantém a publicação e o vínculo ticket↔worktree sem depender do MCP.
- **Por que não é bug:** o Data diz em uma linha qual caminho usou (R17); o caminho do MCP continua o padrão onde existe.

### F4-3: Limite de aninhamento da Orca
- **Problema:** com o Picard como worker do CLI testado, o LaForge e o Q ficam um nível abaixo, e o limite padrão da Orca barrava o `worker-start` (`nested_worker_depth_exceeded`).
- **Decisão:** o usuário configurou o limite em 3 em 2026-11-05 (Settings → Orchestration). O fluxo precisa de no mínimo 2 (Picard worker → LaForge/Q). Ao receber `nested_worker_depth_exceeded`, o Picard para e avisa que o limite precisa ser 2 ou mais, sem contar tentativa do disjuntor (R22).
- **Motivo:** resposta do usuário na spec ("Subir o limite para 2"), superada pela configuração em 3, que cobre o mínimo.
- **Por que não é bug:** o valor 3 é folga da configuração local; a exigência do fluxo continua sendo 2.

### F4-4: Worktree de integração do Picard
- **Problema:** o Handoff, o `proofs.md` e o `verification.md` eram gravados no checkout de quem chamou, e um Picard rodando como worker não tem o ramo `feature/<slug>` à mão.
- **Decisão:** ao criar ou reutilizar o ramo de integração `I`, o Picard cria ou reutiliza um worktree da Orca para `I` e grava ali esses três artefatos (R21). No OpenCode, o worktree do ticket sai antes, com `--base-branch feature/<slug>` (R20).
- **Motivo:** um único lugar para o estado da feature, no mesmo ramo que recebe os merges dos tickets.
- **Por que não é bug:** o escritor único continua sendo o Picard (F3-5); só mudou onde ele escreve.

### F4-5: `install_local --cli codex` substitui um marketplace de outra fonte
- **Problema:** com o marketplace `starcode` já registrado de outra fonte, o `marketplace add` falhava (`already added from a different source`) e o script parava antes do `plugin add` (aceite do Codex).
- **Decisão:** se a saída do `marketplace add` contém essa mensagem, o script roda `codex plugin marketplace remove starcode`, repete o `add`, imprime o que fez e segue para o `plugin add`. Qualquer outra falha continua saindo com código 1; `--dry-run` só imprime o plano.
- **Motivo:** reinstalar a partir de um novo checkout é o uso normal do aceite, e exigir o `remove` manual quebrava o fluxo.
- **Por que não é bug:** reinstalar da mesma fonte não dispara o `remove`; a remoção só ocorre quando o próprio CLI diz que a fonte é outra.

### F4-6: `q-cli` só responde `self-verified` sem CLI de outra família disponível
- **Problema:** `dispatch.py q-cli` respondeu `self-verified` num LaForge Codex embora o Antigravity estivesse disponível: o plugin instalado num CLI só carrega o `capabilities.json` dele, e a falta do registro dos outros CLIs contava como indisponível.
- **Decisão:** um registro que existe decide (`orca_worker` `ok` ou não). Sem registro, o CLI conta como disponível se foi pedido em `--configured` ou se o binário (`codex`, `agy`, `opencode`) está no PATH. Um `--caps-dir` explícito continua sendo autoridade: sem registro nele, o CLI não conta.
- **Motivo:** `self-verified` degrada a verificação (R19) e só vale quando não há como verificar em outra família.
- **Por que não é bug:** um registro `unavailable` ainda vence o binário no PATH.

### F4-7: O briefing carrega as linhas Proof e exige o planejamento commitado
- **Problema:** o briefing citava só os IDs dos checks, e o worker inventava nomes de teste que o `check_proofs` não encontrava (24 provas vermelhas); e o Picard despachou sem commitar `.specs/features/<slug>/`, então o worktree nasceu sem a spec e o `check_scope` falhou.
- **Decisão:** `dispatch.py brief` copia para o CONTEXT, de cada check da task, a linha `**Cn** - ...`, as linhas `Proof:` e as linhas `**Run <nome>**:` que elas leem, exatas, com a regra de que o teste se chama como na linha Proof (a MÉDIA ganha a mesma regra). Sai com código 2 e mensagem em PT-BR quando `spec.md` ou `tasks.md` não está em HEAD.
- **Motivo:** o worker só vê o briefing e o worktree dele nasce de HEAD; o que não está lá não existe para ele.
- **Por que não é bug:** a checagem usa `git cat-file -e HEAD:<arquivo>`, então planejamento commitado e depois alterado no disco não bloqueia.

### F4-8: Família só com vendor e modelo reais; `fallback` em branco não vale
- **Problema:** o Q da Fase 4 achou `dispatch.family("openrouter/anthropic/")` devolvendo `anthropic` e `build.load_capabilities` aceitando `fallback: "   "`; os testes de C15, C16 e C27 só procuravam palavras.
- **Decisão:** `openrouter/<vendor>/<modelo>` só ganha família com vendor e modelo não vazios (senão `unknown`); `fallback` precisa ter texto após `strip()`. C15/C16 passam a conferir os comandos da seção 2b da skill Data e a rodar o gate `publish` (recusa sem IDs, aceita com IDs gravados); C27 exige `VEREDITO: VERDE` e a linha "Modelos efetivos" em cada CLI.
- **Motivo:** uma prova que passa mesmo quando a regra é violada não prova nada (R1, R2, R15–R17, R25, R27).
- **Por que não é bug:** `unknown` já é o tratamento de família indeterminada (compare devolve `unknown`, o Q cai em `self-verified` só sem outra família).

### F5-1: Raiz do plugin nos hooks de cada CLI
- **Problema:** o `dist/` não pode ter caminho absoluto de máquina (R4), mas cada CLI resolve a raiz do plugin de um jeito.
- **Decisão:** no Codex, o comando do hook usa `${CLAUDE_PLUGIN_ROOT}`; no Antigravity e no OpenCode, `tools/install_local.py` grava o caminho absoluto dos scripts na cópia instalada (`hooks.json` e `starcode.js`). Se o aceite mostrar que o Codex não expande a variável, o Codex passa a seguir o mesmo caminho absoluto, como ticket próprio.
- **Motivo:** o Codex 0.166 expande a variável em plugins de terceiros; os outros dois não têm variável de raiz.
- **Por que não é bug:** o `dist/` continua sem caminho de máquina; o absoluto só existe na cópia instalada.

### F5-2: Hook falho deixa o comando passar com aviso `StarCode hook:`
- **Problema:** Python ausente, payload sem comando, JSON inválido ou erro interno poderiam travar o agente.
- **Decisão:** fail-open: o comando passa e o hook escreve uma linha que começa com `StarCode hook:` (R9, no espírito de F1-2).
- **Motivo:** um guarda quebrado não pode paralisar o trabalho; o aviso torna a falha visível.
- **Por que não é bug:** o bloqueio só vale quando o hook roda; sem trust (Codex) ou sem Python, o banner e o setup avisam.

### F5-3: Sem banner por hook no OpenCode
- **Problema:** o OpenCode aceita hook de ferramenta (`execute.before`), mas não há evento de início de sessão que entregue contexto.
- **Decisão:** o plugin do OpenCode só bloqueia; `banner_hook` fica `unavailable` e vale o fallback atual (decisão do usuário: "Bloqueio sim, banner não").
- **Motivo:** não inventar um canal que o CLI não oferece.
- **Por que não é bug:** o roteiro do OpenCode marca o banner como n/a e o aceite não o cobra.

### F5-4: Comando do hook do Antigravity sem aspas no caminho
- **Problema:** no Windows, o agy 1.5.1 passava as aspas do comando do hook literalmente ao python, e o hook falhava.
- **Decisão:** o comando do hook do Antigravity é escrito sem aspas no caminho, e `install_local` recusa caminho com espaço (T12, commit 7510a18).
- **Motivo:** sem aspas o comando funciona no aceite real; recusar o espaço evita gerar um comando que quebraria.
- **Por que não é bug:** a recusa é intencional e a mensagem aponta o caminho; o aceite real do Antigravity cobre o comportamento.

### F5-5: Antigravity extrai a pasta de `workspacePaths[0]`
- **Problema:** o payload real do `PreToolUse` (agy 1.5.2) não traz `Cwd`/`cwd`, só `workspacePaths`, e o hook roda na pasta do plugin.
- **Decisão:** `extract()` usa `workspacePaths[0]` quando faltam os outros campos (T14, commit acd4153).
- **Motivo:** é a única indicação do projeto do usuário no payload real.
- **Por que não é bug:** `Cwd`/`cwd` continuam tendo prioridade quando presentes; o fallback só entra na ausência deles.

### F5-6: Plugin do OpenCode usa `event.input.workdir`
- **Problema:** no OpenCode 2.2.3, `process.cwd()` do plugin é a home do usuário, não o projeto.
- **Decisão:** o plugin usa `event.input.workdir` e só cai em `process.cwd()` sem ele (T16, commit aa01094).
- **Motivo:** o diretório do evento é o do projeto em uso; `process.cwd()` apontaria para o lugar errado.
- **Por que não é bug:** o fallback para `process.cwd()` preserva o comportamento de versões que não enviam `workdir`.

### F5-7: Diff staged sem truncar e banner de hook em `--full`
- **Problema:** o `secret_scan` cortava o diff staged em 2 MB e deixava passar segredo depois disso; os hooks de `SessionStart` do Codex e do Antigravity rodavam o banner sem `--full`, e o do Antigravity podia não receber `cwd` (achados do Q, SC-12).
- **Decisão:** o diff de cada arquivo é examinado inteiro; acima de 64 MB o hook nega com "diff grande demais para verificar" (o mesmo vale para arquivos de `--body-file`). Os hooks do Codex e do Antigravity passam `--full`, e o banner usa `workspacePaths[0]` quando o payload não traz `cwd`.
- **Motivo:** nunca deixar de verificar em silêncio (R5/R6); o hook entrega o mesmo texto de `banner.py --full --text` (R10).
- **Por que não é bug:** o limite de 64 MB nega em vez de pular, e a saída tem o caminho para aprovar o arquivo em `.starcode/secret-allowlist`; o `cwd` do payload continua tendo prioridade sobre `workspacePaths`.

### F6-1: Dia de missão no `starcode-sandbox`, não num projeto real
- **Problema:** o aceite do v1.0 pedia uma feature grande rodada de ponta a ponta, e a spec previa um "projeto real" para isso.
- **Decisão:** o dia de missão roda no `starcode-sandbox`, modo Git 2, do engajar ao gate `done` (roteiro `docs/aceite/roteiros-fase-6/dia-de-missao.md`).
- **Motivo:** escolha do usuário em 2026-11-06.
- **Por que não é bug:** o sandbox exercita o fluxo completo sem risco a um projeto em produção.

### F6-2: Banner mostra setup e engajar no formato de cada CLI
- **Problema:** o banner citava `/starcode:setup` e `/starcode:engajar` em qualquer CLI, mas Codex e Antigravity chamam skills e o OpenCode usa `/sc-setup` e `/sc-engajar`.
- **Decisão:** `hooks/scripts/banner.py` escolhe o texto dos comandos conforme `--cli` (T2, commit 871b9ca).
- **Motivo:** o usuário precisa ver o comando que funciona no CLI em que está.
- **Por que não é bug:** sem `--cli`, o banner mantém o formato do Claude Code.

### F6-3: O instalador do OpenCode troca os caminhos de skill do StarCode
- **Problema:** instalar o OpenCode de clones diferentes acumulava caminhos `dist/opencode/skills/*` em `skills.paths`.
- **Decisão:** `tools/install_local.py` remove os caminhos de skill do StarCode de outros clones e grava os do clone atual, sem tocar nos caminhos alheios nem na ordem deles (T1, commit df8ec8e).
- **Motivo:** a reinstalação limpa do aceite não pode deixar skills duplicadas ou apontando para um clone antigo.
- **Por que não é bug:** caminhos que não são de skills do StarCode ficam intactos.

### F6-4: `tools/release.py` recusa tag que diverge de `VERSION`
- **Problema:** criar `v1.0.0` com `VERSION` diferente, ou sobre uma tag já publicada, quebraria a rastreabilidade do release.
- **Decisão:** `tools/release.py` confere a tag contra `VERSION`, exige a seção da versão no CHANGELOG e só cria tag e release com confirmação (T4, commit 4dc6bf4).
- **Motivo:** R23 e R24: nada de `--force` nem de release sem notas.
- **Por que não é bug:** a recusa sai com código 1 e a mensagem diz o que divergiu.

### F6-5: O eval da CI roda só sob demanda
- **Problema:** a spec previa o eval no gatilho de tag, mas o usuário usa o Claude Code pela assinatura e não tem `ANTHROPIC_API_KEY`, e o runner do GitHub não tem esse login.
- **Decisão:** o job `eval` da CI roda só em `workflow_dispatch`; o gatilho `on.push.tags: ['v*']` continua, porque o `release-check` precisa dele. O eval segue disponível pelo `workflow_dispatch` quando houver o secret.
- **Motivo:** aprovação do usuário em 2026-11-07: "2a"; altera a R7 da fase-6-release.
- **Por que não é bug:** sem o secret o job de tag falharia sempre e bloquearia o release; sob demanda, o eval continua disponível sem travar nada.
