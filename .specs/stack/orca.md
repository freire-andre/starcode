# orca
**Context7 ID**: orca-cli
**Project version**: 1.4.268
**Doc version**: 1.4.268
**Fetched**: 2026-11-21
**Verified**: não verificada (orca --version = 1.4.268, comportamento observado)
## Summary
- Resolução do CLI (F10-14): o `orca` é um aplicativo Electron; para rodar como CLI ele usa `ELECTRON_RUN_AS_NODE`. Por isso o StarCode acha o executável pelo PATH com `shutil.which` (no Windows acha o `orca.cmd`) e chama sem shell, sem stdin e com tempo limite (`scripts/orca_cli.py`).
- Ambiente: o filho não herda `NODE_*`, `ELECTRON_RUN_AS_NODE`, `ORCA_NODE_OPTIONS` nem `ORCA_CLI_COMMAND` (o `orca_cli.env()` tira as chaves); no Windows `USERPROFILE`, `APPDATA` e `LOCALAPPDATA` são completados a partir da pasta do usuário quando faltam.
- `--current` (F10-8): em `orca linear issue --current` e comandos parecidos, "atual" é o terminal que chama; vindo de um worker ou de outro terminal, o resultado é o do terminal de quem chamou, não o do coordenador.
- Falha com `ok:false`: com `--json` a resposta vem como `{"ok": false, "error": {"message": "..."}}` e o código de saída é diferente de 0; a mensagem de erro está em `error.message` (também pode vir como texto em `error`, no stderr ou no stdout).
- `orca plugin test` e `orca plugin check` só rodam com o plugin no mesmo drive da instalação da Orca; fora dele falham com `cannot import "./orca-runtime.mjs"`. Rode o gate num worktree no mesmo drive.
