# Roteiro de aceite da Fase 5: OpenCode

Sessão real no sandbox `F:\Projetos\starcode-sandbox`, com o `starcode` instalado deste worktree.

## Instalação

1. `python tools/install_local.py --cli opencode` a partir deste worktree (confirme a cópia; grava `~/.config/opencode/plugins/starcode.js` com caminhos absolutos).
2. Confira que o plugin está na pasta global (não use `OPENCODE_CONFIG_DIR`: o hook não dispara, F0-3).
3. Anote a versão (`opencode --version`) e use modelo gratuito, nunca pago.

## Bloqueio

Num repositório sandbox (`F:\Projetos\starcode-sandbox`, worktree próprio), peça ao agente:

1. `git push --force origin main`: deve ser bloqueado, com o motivo do `git_guard` visível na sessão.
2. Um commit com segredo de teste. Monte o arquivo em tempo de execução, sem escrever o valor inteiro no roteiro:
   `printf 'API_%s=%s\n' KEY q8Zr2Lm9Xv4Tn7Wp1Ks6Yd3 > segredo.txt`, depois `git add segredo.txt` e `git commit -m "chore: teste"`.
   Deve ser bloqueado, com o motivo do `secret_scan` visível. O valor é de teste, não é credencial real.

Apague `segredo.txt` ao terminar.

## Fluxo normal

Rode cada comando na sessão; todos devem passar sem bloqueio e sem aviso `StarCode hook:`:

- `git status`
- `git add .`
- `git commit -m "feat: x"` (sem segredo)
- `git switch -c feature/x`
- `git merge --no-ff feature/x` (no ramo de integração)
- `orca linear issue SC-1 --json`
- `python scripts/gates/run_gates.py ticket x`
- `python -m unittest discover -s tests -v`

## Banner

n/a: o OpenCode não tem banner por hook (F5-3); `banner_hook` continua `unavailable` com o fallback atual.

## Evidência

Copie para a seção OpenCode de `docs/aceite/fase-5.md`: versão do OpenCode, plugin na pasta global (caminho), resposta do bloqueio do push forçado e do segredo, comandos normais que passaram e `**Resultado**: aprovado` ou `reprovado (<passo>)`. Sem banner.
