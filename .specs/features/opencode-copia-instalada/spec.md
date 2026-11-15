# OpenCode usa cópia instalada: Spec

**Approved**: 2026-11-15 - user: "A"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-184
**May change**: tools/install_local.py, tests/test_install_local.py, README.md, CHANGELOG.md

## Context
O commit `5d8450a` (ramo local `fix/opencode-copia-instalada`, 2026-11-13) nunca foi integrado. Ele faz o `tools/install_local.py` copiar `dist/opencode` para `~/.config/opencode/starcode` e apontar `skills.paths` e o plugin para essa cópia, em vez do `dist/` do clone. A `main` atual ainda aponta para o clone (`tools/install_local.py:151-173`).

## Scope
- Reaplicar `5d8450a` sobre a `main` atual (cherry-pick), resolvendo o conflito do `CHANGELOG.md` com as duas entradas.

## Non-Goals
- Mudar o install dos outros CLIs (codex, antigravity, orca).
- Qualquer comando, opção ou skill novo (congelamento D-i).

## Requirements
- **R1** - WHEN `install_local.py opencode` roda THEN the system SHALL copiar `dist/opencode` para `<home>/.config/opencode/starcode` e gravar em `opencode.json` os caminhos de skill e o plugin apontando para essa cópia, não para o clone.
- **R2** - WHEN o install roda de novo com uma cópia antiga instalada THEN the system SHALL substituir a cópia antiga.
- **R3** - The system SHALL manter o comportamento já testado: caminhos de skill alheios preservados em ordem, sem duplicatas entre dois clones, e o relatório do dry-run.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - O `opencode.json` gravado aponta skills e plugin para `<home>/.config/opencode/starcode`, e não para o clone (R1)
Proof: run unit | test_opencode_uses_installed_copy_not_the_clone ... ok

**C2** - Reinstalar substitui a cópia antiga (R2)
Proof: run unit | test_opencode_reinstall_replaces_stale_installed_copy ... ok

**C3** - Caminhos alheios preservados em ordem (R3)
Proof: run unit | test_opencode_install_keeps_foreign_skill_paths_in_order ... ok

**C4** - Dois clones não duplicam caminhos (R3)
Proof: run unit | test_opencode_install_twice_from_two_clones_no_duplicates ... ok

## Handoff

**Phase:** execute
**Size:** PEQUENA
**Git mode:** 3
**Next:** LaForge reaplica 5d8450a
**Linear:** SC-184
**Integration branch:** feature/opencode-copia-instalada
**Last integrated:** none
**Dispatched:** T1 · SC-184 · base 41db2a7 · claude:claude-sonnet-5-5 · 2026-11-15T18:52:06Z · ctx_dea6cac3d7b9
**Settled:** 2026-11-15: 2026-11-15: opção (a), fix do OpenCode agora: "A"; issue: "Sim"
**Attempts:** none
**Reports:** none
**Breaker:** closed
