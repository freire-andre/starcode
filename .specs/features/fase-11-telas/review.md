# Review: fase-11-telas (PR #28)

**Round**: 1
**Verdict**: COMMENT
**Reviewer**: claude · claude-opus-5-5

## TL;DR

COMMENT. O PR traz a verificação de telas com gates, testes e aceite real. Há dois defeitos reais, sem risco de merge:
- o gate aceita um `screens.md` que omite uma tela vinculante (W1);
- o `tools/aceite.py` grava uma identidade git fixa na cópia de trabalho (W2).

Há também um nit sobre escala ímpar (W3).

Arquivos mecânicos fora do review: `dist/`, `aceite/telas/package-lock.json` e `aceite/telas/src-tauri/Cargo.lock`.

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | 🟠 should-fix | `scripts/gates/validate_verification.py:143` | `screens.md` sem veredito para uma captura vinculante passa no gate. Sondagem: com `home.png` e `sobre.png` vinculantes e só `home` julgada, o `evaluate` sai ok. | `scripts/gates/validate_verification.py:143` | aberto |
| W2 | 🟠 should-fix | `tools/aceite.py:63` | `user.email`/`user.name` fixos no config local da cópia: os commits seguintes saem com o autor "StarCode Aceite" | `tools/aceite.py:63` | aberto |
| W3 | 🟡 nit | `scripts/gates/images.py:119` | Divisão inteira em `css_size`: uma captura `@2x` de tamanho ímpar passa como se fosse par | `scripts/gates/images.py:119` | aberto |

## Escada determinística

- `python tools/build.py && python tools/build.py --check && python scripts/check_decisions.py && python -m unittest discover -s tests && claude plugin validate dist/claude --strict`: exit 0, 658 testes OK
- `run_gates.py proofs` e `done`: verde, 45/45
- CI do PR #28: `checks (ubuntu-latest)` pass; `checks (windows-latest)` pendente no momento do review
- `git diff main...HEAD | scan_bypasses.py`: 43 candidatos, nenhum achado:
  - `noqa: E402`: aceitos, porque seguem o `sys.path.insert` da linha anterior, convenção já presente na main (`scripts/dispatch.py:50`);
  - `noqa: F401`: têm justificativa na própria linha;
  - `hook-bypass` em `SKILL.md`: é a própria proibição.

## Pesquisa

- Context7 `/tauri-apps/tauri-docs`: `mockIPC` simula `window.__TAURI_INTERNALS__.invoke`. A detecção do template (`"__TAURI_INTERNALS__" in window`) segue a documentação.
**Posted**: 2026-11-12 - https://github.com/freire-andre/starcode/pull/28#pullrequestreview-5875471089
