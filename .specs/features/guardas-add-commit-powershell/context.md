# Guardas para add+commit e PowerShell: Context

**Size**: MEDIUM
**Risk triggers**: Security
**Source request**: "proximo passo" → passo 8 do primeiro corte: itens 2.1 e 2.3 de `starcode-triagem-v2-2026-11-13.md` (seção 5), detalhados na seção 4 da triagem v1

## Problem
- **2.1:** quando o mesmo comando faz `git add` antes de `git commit` (ex.: `git add -A && git commit -m x`), o scan de segredos olha só o segmento `commit` e lê `git diff --cached`. Na hora do hook o `add` ainda não rodou, então o diff está vazio e um segredo entra no commit sem bloqueio.
- **2.3:** os hooks `git_guard.py` e `secret_scan.py` estão registrados só com o matcher `Bash`. No Windows, a ferramenta PowerShell do Claude Code roda comandos de shell sem passar por eles; sem Git Bash, a ferramenta Bash nem existe. `git push --force` ou um commit com segredo pedidos pelo PowerShell passam.

## Users
O dono do repositório no Windows e qualquer sessão do StarCode no Claude Code, principalmente com o piloto automático, em que os hooks são a única rede entre os checkpoints humanos.

## Success
- `git add -A && git commit -m x` com segredo falso em arquivo modificado e em arquivo novo é negado; sem segredo, passa.
- Um `git push --force` ou um commit com segredo falso que chega pela ferramenta PowerShell recebe a mesma negação que receberia pela ferramenta Bash.

## Constraints
- Congelamento D-i: nenhuma opção, comando ou perfil novo.
- Nunca editar `dist/` à mão: regenerar com `python tools/build.py`.
- Os guardas só podem ficar mais rígidos, nunca mais permissivos.

## Scope Notes
- Dentro: 2.1 (scan do que o `add` do mesmo comando vai incluir) e 2.3 (matcher `Bash|PowerShell` no adaptador do Claude).
- Fora: 2.2 (heredoc), 2.4 (outros comandos `gh`), 2.5 (handlers destrutivos e modo 1), 2.6 (falsos positivos), um leitor próprio de sintaxe PowerShell e a sessão real em `docs/aceite/` (vira issue de acompanhamento).

## Gray Areas

| Item | Options | User answer | Date |
|---|---|---|---|
| O que o scan lê quando há `git add` antes do `commit` | só o que o add vai incluir / árvore inteira | só o que o add vai incluir: diff dos caminhos passados ao `add` mais os arquivos novos neles; com `-A`, `--all` ou `.`, tudo ("Só o que o add vai incluir") | 2026-11-14 |
| Como o PowerShell é lido | mesmo leitor de comandos / leitor próprio | mesmo tokenizador atual, que já separa `;`, `&&` e `\|`; sintaxe exclusiva do PowerShell fica fora ("Mesmo leitor de comandos") | 2026-11-14 |
| Prova do aceite do 2.3 | teste agora + sessão real após o release / sessão real antes do merge | teste automatizado com o payload documentado da ferramenta PowerShell e o `hooks.json` gerado; sessão real em `docs/aceite/` após o release, em issue de acompanhamento ("Teste agora, sessão real após o release") | 2026-11-14 |
| Adaptadores que ganham o matcher novo | só Claude / todos | só o Claude: Codex, OpenCode e Antigravity não têm ferramenta PowerShell. Default (não perguntado) | 2026-11-14 |
| `add` em outro diretório (`git -C <dir> add`) | segue o `-C` / ignora | segue o `-C`, como o `commit` já faz. Default (não perguntado) | 2026-11-14 |
| `add` e `commit` em comandos separados por `;` ou `\|\|` | só `&&` / qualquer separador | qualquer separador: na dúvida, o scan lê mais. Default (não perguntado) | 2026-11-14 |

## Implicit Requirements

| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | Caminho do `add` inexistente ou fora do repositório não quebra o hook: é ignorado, e o resto do scan segue |
| Failure and partial failure | Falha do `git` ao listar o que o `add` incluiria não libera o commit em silêncio: mantém o comportamento atual do `staged_findings` |
| Observability | A negação nomeia o arquivo e a linha do segredo, no mesmo formato de hoje, também quando o achado vem de arquivo novo |

Demais dimensões: N/A para este escopo.

## Facts Found
- `hooks/scripts/secret_scan.py:171-200` `evaluate`: só o segmento `git commit` chama `staged_findings`, que lê `diff --cached` (`:123-145`); `commit -a`/`--all` já lê `diff HEAD`. Arquivo novo não rastreado não aparece em nenhum dos dois.
- `tools/build.py:268-277` `base_hooks`: `PreToolUse` com `matcher: "Bash"` para `git_guard.py` e `secret_scan.py`; usado por `claude_hooks` (`:281`) e `codex_hooks` (`:293`).
- `hooks/scripts/git_guard.py:296-297` lê `tool_input.command` sem olhar `tool_name`; o `secret_scan.py` usa a mesma entrada. Basta o matcher para cobrir o PowerShell.
- `git_guard.py:32` já conhece `pwsh`/`powershell` como shells aninhados.
- Documentação do Claude Code (Context7, `/websites/code_claude`, páginas hooks e tools-reference): a ferramenta chama `PowerShell`, os campos são os do Bash com o comando em `command`, e a recomendação é o matcher `Bash|PowerShell`; no Windows sem Git Bash a ferramenta Bash não é registrada.
- Testes existentes: `tests/test_secret_scan.py`, `tests/test_git_guard.py`, `tests/test_build.py`.
