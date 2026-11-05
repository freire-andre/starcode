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

**Resultado**: reprovado (falha do núcleo comum na instalação, R29). O roteiro `docs/aceite/roteiros-fase-4/antigravity.md` não rodou, porque o plugin não instala.

Versões: Orca 1.4.248, Antigravity CLI (`agy`) 1.5.1 (a matriz da Fase 0 foi feita com a 1.4.12), plugin `starcode` de `dist/antigravity` (worktree `f4-t10`, base `eca7324`).

**Evidência**:
- **Instalação**: `python tools/install_local.py --cli antigravity` saiu com erro no primeiro passo, `agy plugin validate dist/antigravity --strict`, e o `agy plugin install` nem rodou. Linha exata do erro: `✗ rules/starcode.md: no valid trigger in the frontmatter, so the rule never applies. Set trigger to always_on, model_decision, glob, manual`. Resumo do `agy`: `skills 8 · agents 0 · rules 0 · hooks 0 · mcpServers 0 · sidecars 0` e `Error: validation failed: 1 error, 0 warnings`.
- **Sem `--strict`**: `agy plugin validate dist/antigravity` dá o mesmo erro. Não há contorno pelas flags.
- **Causa provável (não corrigida aqui)**: `dist/antigravity/rules/starcode.md` começa direto em `# StarCode core rules...`, sem frontmatter com `trigger:`. O `agy` 1.5.1 passou a exigir o campo. O aviso de logo (`plugin.json: no logo`) segue sendo só aviso.
- **Não rodou**: setup, engajar, Linear (PROJ), tickets, `run_gates.py done` e os modelos efetivos. Não criei worktree no sandbox nem issue no Linear, porque sem o plugin instalado o worker não teria o fluxo StarCode.
- **Limites do ticket**: `dist/`, `tools/` e `scripts/` estão fora do `May change`, então não corrigi a regra. Nenhum `--dangerously-skip-permissions` foi usado.

**Achados** (vão para o ciclo de correção):
1. O adaptador do Antigravity gera `rules/starcode.md` sem `trigger` no frontmatter, e o `agy plugin validate --strict` (1.5.1) reprova. Correção sugerida: o gerador em `src/` emitir `trigger: always_on` (a regra vale para toda a tripulação) e `dist/antigravity` ser regenerado. Depois, repetir este aceite.
2. O mesmo validador contou `agents 0 · rules 0 · hooks 0`, embora `dist/antigravity` tenha hooks e a regra. Confirmar, depois do ajuste, se o `agy` 1.5.1 ainda lê o layout de agentes e hooks, ou se o manifesto mudou.
3. A matriz da Fase 0 foi medida no `agy` 1.4.12. Com a 1.5.1 a instalação mudou de passa para falha: reexecutar a coluna Antigravity depois da correção.
