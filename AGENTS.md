# AGENTS.md

Plugin StarCode (SDD com tripulação Star Trek). Responda e escreva em PT-BR.

## Comandos (iguais ao CI, `.github/workflows/ci.yml`)
- `python tools/build.py --check`
- `python -m unittest discover -s tests -v`
- `python scripts/check_decisions.py`
- `claude plugin validate dist/claude --strict`

## Regras
- **`dist/`**: gerado por `python tools/build.py`, nunca editado à mão. A fonte fica em `skills/`, `scripts/`, `hooks/` e `src/`. Imposto por `python tools/build.py --check` (`tools/build.py`).
- **`DECISIONS.md` (D30)**: toda mudança em `skills/`, `scripts/` ou `hooks/` ganha uma entrada no mesmo commit ou depois. Imposto por `scripts/check_decisions.py`.
- **Fluxo**: toda mudança passa pelo fluxo StarCode (`/starcode:engajar`) e ganha decisão. A decisão é conferida pelo `scripts/check_decisions.py`.
- **Commits**: tipo convencional, assunto em minúsculas e em PT-BR, `Refs SC-<n>` no corpo. Exemplo: `git log`.

## Limitação conhecida
`orca plugin test` e `orca plugin check` só rodam com o plugin no mesmo drive da instalação da Orca. Fora dele falham com `cannot import "./orca-runtime.mjs"`. Rode o gate num worktree no mesmo drive. Detalhe: `.specs/features/ponte-missao-ativa/retro.md`, item 1.
