**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR
COMMENT. A troca para 1.9.0 está correta nos manifestos, no `dist/` e no `CHANGELOG`, e o marketplace do Codex fica sem `version`, como o R2 corrigido pede. Um should-fix: `changelog_recent` só olha `[Unreleased]` e a versão mais recente. Com isso, os 22 testes que procuram SC-186 a SC-213 quebram de novo na próxima versão, quando esses itens deixarem de estar na seção mais recente. Isso contradiz o motivo da escolha e a frase do corpo do PR. Arquivos mecânicos fora do review: `dist/`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | `tests/test_support.py:28` | `changelog_recent` cobre só `[Unreleased]` e a versão mais recente. Na 1.10.0, os itens da 1.9.0 saem dessa janela e os 22 testes quebram. Correção: um helper que devolve todo o texto a partir de `## [Unreleased]`, usado pelos testes de entrada de issue. | `tests/test_support.py:28` | aberto |

## Escada determinística
- CI local do PR (evidência do PR): `build --check`, `check_decisions`, `claude plugin validate --strict` e a suíte inteira no gate proofs (C:, 763 s), todos verdes.
- `scan_bypasses.py`: 0 candidatos.

## Pesquisa
Nenhuma superfície externa: só a biblioteca padrão (`re`, `json`, `pathlib`).
