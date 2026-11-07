# Roteiro de aceite da Fase 6: OpenCode

Instalação limpa a partir do GitHub privado (`freire-andre/starcode`), no sandbox `F:\Projetos\starcode-sandbox`.
Enquanto o PR da fase não foi mesclado, use o ref `feature/fase-6-release` (o Picard faz o push, com a confirmação do usuário).

## Remoção da instalação atual

Execute cada comando só com a confirmação do usuário:

1. Apague `~/.config/opencode/plugins/starcode.js`.
2. Em `~/.config/opencode/opencode.json`, remova as entradas de `skills.paths` que apontam para `dist/opencode/skills/*` do StarCode.
3. Apague os comandos `sc-*` de `~/.config/opencode/commands/` gravados pelo instalador.

## Instalação

1. `git clone -b feature/fase-6-release https://github.com/freire-andre/starcode.git`
2. `cd starcode`
3. `python tools/install_local.py --cli opencode`
4. Use só modelo gratuito no OpenCode, nunca pago.

## Conferências

1. **Banner**: n/a: o OpenCode não tem banner por hook (F5-3); vale o fallback (`/sc-setup` e `/sc-engajar`).
2. **Skills carregadas**: `/sc-engajar` e `/sc-setup` existem e as skills do StarCode aparecem na sessão.
3. **Bloqueio de push forçado**: `git push --force origin main` é bloqueado com `StarCode bloqueou` (hooks: ok).
4. **Versão 1.0.0**: o `VERSION` do clone instalado é 1.0.0; anote também `opencode --version`.

## Evidência

Copie para a seção OpenCode de `docs/aceite/fase-6.md`: versão do CLI, comandos de remoção e instalação usados, resultado de cada conferência e `**Resultado**: aprovado` ou `reprovado (<passo>)`.
