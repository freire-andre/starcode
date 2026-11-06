# Aceite da Fase 4 (SC-11): paridade com Codex, Antigravity e OpenCode

Data: 2026-11-05. Repositório de teste: `F:\Projetos\starcode-sandbox` (worktree Orca próprio, criado de `main`), time PROJ do Linear (nenhum projeto de teste no time SC).
Roteiros: `docs/aceite/roteiros-fase-4/<cli>.md`. Cada CLI tem a sua seção abaixo.

## Codex

**Resultado**: aprovado

Versões: Orca 1.4.248, codex-cli 0.166.0, plugin `starcode` 0.1.0 instalado de `dist/codex` (worktree `f4-integ`, commit `612ad08`).
Roteiro `docs/aceite/roteiros-fase-4/codex.md`: feature `vencimento-tarefas` (`add --vence`, `[VENCIDA]` no `list`), classificada GRANDE, modo Git 2.

**Evidência**:
- **Instalação**: `tools/install_local.py --cli codex` passou depois de remover o marketplace antigo (ver o achado abaixo). `codex plugin add starcode@starcode` instalou em `~/.codex/plugins/cache/starcode/starcode/0.1.0`.
- **Despacho**: Picard do Codex como worker da Orca (`worker-start --agent codex --model gpt-6-luna`, dispatch `ctx_ec4a791995aa`) em worktree novo do sandbox. Aninhamento: eu (1), Picard (2), LaForge e Q dele (3). Sem `--dangerously-skip-permissions` e sem `--dangerously-bypass-hook-trust`.
- **Setup e engajar**: o `setup` gravou `.starcode/config.json` (time PROJ; Todo/In Progress/Done; sem estado de revisão; base `main`) com a aprovação do coordenador, e as 12 labels crew já existiam. O `engajar` passou no preflight Orca/Linear.
- **Linear (PROJ)**: PROJ-11 (mãe), PROJ-12 (T1) e PROJ-13 (T2). Caminho: issue-mãe pelo `orca linear`, porque o MCP do Linear do Codex não estava disponível (sem login). Os três receberam o comentário "pronto para revisão".
- **Commits** (ramo `feature/vencimento-tarefas`, sem push):
  - T1 (PROJ-12): `37b7dd4`.
  - T2 (PROJ-13): `ed077ff`, integrado em `cc84579`.
  - Correção dos achados do Q: `f5298c1`.
  - Provas: `88cd6cd` e `0871a07`; fechamento da verificação: `2decf6d`.
  - HEAD: `575dd05`.
- **Gates**: `run_gates.py ticket` verde em T1 e T2. `run_gates.py done vencimento-tarefas` em `575dd05`: `VEREDITO: VERDE (etapa done, 1 gate(s))` (reexecutado por mim). `python -m unittest` passa.
- **Q**: antigravity, de outra família, pedido e efetivo `gemini-3.8-flash-high`. Primeiro veredito FAIL com 4 achados de teste (C2, C3, C4 e R1 sem teste), corrigidos em `f5298c1`; veredito final PASS (`verification.md`).
- **Modelos efetivos**: Picard, Troi, Spock, Data e LaForge `codex · gpt-6-luna` (relatado pelo worker; `config.toml` do Codex também diz `gpt-6-luna`). Q `antigravity · gemini-3.8-flash-high`.
- **Disjuntor**: `gate-T1-check_scope=1` (execução pré-commit, sem commit no intervalo). Uma tentativa de gate de commit com mensagem fora do formato, corrigida antes do commit. Nenhum disjuntor aberto.

**Achados** (vão para o ciclo de correção):
1. `tools/install_local.py --cli codex` não trata um marketplace já existente com outra fonte. Saída exata: `Error: marketplace 'starcode' is already added from a different source; remove it before adding this source`. O passo seguinte do script (`plugin add`) nem roda. Contorno: `codex plugin marketplace remove starcode` e rodar de novo. Sugestão: o script detectar a fonte atual e pedir/oferecer a troca.
2. `dispatch.py q-cli` respondeu `self-verified` por falta de capability record do Codex, embora o worker do Antigravity tenha sido usado explicitamente e a verificação tenha de fato rodado em outra família.
3. O marketplace `starcode` do Codex ficou apontando para o worktree `f4-integ` (que some depois do PR). O Picard deve re-apontá-lo para `F:\Projetos\StarCode` depois do merge.

## Antigravity

**Resultado**: aprovado (tentativa 2).

**Histórico**:
- **Tentativa 1: reprovado (instalação)**, base `eca7324`. `agy plugin validate dist/antigravity --strict` (agy 1.5.1) falhou com `rules/starcode.md: no valid trigger in the frontmatter, so the rule never applies. Set trigger to always_on, model_decision, glob, manual`. O roteiro não rodou. A correção saiu no SC-41 (`3b0348c`, `trigger: always_on`).
- **Tentativa 2: aprovado** (esta seção).

Versões: Orca 1.4.248, Antigravity CLI (`agy`) 1.5.1, plugin `starcode` 0.1.0 instalado de `dist/antigravity` (worktree `f4-integ`, commit `39c0813`).
Roteiro `docs/aceite/roteiros-fase-4/antigravity.md`: feature `buscar-tarefas` (`buscar TERMO`), modo Git 2.

**Evidência**:
- **Instalação**: `python tools/install_local.py --cli antigravity` passou. `validate --strict` deu `skills 8 · agents 0 · rules 1 · hooks 0 · mcpServers 0 · sidecars 0` e `Validation passed` (só o aviso de logo). `agy plugin install` instalou 8 skills e 1 regra em `~/.gemini/config/plugins/starcode`.
- **Despacho**: Picard do Antigravity como worker da Orca (`worker-start --agent antigravity --model gemini-3.8-flash-high`, dispatch `ctx_a006af4a40fa`) em worktree novo do sandbox, criado de `main` (`f4-antigravity-aceite`). Aninhamento: eu (1), Picard (2), LaForge e Q dele (3). Sem `--dangerously-skip-permissions` e sem `--dangerously-bypass-hook-trust`.
- **Setup e engajar**: o `setup` gravou `.starcode/config.json` (time PROJ; Todo/In Progress/Done; sem estado de revisão) e o `engajar` passou, ambos com a aprovação pré-gravada do roteiro (`roteiro pré-aprovado em 2026-11-05`).
- **Linear (PROJ)**: PROJ-14 (mãe), PROJ-15 (T1) e PROJ-16 (T2). Caminho: issue-mãe pelo `orca linear`, porque o MCP do Linear não está disponível no Antigravity.
- **Commits** (ramo `feature/buscar-tarefas`, sem push): T1 (PROJ-15) `ca78587`; T2 (PROJ-16) `532e192`; provas `17d1a30`; verificação do Q `650cfec`; correção do achado do Q `1b01009`; fechamento `d335920`; HEAD `f9bbb6c`.
- **Gates**: `run_gates.py done buscar-tarefas` em `f9bbb6c`: `VEREDITO: VERDE (etapa done, 1 gate(s))` (reexecutado por mim). `python -m unittest`: 13 testes OK.
- **Q**: codex, de outra família (pedido `cli-default`, efetivo `gpt-6-luna`). O achado único (R1: `lower()` não trata `ß` ≈ `SS`) foi corrigido com `casefold()` em `1b01009` e marcado como fechado. O cabeçalho de `verification.md` ainda mostra `Verdict: FAIL`, escrito antes da correção; o gate `validate_verification` passa com 0 erro.
- **Modelos efetivos**: Picard e LaForge `antigravity · gemini-3.8-flash-high` (terminal: "Gemini 3.8 Flash · high"); Troi, Spock e Data rodaram no Picard, no mesmo modelo.

**Achados** (vão para o ciclo de correção):
1. O `agy` 1.5.1 contou `agents 0 · hooks 0` para `dist/antigravity`, que tem `hooks/scripts` e `crew.json` mas nenhum `hooks.json` na raiz. Sem os hooks nativos, o banner e o bloqueio de comandos do StarCode não funcionam no Antigravity. O fluxo funcionou por fallback (o `engajar` faz o preflight sozinho). Gerar o `hooks.json` no adaptador e reexecutar a célula de hook e banner.
2. O MCP do Linear não ficou disponível; o `orca linear` cobriu a publicação.
3. O plugin de teste `starcode-hello` (Fase 0) continua instalado no `agy` junto com o `starcode`. Desinstalar depois do aceite.
4. Divergência de estado: `verification.md` com `Verdict: FAIL` e achado fechado. O Q deveria regravar o veredito depois do fechamento.

## OpenCode

**Resultado**: aprovado (com troca de modelo no meio do aceite).

**Troca de modelo** (pedido do usuário, 2026-11-05): o roteiro `docs/aceite/roteiros-fase-4/opencode.md` pede `openrouter/deepseek/deepseek-v4-pro` (pago). O usuário trocou para o gratuito `openrouter/nvidia/nemotron-3.5-super-vl:free`. O roteiro não foi alterado (fora do escopo do ticket); a divergência fica registrada aqui. Política de fallback pedida pelo usuário, caso o nemotron fosse bloqueado: `opencode/mimo-v2.6-flash-free`, depois `opencode/deepseek-v4.1-flash-free`, depois `opencode/glm-5.3-flash-free`, nunca voltar a modelo pago. Nenhum bloqueio ocorreu, então nenhum fallback foi usado.

**Histórico**:
- **1ª execução (deepseek-v4-pro), interrompida pelo coordenador**: o Picard fez `setup`, `engajar`, Troi, Spock e Data (PROJ-17, PROJ-18 e PROJ-19), criou o ramo `feature/exportar-md` e despachou o LaForge do T1 (ramo `freire-andre/T1-exportar-md`, commit `da2d7b2`). Parou em `Dispatched: T1 · PROJ-18 · base 9d1d904`, antes de qualquer ticket integrado.
- **2ª execução (nemotron-3.5-super-vl:free)**: retomou pelo Handoff, sem recriar as issues PROJ.

Versões: Orca 1.4.248, OpenCode v2.2.3, plugin `starcode` 0.1.0 instalado de `dist/opencode` (worktree `f4-integ`, commit `4e97042`).
Roteiro `docs/aceite/roteiros-fase-4/opencode.md`: feature `exportar-md` (`exportar-md ARQ`), tamanho MÉDIA, modo Git 2.

**Evidência**:
- **Instalação**: `python tools/install_local.py --cli opencode` gravou 8 caminhos de skill em `~/.config/opencode/opencode.json` (cópia prévia em `opencode.json.bak-f4`; o plugin e o MCP do usuário foram mantidos) e copiou 8 comandos `sc-*.md`.
- **Formato do campo `skills`** (ponto em aberto da T4): `{"skills":{"paths":[...]}}` está correto no OpenCode v2.2.3. As skills `setup`, `engajar`, `troi`, `spock`, `data`, `laforge`, `mccoy` e `q` apareceram e carregaram, e o fluxo inteiro rodou a partir delas.
- **Despacho**: Picard do OpenCode como worker da Orca (`worker-start --agent opencode --model openrouter/nvidia/nemotron-3.5-super-vl:free`, dispatch `ctx_6fa7ab922952`; 1ª execução `ctx_36dd7e0df4cb`) em worktree novo do sandbox, criado de `main` (`f4-opencode-aceite`). Aninhamento: eu (1), Picard (2), LaForge e Q dele (3). Sem `--dangerously-skip-permissions` e sem `--dangerously-bypass-hook-trust`.
- **Setup e engajar**: `.starcode/config.json` (time PROJ; Todo/In Progress/Done; sem estado de revisão; base `main`), commit `9adf82d`; spec, contexto e tasks em `817ff56`. Aprovações pré-gravadas do roteiro (`roteiro pré-aprovado em 2026-11-05`).
- **Linear (PROJ)**: PROJ-17 (mãe), PROJ-18 (T1) e PROJ-19 (T2), criadas na 1ª execução e reaproveitadas na 2ª. Caminho: `orca linear` (o OpenCode não tem o MCP do Linear).
- **Commits** (ramo `feature/exportar-md`, sem push): T1 (PROJ-18) `8d61c93`, integrado em `d2a475a`; T2 (PROJ-19) `e055909`, integrado em `79d58ee`; correção do achado do Q `aa59eb5`, integrada em `f36df5e`; HEAD `f36df5e`.
- **Gates**: `run_gates.py done exportar-md` em `f36df5e`: `VEREDITO: VERDE (etapa done, 1 gate(s))` (reexecutado por mim no worktree `exportar-md`; `validate_verification` 0 erro). `python -m unittest`: 7 testes OK.
- **Q**: codex, de outra família (modelo efetivo não relatado pelo worker). Veredito final APROVADO. Achado único: o teste de C1 não falsificava a ordenação por ID, corrigido em `aa59eb5`.
- **Modelos efetivos**: Picard, Troi, Spock, Data e LaForge `opencode · openrouter/nvidia/nemotron-3.5-super-vl:free` (relatado pelo worker e confirmado no rodapé do terminal: "Nemotron 3.5 Super VL (free) OpenRouter"). Q no codex.

**Achados** (vão para o ciclo de correção):
1. **Artefatos de planejamento fora do ramo de integração (F2-7)**: na 1ª execução, o Picard despachou o LaForge sem commitar `.specs/features/exportar-md/`, e o gate `check_scope` do LaForge falhou com `.specs/features/exportar-md/` ausente (o diretório `.specs/features` nem existia no ramo). Na 2ª execução, o Picard commitou os artefatos (`817ff56`) antes do despacho, depois de um aviso do coordenador. O Picard deveria fazer isso sozinho; reforçar na skill `engajar`/`laforge`.
2. **Handoff desatualizado**: ao fim, o `## Handoff` de `tasks.md` ainda mostra `Phase: execute` e `Dispatched: T1 · PROJ-18`, sem `Settled` nem `Last integrated`. O Picard não o atualizou depois dos tickets.
3. **`proofs.md` e `verification.md` sem commit**: ficaram untracked no worktree `exportar-md`; o `run_gates.py done` passa por ler o disco, mas o ramo de integração não os contém.
4. **Hook e banner não exercitados**: o OpenCode não tem evento de início de sessão (`banner_hook` indisponível) e o hook de bloqueio do `starcode` não foi testado neste aceite (extras ficam como na Fase 0).
5. **Modelo gratuito**: o aceite passou com o nemotron `:free`, sem 429 nem bloqueio do provedor. Não confirma o mesmo resultado com o `deepseek-v4-pro` do roteiro.
