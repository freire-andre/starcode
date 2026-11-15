**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
COMMENT. O `q-check` relata certo renomeação entre permitidos e de/para fora, acento (`core.quotepath=off`), diretório novo (lista cada arquivo), `--root` em subdiretório, slug com `.` e `+`, outra feature, `captures/x.png` contra `x.running.png` e apagado no índice; nunca altera a árvore. Dois defeitos reais: caminho permitido com espaço sai entre aspas no porcelain e vira falso "fora da lista" (W1), e o passo 4 do `execute.md` grava `--dispatched` no Handoff depois do commit e antes do `worker-start`, o que suja a árvore do Q e faz o passo 7 mandar restaurar o próprio Handoff (W2). C1, C4 e C5 comparam a linha inteira; C6 ainda usa trechos (W4). Escada verde, 0 candidatos de bypass, `dist/` em dia. Arquivos mecânicos fora do review: `dist/` (5 alvos), `.specs/lessons.json`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/dispatch.py:494 | porcelain v1 sem `-z` põe entre aspas caminho com espaço; `captures/tela inicial.running.png` (permitido) sai como "fora da lista" e o passo 7 manda apagá-lo | scripts/dispatch.py:494, :507; https://git-scm.com/docs/git-status; sonda: arquivo novo `captures/tela inicial.running.png` → `fora da lista: ?? ".specs/.../tela inicial.running.png"`, exit=1 | aberto (confirmed) |
| W2 | 🟠 should-fix | skills/engajar/references/execute.md:144 | `--dispatched "Q · <sha>"` grava o Handoff depois do commit do passo 2 e antes do `worker-start`, no mesmo worktree do Q; o passo 7 manda restaurá-lo | execute.md:137, :144, :164; sonda: `handoff.py set demo --phase review` + commit, `--dispatched`, Q escreve `verification.md` → `fora da lista:  M .specs/features/demo/spec.md`, exit=1 | aberto (confirmed) |
| W3 | 🟡 nit | scripts/dispatch.py:1001 | sem git no PATH a saída é 2, mas a mensagem é `dispatch: arquivo não encontrado: [WinError 2] ...`, sem nomear o git nem seguir R6 | scripts/dispatch.py:1001; sonda: `PATH=/nonexistent` → exit=2 | aberto (confirmed) |
| W4 | 🟡 nit | tests/test_dispatch_qcheck.py:118 | C6 confere trechos (Decisão, Motivo) e só presença (Problema, Por que não é bug), contra a L2 | tests/test_dispatch_qcheck.py:127, :133 | aberto (confirmed) |
| W5 | 🟡 nit | tests/test_dispatch_qcheck.py:80 | `test_q_check_renomeacao` não cobre destino fora da lista, embora o DECISIONS.md:1063 diga que sim; o código está certo | tests/test_dispatch_qcheck.py:80; DECISIONS.md:1063; sonda: `git mv verification.md fora.md` → `fora da lista: R  ... -> .../fora.md`, exit=1 | aberto (confirmed) |

Perguntas (fora da contagem):
- Arquivo tirado do índice com `git rm --cached` sai em duas linhas (`D ` e `??`) e conta como 2 arquivos. É o esperado de "uma linha por caminho" do R4?
- O slug não é validado: `q-check ""` e `q-check demo/../demo` tratam tudo como fora da lista (exit 1, só ruído). Vale recusar slug que não exista em `.specs/features/`?

Sondas sem achado (repositórios Git temporários, `dispatch.py` do ramo): renomeação `verification.md → captures/v.running.png` sai 0; `verification.md → fora.md` e `spec.md → captures/n.running.png` saem 1 com a linha `R`; cópia não aparece no `git status` mesmo com `status.renames=copies` (o ramo `C` é inócuo); `ação.md` sai sem aspas; `novo/d/x` e `novo/y` listados um a um; `--root sub` usa caminhos da raiz (porcelain v1 sempre relativo à raiz); slug `a.b+c` não aceita `aXbbc` nem `aXb+c`; `captures/x.png`, `captures/.running.png` e `captures/sub/y.running.png` saem fora da lista; `.git/HEAD` corrompido sai 2 com `ERRO: git status falhou em <pasta>: fatal: ...`.

Provas e `execute.md`: C1 compara a linha exata de R1 dentro de `## Rules` (tests/test_dispatch.py e tests/test_q_skill.py); C4 compara o stderr inteiro; C5 compara as linhas do comando de fase, do passo anterior e do `q-check` logo após o `worker_done`. A ordem do `execute.md` segue provas → `handoff --phase review` → commit do Handoff → `worker-start` do Q → `worker_done` → `q-check` → restaurar extras → commit da verificação, com a exceção do `--dispatched` (W2).

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `python scripts/check_decisions.py`: OK (DECISIONS.md em 81e1bb24, depois de f5af8113).
- `claude plugin validate dist/claude --strict`: Validation passed.
- `python -m unittest test_dispatch test_dispatch_qcheck test_q_skill test_skills_exec` (em `tests/`): 65 testes, OK.
- `git diff main...HEAD | python scripts/review/scan_bypasses.py`: 0 candidatos.
- `review_gate.py review.json`: exit 0.

## Pesquisa
- https://git-scm.com/docs/git-status (porcelain v1: caminho com espaço é posto entre aspas; `-z` não põe aspas, separa por NUL e inverte a ordem na renomeação; caminhos sempre relativos à raiz).
