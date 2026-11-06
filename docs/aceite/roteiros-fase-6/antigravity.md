# Roteiro de aceite da Fase 6: Antigravity

Instalação limpa a partir do GitHub privado (`freire-andre/starcode`), no sandbox `F:\Projetos\starcode-sandbox`.
Enquanto o PR da fase não foi mesclado, use o ref `feature/fase-6-release` (o Picard faz o push, com a confirmação do usuário).

## Remoção da instalação atual

Execute cada comando só com a confirmação do usuário:

1. `agy plugin uninstall starcode`
2. Confirme com `agy plugin list` que o `starcode` saiu.

## Instalação

1. `git clone -b feature/fase-6-release https://github.com/freire-andre/starcode.git` em um caminho sem espaço.
2. `cd starcode`
3. `python tools/install_local.py --cli antigravity`

## Conferências

1. **Banner**: sessão nova: o banner chega por `injectSteps` e termina em `CLI: antigravity`.
2. **Skills carregadas**: `agy plugin list` mostra `starcode` e a sessão carrega as skills do StarCode (`hooks 2`).
3. **Bloqueio de push forçado**: `git push --force origin main` é negado com `StarCode bloqueou` (hooks: ok).
4. **Versão 1.0.0**: `agy plugin list` mostra `starcode` 1.0.0.

## Evidência

Copie para a seção Antigravity de `docs/aceite/fase-6.md`: versão do CLI, comandos de remoção e instalação usados, resultado de cada conferência e `**Resultado**: aprovado` ou `reprovado (<passo>)`.
