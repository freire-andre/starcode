# Roteiro de aceite da Fase 6: Claude

Instalação limpa a partir do GitHub privado (`freire-andre/starcode`), no sandbox `F:\Projetos\starcode-sandbox`.
Enquanto o PR da fase não foi mesclado, use o ref `feature/fase-6-release` (o Picard faz o push, com a confirmação do usuário).

## Remoção da instalação atual

Execute cada comando só com a confirmação do usuário:

1. `claude plugin uninstall starcode@starcode` (ou `/plugin uninstall starcode@starcode`)
2. `claude plugin marketplace remove starcode`

## Instalação

1. `claude plugin marketplace add freire-andre/starcode@feature/fase-6-release` (sintaxe `@ref` confirmada; clona por HTTPS)
2. `claude plugin install starcode@starcode`
3. Reinicie a sessão do Claude Code.

## Conferências

1. **Banner**: abra uma sessão nova no sandbox: o hook de SessionStart entrega o banner (`StarCode · Diário do Capitão` até `Tripulação ativa`). No Claude o banner não tem a linha `CLI: claude`: só os outros CLIs passam `--cli`.
2. **Skills carregadas**: a lista de skills da sessão mostra as do StarCode (`engajar`, `setup`, `spock`, `troi`, `data`, `laforge`, `mccoy`, `q`).
3. **Bloqueio de push forçado**: peça ao agente `git push --force origin main`: deve ser bloqueado com `StarCode bloqueou` (hooks: ok).
4. **Versão 1.0.0**: `claude plugin list` lista `starcode` na versão 1.0.0.

## Evidência

Copie para a seção Claude de `docs/aceite/fase-6.md`: versão do CLI, comandos de remoção e instalação usados, resultado de cada conferência e `**Resultado**: aprovado` ou `reprovado (<passo>)`.
