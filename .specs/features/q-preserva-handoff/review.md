**Round**: 2
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE. As sondas da rodada 1 foram refeitas em repositórios Git temporários com o `dispatch.py` do ramo (8759cd9). W1, W2, W3 e W5 estão resolvidos. W4 está parcial: segue como nit e não impede a aprovação. A troca para `-z` não regrediu em nenhum dos casos sondados, e não há blocker novo. Escada verde: 68 testes, 0 candidatos de bypass, `dist/` em dia.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/dispatch.py:495 | caminho com espaço virava falso "fora da lista" | scripts/dispatch.py:495, :507 (`--porcelain=v1 -z`, separa por NUL); sonda: `captures/tela inicial.running.png` novo, com e sem `verification.md` alterado, exit=0 (na rodada 1 dava 1); com `--root sub`, exit=0; teste `test_q_check_caminho_com_espaco` | resolvido (8759cd9), confirmado por sonda |
| W2 | 🟠 should-fix | skills/engajar/references/execute.md:137 | `--dispatched` gravado depois do commit do Handoff sujava a árvore do Q | execute.md:137 (`--phase review --dispatched "Q · <sha of I>"` no mesmo commit), :144; sonda: passos 2 a 7 seguidos à risca (provas commitadas, `handoff.py set --phase review --dispatched`, commit, `q-brief`, `crew_live.py set q 1`, Q escreve `verification.md`, `set q 0`, linha `**Verifier**`): a árvore fica só com `?? verification.md` e o `q-check` dá exit=0 | resolvido (8759cd9), confirmado por sonda |
| W3 | 🟡 nit | scripts/dispatch.py:498 | sem git no PATH, a mensagem fugia do formato R6 | scripts/dispatch.py:498-499; sonda: PATH só com o Python dá exit=2, `ERRO: git status falhou em <pasta>: git não encontrado`; teste `test_q_check_sem_git_sai_2` | resolvido (8759cd9), confirmado por sonda |
| W4 | 🟡 nit | tests/test_dispatch_qcheck.py:160 | C6 conferia trechos | :150 (um de cada campo), :152-158 (Problema e Motivo com `assertEqual` da linha inteira); Decisão segue com três `assertIn` de trecho (:160-162) e Por que não é bug só com `startswith` (:163) | parcial, aberto (nit, não impede) |
| W5 | 🟡 nit | tests/test_dispatch_qcheck.py:91 | faltava o teste de renomeação para fora | `test_q_check_renomeacao_para_fora` (:91); sonda: `git mv verification.md fora.md` dá exit=1, `fora da lista: R  .../verification.md -> .../fora.md` | resolvido (8759cd9), confirmado por sonda |

Regressões da troca para `-z`, sondadas sem achado (cada caso em um repositório temporário):
- **Renomeação.**
  - `verification.md → screens.md`: exit=0.
  - `src/a.py → src/b.py`: exit=1 com a linha `R  src/a.py -> src/b.py`, a mesma com destino `src/b c.py`.
  - Renomeação seguida de `verification.md` e `captures/x.running.png` alterados: a renomeação é listada sozinha e os registros seguintes continuam alinhados.
  - Renomeação com status `RD` de `captures/q"r.running.png` para `src/q"r.py`: listada com a origem na ordem certa, exit=1.
  - `rm verification.md` seguido de `mv tasks.md verification.md`: o git mostra `D tasks.md`, exit=1.
- **Cópia.** Com `status.renames=copies`, o `git status` não marca cópia. Um `screens.md` novo com o conteúdo de outro arquivo sai como `A`, exit=0, o que é correto porque a origem não muda.
- **Nomes.** Os nomes abaixo foram postos no índice com `core.protectNTFS=false`, porque o Windows recusa esses caracteres na árvore.
  - `captures/ação.running.png`: exit=0. `src/ção.py`: exit=1, sem aspas.
  - Aspas, tab, quebra de linha e ` -> ` no nome de uma captura: exit=0.
  - Os mesmos caracteres em `src/`: exit=1, um registro por caminho, sem aspas nem escape.
  - `verification.md\nx`: exit=1, porque não é o permitido.
- **Arquivos e diretórios.**
  - Diretório novo: cada arquivo é listado.
  - Apagado na árvore (` D`) e no índice (`D `): exit=1.
  - `verification.md` apagado: exit=0.
  - `captures/s/x.running.png`: fora da lista.
- **`--root`.** `--root sub` com `.specs` na raiz: `verification.md` e uma captura com espaço dão exit=0, e `sub/a` alterado dá exit=1.
- **Repositório sem commits.** Tudo aparece como `??` e é listado, exit=1.

Observações fora da contagem (a rodada 2 só aceita blocker novo):
- `--root` apontando para um projeto com `.specs` dentro de um subdiretório do repositório (`pkg/.specs/...`) lista o próprio `verification.md` como fora da lista. O porcelain v1 sempre dá caminhos relativos à raiz, com `-z` ou sem ele, então isso não é regressão desta correção. Só importa se um projeto StarCode puder morar num subdiretório do repositório.
- No caminho sem worker (`self-verified`), o passo 4 manda `--dispatch-remove Q` "after the subagent ends" (execute.md:144). Se o Picard fizer isso antes do `q-check` do passo 7, o `tasks.md` aparece como fora da lista. Sonda: exit=1 com ` M .../tasks.md`. Vale dizer que a remoção vem depois do `q-check` e do commit de `verification.md`.

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `python scripts/check_decisions.py`: OK (DECISIONS.md atualizado no mesmo commit 8759cd95).
- `python -m unittest test_dispatch test_dispatch_qcheck test_q_skill test_skills_exec` (em `tests/`): 68 testes, OK.
- `git diff main...HEAD | python scripts/review/scan_bypasses.py`: 0 candidatos.
- `review_gate.py review.json`: exit 0.

## Pesquisa
- https://git-scm.com/docs/git-status (porcelain v1 com `-z`: sem aspas, registros separados por NUL, na renomeação o caminho antigo vem no registro seguinte; caminhos sempre relativos à raiz).

---

# Rodada 1

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
