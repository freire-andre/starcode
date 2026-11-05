# Fase 4 — Paridade com Codex, Antigravity e OpenCode: Spec

**Approved**: 2026-11-05 - user: "sim"

**Size**: LARGE
**Risk triggers**: múltiplos CLIs (contrato de instalação de cada um), integração externa (Orca, Linear, provedores de modelo)
**Status**: Approved

## Context

O StarCode foi aceito só no Claude Code (Fases 1–3). O `dist/` já gera pastas para Codex, Antigravity e
OpenCode, mas nenhum fluxo rodou nelas. Esta fase faz o núcleo comum funcionar em cada CLI:
- instalação local a partir do `dist/`;
- `setup` e `engajar`;
- planejamento com Troi, Spock e Data;
- execução no modo 2 com LaForge e com o Q de outra família.

Cada extra que um CLI não tem (hooks, banner por hook, MCP do Linear, subagente com outro modelo) fica
marcado como indisponível, com um fallback que funciona e que o banner informa. Entram também três itens
herdados da Fase 3.

Sucesso: o aceite completo passa em cada CLI no sandbox, conduzido por worker automático com roteiro.
Discovery: `.specs/features/fase-4-paridade/context.md`.

## Scope

- Matriz de recursos por CLI (`src/capabilities.yaml`) emitida no `dist/` e lida pelo banner e pelas skills.
- Gerador (`tools/build.py`): marcador `{{CMD:<skill>}}` por CLI e marcador `{{CLI}}`.
- Instalação local para desenvolvimento (`tools/install_local.py`) em Codex, Antigravity e OpenCode.
- Banner: CLI atual, extras indisponíveis com o fallback e correção do falso positivo de verificação degradada.
- Data: fallback de publicação sem o MCP do Linear (issue-mãe com sub-issues).
- Picard:
  - escolha do CLI do Q pela família;
  - despacho de worker OpenCode em worktree existente;
  - Handoff, provas e verificação no worktree de integração.
- `dispatch.py`: briefing de feature MÉDIA a partir da spec; famílias `deepseek` e `openrouter/<vendor>/...`.
- Roteiros de aceite por CLI e evidência em `docs/aceite/fase-4.md`. A matriz da Fase 0
  (`docs/compatibilidade.md`) ganha o resultado da Fase 4.

## Non-Goals

- Hooks `git_guard`, `secret_scan` e banner por hook em Codex, Antigravity e OpenCode (Fase 5). Aqui o banner vem do `engajar` rodando `banner.py --full --text`.
- Marketplace privado, instalação a partir do GitHub, CI e release (Fase 6).
- Modo Frota (Fase 7) e despacho de vários CLIs ao mesmo tempo.
- Evals de roteamento (`claude plugin eval`) fora do Claude Code.
- Mudar as regras do fluxo já aceitas nas Fases 1–3 (aprovações, gates, disjuntor, escritor único) além do que está nos requisitos abaixo.
- Mudar automaticamente a configuração da Orca: o limite de profundidade é trocado pelo usuário.

## Requirements

Convenções: `<cli>` ∈ {claude, codex, antigravity, opencode}; "extra" é um recurso da matriz que não faz parte do núcleo comum; `I` é o ramo de integração `feature/<slug>`; "família" é a de `scripts/dispatch.py family`.

Matriz e banner:

- **R1** - The system SHALL manter em `src/capabilities.yaml`, para cada `<cli>`, os extras `hooks`, `banner_hook`, `linear_mcp`, `subagent_model` e `orca_worker`, cada um com `status` (`ok` ou `unavailable`) e, quando `unavailable`, um texto `fallback` não vazio.
- **R2** - WHEN `tools/build.py` roda THEN the system SHALL gravar `capabilities.json` na raiz de cada `dist/<cli>` só com os extras daquele CLI, e SHALL falhar com `BuildError` se um extra `unavailable` não tiver `fallback`.
- **R3** - WHEN `banner.py --full --text --cli <cli>` roda THEN the system SHALL imprimir a linha `CLI: <cli>` e, para cada extra `unavailable` desse CLI, a linha `Indisponível neste CLI: <extra> → <fallback>`.
- **R4** - IF `banner.py` roda sem `--cli` THEN the system SHALL usar `claude` e manter a saída da Fase 3 sem a linha `CLI:`.
- **R5** - The system SHALL marcar uma feature como verificação degradada no banner só quando o `verification.md` tiver uma linha que comece com `**Verification:** degraded` ou `**Verification:** self-verified`. Um texto que só cita essas palavras em outra linha não conta.

Gerador e instalação:

- **R6** - The system SHALL renderizar `{{CMD:<skill>}}` em qualquer arquivo de skill como `/starcode:<skill>` (claude), `/sc-<skill>` (opencode) e "a skill `<skill>` do StarCode" (codex e antigravity), e `{{CLI}}` como o nome do CLI do `dist/` sendo gerado.
- **R7** - The system SHALL substituir nas skills toda referência literal a `/starcode:<skill>` por `{{CMD:<skill>}}`, de modo que nenhum `dist/<cli>` que não seja o do Claude contenha a string `/starcode:`.
- **R8** - The system SHALL fazer o passo 1 do `engajar` rodar `banner.py --full --text --cli {{CLI}}` em todo CLI.
- **R9** - WHEN `tools/install_local.py --cli codex` roda THEN the system SHALL registrar o marketplace do repositório e instalar o plugin `starcode` lido de `dist/codex` com o próprio CLI do Codex, e imprimir o comando que rodou.
- **R10** - WHEN `tools/install_local.py --cli antigravity` roda THEN the system SHALL rodar `agy plugin validate dist/antigravity --strict` e, só com sucesso, `agy plugin install <caminho absoluto>/dist/antigravity`.
- **R11** - WHEN `tools/install_local.py --cli opencode` roda THEN the system SHALL gravar no `opencode.json` global (`~/.config/opencode/opencode.json`) o caminho absoluto de cada pasta de skill de `dist/opencode/skills` e copiar `dist/opencode/commands/*.md` para `~/.config/opencode/commands/`, preservando as chaves que já existiam no arquivo.
- **R12** - WHEN `tools/install_local.py` roda de novo para o mesmo CLI THEN the system SHALL deixar o resultado igual ao da primeira vez, sem entradas duplicadas no `opencode.json`, nos comandos ou no marketplace.
- **R13** - IF o binário do CLI pedido não está no `PATH` ou a pasta `dist/<cli>` não existe THEN `tools/install_local.py` SHALL sair com código 2 e a mensagem `<cli>: <binário ou pasta> não encontrado`, sem alterar nada.
- **R14** - WHEN `tools/install_local.py` roda com `--dry-run` THEN the system SHALL imprimir cada ação que faria e sair com código 0 sem alterar nenhum arquivo nem rodar comandos que instalam.

Data sem o MCP do Linear:

- **R15** - IF o extra `linear_mcp` do CLI atual é `unavailable` THEN the system SHALL publicar a feature criando com `orca linear create` uma issue-mãe com o título da feature e a spec como descrição, e cada ticket como sub-issue dela (`--parent <ID da mãe>`), em vez de criar o Projeto e o Documento.
- **R16** - WHEN a publicação usa a issue-mãe THEN the system SHALL criar as relações `blocks` entre os tickets como na Fase 2, gravar os IDs no `tasks.md` com `tasks_export.py record`, e o `run_gates.py publish` SHALL aceitar a issue-mãe no lugar do Projeto.
- **R17** - The system SHALL fazer o Data dizer em uma linha qual caminho usou ("Projeto e Documento pelo MCP" ou "issue-mãe pelo orca linear, MCP indisponível neste CLI").

Picard nos outros CLIs:

- **R18** - WHEN o Picard escolhe o CLI do Q THEN the system SHALL usar o primeiro, na ordem (Q configurado, codex, antigravity, opencode), cuja família seja diferente da família do LaForge efetivo e cujo extra `orca_worker` esteja `ok`.
- **R19** - IF nenhum CLI da ordem de R18 tem família diferente da do LaForge THEN the system SHALL rodar o Q como `self-verified` e marcar `**Verification:** self-verified`, como na Fase 3.
- **R20** - WHEN o CLI do LaForge é `opencode` THEN the system SHALL criar antes o worktree do ticket com `orca worktree create --base-branch feature/<slug>` e só então rodar `orca orchestration worker-start --agent opencode --model <modelo> --worktree <esse worktree>`.
- **R21** - WHEN o ramo de integração `I` é criado ou reutilizado THEN the system SHALL criar ou reutilizar um worktree da Orca para `I` e gravar ali o Handoff, o `proofs.md` e o `verification.md` da feature.
- **R22** - IF o `worker-start` falha com `nested_worker_depth_exceeded` THEN the system SHALL parar e dizer, em uma linha, que o limite de profundidade da Orca precisa ser 2 ou mais (Settings → Orchestration), sem contar tentativa do disjuntor.

`dispatch.py`:

- **R23** - WHEN `dispatch.py brief <slug> <ID>` roda numa feature sem `tasks.md` THEN the system SHALL montar o briefing a partir do `spec.md`: título, `**Linear**:`, `## Scope`, `## Requirements` e `## Checks`, mais as regras fixas do worker com o caminho absoluto do `run_gates.py`.
- **R24** - IF a feature não tem `tasks.md` e o `spec.md` não tem `## Checks` THEN `dispatch.py brief` SHALL sair com código 2 e a mensagem `spec sem ## Checks: não há o que entregar ao worker`.
- **R25** - The system SHALL classificar em `dispatch.py family` os modelos com prefixo `deepseek` como família `deepseek`, `gpt-oss` como `openai`, e um modelo `openrouter/<vendor>/<modelo>` pela família do `<vendor>` (`anthropic`, `openai`, `google`, `deepseek`), ou `unknown` para outro vendor.

Aceite:

- **R26** - The system SHALL ter, para cada CLI de {codex, antigravity, opencode}, um roteiro de aceite autossuficiente em `docs/aceite/roteiros-fase-4/<cli>.md` com a missão, as respostas da Troi, as aprovações marcadas como `roteiro pré-aprovado em <data>`, o modelo de cada papel e o relatório esperado no `worker_done`.
- **R27** - WHEN o aceite de um CLI roda THEN the system SHALL, com o Picard, a Troi, o Spock, o Data e o LaForge naquele CLI e o Q num CLI de outra família, rodar `setup` e `engajar`, planejar até a publicação no Linear (time PROJ, sem projeto de teste no time SC), executar de 2 a 3 tickets no modo 2 e terminar com `run_gates.py done` em VEREDITO VERDE.
- **R28** - The system SHALL registrar em `docs/aceite/fase-4.md` uma seção por CLI com resultado e evidência (commits, issues PROJ, vereditos dos gates e modelos efetivos), e em `docs/compatibilidade.md` o status de cada extra por CLI depois da Fase 4.
- **R29** - IF um passo do núcleo comum falha num CLI THEN the system SHALL registrar esse CLI como reprovado no aceite, com a linha exata do erro, e SHALL não marcar o passo como extra indisponível.

## Data & Contracts

- `src/capabilities.yaml` (YAML mínimo do `miniyaml`):

      codex:
        hooks: {status: unavailable, fallback: "Fase 5; gates rodam pelo Picard"}
        linear_mcp: {status: unavailable, fallback: "issue-mãe pelo orca linear"}
        ...

- `dist/<cli>/capabilities.json`: `{"cli": "<cli>", "extras": {"<extra>": {"status": "...", "fallback": "..."}}}`.
- `tools/install_local.py --cli <cli> [--dry-run]`: exit 0 em sucesso, 1 quando o comando do CLI falha (a saída dele é repassada), 2 em pré-condição (R13).
- Linha do banner: `Indisponível neste CLI: <extra> → <fallback>`.
- Roteiro de aceite (`docs/aceite/roteiros-fase-4/<cli>.md`): seções `## Missão`, `## Respostas`, `## Aprovações`, `## Tripulação`, `## Relatório esperado`.

## States

- O ciclo de vida da feature segue as Fases 2–3 (`discovery` → `spec` → `spec-approved` → `published` → `execute` → `review` → `done`).
- O aceite de cada CLI: `pendente` → `aprovado` | `reprovado (<passo>)`.

## Edge Cases

- **OpenCode sem saldo no OpenRouter:** o worker para com a linha do provedor, e o CLI fica reprovado com o erro (R29); não é extra indisponível.
- **Codex sem login no MCP do Linear:** o extra `linear_mcp` fica `unavailable` e o Data usa a issue-mãe (R15).
- **Antigravity:** `subagent_model` só aceita `inherit`, `flash` ou `pro` (Fase 0), por isso fica `unavailable`. O fallback é o Q por worker da Orca.
- **Codex com hooks pendentes de trust:** sem `hooks.json` no `dist/codex` nesta fase, não há prompt de trust. Se o usuário tiver hooks de outro plugin pendentes, o `worker-start` falha com `agent-hooks-review-prompt`, e o aceite registra o erro.
- **LaForge e Q do mesmo vendor por caminhos diferentes** (ex.: `openrouter/anthropic/...` e `claude`): a família é a mesma (R25), e a regra R18 pula esse Q.
- **`install_local.py` com `opencode.json` sem a chave `skills`:** cria a chave. Com JSON inválido, sai com código 2 sem gravar.
- **Feature MÉDIA com `**Linear**:` vazio:** o briefing sai com `Issue: sem issue`.

## Decisions

| Item | Options | Status |
|---|---|---|
| Quem conduz o aceite em cada CLI | usuário interativo · worker automático com roteiro | approved - user: "Worker automático com roteiro" |
| Modelo do OpenCode no aceite | deepseek-v4-pro (OpenRouter) · claude-sonnet-5.5 (OpenRouter) · gratuito/Nvidia | approved - user: "deepseek-v4-pro (Recommended)" |
| Papéis no CLI testado | tripulação toda com o Q fora · só o Picard | approved - user: "Tripulação toda, Q fora (Recommended)" |
| Feature por CLI | nova e pequena por CLI · reusar csv-import-export | approved - user: "Uma nova e pequena por CLI (Recommended)" |
| Aninhamento de workers na Orca | subir o limite para 2 · Picard como agente de topo · usuário interativo | approved - user: "Subir o limite para 2 (Recommended)" |
| Escopo e aceite da fase | aceite completo por CLI · núcleo por CLI + 1 completo | approved - user: "Completo por CLI (Recommended)" |

## Open Questions
None.

## Sources

- `PLANO_STARCODE.md` §10 "Fase 4"; D21, D32; `DECISIONS.md` F0-1 a F0-6 e F3-1 a F3-9.
- `docs/compatibilidade.md` (matriz da Fase 0) e `docs/aceite/fase-3.md` (observações 4, 5 e 8).
- Sondagem de 2026-11-05: `worker-start` dentro de um worker devolveu `nested_worker_depth_exceeded: Sub-worker dispatch is not permitted at depth 2 (max 1)`; o limite muda em Settings → Orchestration.
- `codex-cli 0.166.0`, `agy 1.4.12`, `opencode v2.2.3` (versões lidas dos próprios binários).

## Handoff

**Phase:** spec-approved
**Size:** LARGE
**Git mode:** 3
**Next:** Data quebra em tasks
**Linear:** SC-11
**Integration branch:** not created
**Last integrated:** none
**Dispatched:** none
**Settled:** 2026-11-05: spec aprovada: "sim"
**Attempts:** none
**Reports:** none
**Breaker:** closed
