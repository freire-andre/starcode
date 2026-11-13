**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
COMMENT. A regra única `gates_common.effective_may_change` é chamada pelo brief da GRANDE (`with_decisions`), pelo brief da MÉDIA (`spec_brief`) e pelo `check_scope` nos dois caminhos. As recusas da MÉDIA (spec sem `**Linear**:`, ticket de outra feature, ramo ausente, entrada aberta) saem com 2 antes de gravar o Handoff e antes de chamar a Orca, e o `settle` da MÉDIA remove só a entrada `T1`. Um should-fix: o novo `except FileNotFoundError` de `main` também captura o executável ausente (`orca` fora do PATH) depois que o `start` já gravou a entrada `Dispatched`, e o `start` sai com 2, que o `execute.md` lê como recusa sem gravação. Dois nits: `verification.md` segue com `Verdict: FAIL` e a leitura do `**Linear**:` da spec está duplicada em `dispatch.py`. `dist/` é mecânico e ficou fora (`build --check` em dia).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | scripts/dispatch.py:959 | O `except FileNotFoundError` de `main` captura também o executável ausente. Com `orca` fora do PATH, o `start` já gravou a entrada `Dispatched` (linha 733) e sai com 2 e `dispatch: arquivo não encontrado: orca`, contrariando "exit 2 = recusa antes de gravar" (execute.md:44, docstring da linha 674). Reproduzido com probe sobre `MediaStartTests`: exit 2 e entrada gravada. Correção: no `start`, tratar `FileNotFoundError`/`OSError` das chamadas à Orca com `unrecord()` e exit 1, ou restringir o handler de `main` aos arquivos lidos. | scripts/dispatch.py:959, scripts/dispatch.py:733 | open |
| W2 | 🟡 nit | .specs/features/despacho-media-escopo/verification.md:3 | `verification.md` segue com `**Verdict**: FAIL` e `**HEAD**: d8507bf`, com os 4 achados fechados em 8c5fb8e, 0010fd1 e e0a81e9. Correção: nova rodada do Q no HEAD atual ou registrar no Handoff que a reverificação ficou pendente. | .specs/features/despacho-media-escopo/verification.md:3 | open |
| W3 | 🟡 nit | scripts/dispatch.py:667 | `spec_issue` repete a leitura do `**Linear**:` que `medium_ticket` (linha 656) já faz; o `start` lê o spec.md duas vezes. Correção: `medium_ticket` usar `spec_issue(fdir)`. | scripts/dispatch.py:656 | open |

## Escada determinística
- `python tools/build.py --check`: OK, dist/ em dia.
- `claude plugin validate dist/claude --strict`: Validation passed.
- `python scripts/check_decisions.py`: exit 0, OK (DECISIONS.md em 0010fd1a, depois de 14385d9e).
- `python -m unittest discover -s tests`: Ran 834 tests, OK (skipped=1).
- CI do PR #48 (`gh pr checks 48`): checks (ubuntu-latest) pass; checks (windows-latest) pendente; eval e release-check pulados.
- `git diff main...HEAD | scan_bypasses.py`: 0 candidatos.

## Pesquisa
- https://docs.python.org/3/library/subprocess.html (seção Exceptions: executar arquivo inexistente levanta `OSError`/`FileNotFoundError`, base do W1).
