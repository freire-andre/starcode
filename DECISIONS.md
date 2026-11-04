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
