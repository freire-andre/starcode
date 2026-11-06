# Roteiro de aceite da Fase 5: Codex

Sessão real no sandbox `F:\Projetos\starcode-sandbox`, com o `starcode` instalado deste worktree.

## Instalação

1. `python tools/install_local.py --cli codex` a partir deste worktree (remove um marketplace `starcode` de outra fonte, F4-5).
2. Abra o Codex no sandbox e rode `/hooks`: **o usuário** aprova os hooks do `starcode` (trust). O agente nunca dá o trust (R11).
3. Se o plugin legado `starcode-hello` aparecer, anote (o relatório de concorrentes mostra o comando para removê-lo).
4. Anote a versão: `codex --version`.

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

Abra uma sessão nova no sandbox: o banner deve chegar como contexto da sessão (`additionalContext`), igual ao `banner.py --full --text --cli codex`. Sem trust, deve aparecer `Hooks do Codex sem trust: aprove em /hooks` (R16). Anote o texto recebido.

## Evidência

Copie para a seção Codex de `docs/aceite/fase-5.md`: versão do Codex, passo de trust feito, resposta do bloqueio do push forçado e do segredo, comandos normais que passaram, banner (ou aviso de trust) e `**Resultado**: aprovado` ou `reprovado (<passo>)`. Se `${CLAUDE_PLUGIN_ROOT}` não foi expandido, é reprovação com esse motivo.
