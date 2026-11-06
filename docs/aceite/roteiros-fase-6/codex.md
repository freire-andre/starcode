# Roteiro de aceite da Fase 6: Codex

Instalação limpa a partir do GitHub privado (`freire-andre/starcode`), no sandbox `F:\Projetos\starcode-sandbox`.
Enquanto o PR da fase não foi mesclado, use o ref `feature/fase-6-release` (o Picard faz o push, com a confirmação do usuário).

## Remoção da instalação atual

Execute cada comando só com a confirmação do usuário:

1. `codex plugin remove starcode@starcode` (ou o comando equivalente de `codex plugin --help`)
2. `codex plugin marketplace remove starcode` (remove o marketplace `starcode` local, inclusive o de outra fonte)

## Instalação

1. `codex plugin marketplace add freire-andre/starcode --ref feature/fase-6-release`
2. `codex plugin add starcode@starcode`
3. Abra `/hooks` no Codex: **o usuário** aprova (trust) os hooks do `starcode`. O agente nunca dá o trust.

## Conferências

1. **Banner**: sessão nova no sandbox: o banner chega como contexto (`additionalContext`) e termina em `CLI: codex`. Sem trust, aparece o aviso `Hooks do Codex sem trust`.
2. **Skills carregadas**: a lista de skills da sessão mostra as do StarCode.
3. **Bloqueio de push forçado**: depois do trust, `git push --force origin main` é bloqueado com `StarCode bloqueou` (hooks: ok).
4. **Versão 1.0.0**: `codex plugin list` mostra `starcode` 1.0.0.

## Evidência

Copie para a seção Codex de `docs/aceite/fase-6.md`: versão do CLI, comandos de remoção e instalação usados, resultado de cada conferência e `**Resultado**: aprovado` ou `reprovado (<passo>)`.
