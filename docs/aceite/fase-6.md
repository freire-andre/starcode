# Aceite da Fase 6 (SC-61): release 1.0.0

Roteiros: `docs/aceite/roteiros-fase-6/<cli>.md` e `dia-de-missao.md`. Cada seção é preenchida numa sessão real, com instalação limpa a partir do GitHub privado.

## Versões

| Item | Versão |
| --- | --- |
| StarCode | 1.0.0 |
| Claude Code | 2.1.319 |
| Codex | 0.166.0 |
| Antigravity (agy) | 1.5.2 |
| OpenCode | 2.2.3 |

## Claude

**Resultado**: aprovado

- **Versão do CLI**: Claude Code 2.1.319 (subcomandos não interativos em `F:\Projetos\starcode-sandbox`; conferências em sessões `claude -p` novas). O usuário autorizou a remoção da instalação anterior (`starcode@starcode` 0.1.0, marketplace de pasta local `F:\Projetos\StarCode`).
- **Comandos**: `claude plugin uninstall starcode@starcode`; `claude plugin marketplace remove starcode`; `claude plugin marketplace add freire-andre/starcode@feature/fase-6-release` (a sintaxe `@ref` funcionou: clonou `https://github.com/freire-andre/starcode.git` no ref); `claude plugin install starcode@starcode`.
- **Banner**: sessão nova, o hook de SessionStart entregou o banner: `StarCode · Diário do Capitão` / `Repositório: starcode-sandbox · ramo chore/starcode-specs · modo Git: 2 ...` / `Config do usuário: ✅ válido` / `Config do repositório: ✅ válido (time PROJ, ramo base main)` / `Orca: ✅ disponível` / `Trabalho em andamento: ...` / `Tripulação ativa: ...`. No Claude o banner não traz a linha `CLI: claude` (só `--cli` a imprime, usado pelos outros CLIs); o roteiro foi corrigido.
- **Skills**: `starcode:data`, `starcode:engajar`, `starcode:laforge`, `starcode:mccoy`, `starcode:q`, `starcode:setup`, `starcode:spock`, `starcode:troi` (8).
- **Bloqueio de push forçado**: `git push --force origin main` bloqueado antes de executar: `PreToolUse:Bash hook error: StarCode bloqueou `git push` forçado (--force, -f, --force-with-lease, +refspec ou --mirror). Reescrever o histórico remoto é proibido no fluxo. Se o usuário pediu isso de forma explícita, peça que ele mesmo rode o comando no terminal.`
- **Versão do plugin**: `claude plugin list` mostra `starcode@starcode` 1.0.0, escopo user, enabled; marketplace `starcode` com fonte `GitHub (freire-andre/starcode@feature/fase-6-release)`.

## Codex

**Resultado**: aprovado

- **Versão do CLI**: codex-cli 0.166.0 (`codex exec` em `F:\Projetos\starcode-sandbox`, sem flag de bypass). O usuário autorizou a remoção do marketplace `starcode` anterior (apontava para `F:\Projetos\StarCode`); não havia plugin `starcode` instalado.
- **Comandos**: `codex plugin marketplace remove starcode`; `codex plugin marketplace add freire-andre/starcode --ref feature/fase-6-release` (clonou `https://github.com/freire-andre/starcode.git#feature/fase-6-release`); `codex plugin add starcode@starcode`.
- **Trust (`/hooks`)**: antes do trust, o SessionStart do `starcode` falhou e nenhum banner chegou. O usuário abriu `/hooks` e aprovou os 3 hooks de `starcode@starcode` (`pre_tool_use:0:0`, `pre_tool_use:0:1`, `session_start:0:0`; `~/.codex/config.toml` ganhou os `trusted_hash` novos). O agente não deu o trust.
- **Banner**: após o trust, o contexto de SessionStart trouxe: `StarCode · Diário do Capitão` / `Repositório: starcode-sandbox · ramo chore/starcode-specs · modo Git: 2 ...` / `Config do usuário: ✅ válido` / `Config do repositório: ✅ válido (time PROJ, ramo base main)` / `Orca: ✅ disponível` / `Linear: ✅ ...` / `Tripulação ativa: ...` / `CLI: codex` / `Indisponível neste CLI: linear_mcp → issue-mãe pelo orca linear` / `Indisponível neste CLI: subagent_model → Q por worker da Orca`. Sem o aviso `Hooks do Codex sem trust`.
- **Skills**: `starcode:data`, `starcode:engajar`, `starcode:laforge`, `starcode:mccoy`, `starcode:q`, `starcode:setup`, `starcode:spock`, `starcode:troi` (8).
- **Bloqueio de push forçado**: `git push --force origin main` bloqueado: `Command blocked by PreToolUse hook: StarCode bloqueou `git push` forçado (--force, -f, --force-with-lease, +refspec ou --mirror). Reescrever o histórico remoto é proibido no fluxo. Se o usuário pediu isso de forma explícita, peça que ele mesmo rode o comando no terminal.`
- **Versão do plugin**: `codex plugin list` mostra `starcode@starcode` 1.0.0, installed, enabled, fonte `~\.codex\.tmp\marketplaces\starcode\dist\codex`.
- **Observações**: avisos alheios, não corrigidos: `hooks.json` do plugin `fala` com campo `modules` desconhecido; `features.experimental_use_rmcp_client` ignorado.

## Antigravity

**Resultado**: aprovado

- **Versão do CLI**: agy 1.5.2 (sessões `agy --dangerously-skip-permissions -p`, em repositório descartável com `origin` apontando para um bare local). Clone novo do GitHub privado em `C:/Users/freir/starcode-aceite` (sem espaço, ref `feature/fase-6-release`, commit `9b99f56`, `VERSION` 1.0.0). O usuário autorizou a remoção da instalação anterior (`starcode` 0.1.0; `starcode-hello` e os demais plugins ficaram).
- **Comandos**: `agy plugin uninstall starcode`; `git clone -b feature/fase-6-release https://github.com/freire-andre/starcode.git C:/Users/freir/starcode-aceite`; `python tools/install_local.py --cli antigravity` (validação passou; 8 skills, 1 rule, 2 hooks; instalado em `~/.gemini/config/plugins/starcode`).
- **Banner**: sessão nova, o banner chegou por `injectSteps`: `StarCode · Diário do Capitão` / `Repositório: work · ramo main · modo Git: não definido ...` / `Config do usuário: ✅ válido` / `Orca: ✅ disponível` / `Linear: ✅ ...` / `Tripulação ativa: ...` / `CLI: antigravity` / `Indisponível neste CLI: linear_mcp ...` / `Indisponível neste CLI: subagent_model ...`.
- **Skills**: `agy plugin list` mostra `starcode` com 8 skills (`data`, `engajar`, `laforge`, `mccoy`, `q`, `setup`, `spock`, `troi`), 1 rule e `hooks 2` (`starcode-banner`, `starcode-guard`); a sessão também listou as skills.
- **Bloqueio de push forçado**: `git push --force origin main` negado: `tool call denied by pre-tool hook: StarCode bloqueou `git push` forçado (--force, -f, --force-with-lease, +refspec ou --mirror). ...` O bare de teste continuou em `8718524`. Na 1ª tentativa o próprio modelo recusou sem rodar o comando; na 2ª, com o pedido explícito, o hook negou.
- **Versão do plugin**: `agy plugin list` mostra `starcode` 1.0.0, enabled.
- **Reinstalação**: depois do aceite, com a confirmação do usuário, `python tools/install_local.py --cli antigravity` rodado de `F:/Projetos/StarCode` (substituiu a instalação; o checkout principal está em 0.1.0, então `agy plugin list` voltou a mostrar `starcode` 0.1.0).

## OpenCode

**Resultado**: aprovado

- **Versão do CLI**: OpenCode 2.2.3 (`opencode run` em repositório descartável). `VERSION` do clone instalado: 1.0.0. Modelo gratuito `openrouter/nvidia/nemotron-3.5-super-vl:free`; os modelos `opencode/*-free` testados deram `Free usage limit reached` e nenhum modelo pago foi usado. O usuário autorizou a remoção da instalação anterior.
- **Comandos**: removidos `~/.config/opencode/plugins/starcode.js`, os 8 `commands/sc-*.md` e as 8 entradas `skills.paths` de `F:\Projetos\StarCode\dist\opencode\skills\*`; `git clone -b feature/fase-6-release https://github.com/freire-andre/starcode.git C:/Users/freir/starcode-aceite`; `python tools/install_local.py --cli opencode`.
- **Banner**: n/a, o OpenCode não tem banner por hook (F5-3); vale o fallback `/sc-setup` e `/sc-engajar`.
- **Skills**: `commands/` ganhou os 8 `sc-*.md` (inclui `sc-engajar` e `sc-setup`); a sessão listou `engajar`, `laforge`, `mccoy`, `q`, `setup`, `spock`, `troi`. Depois do install, `skills.paths` ficou só com as 8 skills do clone novo (`C:\Users\freir\starcode-aceite\dist\opencode\skills\*`), sem nenhuma de `F:\Projetos\StarCode` (R17). Prova de R17: com o `skills.paths` contendo as 8 entradas de `F:ProjetosStarCode`, `python tools/install_local.py --cli opencode --dry-run` rodado em `C:/Users/freir/starcode-aceite` (`9b99f56`, com a T1) imprime `[dry-run] remover 8 e gravar 8 caminhos de skill do StarCode em C:\Users\freir\.config\opencode\opencode.json`: o install do clone substitui, não acumula. O acúmulo visto (16 entradas) veio do install rodado de `F:/Projetos/StarCode`, que está na `main` (0.1.0, sem a T1).
- **Bloqueio de push forçado**: `git push --force origin main` falhou antes de executar: `StarCode bloqueou `git push` forçado (--force, -f, --force-with-lease, +refspec ou --mirror). ...` O bare de teste continuou em `8718524`. Na 1ª tentativa o modelo recusou sozinho; na 2ª, com o pedido explícito, o hook bloqueou.
- **Versão do plugin**: `VERSION` 1.0.0 no clone instalado; `plugins/starcode.js` com `STARCODE_ROOT` apontando para o clone.
- **Reinstalação**: depois do aceite, com a confirmação do usuário, `python tools/install_local.py --cli opencode` rodado de `F:/Projetos/StarCode`; as 8 entradas do clone de aceite saíram do `skills.paths`, que ficou só com `F:\Projetos\StarCode\dist\opencode\skills\*`, e `STARCODE_ROOT` voltou para `F:/Projetos/StarCode/dist/opencode`.

## Dia de missão

**Resultado**: pendente
