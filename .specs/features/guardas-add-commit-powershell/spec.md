# Guardas para add+commit e PowerShell: Spec

**Approved**: 2026-11-14 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: Security
**Status**: Approved
**Linear**: SC-178
**May change**: hooks/scripts/secret_scan.py, tools/build.py, tests/test_secret_scan.py, tests/test_git_guard.py, tests/test_build.py, DECISIONS.md, dist/

## Context
Itens 2.1 e 2.3 da triagem (seção 4 da v1; seção 5 da v2, `starcode-triagem-v2-2026-11-13.md`, fora do Git). Discovery em `context.md`. O `secret_scan.py` (`evaluate`, `:171-200`) só escaneia no segmento `git commit` e lê `diff --cached`, que está vazio quando o `git add` do mesmo comando ainda não rodou. Os dois guardas são registrados só com o matcher `Bash` (`tools/build.py:268-277`); a ferramenta PowerShell do Claude Code passa por fora deles. Sucesso: `git add -A && git commit -m x` com segredo é negado, e o mesmo pedido pela ferramenta PowerShell recebe a mesma negação que pela Bash.

## Scope
- 2.1: o scan do commit também lê o que um `git add` anterior no mesmo comando vai incluir.
- 2.3: o `hooks.json` do Claude registra os dois guardas com o matcher `Bash|PowerShell`.

## Non-Goals
- 2.2 (heredoc), 2.4 (outros comandos `gh`), 2.5 (handlers destrutivos e modo 1) e 2.6 (falsos positivos).
- Leitor próprio de sintaxe PowerShell (crase, aspas simples literais, operador `&`).
- Matcher novo para Codex, OpenCode e Antigravity.
- A sessão real no Windows registrada em `docs/aceite/` (issue de acompanhamento, após o release).
- Qualquer opção ou comando novo (congelamento D-i).

## Requirements
- **R1** - WHEN um comando tem um segmento `git add` antes de um segmento `git commit`, com qualquer separador (`&&`, `;`, `||`, `|` ou nova linha), THEN the system SHALL escanear, além do que já está no índice, as mudanças em arquivos rastreados (contra `HEAD`) dentro dos caminhos passados ao `add` e o conteúdo inteiro dos arquivos não rastreados e não ignorados dentro desses caminhos.
- **R2** - WHEN o `add` usa `-A`, `--all` ou `.` sem outro caminho THEN the system SHALL escanear todas as mudanças rastreadas e todos os arquivos não rastreados e não ignorados do repositório (no caso de `.`, do diretório do comando).
- **R3** - WHEN o `add` usa `-u` ou `--update` THEN the system SHALL escanear só as mudanças rastreadas dentro dos caminhos, sem arquivos não rastreados.
- **R4** - The system SHALL NOT escanear arquivo fora dos caminhos do `add`: `git add a.py && git commit -m x` com segredo só em `b.py`, modificado ou novo, SHALL passar sem achado.
- **R5** - The system SHALL relatar o achado de arquivo novo no mesmo formato do índice, `<caminho>:<linha>: <tipo> (<mascarado>)`, e um `.env` novo com `<caminho>: arquivo .env no commit (variáveis de ambiente não vão para o Git)`; a allowlist e os lockfiles SHALL valer como no índice.
- **R6** - WHEN o `add` usa `git -C <dir> add` THEN the system SHALL resolver os caminhos e o repositório a partir de `<dir>`.
- **R7** - The system SHALL gerar `dist/claude/hooks/hooks.json` com o primeiro grupo de `PreToolUse` com `matcher` exatamente `Bash|PowerShell`, contendo `git_guard.py` e `secret_scan.py` com os timeouts atuais (15 e 30); o Codex SHALL continuar com `["Bash", "Bash"]` e o Antigravity com `["run_command"]`.
- **R8** - WHEN o payload chega com `tool_name` `PowerShell` e o comando em `tool_input.command` THEN `git_guard.py` e `secret_scan.py` SHALL negar exatamente como negam o mesmo comando com `tool_name` `Bash`.
- **R9** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-178:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**, citando `git add`, `PowerShell` e `Bash|PowerShell`.

## Decisions

| Decisão | Opções | Resposta |
|---|---|---|
| O que o scan lê com `git add` antes do `commit` | só o que o add vai incluir / árvore inteira | approved - user: "Só o que o add vai incluir" |
| Como o PowerShell é lido | mesmo leitor de comandos / leitor próprio | approved - user: "Mesmo leitor de comandos" |
| Prova do aceite do 2.3 | teste agora + sessão real após o release / sessão real antes do merge | approved - user: "Teste agora, sessão real após o release" |

## Edge Cases
- Segredo em arquivo novo e em arquivo modificado com `add -A`: R1, R2 (C1).
- Sem segredo, `add -A && commit` passa: C2.
- `add` de um caminho com segredo em outro: R4 (C4).
- `add -u` com segredo só em arquivo novo: passa (R3, C3).
- `.env` novo adicionado: R5 (C5).
- `git -C sub add -A; git -C sub commit -m x`: R6 (C6).
- Repositório sem commit ainda (`HEAD` inexistente): escaneia índice e não rastreados (C1 roda também sem `HEAD`).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Repositório temporário: segredo falso do GitHub em `README.md` rastreado e modificado e em `app/novo.py` não rastreado; `evaluate("git add -A && git commit -m x")` dá exatamente 2 achados, um começando por `README.md:1:` e outro por `app/novo.py:1:`, ambos com `token do GitHub`; o mesmo vale para `git add . ; git commit -m x` e num repositório sem `HEAD` (R1, R2)
Proof: run unit | test_add_antes_do_commit_escaneia_novo_e_modificado ... ok

**C2** - Mesmo repositório sem segredo nos arquivos: `assertEqual(evaluate("git add -A && git commit -m x"), [])` (R1)
Proof: run unit | test_add_antes_do_commit_sem_segredo_passa ... ok

**C3** - Segredo só em arquivo não rastreado: `assertEqual(evaluate("git add -u && git commit -m x"), [])`; segredo em arquivo rastreado modificado: `git add -u && git commit -m x` dá 1 achado (R3)
Proof: run unit | test_add_update_ignora_nao_rastreados ... ok

**C4** - Segredo em `b.py` (modificado) e em `c.py` (novo); `a.py` limpo e modificado: `assertEqual(evaluate("git add a.py && git commit -m x"), [])`; `git add a.py c.py && git commit -m x` dá exatamente 1 achado, que começa por `c.py:1:` (R1, R4)
Proof: run unit | test_add_so_escaneia_caminhos_passados ... ok

**C5** - `.env` novo e não ignorado: `evaluate("git add -A && git commit -m x")` é exatamente `[".env: arquivo .env no commit (variáveis de ambiente não vão para o Git)"]`; um arquivo novo coberto por `path:` na allowlist não gera achado (R5)
Proof: run unit | test_add_arquivo_novo_env_e_allowlist ... ok

**C6** - Repositório em `sub/` com segredo em arquivo novo; `evaluate("git -C sub add -A; git -C sub commit -m x", cwd=<pai>)` dá exatamente 1 achado (R6)
Proof: run unit | test_add_com_dash_c ... ok

**C7** - `build` gera `dist/claude/hooks/hooks.json` com `[e["matcher"] for e in PreToolUse]` igual a `["Bash|PowerShell", "Skill"]` e o primeiro grupo com exatamente `[('python "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/git_guard.py"', 15), ('python "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/secret_scan.py"', 30)]`; `test_codex_hooks_json_registers_guards_and_banner` continua passando com `["Bash", "Bash"]` (R7)
Proof: run unit | test_claude_hooks_cobrem_powershell ... ok

**C8** - `git_guard.py` com payload `{"tool_name": "PowerShell", "tool_input": {"command": "git push --force origin main"}}` sai com `permissionDecision == "deny"` e o mesmo `permissionDecisionReason` do payload com `tool_name` `Bash` (R8)
Proof: run unit | test_git_guard_nega_push_force_pelo_powershell ... ok

**C9** - `secret_scan.py` com payload `{"tool_name": "PowerShell", "tool_input": {"command": "git add -A; git commit -m x"}, "cwd": <repo>}` e segredo em arquivo novo sai com `permissionDecision == "deny"` e o mesmo motivo do payload com `tool_name` `Bash` (R1, R8)
Proof: run unit | test_secret_scan_nega_commit_pelo_powershell ... ok

**C10** - A entrada `### SC-178:` do `DECISIONS.md` contém `**Problema**`, `**Decisão**`, `**Motivo**` e `**Por que não é bug**`, cada um asserido dentro da entrada, mais `git add`, `PowerShell` e `Bash|PowerShell` (R9)
Proof: run unit | test_decisions_guardas_add_commit_powershell ... ok

## Handoff

**Phase:** done
**Size:** MÉDIA
**Git mode:** 3
**Next:** passo 9 da triagem (1.1)
**Linear:** SC-178
**Integration branch:** feature/guardas-add-commit-powershell
**Last integrated:** 613d5a9
**Dispatched:** none
**Settled:** 2026-11-14: aprovação da spec e issue: "sim"; 2026-11-14: push + PR: "Sim"; 2026-11-14: PR aberto: https://github.com/freire-andre/starcode/pull/54; 2026-11-14: W7/W8 em issue de acompanhamento: "Sim"; 2026-11-14: push + merge após CI: "Push + merge após CI"; 2026-11-14: merge do PR #54: 0415174; 2026-11-14: SC-178 Done: "Sim"
**Attempts:** none
**Reports:** 2026-11-14: T1: scan do add antes do commit (R1-R6), matcher Bash|PowerShell no Claude (R7), C1-C10; ticket gate verde; a5090b9, 613d5a9; 2026-11-14: Q: codex · FAIL, 2 achados em testes (formato integral do achado de arquivo novo; sem check de arquivo novo grande); 893 OK; 2026-11-14: T1-fix: 49fab08 (formato integral; arquivo novo grande); 2026-11-14: Guinan: L2 e L4 recorrentes (confirmed); retro com 3 sugestões; provas e done verdes; 2026-11-14: Worf r1: COMMENT; W1 add -f ignorado, W2 quotepath não ASCII, W3 pathspec :/ (should-fix); W4 stage, W5 pathspec-from-file, W6 binário grande (nit); W7 falha do git libera; W8 commit <caminho> pré-existente; 2026-11-14: acompanhamento: SC-179 (W7, W8); 2026-11-14: W-fix: abbedcd (W1-W6 + 6 testes), c2250c5 (dist); ticket gate verde; 2026-11-14: Worf r2: COMMENT; W2,W4,W5,W6 fechados; W1 parcial (-Af libera ignorado); W3 com regressão (add -A em subdiretório não vê novo na raiz); 2026-11-14: W-fix2: 9a19794 (W1 flags combinadas, W3 raiz, commit do índice em subdiretório), cddaba4 (dist); 2026-11-14: Worf r3: APPROVE; W1 e W3 fechados (57 sondas); provas e done verdes; 2026-11-14: acompanhamento: SC-180 (aceite real no Windows)
**Breaker:** closed
