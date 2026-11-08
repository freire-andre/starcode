# Matriz de compatibilidade (Fase 0)

Data: 2026-11-03. Ticket: CIF-7. Plugin de teste: `starcode-hello`, gerado por `tools/build_hello.py` em `dist/<cli>/`.

Versões testadas: Orca 1.4.247, Claude Code 2.1.317, Codex 0.166.0, Antigravity CLI (`agy`) 1.4.12, OpenCode 2.2.3 (V2), Python 3.14.
As saídas de `--help` de cada comando usado estão em `docs/cli-baseline/`.

**Mudança de escopo (D32):** o Gemini CLI saiu do projeto, porque o login não funciona neste ambiente e o Google pôs o Antigravity no lugar. O Antigravity CLI é o 4º CLI. As notas do Gemini ficam no fim deste documento, só como histórico.

Legenda: ✅ passou · ❌ falhou · ⏳ depende de ação do usuário · ⚠️ passou com ressalva · n/a não se aplica

## Matriz

| Recurso testado | Claude | Codex | Antigravity | OpenCode |
|---|---|---|---|---|
| Instala a partir do marketplace/pasta em `dist/` | ✅ | ✅ | ✅ ¹ | ⚠️ ² |
| Nenhum arquivo de outro CLI é carregado | ✅ | ✅ | ✅ | ✅ |
| Skill `hello` carregada e invocável | ✅ | ✅ | ✅ | ✅ |
| Uma skill chamando outra pelo nome | ✅ | ✅ ⁴ | ✅ | ✅ |
| Hook que bloqueia um comando de teste | ✅ | ✅ ⁵ | ✅ ¹ | ⚠️ ² |
| Banner no início da sessão | ✅ | ✅ ⁵ | ✅ ¹ | n/a ⁶ |
| Subagente com outro modelo | ✅ | n/a | ⚠️ inconclusivo ³ | ⚠️ inconclusivo ⁷ |
| `orca agent launch --agent <id>` | ✅ | ✅ | ✅ | ✅ |
| `orca worktree create --agent <id> --linear-issue` | ✅ | ✅ | ✅ | ✅ |
| `orca orchestration worker-start` (`--spec-file`, resultado, modelo) | ✅ ⁸ | ✅ ⁵ | ✅ ⁸ | não testado ⁹ |
| MCP do Linear disponível | ✅ | ⏳ ¹⁰ | ⚠️ ¹⁰ | ❌ ¹⁰ |
| Fluxo StarCode completo (aceite da Fase 4) | ✅ ¹¹ | ✅ ¹¹ | ✅ ¹² | ✅ ¹³ |
| Cabeçalho por hook | ✅ | ✅ (após confiança) | em sondagem | em sondagem |

## Notas

1. **Antigravity**: `agy plugin validate dist/antigravity --strict` passa, com um aviso de falta de logo. `agy plugin install <pasta>` copia o plugin para `~/.gemini/config/plugins/<nome>`. O formato nativo:
   - `plugin.json` fica na raiz, com `author` como string.
   - O `hooks.json` fica na raiz, com hooks nomeados.
   - O bloqueio usa `PreToolUse` com matcher `run_command`. O comando chega em `toolCall.args.CommandLine`, e o hook responde `{"decision":"deny","reason":...}` com exit 0. O teste devolveu `tool call denied by pre-tool hook: STARCODE-HOOK-BLOCKED`.
   - O banner usa `SessionStart` com `{"injectSteps":[{"ephemeralMessage": ...}]}`. Com `systemMessage`, o modelo não viu o marcador, mas com `ephemeralMessage` e `userMessage` viu.
   - **Conversão automática:** `agy plugin install dist/claude` converte o plugin do Claude (skills, agentes e hooks), mas copia o `hooks.json` do Claude sem mudar nada (matcher `Bash`). Por isso, o hook não dispara. Daí a necessidade de um adaptador nativo (F0-6).
   - **Permissões no modo `-p`:** o `--dangerously-skip-permissions` não foi usado. Os testes liberaram só `echo` por `--settings '{"permissions":{"allow":["command(regex:^echo .*)"]}}'`.
2. **OpenCode**: as skills são carregadas pelo campo `skills` do `opencode.json` com caminho absoluto. O plugin (hook) **só dispara** quando o arquivo está em `.opencode/plugins/` do projeto ou em `~/.config/opencode/plugins/`. Via `OPENCODE_CONFIG_DIR` ou caminho absoluto em `plugins`, o plugin carrega mas o hook não dispara. O plugin não pode importar `@opencode/plugin` sem instalar o pacote, senão é ignorado em silêncio. A saída é exportar um objeto puro `{ id, setup }`. A ferramenta de shell se chama `shell` (`input.command`).
3. **Antigravity, subagente**: o `agents/hello-agent.md` (`model: flash`) é instalado, mas no modo `-p --mode auto` o modelo usou `read_file`/`run_command` em vez de `invoke_subagent`. Fica para a Fase 4. O modelo de subagente no Antigravity só aceita os níveis `inherit`, `flash` e `pro`.
4. **Codex**: o Codex carrega a skill lendo o arquivo pelo shell. Uma skill que proíbe o shell quebra o encadeamento, por isso a skill não pode proibir o shell.
5. **Codex, hooks**:
   - O Codex 0.166 **lê o `hooks/hooks.json` do plugin**, ao contrário do que o plano supunha.
   - Hooks de projeto e de plugin exigem trust. Sem trust, a sessão para em "Hooks need review", e o `worker-start` falha com `agent_readiness: Agent startup blocked: agent-hooks-review-prompt`.
   - Se o usuário só abre "1. Review hooks" e sai, o trust não fica registrado e o `codex exec` pula os hooks sem avisar. A flag `--dangerously-bypass-hook-trust` não foi usada.
   - **Bloqueio no Windows:** o Codex roda os hooks por `pwsh -Command`, que reduz qualquer exit diferente de 0 a 1. Por isso, "exit 2 + stderr" vira "hook exited with code 1" e o comando passa (fail-open). A solução foi o JSON `hookSpecificOutput.permissionDecision: "deny"` com exit 0, que passou no Codex (`PreToolUse Blocked`) e no Claude (`claude -p --plugin-dir dist/claude`).
   - Depois do trust, passaram o banner, o `agent launch`, o `worktree create` e o `worker-start --model gpt-6-luna` (`worker_done: succeeded`).
   - O `SessionStart Failed` que aparece vem do plugin `impeccable`, de terceiros, cujos hooks usam sintaxe de bash.
6. **OpenCode**: o plano não prevê banner por hook no OpenCode, que não tem evento equivalente. O contexto inicial vem do `AGENTS.md`/instruções.
7. **OpenCode, subagente**: o subagente com outro modelo (`nvidia/z-ai/glm-5.3-flash`) deu timeout duas vezes. O modelo gratuito padrão atingiu o limite de uso. Repetir com um provedor pago.
8. **Workers e modelo**:
   - Claude: `--model claude-haiku-5-5`, e o terminal confirmou o Haiku 5.5.
   - Antigravity: `--model gemini-3.8-flash-medium`, e o terminal confirmou "Gemini 3.8 Flash (Medium)". No `agent launch` e no `worktree create` com `gemini-3.8-flash-low`, o terminal mostrou "Gemini 3.8 Flash (Low)".
   - O resultado do `worker-start` traz `"model"` (o modelo pedido). O recibo do `agent launch` e do `worktree create` **não** traz o modelo (F0-2).
9. **OpenCode, worker**: a ajuda diz que o `--model` só vale em worktree existente. Fica para a Fase 4.
10. **MCP do Linear**:
    - Claude: ativo.
    - Codex: configurado, mas sem login.
    - Antigravity: `linear` configurado via `mcp-remote`; o login não foi verificado.
    - OpenCode: sem MCP.
    - O StarCode usa o `orca linear` para quase tudo (D2).
11. **Aceite da Fase 4, Codex**: aprovado em 2026-11-05 (`docs/aceite/fase-4.md`, seção Codex). Picard e equipe em `gpt-6-luna`, Q no Antigravity; `run_gates.py done` deu VEREDITO VERDE e PROJ-11 a PROJ-13 foram publicadas pelo `orca linear` (o MCP do Linear do Codex segue sem login). Claude: aceite da Fase 3 (`docs/aceite/fase-3.md`).
12. **Aceite da Fase 4, Antigravity**: aprovado em 2026-11-05 na 2ª tentativa (`docs/aceite/fase-4.md`, seção Antigravity). A 1ª reprovou na instalação (`rules/starcode.md` sem `trigger`, `agy` 1.5.1), corrigida no SC-41. Picard e equipe em `gemini-3.8-flash-high`, Q no codex (`gpt-6-luna`); `run_gates.py done` deu VEREDITO VERDE e PROJ-14 a PROJ-16 foram publicadas pelo `orca linear`. Ressalva: o `agy` 1.5.1 contou `agents 0 · hooks 0` para `dist/antigravity` (sem `hooks.json` na raiz), então hook de bloqueio e banner do `starcode` não foram exercitados; as linhas de hook e banner da coluna seguem da Fase 0 (`agy` 1.4.12, plugin `starcode-hello`).
13. **Aceite da Fase 4, OpenCode**: aprovado em 2026-11-05 (`docs/aceite/fase-4.md`, seção OpenCode). O roteiro pede `openrouter/deepseek/deepseek-v4-pro`, mas o usuário trocou para o gratuito `openrouter/nvidia/nemotron-3.5-super-vl:free` (a 1ª execução parou no T1). Picard e equipe em nemotron, Q no codex; `run_gates.py done` deu VEREDITO VERDE e PROJ-17 a PROJ-19 foram publicadas pelo `orca linear`. O formato `skills.paths` do `opencode.json` foi confirmado no OpenCode 2.2.3 (as 8 skills carregaram). Ressalva: hook de bloqueio e banner do `starcode` não foram exercitados.

## Fase 4: extras por CLI

Fonte: `src/capabilities.yaml` (gera `dist/<cli>/capabilities.json` e a linha `Indisponível neste CLI` do banner). `ok` = o extra funciona no CLI; `unavailable` = não funciona, e o fallback entra no lugar. Um passo do núcleo comum que falha no aceite é `reprovado (<passo>)` em `docs/aceite/fase-4.md` (R29), nunca um extra indisponível.

| Extra | claude | codex | antigravity | opencode |
|---|---|---|---|---|
| `hooks` | ok | ok | ok | ok |
| `banner_hook` | ok | ok | ok | unavailable: sem evento de início de sessão; o banner vem do engajar |
| `linear_mcp` | ok | unavailable: issue-mãe pelo `orca linear` | unavailable: issue-mãe pelo `orca linear` | unavailable: issue-mãe pelo `orca linear` |
| `subagent_model` | ok | unavailable: Q por worker da Orca | unavailable: Q por worker da Orca | unavailable: Q por worker da Orca |
| `orca_worker` | ok | ok | ok | ok |

## Fase 5: hooks no Codex, Antigravity e OpenCode

Fonte: `docs/aceite/fase-5.md` (uma seção por CLI, sessões reais). A tabela de extras acima já reflete esses resultados (`src/capabilities.yaml`, R18).

| CLI | Resultado | Hooks | Banner por hook |
|---|---|---|---|
| Codex 0.166.0 | aprovado (T9) | push forçado e segredo bloqueados, 8 comandos normais passam | ok, `additionalContext` (exige trust em `/hooks`) |
| Antigravity `agy` 1.5.2 | aprovado na tentativa 3 (T15) | `hooks 2`, push forçado e segredo bloqueados | ok, `injectSteps` |
| OpenCode 2.2.3 | aprovado na tentativa 2 (T17) | push forçado e segredo bloqueados, 8 comandos normais passam | n/a, `unavailable` (sem evento de início de sessão) |

Achados registrados, sem correção nesta fase:

- **Antigravity, `cwd`**: o payload do `agy` não traz `cwd` e os guards usavam o diretório do processo; a T14 passou a ler o repositório de `workspacePaths`. A tentativa 2 reprovou por isso (o commit com segredo foi criado).
- **Antigravity, banner**: o banner diz "fora de um repositório Git" mesmo numa sessão dentro de um clone; o `SessionStart` do `agy` parece rodar fora do repositório.
- **Codex, banner**: sem config do repositório, o banner sugere `/starcode:setup` (`Config do repositório: ausente`).
- **OpenCode, `cwd`**: na tentativa 1 (T11) o plugin usava `process.cwd()`, que no OpenCode 2.2.3 é a home do usuário, e o `secret_scan` deixou o commit com segredo passar (reprovado). A T16 passou a usar `event.input.workdir` e a tentativa 2 (T17) foi aprovada.

## Procedimentos (por célula)

| Célula | Pré-requisito | Disparo | Evidência esperada |
|---|---|---|---|
| Instalação Claude | `python tools/build_hello.py` | `claude plugin marketplace add <repo>` + `claude plugin install starcode-hello@starcode` | plugin listado, lido de `dist/claude` |
| Instalação Codex | idem | `codex plugin marketplace add <repo>` + install | escolhe `.agents/plugins/marketplace.json` |
| Instalação Antigravity | idem | `agy plugin validate dist/antigravity --strict` + `agy plugin install <caminho>/dist/antigravity` | skills 2, agents 1, hooks 2 |
| Instalação OpenCode | idem | `opencode.json` com `skills` absolutos; plugin copiado para `.opencode/plugins/` | skill e hook ativos |
| Skill | plugin instalado | prompt "starcode hello test" | `STARCODE-HELLO-OK` |
| Encadeamento | idem | prompt "starcode chain test" | `STARCODE-HELLO-OK` + `STARCODE-CHAIN-OK` |
| Hook | idem | pedir `echo STARCODE_BLOCK_TEST` | comando bloqueado, `STARCODE-HOOK-BLOCKED` |
| Banner | idem | nova sessão, perguntar pelo marcador | `STARCODE-BANNER-OK` |
| Subagente | `agents/hello-agent.md` | pedir o hello-agent | `STARCODE-AGENT-OK`, modelo no transcript |
| agent launch | worktree existente | `orca agent launch --agent <id> --worktree name:<wt> --surface terminal --prompt ...` | `STARCODE-LAUNCH-OK` no terminal |
| worktree create | repo registrado | `orca worktree create --agent <id> --model <m> --linear-issue CIF-7 --prompt ...` | `linkedLinearIssue` + `STARCODE-WT-OK` |
| worker-start | repo registrado | `orca orchestration worker-start --spec-file spec.md --agent <id> --model <m> --worktree new-child ...` | `worker_done` com `outcome: succeeded` |

## Consequências para o plano

- **Codex**: os hooks vêm do plugin, mas dependem de trust. O setup orienta a aprovação em `/hooks` e o banner avisa quando os hooks não estão confiáveis. O Picard checa se há hooks pendentes antes de despachar um worker do Codex.
- **Antigravity**: o adaptador é nativo (F0-6), e o Antigravity é agente de despacho da Orca com `--model`. Ele serve de opção para o Q com um modelo de outra família (Gemini).
- **OpenCode**: o setup copia o plugin para `~/.config/opencode/plugins/` e grava as skills com caminho absoluto.
- **D17 (modelo registrado)**: o recibo da Orca não traz o modelo. A fonte é o campo `model` do resultado do `worker-start` (pedido) mais a confirmação no terminal ou no transcript (efetivo) (F0-2).
- A Orca **não** moveu a CIF-7 sozinha ao vincular; o teste ficou inconclusivo porque a issue já estava em In Progress.

## Histórico: Gemini CLI 0.66 (removido pela D32)

`gemini extensions validate` passava e a instalação local funcionava, pedindo trust da pasta. O Gemini não instala a partir de subpasta de repo Git, só com `--ref`. Os testes de uso ficaram bloqueados porque o login não funcionou (`gemini -p` saía com exit 41).
