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

## Ajustes depois do v1.0 (antes da Fase 7)

### F6-6: Cabeçalho de apresentação no início de cada etapa
- **Problema:** o usuário não via qual tripulante tinha assumido a tarefa; o bordão solto no chat passava despercebido.
- **Decisão:** cada skill (Picard, Troi, Spock, Data, LaForge, McCoy, Q) abre a etapa com o cabeçalho impresso por `scripts/crew_live.py start <membro>` (emoji, nome, papel, cli · modelo, bordão de abertura), colado sem alteração no topo da resposta. Ele substitui o bordão de abertura solto.
- **Motivo:** pedido do usuário em 2026-11-07. Um script mantém o formato igual em todos os CLIs e gasta uma chamada curta.
- **Por que não é bug:** a F2-10 proíbe o bordão **depois** de uma pergunta, porque soa como resposta sugerida; o cabeçalho fica no topo, então pode abrir um turno que termina com pergunta. O bordão de fechamento continua sob a F2-10.

### F6-7: Status da tripulação em `.starcode/live/crew.json`
- **Problema:** um sistema visual precisa saber quem está trabalhando sem ler o chat.
- **Decisão:** `{"<membro>": 0|1}` no worktree principal (resolvido pelo diretório Git comum, então os workers em outros worktrees gravam no mesmo arquivo), pasta que se ignora sozinha no Git, escrita atômica. `start`/`stop` nas skills; o Picard também faz `set laforge|q 1|0` em volta dos workers.
- **Motivo:** pedido do usuário em 2026-11-07: simples e barato em tokens. JSON plano é o formato mais fácil de ler por um painel (Fase 10 "Ponte").
- **Por que não é bug:** com tickets em paralelo (Fase 7), dois LaForge dividem o mesmo `1`; o primeiro que termina zera o status. Fica para a Fase 7 trocar por contagem, se o painel precisar. Um processo que morre sem `stop` deixa `1`: `crew_live.py reset` limpa, e o Picard marca os workers ele mesmo.

### F6-8: Progresso da feature em `.starcode/live/progress.json`
- **Problema:** o usuário quer uma barra de progresso dos tickets depois da aprovação.
- **Decisão:** `{"<slug>": {"done", "total", "percent", "phase"}}`. `crew_live.py progress <slug>` conta os tickets do `tasks.md` integrados em `feature/<slug>` com a mesma regra do `dispatch.py next` (Git é a evidência); MÉDIA/PEQUENA passam `--done/--total` (um ticket). O Picard roda depois da publicação, de cada merge e no `done` (100%).
- **Motivo:** pedido do usuário em 2026-11-07. Contar pelo Git evita um contador que diverge do que foi de fato integrado.
- **Por que não é bug:** os arquivos ao vivo nunca decidem nada no fluxo; Git e o Handoff continuam a fonte da verdade, e uma falha desses comandos não para a missão.

### F6-9: Statusline do Claude Code com o tripulante ativo e a barra de progresso
- **Problema:** o usuário quer ver no rodapé do Claude Code quem está trabalhando e quanto da feature já foi integrado, sem abrir os arquivos ao vivo.
- **Decisão:** `scripts/statusline.py` lê `.starcode/live/crew.json` e `progress.json` do worktree principal e devolve um segmento: tripulantes com `1` e a barra de 10 células da feature mais recente (`updatedAt`, novo campo do `progress.json`), em degradê #C5DBFF (0%) → #75C3FF (50%) → #0028B3 (100%), cada célula na cor da sua posição. Funciona como statusline inteira ou importado por uma statusline pessoal (`segment(cwd)`). Uma feature concluída fica 12 h na linha, em 100%.
- **Motivo:** pedido do usuário em 2026-11-07, com as cores escolhidas por ele. O script só usa stdlib e não importa nada do plugin, para ser rápido a cada atualização da linha.
- **Por que não é bug:** fora de um repositório, sem a pasta `live/` ou com arquivo corrompido, o segmento sai vazio e a statusline continua; o plugin não altera a statusline do usuário sozinho: a `statusLine` é uma escolha pessoal, ligada no `settings.json` ou numa statusline própria.

## Decisões da Fase 7 (2026-11-07, SC-14)

### F7-1: Pool `fleet.workers` com troca na confirmação
- **Problema:** um lote em paralelo pode usar mais de um CLI/modelo, e o usuário quer variar sem editar o config a cada lote.
- **Decisão:** `fleet.workers` (1 a 10 pares `<cli>:<model>` únicos) é um pool; `dispatch.py batch` atribui os pares em rodízio, começando depois do último par usado pelos tickets ativos. A troca acontece na confirmação do lote: a resposta do usuário vira `--assign <Tn>=<cli>:<model>`. Sem a chave, todos usam o LaForge efetivo (sessão > config do usuário > `crew.yaml`).
- **Motivo:** R8 a R10: o rodízio é previsível e o usuário decide no momento em que vê o custo.
- **Por que não é bug:** pool com mais pares que tickets deixa pares sobrando e pool menor repete pares; os dois são válidos.

### F7-2: Faixa de custo relativa, sem preço
- **Problema:** o usuário precisa comparar o custo de um lote, mas preço em moeda envelhece e depende do plano de cada um.
- **Decisão:** o mapa `costTiers` do `crew.yaml` dá a faixa de custo (`grátis`, `$`, `$$`, `$$$`); modelo `:free` ou `-free` sem entrada é `grátis` e modelo sem entrada é `?`. O `costTotal` é a contagem por faixa (`2× $$ + 1× grátis`).
- **Motivo:** R11 e R12: o dono do repositório declara os valores, e mudar um valor não muda nenhuma regra.
- **Por que não é bug:** a faixa `?` não bloqueia o lote; só avisa que a faixa é desconhecida.

### F7-3: Integração na chegada, serial
- **Problema:** esperar o lote inteiro para integrar atrasa os tickets prontos e deixa um worker lento segurar os outros.
- **Decisão:** cada `worker_done` com sucesso é integrado na hora, um merge por vez (`run_gates.py ticket` e `git merge --no-ff` em `feature/<slug>`); dois `worker_done` quase juntos esperam em fila. Conflito: `git merge --abort`, ticket volta à fila e os outros seguem.
- **Motivo:** R21 e R26: o ramo de integração só recebe ticket com gates verdes, e a fronteira por dono de arquivo reduz conflitos.
- **Por que não é bug:** a integração serial não contradiz o paralelismo: os workers rodam juntos, só o merge é um de cada vez.

### F7-4: Oferta do lote a cada rodada (2 ou mais elegíveis)
- **Problema:** o Picard não deve decidir sozinho gastar mais workers, nem perguntar quando só há um ticket.
- **Decisão:** a cada rodada em que não há ticket ativo e `batch` devolve 2 ou mais tickets, o Picard mostra o lote numa só mensagem (ticket, issue, CLI, modelo, faixa, total e excluídos) e pede uma confirmação. Com 1 ticket segue o fluxo sequencial da Fase 3, sem pergunta; no modo Git 1 a Frota não existe.
- **Motivo:** R13, R27 e R28: o usuário confirma custo e pares, e o fluxo sequencial não muda.
- **Por que não é bug:** `fleet.maxBatch` = 1 faz todo lote ter 1 ticket, então a pergunta nunca aparece.

### F7-5: Timeout pelo `check --wait` e prazo no Handoff, não pelo `--timeout-ms` do `worker-start`
- **Problema:** o `--timeout-ms` do `worker-start` parece limitar o tempo do worker, mas só limita a espera pelo início dele.
- **Decisão:** o prazo de cada ticket é o horário do despacho (no Handoff, em UTC) mais `fleet.timeoutMinutes` (padrão 30). O Picard espera com `orca orchestration check --wait --types worker_done,question --timeout-ms <até o prazo mais próximo>` e usa `dispatch.py overdue` para achar os atrasados. Atrasado vira bloqueio (estado `blocked` ou comentário na issue) com o sufixo ` · blocked`; os arquivos continuam reservados e não há `worker-stop` nem novo despacho automático.
- **Motivo:** R20 a R23: o prazo precisa sobreviver a uma sessão interrompida, e o Handoff é a fonte.
- **Por que não é bug:** um `worker_done` tardio de ticket `· blocked` é integrado normalmente.

### F7-6: Sem `--deps` no lote
- **Problema:** o `worker-start` aceita `--deps`, e usá-lo parece o jeito certo de ordenar tickets.
- **Decisão:** o lote nunca usa `--deps`, e cada worker começa com `--base-branch feature/<slug>`.
- **Motivo:** R1 e R16: todo ticket do lote já tem as dependências integradas em `feature/<slug>`, então não há o que esperar.
- **Por que não é bug:** a dependência é respeitada antes do despacho, pelo `batch`, e não durante.

### F7-7: `crew.json` com a contagem de LaForges
- **Problema:** a F6-7 deixava o LaForge em 0/1, e com tickets em paralelo o primeiro que terminava zerava o status dos outros.
- **Decisão:** `crew_live.py set laforge <n>` grava a contagem de workers ativos (0 a 10), igual ao número de entradas em `**Dispatched:**`; os outros tripulantes continuam 0/1.
- **Motivo:** R18: resolve o ponto que a F6-7 deixou para a Fase 7.
- **Por que não é bug:** quem lê `crew.json` como booleano continua certo, porque `n > 0` significa ativo.

### F7-8: Vários despachos no Handoff e Q fora das famílias dos LaForges
- **Problema:** o Handoff guardava um despacho só, e o Q precisa de família diferente de todos os LaForges de uma feature com modelos variados.
- **Decisão:** `**Dispatched:**` guarda uma entrada por ticket separada por `; ` (`handoff.py set --dispatch-add` e `--dispatch-remove`; `--dispatched` continua substituindo o campo inteiro). `dispatch.py q-cli --laforge` aceita repetição e escolhe o primeiro CLI (`codex` → `antigravity` → `opencode`) de família diferente de todas; sem opção serve `self-verified`.
- **Motivo:** R15 e R29: compatibilidade com o fluxo sequencial e independência do Q.
- **Por que não é bug:** `next` segue devolvendo exit 3 com despacho aberto e não integrado (R19).

### F7-9: Correções pós-Q da Frota (motivo sensível, entrada de despacho, base do gate, bloqueados no overdue)
- **Problema:** o Q (antigravity, gemini-3.8-flash-high) achou 4 desvios da spec: `batch` mostrava `roda sozinho: Runs alone` em vez do padrão sensível; o 1º `--dispatch-add` do `execute.md` 2F tinha 3 campos (sem par e horário, o `overdue` sai com 2); o gate de integração não fixava a base gravada no despacho; `overdue` relistava entradas `· blocked`.
- **Decisão:** o padrão sensível tem prioridade sobre `Runs alone` no motivo; a entrada tem os 5 campos desde o primeiro registro; o gate de cada ticket usa `<base gravada na entrada>..<ramo do ticket>`, nunca o HEAD atual de `feature/<slug>`; `overdue` ignora entradas `· blocked`.
- **Motivo:** R3, R5, R14, R21–R23 e o achado do aceite (o HEAD atual acusou falsamente arquivos fora do `May change` depois de outro ticket integrado).
- **Por que não é bug:** um ticket bloqueado continua reservando os arquivos (R23); só deixa de gerar avisos repetidos.

### F7-10: Release recusa seção não lançada e confere aceites a partir da Fase 6
- **Problema:** o release aceitava `## [1.1.0] - não lançada` e olhava só `fase-6.md`, deixando passar aceites pendentes das fases seguintes.
- **Decisão:** `tools/release.py create` sai com 1 se a seção da versão no `CHANGELOG.md` não tem data `AAAA-MM-DD` (com e sem `--yes`), e confere todo `docs/aceite/fase-<N>.md` com N ≥ 6, em ordem numérica, citando o primeiro pendente.
- **Motivo:** R1 e R3: as Fases 1–5 usam outro formato de resultado, por isso a conferência começa na Fase 6.
- **Por que não é bug:** `fase-1.md` a `fase-5.md` não terem `**Resultado**:` no formato novo é esperado e não bloqueia o release.

### F7-11: `May change` da MÉDIA vive na spec e o gate `ticket` vale para ela
- **Problema:** a MÉDIA não tem `tasks.md`; `check_scope` e `run_gates.py ticket` falhavam e o brief não trazia os arquivos permitidos (o Picard os acrescentava à mão na SC-81).
- **Decisão:** a spec breve ganha `**May change**:` depois de `**Linear**:`. Sem `tasks.md`, `check_scope` usa essa linha (path, glob, pasta com `/`), aceita o ID do Linear da spec ou `T1`, e `run_gates.py ticket` confere o `Refs` com esse ID. A linha ausente é aviso (não erro) no `validate_spec` (R1) e no `check_scope` (R3), que mantém os erros de `STATE.md`, `## Handoff` e intervalo sem commit. O brief da MÉDIA tem `## BOUNDARIES` (R6) e o `execute.md` seção 8 integra com o gate `ticket` (R7).
- **Motivo:** R1–R7: o mesmo gate de escopo para todas as features com spec.
- **Por que não é bug:** specs MÉDIAS antigas sem a linha continuam válidas; a feature com `tasks.md` ignora a linha da spec.

### F7-12: Cabeçalho e status da tripulação robustos no Claude Code (`crew_hook.py` e `sessions.json`)
- **Problema:** o cabeçalho (F6-6) e o `crew.json` (F6-7) dependiam do modelo rodar `crew_live.py start/stop`; com o plugin desatualizado ou a instrução perdida nada aparecia, e uma sessão que acabava sem `stop` deixava o tripulante em 1 para sempre.
- **Decisão:** (R1) `hooks/scripts/crew_hook.py` grava a sessão em `.starcode/live/sessions.json` e imprime só `{"systemMessage": "<cabeçalho>"}` no `PreToolUse` de `Skill` (`starcode:<skill>` ou `<skill>` de um tripulante) e no `UserPromptExpansion` de `starcode:<skill>`; (R2) o cabeçalho é texto puro, com `Missão:` cortada em 80 caracteres; (R3) `PostToolUse` só renova o `at`; (R4) `Stop` marca `active: false` e `UserPromptSubmit` volta para `true`; (R5) `SessionEnd` remove a entrada; (R6) o `crew.json` continua plano e é recalculado a cada escrita: entrada `hook` vale 15 min, `cli` (`crew_live.py start|set`) 60 min, LaForge vale o maior entre as sessões ativas e o `set laforge <n>`, e as vencidas somem na escrita seguinte; (R7) qualquer falha sai com 0 e sem saída; (R8) `tools/build.py` registra os 6 eventos só em `dist/claude/hooks/hooks.json`; (R9) só as skills de `dist/claude` trocam "Header first (F6-6)" pela frase que manda não repetir o cabeçalho nem rodar `start/stop`; (R10) a statusline aplica a validade sem gravar e mostra `🔧 LaForge ×<n>`; (R11) o banner avisa quando o repositório aberto é o StarCode e o plugin em execução é mais antigo que o `VERSION`; (R12) este registro e o CHANGELOG.
- **Motivo:** o cabeçalho e o status no Claude passam a vir do hook, não do modelo, e a validade evita o status preso. `systemMessage` em texto puro porque a renderização de markdown nele não foi verificada. Codex, Antigravity e OpenCode ficam para depois (escolha do usuário).
- **Por que não é bug:** o `crew_live.py start/stop` continua existindo e valendo 60 min para os outros CLIs; o `set laforge <n>` vira uma entrada `cli`, por isso também vence em 60 min.

### F7-13: Correção pós-Q da F7-12 (validade recusa hora futura e origem desconhecida)
- **Problema:** o Q (Codex) mostrou que `entry_valid` aceitava `at` no futuro e `source` diferente de `hook`/`cli`, o que podia manter um tripulante ativo indevidamente; o teste do cabeçalho (C2) não conferia os valores exatos.
- **Decisão:** uma entrada com `at` mais de 60 s no futuro (`FUTURE_SKEW`), `at` ilegível ou `source` fora de `hook`/`cli` vale 0 e é removida na escrita seguinte; o teste do cabeçalho compara cada linha exata (missão de 80 caracteres inteira, de 81 cortada, sem `Missão:` sem argumentos).
- **Motivo:** fecha os 2 achados do Q (fd18f19) sem mudar o formato do `crew.json` nem do `sessions.json`.
- **Por que não é bug:** a folga de 60 s cobre relógios levemente adiantados entre processos; a missão não remove markdown, só corta em 80 caracteres (R2 pede texto puro nas linhas fixas).

### F7-14: Cabeçalho e status da tripulação por hook no Codex (`crew_hook.py --cli codex`)
- **Problema:** depois da F7-12 só o Claude mostrava o cabeçalho e o status por hook; no Codex ele ainda dependia de o modelo rodar `crew_live.py start/stop`.
- **Decisão:** (R1) `crew_hook.py --cli codex` reconhece o tripulante no `PreToolUse` de `Bash` quando `tool_input.command` lê um `starcode…/skills/<skill>/SKILL.md` (sem diferenciar maiúsculas; o Codex não tem ferramenta Skill) e imprime só `{"systemMessage": "<cabeçalho>"}`; (R2) no `UserPromptSubmit` reconhece `$starcode:<skill>` ou `$<skill>` no início ou depois de espaço, com a missão vinda do resto da linha (80 caracteres), e um prompt sem o token só reativa a sessão; (R3) `PostToolUse`, `Stop` e `SessionEnd` fazem o mesmo que no Claude; (R4) o mesmo tripulante já ativo na sessão só renova o `at`, sem repetir o cabeçalho; (R5) qualquer falha sai com 0 e sem saída; (R6) `tools/build.py` registra os 5 eventos (timeout 10 s) em `dist/codex/hooks/hooks.json`, mantendo `git_guard`, `secret_scan` e `banner`, e `dist/antigravity` e `dist/opencode` seguem sem `crew_hook`; (R7) as skills de `dist/codex` trocam "Header first (F6-6)" pela frase que manda não rodar `start/stop` nem repetir o cabeçalho; (R8) o banner do Codex avisa quando algum hook da tripulação não tem entrada confiável em `hooks.state`; (R9) este registro, o CHANGELOG e a linha "Cabeçalho por hook" em `docs/compatibilidade.md`.
- **Motivo:** o Codex pede confiança do usuário para hooks de plugin (F0-1), então sem ela nada roda; por isso o banner avisa e a skill não repete o cabeçalho. A grafia `systemMessage` e a exibição no Codex ficam para o aceite. Antigravity e OpenCode seguem em sondagem.
- **Por que não é bug:** o `crew_live.py start/stop` continua valendo 60 min para os CLIs sem hook, e o Claude não mudou (o modo `--cli codex` é opt-in).

### F7-15: Correção pós-Q da F7-14 (nome da skill sem diferenciar maiúsculas e CLI real no cabeçalho do Codex)
- **Problema:** o Q achou que `member_for` comparava o nome da skill com distinção de maiúsculas, então `.../skills/Troi/SKILL.md`, `...\SPOCK\SKILL.md`, `$Spock` e `$TROI` não casavam apesar de a F7-14 prometer isso; os testes não cobriam esses casos nem o cabeçalho de `$troi` sem argumentos. O Picard notou que no modo `--cli codex` a linha `<papel> · <cli> · <modelo>` mostrava o CLI e o modelo configurados para o tripulante (ex.: `claude · claude-sonnet-5-5`), mas quem roda é o Codex.
- **Decisão:** (1) `member_for` normaliza o nome para minúsculas dos dois lados; (2) os testes do Codex ganham caminhos em maiúsculas/misto, `$Spock`/`$TROI` e o cabeçalho completo de `$troi` sem `Missão:`; (3) no modo Codex a linha mostra `codex · <model>` com o `model` da entrada do hook, ou `codex · padrão do CLI` se faltar ou não for texto, coberto por `test_crew_hook_codex_header_shows_running_cli`.
- **Motivo:** o cabeçalho deve dizer quem de fato roda, e a leitura de skill em Windows costuma vir com maiúsculas variadas.
- **Por que não é bug:** o modo Claude não muda (continua mostrando o CLI e o modelo configurados, e a comparação em minúsculas só acrescenta casamentos); o `crew.json` e o `sessions.json` não mudam.

### F7-16: Cabeçalho e status da tripulação por hook no Antigravity e no OpenCode
- **Problema:** depois da F7-14 só Claude e Codex mostravam o cabeçalho e o status por hook; no Antigravity e no OpenCode ele ainda dependia de o modelo rodar `crew_live.py start/stop`.
- **Decisão:** (R1) `crew_hook.py --cli antigravity` reconhece o tripulante no `PreToolUse` de `read_file`, `view_file` ou `run_command` cujo `Path` ou `CommandLine` lê um `SKILL.md` da tripulação, grava a sessão `conversationId` (`workspacePaths[0]` como pasta) e guarda o cabeçalho em `.starcode/live/pending.json`; (R2) nesse modo nunca imprime campo de decisão nem mensagem de exibição, e o `PreToolUse` sai vazio; (R3) no `PostInvocation` imprime só `injectSteps` com a ordem e o cabeçalho e remove a pendência; (R4) o cabeçalho segue o do Codex, com `antigravity · <modelName>` ou `opencode · <modelo da config>`; (R5) `PostToolUse` renova, `PreInvocation` 0 ativa e `Stop` desativa; (R6) `--cli opencode` recebe `skill`, `pulse`, `prompt` e `idle` e imprime `{"header"}` só para `skill`; (R7) `hooks/opencode/starcode.js` registra `execute.before`, `execute.after`, `prompt` e `experimental.idle` sem `await`, injeta o cabeçalho com `ctx.session.synthetic` (`resume: false`) e engole qualquer erro, mantendo os guardas; (R8) `dist/antigravity/hooks.json` ganha o grupo `starcode-crew` (5 eventos, timeout 10 s); (R9) as skills dos dois CLIs trocam "Header first (F6-6)" por uma frase que manda iniciar a resposta com o cabeçalho enviado e não rodar `start/stop`; (R10) qualquer falha sai com 0 e sem saída; (R11) este registro, o CHANGELOG e a linha "Cabeçalho por hook".
- **Motivo:** nesses CLIs o hook não imprime na tela do usuário, então ele só consegue pedir ao modelo que repita o cabeçalho; por isso a entrega é "o modelo repete". O agy nunca decide para que um erro do hook de tripulação não bloqueie ferramentas.
- **Por que não é bug:** Claude e Codex não mudam; o `crew_live.py start/stop` continua valendo 60 min para quem não usa hook; sem `SessionEnd` no agy e no OpenCode a sessão vence pela validade de 15 min (F7-12).

### F7-17: Evento do Antigravity pela linha de comando (correção da F7-16 na integração)
- **Problema:** na integração do SC-86 o Picard notou que a entrada dos hooks do agy 1.5.2 não traz o nome do evento (a sondagem de 2026-11-08 lista só `conversationId`, `lastUserInput`, `modelName`, `transcriptPath`, `artifactDirectoryPath` e `workspacePaths`), mas o modo `--cli antigravity` procurava `hookEventName` na entrada; no agy real nenhum evento seria reconhecido.
- **Decisão:** cada comando do grupo `starcode-crew` passa o evento como `--event <Nome>` (`PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, `Stop`); o `crew_hook.py` usa esse valor e só recorre ao campo da entrada quando `--event` falta; evento ausente ou desconhecido sai com 0 e sem saída. Os testes do modo antigravity usam entrada sem nome de evento, como a real (943ef04).
- **Motivo:** o hook só faz sentido se reconhecer o evento no CLI real; o registro em `hooks.json` é o único lugar que sabe qual evento disparou.
- **Por que não é bug:** o comportamento de R1–R11 da F7-16 não muda; Claude, Codex e OpenCode não mudam.

### F7-18: Correção pós-Q da F7-16 (releitura da skill, erros do plugin do OpenCode e cabeçalho integral nos testes)
- **Problema:** o Q (codex gpt-6-luna) achou que (1) uma nova leitura do `SKILL.md` do mesmo tripulante, na mesma sessão, recriava a pendência do cabeçalho no agy (e o `header` no OpenCode), contra o caso de borda aprovado; (2) o C6 só conferia o texto do `starcode.js` e não provava que os erros são engolidos (R7); (3) os testes de cabeçalho de C3 e C5 usavam `assertIn`/`startswith`.
- **Decisão:** (1) quando a sessão já tem entrada ativa e válida do mesmo tripulante, a leitura só renova `at`, sem pendência nem `header` (6d227fb); (2) um teste carrega o plugin no Node com um `ctx` falso e prova que `synthetic` que lança ou rejeita, registro que falha, Python ausente e pasta inválida não escapam; sem Node o teste é pulado (699abd9); o plugin já engolia tudo e não mudou; (3) C3 e C5 comparam o cabeçalho inteiro (005e69f).
- **Motivo:** repetir o cabeçalho a cada releitura poluiria a conversa, e R7 exige comportamento sob erro, não só a presença de `catch`.
- **Por que não é bug:** R1–R11 da F7-16 e o `--event` da F7-17 não mudam; Claude e Codex não mudam.

### F7-19: Formato do hooks.json do agy e pasta do projeto no plugin do OpenCode (aceite real da F7-16)
- **Problema:** no aceite real de 2026-11-08, (1) `agy plugin validate --strict` (agy 1.5.2) recusou o grupo `starcode-crew`: nos eventos sem ferramenta o invólucro `{"hooks": [...]}` não vale e o loader ignorava o `hooks.json` inteiro, inclusive guard e banner; (2) no OpenCode 2.2.3 o `process.cwd()` do plugin é a pasta do usuário e o evento da skill não traz `workdir`, então o `crew_hook.py` via pasta sem Git e não gravava nada.
- **Decisão:** (1) `PreInvocation`, `PostInvocation` e `Stop` em lista plana de comandos, como o `SessionStart` do banner, e um teste roda o `agy plugin validate --strict` real quando o `agy` está no PATH (ed60c99); (2) a pasta enviada ao `crew_hook.py` e aos guardas vem de `input.workdir`, depois de `ctx.location.directory` capturado no `setup`, e só por último de `process.cwd()` (c1cc4d8).
- **Motivo:** os testes só simulavam as entradas; o aceite nos CLIs reais mostrou os dois formatos. Com as correções, o Antigravity e o OpenCode mostraram o cabeçalho repetido pelo modelo e gravaram a sessão no `sessions.json`.
- **Por que não é bug:** R1–R11 da F7-16 não mudam (a pasta de `ctx.location.directory` já estava em R6); Claude e Codex não mudam.

### F7-20: Cabeçalho do OpenCode mostra "padrão do CLI"
- **Problema:** no aceite real da F7-16 o cabeçalho do OpenCode mostrou o modelo configurado para o tripulante (`opencode · claude-opus-5-5`), mas quem rodava era o modelo da sessão do OpenCode (nemotron). O plugin não tem acesso confiável ao modelo real: os eventos de skill e de prompt não trazem o modelo, e os ganchos `session.model.request` e `ctx.session.get` travaram o `opencode run` na sondagem de 2026-11-08.
- **Decisão:** no modo `--cli opencode` a linha do papel é sempre `<papel> · opencode · padrão do CLI` (escolha do usuário em 2026-11-08: "2, padrão do CLI"), substituindo a parte do OpenCode em R4 da F7-16 (253f028).
- **Motivo:** o cabeçalho não deve afirmar um modelo que pode não ser o que roda; "padrão do CLI" é honesto.
- **Por que não é bug:** Claude, Codex e Antigravity continuam mostrando o modelo como antes; o `crew.json` e o `sessions.json` não mudam.

## Decisões da Fase 8 (2026-11-08, SC-99)

### F8-1: Templates fixos e um script, sem geração livre pelo modelo
- **Problema:** deixar o modelo escrever a estrutura de cada projeto novo produz resultados diferentes a cada execução e mistura versões de memória com versões reais.
- **Decisão:** cada stack é um perfil em `profiles/<nome>/` (`profile.yaml` mais `template/` com marcadores `{{name}}`, `{{description}}`, `{{module}}` e `{{version:<pacote>}}`); o `scripts/scaffold.py` copia o template, injeta o perfil de banco e troca os marcadores; o `tools/build.py` copia `profiles/` para `dist/<cli>/profiles/` nos 4 CLIs e o `--check` acusa perfil desatualizado.
- **Motivo:** o template é revisado uma vez e testado; o script é determinístico e igual nos 4 CLIs.
- **Por que não é bug:** o modelo (Kirk) só escolhe o perfil e chama o script; nenhum número de versão fica escrito no template (`test_templates_have_no_hardcoded_versions`).

### F8-2: Versões pelas APIs dos registros
- **Problema:** versões escritas de memória ficam velhas e inventam números que não existem.
- **Decisão:** `scaffold.py versions` consulta a API de cada registro (PyPI, npm, crates.io, Docker Hub); o marcador `{{version:<pacote>}}` recebe esse número, nunca um valor escrito no template.
- **Motivo:** D10 pede versões do registro de pacotes; o registro é a fonte que o gerenciador de pacotes usa de fato.
- **Por que não é bug:** sem rede ou com registro fora do ar o script falha com mensagem clara e não gera projeto com versão chutada.

### F8-3: Série testada (`tested`) e Context7 antes do scaffold
- **Problema:** a última versão do registro pode ter quebrado o template, e o Context7 só vale para a versão que foi consultada.
- **Decisão:** toda dependência principal do `profile.yaml` declara `tested` (major para versões 1 ou mais, `major.minor` para 0.x) e `docs` (Context7 ID e data da consulta); o scaffold usa a última versão da série testada e só passa dela com `--allow-new`; a documentação dessas versões entra no cache do Uhura (`.specs/stack/`) antes de o código ser gerado.
- **Motivo:** o template é escrito contra uma série; a documentação precisa ser a da versão que vai para o projeto.
- **Por que não é bug:** `--pin` fixa a série testada; uma série nova só entra por decisão explícita do usuário.

### F8-4: `.starcode/stack.json`
- **Problema:** depois do scaffold (ou num projeto existente) o StarCode precisa saber qual perfil, quais versões e quais gates valem, sem refazer a detecção.
- **Decisão:** o scaffold grava `.starcode/stack.json` com perfis e versões resolvidas; `detect` lê manifestos e lockfiles de um projeto existente e `record` grava o mesmo arquivo; o Scotty e o Data leem os gates do perfil por ele.
- **Motivo:** um arquivo só, legível e versionável, em vez de reconstruir o estado a cada skill.
- **Por que não é bug:** sem o arquivo as skills pedem `detect`; arquivo corrompido é recusado, nunca corrigido em silêncio.

### F8-5: Banco efêmero só em Docker, com `--reuse-env`
- **Problema:** os gates de integração precisam de um banco, e nunca podem apontar para um banco real.
- **Decisão:** `scripts/ephemeral_db.py run <engine> -- <comando>` sobe um container (porta livre em `127.0.0.1`, dados fictícios), exporta `DATABASE_URL` só para o comando e remove o container no fim; não há instância local temporária. `--reuse-env` reaproveita um `DATABASE_URL` local já definido, sem subir container (T2).
- **Motivo:** o Docker dá isolamento e remoção garantidos; instalar banco na máquina do usuário não é aceitável.
- **Por que não é bug:** sem Docker o gate de integração fica indisponível com o motivo, e a verificação é registrada como degradada.

### F8-6: CI do banco em `ci-db.yml` separado e `ruff.toml` sem `scripts/`
- **Problema:** o CI do app não tem banco, e o `scripts/ephemeral_db.py` copiado para o projeto não segue o estilo do template.
- **Decisão:** os perfis `postgresql` e `mysql` entregam `.github/workflows/ci-db.yml` (T9) como arquivo à parte; o `ci.yml` do app continua só com os gates do app. O `ruff.toml` dos perfis de banco exclui `scripts/` (T9).
- **Motivo:** o app com banco ganha dois jobs independentes, e o lint não reprova um script do StarCode.
- **Por que não é bug:** `test_app_templates_have_ci_and_gitignore` confere o `ci.yml` de cada app e o `ci-db.yml` de cada banco.

### F8-7: Biome para TypeScript
- **Problema:** TypeScript pede lint e formato; ESLint com Prettier são duas ferramentas e muita configuração.
- **Decisão:** os perfis `typescript` e `tauri` usam o Biome (`npx biome check .`) para lint e formato, mais `tsc --noEmit` e `vitest`.
- **Motivo:** uma ferramenta, uma configuração (`biome.json`), um comando de gate.
- **Por que não é bug:** o gate exato está em R2 e é conferido por `test_profiles_gate_commands_exact`.

### F8-8: GPUI experimental
- **Problema:** o GPUI ainda não tem versão 1 e muda de API entre releases.
- **Decisão:** o perfil `gpui` tem `experimental: true` e `tested: "0.2"` (major.minor).
- **Motivo:** o usuário precisa saber que o template pode quebrar numa série nova.
- **Por que não é bug:** o campo é conferido por `test_profiles_all_seven_with_required_fields`.

### F8-9: Kirk sem grill-me e sem remoto
- **Problema:** o Kirk (`nova-missao`) cria projetos do zero; a entrevista longa (grill-me) e criar repositório remoto estão fora do que ele deve fazer sozinho.
- **Decisão:** `nova-missao` faz poucas perguntas (nome, descrição, perfil e banco), roda o scaffold e os gates e para; não faz `git remote add`, não cria repositório no GitHub e não faz push.
- **Motivo:** D11: push e criação de remoto exigem confirmação na hora; o Kirk não é um fluxo de feature.
- **Por que não é bug:** `nova-missao` só dispara para projeto novo, nunca para um repositório que já existe (eval `neg-nova-missao-existing`).

### F8-10: Resumo dos evals vem da fonte
- **Problema:** `uhura`, `scotty` e `nova-missao` entraram no roteamento, e o T7 editou só a cópia gerada `dist/claude/evals/README.md`, o que deixou o `build.py --check` vermelho.
- **Decisão:** a linha de `routing/` (24 frases: 14 que devem disparar e 10 que não devem) vive em `evals/README.md`; arquivo gerado nunca se edita à mão.
- **Motivo:** a cópia gerada é descartada a cada build.
- **Por que não é bug:** `build.py --check` verde prova que fonte e `dist/` coincidem.

### F8-11: `new` aceita pasta só com `.specs/` e Biome ignora `.specs`
- **Problema:** no aceite real (`docs/aceite/fase-8.md`, achados 1 e 2), a `nova-missao` grava o cache `.specs/stack/` antes do `scaffold.py new` (R31), e o `new` recusava a pasta não vazia (exit 2); além disso, o `biome check` do perfil tauri formatava os `.md` do cache.
- **Decisão:** o `new` aceita a pasta quando ela contém só `.specs/` (qualquer outro conteúdo continua exit 2, e o `.specs/` preexistente é preservado se o `new` falhar); os `biome.json` dos perfis `tauri` e `typescript` excluem `.specs`.
- **Motivo:** o cache de stack é gravado antes do scaffold por desenho, então a pasta "quase vazia" é o caso normal do Kirk, e o gate não deve mexer em arquivos de cache.
- **Por que não é bug:** testes em `tests/test_scaffold.py` e `tests/test_profile_ts_tauri.py` e os cenários 1 e 2 do aceite, aprovados.

### F8-12: `Doc version` desconhecida é `ok (doc sem versão)` no `check`
- **Problema:** o Context7 muitas vezes não informa a versão dos docs, então o `write` grava `Doc version: desconhecida`; o `check` comparava esse valor com a versão do projeto e devolvia `outra versão` (exit 1) logo após o `write`, o que travava o bootstrap (achado do Q, C27).
- **Decisão:** em `scripts/stack_cache.py`, `Doc version` `desconhecida` pula só a comparação de `outra versão`; a entrada continua julgada pela idade (mais de 30 dias é `velha`) e pela versão do manifesto (`versão mudou`). Se passar nas duas, o estado é `ok (doc sem versão)` e conta como `ok` no exit (0). Decisão do usuário (opção "a") em 2026-11-09, emenda do R27.
- **Motivo:** o cache que o próprio fluxo grava não pode nascer inválido, e a idade e o manifesto ainda protegem contra doc velho.
- **Por que não é bug:** `test_stack_cache_check_states` e `test_stack_cache_unknown_doc_version_flow` cobrem `ok (doc sem versão)`, 30 dias (ok), 31 dias (`velha`) e outro major (`versão mudou`).
- **Emenda (segundo Q):** só o literal `desconhecida` é aceito para pular a comparação. No `check`, qualquer outro `Doc version` sem versão numérica válida é `inválida` (exit 1); no `write`, `--doc-version` tem de ser uma versão numérica ou `desconhecida`, senão sai com exit 2 (`doc-version inválida: use uma versão (ex.: 3.1) ou desconhecida`) sem gravar nada. O teste `test_stack_cache_unknown_doc_version_flow` cobre o caso `abc`.

### F8-13: Biome com `linter.rules.preset: "recommended"`
- **Problema:** o Biome 2.5+ marca `linter.rules.recommended` como obsoleto (aviso no Biome 2.6.6, limite registrado pelo Q).
- **Decisão:** os `biome.json` dos perfis `typescript` e `tauri` usam `"rules": { "preset": "recommended" }`, que ativa o mesmo conjunto de regras recomendadas (sem as de `nursery`). Fonte: documentação do Biome via Context7 (`/biomejs/website`, referência de configuração e nota da versão 2.5).
- **Motivo:** `recommended` será removido na próxima versão maior; `preset` é a forma atual e o `biome migrate --write` produz a mesma troca.
- **Por que não é bug:** `test_biome_uses_preset_not_deprecated_recommended` confere os dois arquivos e os gates reais de `tests_slow/test_slow_ts_tauri.py` passam.

## Decisões da Fase 9 (2026-11-09, SC-103)

### F9-1: Review com publicação confirmada
- **Problema:** o Worf poderia postar comentários no PR sem o usuário ver.
- **Decisão:** `post_review.py` só publica depois de o usuário confirmar o texto, e nada é postado em modo seco.
- **Motivo:** D11: ação voltada para fora exige confirmação na hora.
- **Por que não é bug:** `tests/test_review_post.py` cobre a recusa sem confirmação.

### F9-2: Rodada no `review.md`
- **Problema:** reviews repetidos do mesmo PR se misturavam.
- **Decisão:** cada passada do Worf grava uma rodada numerada no `review.md` da feature.
- **Motivo:** o histórico mostra o que mudou entre rodadas.
- **Por que não é bug:** `tests/test_review_gate.py` confere o formato da rodada.

### F9-3: Portão de evidência de segurança
- **Problema:** achado de segurança sem prova gera ruído e falso alarme.
- **Decisão:** `review_gate.py` recusa achado de segurança sem evidência (arquivo, linha e caminho do dado); a regra foi escrita do zero, inspirada na Cloudflare security-audit-skill (MIT).
- **Motivo:** sem evidência o achado vira pergunta, não bloqueio.
- **Por que não é bug:** `tests/test_review_gate.py` cobre achado com e sem evidência.

### F9-4: Lições por repo nos briefs e sinal `review_finding`
- **Problema:** as lições dos reviews não voltavam para os briefs.
- **Decisão:** `lessons.py` guarda lições por repo com o sinal novo `review_finding`, e o `dispatch.py` injeta as lições confirmadas nos briefs.
- **Motivo:** o mesmo erro não deve se repetir de um ticket para outro.
- **Por que não é bug:** `tests/test_lessons.py` e `tests/test_dispatch_lessons.py`.

### F9-5: Guinan antes do PR e Worf depois do PR
- **Problema:** a ordem das etapas no fluxo do Picard era indefinida.
- **Decisão:** a Guinan roda antes do PR (retro e lições da feature) e o Worf roda depois do PR aberto (review do diff publicado).
- **Motivo:** a retro alimenta as lições; o review precisa de um PR real para comentar.
- **Por que não é bug:** `tests/test_flow_worf_guinan.py` confere a ordem.

### F9-6: harness-score fixado via `npx` e Track A junto
- **Problema:** o diagnóstico dependia de versão solta do `harness-score`.
- **Decisão:** `diagnostico.py` roda `npx --yes harness-score@<versão fixada>` e o Track A (`scripts/harness/`) juntos; se o `npx` falhar, o relatório diz `não executado` e segue.
- **Motivo:** versão fixa dá resultado reproduzível, e o Track A não depende de rede.
- **Por que não é bug:** `tests/test_diagnostico.py`.

### F9-7: Tracks B e C com aprovação por execução
- **Problema:** os tracks B e C gastam modelo e tokens.
- **Decisão:** o `diagnostico` pede aprovação de custo a cada execução dos tracks B e C; a aprovação de uma execução não vale para a próxima (aprovação por execução).
- **Motivo:** D11: gasto voltado para fora exige confirmação na hora.
- **Por que não é bug:** `tests/test_diagnostico_skill.py`.

### F9-8: Scripts em `scripts/review/` e `scripts/harness/`
- **Problema:** os scripts adaptados de terceiros se misturavam com os do StarCode.
- **Decisão:** os scripts do the-judge ficam em `scripts/review/` e os do harness-eval em `scripts/harness/`, cada um com o comentário `Origem:` no topo; `CREDITS.md` lista as fontes.
- **Motivo:** separar facilita a licença CC-BY-4.0 e as atualizações.
- **Por que não é bug:** `tests/test_credits_f9.py` confere fontes e comentários; `tests/test_build.py` confere os 4 `dist/<cli>/`.

### F9-9: campos de segurança do review exigem texto não vazio
- **Problema:** o Q achou que o `review_gate.py` aceitava `attacker: []` (valor não textual vazio) num achado de segurança.
- **Decisão:** cada campo textual de segurança e `evidence`/`missing_fact`/`reason` exigem string não vazia após strip; o resto vira `security: campo <nome> ausente`.
- **Motivo:** o portão de evidência (plano §3.1) só vale se cada resposta existir de fato.
- **Por que não é bug:** `tests/test_review_gate.py::test_gate_security_fields_required` testa `[]`, `{}`, `0` e espaço; correção em 9e7679a.

### F9-10: emoji do comentário inline sem repetição
- **Problema:** o comentário inline saía como `🔴 **blocker** (W1): 🔴 ...`, porque o `body` do achado já abre com o emoji da severidade.
- **Decisão:** `post_review.py` só põe o emoji da severidade no prefixo quando o `body` (após `lstrip`) não começa com ele; senão o prefixo vai sem emoji e o do `body` fica.
- **Motivo:** o emoji aparece uma vez só, sem mudar o formato dos achados que não o trazem.
- **Por que não é bug:** `tests/test_review_post.py::test_inline_comment_does_not_repeat_severity_emoji` confere os dois casos.

### F10-1: o `ponte.py` lê o estado em Python e o worker só orquestra
- **Problema:** o painel Ponte precisa mostrar a tripulação e o progresso, e um worker não deve guardar estado nem decidir o que mostrar.
- **Decisão:** o `ponte.py` lê o estado (`crew.json`, `progress.json`) direto em Python e monta o que o painel exibe; o worker só orquestra (abre o painel e pede a atualização).
- **Motivo:** um caminho só para o estado deixa o painel testável sem a Orca e sem modelo.
- **Por que não é bug:** `tests/test_ponte.py` roda o `snapshot` do `ponte.py` sobre arquivos de estado de exemplo.

### F10-2: `dist/orca` com instalação local, sem catálogo
- **Problema:** a Orca não tem catálogo de plugins para o StarCode publicar o painel.
- **Decisão:** `tools/build.py` gera `dist/orca` e `tools/install_local.py --cli orca` instala o plugin direto da pasta, sem catálogo.
- **Motivo:** a instalação local funciona hoje e não depende de publicar nada fora do repositório.
- **Por que não é bug:** `tests/test_build.py` confere o `dist/orca`; `tests/test_install_local.py` confere a instalação.

### F10-3: R20 usa `sidebar.right.toggle`
- **Problema:** a API do plugin da Orca não abre um painel por conta própria.
- **Decisão:** o R20 abre a Ponte pelo atalho `sidebar.right.toggle` da barra lateral direita, e o texto da spec diz isso em vez de prometer "abrir o painel".
- **Motivo:** prometer o que a API não faz deixaria a spec falsa.
- **Por que não é bug:** `tests/test_orca_manifest.py::test_manifest_toggle_da_barra` confere a ação `sidebar.right.toggle` no manifesto.

### F10-4: capabilities mínimas e aprovação sempre do usuário
- **Problema:** um plugin com capabilities demais, ou aprovado sozinho, daria à Orca acesso que o usuário não pediu.
- **Decisão:** o manifesto declara só as capabilities que o painel usa, e a aprovação do plugin na Orca é sempre do usuário; nenhum worker ou script aprova.
- **Motivo:** D11: o que muda o ambiente do usuário exige confirmação dele.
- **Por que não é bug:** `tests/test_orca_manifest.py::test_manifest_capabilities_e_engines` confere a lista de capabilities.

### F10-5: Cena da Ponte em painel HTML com arte gerada por código
- **Problema:** a Ponte precisa de uma cena animada com a tripulação, e copiar sprites ou código de terceiros traria licença e dívida.
- **Decisão:** a Cena da Ponte é um painel HTML cuja arte é gerada por código (canvas/SVG escritos do zero), inspirada no Pixel Agents e no Habblaud, sem copiar código nem sprites; `CREDITS.md` registra as duas inspirações.
- **Motivo:** a ideia é livre, a arte e o código são nossos, e o painel não carrega arquivos binários.
- **Por que não é bug:** `tests/test_release_docs_f10.py` confere os créditos; o painel não carrega arquivos de imagem, e `CREDITS.md` diz que nada foi copiado.

### F10-6: o `dist/orca` precisa do `crew.json` gerado (rodada 2 da T7)
- **Problema:** na T7 o `dist/orca` saiu sem o `crew.json`, e o `ponte.py` caía em `miniyaml`, que só existe em `tools/` e não vai para o plugin instalado.
- **Decisão:** `tools/build.py` grava o `crew.json` em `dist/orca` e o `ponte.py` lê a tripulação dele, sem importar `miniyaml`.
- **Motivo:** o plugin instalado só leva o que está em `dist/orca`; depender de `tools/` quebra fora do repositório.
- **Por que não é bug:** `tests/test_build.py` confere o `crew.json` em `dist/orca`; correção em 8c64378.

### F10-7: workers testam o plugin; a instalação real é do usuário
- **Problema:** um worker instalar o plugin na Orca do usuário mudaria o ambiente dele sem pedido.
- **Decisão:** os workers rodam o plugin só em teste (`orca plugin test/check`); a instalação real e a aprovação na Orca são do usuário (T9).
- **Motivo:** liga o F10-4 ao fluxo de trabalho: quem aprova é quem é dono do ambiente.
- **Por que não é bug:** `tests/test_ci_workflow.py::test_ci_valida_plugin_orca_condicional` só valida o plugin, sem instalar.

### F10-8: cena com `entry` `.ts` e issue pelo vínculo do worktree (T10, aceite real)
- **Problema:** no plugin instalado a cena saiu em branco (o `scene.html` carregava `./scene.ts` sem transpilar e importava `./scene-model` sem extensão) e `orca linear issue --current` respondia `linear_no_linked_issue` no worker, que não é o terminal do worktree.
- **Decisão:** o painel `ponte-cena` usa `entry` `src/scene.ts` (a Orca transpila e gera a página), o script cria o canvas quando falta e os imports usam `.ts`; o worker lê `linkedLinearIssue` de `orca worktree show --worktree path:<caminho> --json` e consulta `orca linear issue <ID> --json`, com a nota do Handoff quando não há vínculo.
- **Motivo:** o aceite real (T9) mostrou que só o `entry` `.ts` é transpilado e que `--current` olha o terminal que chama, não o `cwd` do worker.
- **Por que não é bug:** `tests/test_orca_manifest.py` confere o `entry` `src/scene.ts`; os testes `cena cria o canvas e importa com caminho servido` e `worker consulta a issue vinculada e guarda em cache por 60 s` cobrem os dois casos.

### F10-9: duas limitações da Orca aceitas no reaceite (T13)
- **Problema:** no reaceite o Iniciar Picard abre o Claude Code em segundo plano, sem aba visível e sem enviar o prompt `/starcode:engajar`; e o `orca` chamado de dentro do worker falha com `node:internal/modules/cjs/loader:1575`, então a Issue mostra só o ID do Handoff com "Linear indisponível".
- **Decisão:** o usuário aceitou as duas limitações (aprovado com limitações). O painel passa a dizer "Picard iniciado em segundo plano" e avisa no botão; a Issue segue pelo ID do Handoff. Nada é contornado no plugin.
- **Motivo:** as duas vêm do comportamento da Orca 1.4.x, fora do alcance do plugin.
- **Por que não é bug:** `docs/aceite/fase-10.md` (`## Reaceite`) registra o caso e `test_fase10_limitacoes_registradas` exige o registro.

### F10-10: correção pós-Q da Ponte (R8, ids repetidos, checks fracas)
- **Problema:** o Q achou que `scripts/ponte.py` ignorava em silêncio um Handoff acima de 1 MiB nas features não escolhidas, que `linear_ids` devolvia IDs repetidos e que as checks C8, C21 e C26 não falhariam se a condição fosse falsa.
- **Decisão:** `handoff_of` passa a registrar em `errors` o Handoff acima de 1 MiB ou ilegível, com a fonte e o motivo, sem abortar o snapshot (R8), e erros idênticos não se repetem; `linear_ids` deduplica mantendo a ordem; C8 cobre fonte ilegível e Handoff grande, C21 verifica `plugin.request('ponte.state')` com `timeoutMs: 15000` e C26 verifica que só aparecem a frase e o Atualizar agora.
- **Motivo:** R8 pede que toda fonte inválida apareça em `errors`, e o painel não deve mostrar o mesmo ID duas vezes.
- **Por que não é bug:** `test_snapshot_handoff_grande_vira_erro`, `test_linear_ids_sem_duplicatas` e `test_snapshot_fonte_invalida` cobrem o código; os testes `painel pede o estado ao abrir` e `painel sem StarCode` cobrem o painel.

### F10-11: novo visual da Cena da Ponte, vista de cima (R38, R39, R41, R42, R43, R50)
- **Problema:** o usuário achou a cena confusa: estações sem nome, inativos empilhados no turbolift com rótulos sobrepostos, engenharia grande e vazia e desenho horizontal pequeno numa lateral alta.
- **Decisão:** grade vertical de 48 x 72 com escala inteira (mínimo 5 px por célula, 240 px de largura): telão no topo (slug, fase, `done/total` e percentual, ou a frase do estado vazio), cadeira do Picard no centro, as outras 10 estações em volta com emoji e nome, LaForge no cabeçalho da faixa da engenharia (6 vagas, `✓` e `+N`) e a legenda embaixo; sem turbolift, o inativo fica esmaecido na própria estação. `buildScene` devolve `rotulos` com a caixa de cada texto (fonte mínima de 2 células = 10 px a 240 px) e a pintura só lê esse resultado.
- **Motivo:** o teste precisa provar que nenhum rótulo se sobrepõe e que o texto é legível; isso só é possível se o modelo (puro) fornecer as caixas.
- **Por que não é bug:** `cena sem rótulos sobrepostos`, `cena mostra o telão com fase e progresso` e os testes de C38, C39, C41, C42 e C43 cobrem o layout. Nenhum arquivo de `scripts/` mudou.

### F10-12: Cena da Ponte com vida: arco, bonecos, contraste e engenharia compacta (R39, R41, R51, R52, R53)
- **Problema:** na avaliação da T14 a cena pareceu um painel de caixas: estações iguais em grade, Picard sem destaque, ativo e livre quase iguais, engenharia com 6 vagas vazias ocupando um terço da altura e emoji num pedestal no lugar de personagem.
- **Decisão:** grade de 48 x 92; as 11 estações (LaForge incluído) ficam num console em arco ao redor da cadeira do Picard (escala 1,5, no centro), sobre um piso com anel e plataforma; cada tripulante é um boneco em pixel art com cabeça e corpo na cor da divisão e o emoji como insígnia, sentado digitando (braços alternam a cada 250 ms) quando ativo e de pé parado quando livre. O ativo tem console aceso com brilho na cor da divisão e "há N min" de `lastAt` (horas ou dias quando passa de 60 min, para caber); o livre sai com 40% de opacidade; o telão conta os ativos. A engenharia desenha só os workers reais (também bonecos) ou uma linha "Nenhum worker na engenharia", e a altura liberada estica o arco (até 1,25x) na ponte.
- **Motivo:** o usuário escolheu os quatro itens; colunas a 11 células e linhas a 12 garantem que nenhum rótulo se sobrepõe nem com todos ativos e com balão.
- **Por que não é bug:** `cena compacta a engenharia sem workers`, `cena acende o ativo e conta os ativos no telão`, `cena desenha a ponte em arco com bonecos` e `cena sem rótulos sobrepostos` (agora com todos ativos) cobrem o layout; a pintura segue só com `fillRect`, `fillText` e `strokeRect`.

### F10-13: ajustes finos da Cena da Ponte: "agora", bonecos maiores e anel na altura do painel (R52, R54)
- **Problema:** na captura da T15 o ativo recente mostrava "há 0 min", os bonecos pareciam pequenos e, numa lateral alta, sobrava uma faixa vazia abaixo da legenda, porque a grade tinha altura fixa (48 x 92) e o arco só esticava até 1,25x.
- **Decisão:** `haQuanto` devolve "agora" com menos de 1 minuto e segue com "há N min", "há N h" e "há N d". Os bonecos (tripulantes e workers) ficam 1,3x maiores: a 240 px, o sentado tem cerca de 27 px e o de pé cerca de 38 px, com pernas visíveis; colunas a 11 células e a mesma coluna a 13 mantêm as áreas sem se tocar. A largura da grade continua com 48 células, e a altura passa a ser `linhasDoPainel(largura, altura)` (proporção do palco, mínimo de 102 e teto de 400 linhas); `buildScene(estado, agentes, agora, linhas)` continua pura e devolve `anel`, que ocupa a ponte inteira, e as estações esticam sem teto ao longo dele. O `scene.ts` põe o palco em `100vh`, mede largura e altura com `ResizeObserver` (`dimensoes`) e refaz o canvas com `linhas x escala`.
- **Motivo:** o usuário pediu os três ajustes; com a grade na proporção do palco, o canvas esticado em `width: 100%` ocupa a altura do painel (sobra menos de uma linha), sem `drawImage` e sem quebrar a escala inteira mínima de 5 px.
- **Por que não é bug:** `cena mostra agora para atividade recente` (C56) e `cena estica o anel e aumenta os bonecos` (C57) cobrem os ajustes; o teste do arco agora compara as distâncias com o esticamento desfeito (o anel é uma elipse), e `cena sem rótulos sobrepostos` continua valendo. Folgas de 0,1 e 0,01 célula evitam que caixas encostadas se sobreponham por arredondamento em grades altas.
- **Correção do reaceite (T16):** na Orca o painel (465 x 930) era mais baixo que a proporção mínima da grade (102 linhas para 48 colunas), e o canvas com `width: 100%; height: auto` passava da altura, com rolagem e a legenda fora da vista. Agora o palco é `position: fixed` nas quatro bordas com `overflow: hidden`, o corpo e a raiz ficam sem margem, padding e rolagem, e `ajustaCanvas` define o tamanho exibido em px (`dimensoes`: célula = min(largura / 48, altura / linhas), arredondada para baixo, canvas centrado na largura). `cena cabe no palco sem rolagem` falha se a altura desenhada passar da altura do palco.

### F10-14: o CLI da Orca no worker do plugin (W1 do review e falha do loader)
- **Problema:** o review do Worf (W1) achou que o "worktree inválido" do `ponte.py` não chegava ao painel. Na Orca instalada, o diário repetia "orca worktree show falhou: node:internal/modules/cjs/loader:1575" e o botão "Abrir issue no Linear" ficava sempre desabilitado. A causa: no Windows, `execFile('orca')` busca primeiro no diretório do executável que chama, e lá o `orca` resolve para o `Orca.exe` (o app Electron, em modo node pelo `ELECTRON_RUN_AS_NODE`). Além disso, o worker roda com um env sem `APPDATA`, e o CLI responde `runtime_unavailable`.
- **Decisão:**
  - o worker resolve o CLI por caminho explícito (`resources/bin/orca.exe` ao lado do `execPath`, variáveis `ORCA_CLI*` e busca manual no PATH) e nunca chama o próprio `execPath`;
  - o env do CLI é completado (`USERPROFILE`, `APPDATA` e `LOCALAPPDATA` vêm do `os.homedir()`), sem as variáveis `NODE_*`, `ELECTRON_RUN_AS_NODE` e `ORCA_NODE_OPTIONS`/`ORCA_CLI_COMMAND`;
  - um worktree sem vínculo consulta a issue da feature (`orca linear issue <ID>`);
  - o diário não repete a mesma falha, e o orca.log guarda o diagnóstico, só com os nomes das variáveis.
- **Motivo:** a limitação "orca falha dentro do worker" da F10-9 tinha causa no plugin, não na Orca. Com a correção, a Issue mostra título, estado e o link no reaceite de 2026-11-11.
- **Por que não é bug:** os testes do worker cobrem a resolução do CLI com `execPath` falso, o env completado, a issue da feature e o diário sem repetição (60 testes do plugin). A limitação do Iniciar Picard em segundo plano segue como na F10-9.

### F10-15: Iniciar Picard numa aba visível pelo CLI (SC-131)
- **Problema:** o `agent.launch` da API de plugins inicia em segundo plano por definição: o Iniciar Picard não mostrava aba nem enviava o prompt `/starcode:engajar` (limitação da F10-9).
- **Decisão:** o worker roda `orca agent launch --agent <cli> --worktree path:<caminho> --prompt <prompt> --surface terminal --focus --json` pelo `execOrca` (F10-14), com `--model` só quando o `cliModel` do Picard traz um modelo real ("padrão do CLI" não conta). O painel recebe `{ terminalId, visible: true }` e o diário grava "Picard iniciado numa aba visível". Se o CLI falhar (exceção ou `ok:false`), o worker registra a falha e volta ao `agent.launch` da API, responde `visible: false` e grava "Picard iniciado em segundo plano"; o painel só mostra o aviso de segundo plano nesse caso. A trava `launching`, a validação e o mapa de prompts não mudam.
- **Pasta instalada:** o worker nunca escreve na pasta instalada do plugin (o `contentHash` da instalação a verifica; um `scripts/__pycache__` fez a Orca recusar o painel), por isso o python do `ponte.py` roda com `-B` e `PYTHONDONTWRITEBYTECODE=1`.
- **Motivo:** a limitação da F10-9 tinha saída pelo CLI, que abre a aba de agente e envia o prompt.
- **Por que não é bug:** os testes do worker cobrem os argumentos do CLI (com e sem `--model`), a volta para a API e o diário; os do painel cobrem as duas mensagens e o aviso.


### F11-1: leitura de imagem só com stdlib, escala pelo nome e tamanho em CSS (R11, R12)
- **Problema:** os gates da fase 11 precisam comparar a captura de design com a foto da tela rodando, sem dependência externa (o plugin só usa stdlib) e sem confundir uma foto 2x com uma tela de outro tamanho.
- **Decisão:** `scripts/gates/images.py` lê o tamanho de PNG (IHDR), JPEG (marcadores SOF0–SOF15, exceto DHT, JPG e DAC) e WebP (`VP8 `, `VP8L`, `VP8X`) pelos bytes do cabeçalho. Arquivo ausente, formato não suportado ou cabeçalho ilegível viram `ImageError` com o caminho e o motivo em PT-BR, sem stack trace. A escala vem do nome (`@2x`, `@3x` antes da extensão; sem sufixo, 1) e o tamanho em CSS é o tamanho em pixels dividido por ela. A foto (`<nome>.running.png`) passa quando `px / k == css` para algum k em 1, 2, 3, com divisão exata.
- **Motivo:** a escala pelo nome dispensa ler metadados de densidade e aceita foto em qualquer densidade comum; a divisão exata evita arredondamento que mascare uma tela de outro tamanho.
- **Por que não é bug:** `test_image_size_*`, `test_capture_scale_e_css`, `test_same_css_1x_2x_3x` e `test_list_captures_ignora_running_e_duplicadas` cobrem o método, com imagens sintéticas geradas no teste. Adaptado de `_image_size` e `_same_layout` do tlc (CC-BY-4.0).

### F11-2: regras de captura de volta no `validate_spec` (R1, R2, R3, R4)
- **Problema:** a D25 removeu as regras de captura da spec; com a fase 11 a pasta `captures/` volta a ser a fonte do design e uma captura esquecida em `## Sources`, sem requisito ou sem imagem na spec deixaria a tela sem prova.
- **Decisão:** com `images.list_captures` encontrando capturas, o `validate_spec.py` dá ERRO quando: (R1) falta `## Sources`; (R2) uma captura não tem linha em `## Sources` (a linha cita `captures/<arquivo>`) ou a linha `non-binding` não traz `user: "<palavras>"`; (R3) uma captura vinculante (linha sem `non-binding`) não é citada entre crases (`captures/<arquivo>` ou o caminho completo) numa linha de requisito `**R<n>**`; (R4) a spec não tem `![...](captures/<arquivo>)`. Feature sem `captures/` fica como antes; duas capturas para a mesma foto (`ImageError`) viram ERRO com a mensagem do `images.py`.
- **Motivo:** cada captura precisa de uma linha com papel declarado (vinculante ou não, com a palavra do usuário), de um requisito que a cobre e da imagem visível na spec aprovada.
- **Por que não é bug:** os seis testes de `tests/test_validate_spec_captures.py` cobrem cada regra, a spec completa e a feature sem `captures/`. Adaptado de `_check_captures` do tlc (CC-BY-4.0).
