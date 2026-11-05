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
