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

**C5** - O dry-run relata a cópia, o plugin e os caminhos removidos e gravados, sem escrever nada (R3)
Proof: run unit | test_opencode_dry_run_reports_removed_and_written ... ok

## Handoff

**Phase:** review
**Size:** PEQUENA
**Git mode:** 3
**Next:** LaForge corrige W1-W2; Worf r2
**Linear:** SC-184
**Integration branch:** feature/opencode-copia-instalada
**Last integrated:** 4194e77
**Dispatched:** W-fix · SC-184 · base pendente · claude:claude-sonnet-5-5 · 2026-11-15T19:53:46Z
**Settled:** 2026-11-15: 2026-11-15: opção (a), fix do OpenCode agora: "A"; issue: "Sim"; 2026-11-15: 2026-11-15: push + PR: "Sim"; 2026-11-15: 2026-11-15: PR aberto: https://github.com/freire-andre/starcode/pull/57
**Attempts:** none
**Reports:** 2026-11-15: T1: cherry-pick de 5d8450a como 932a4c2; CHANGELOG em [Unreleased]; 924 OK; ticket gate verde; 2026-11-15: Q: codex · effective unconfirmed · FAIL, 3 achados (C1 sem caminhos exatos; dry-run sem check: C5 acrescentado pelo Picard; .pyc fora de __pycache__ sem teste); 924 OK; q-check 0; 2026-11-15: T1-fix: d157d4a (C1, C5 estritos; .pyc solto); 924 OK; ticket gate verde; 2026-11-15: provas e done verdes (924 OK); C5 na verificação marcado como não julgado pelo Q; 2026-11-15: Guinan: L2, L10, L13 (promovida) por --id; retro com 3 sugestões; 2026-11-15: Worf r1: COMMENT; W1 should-fix (rmtree antes do copytree deixa cópia incompleta se a cópia falhar); W2 nit (skill removida deixa caminho morto)
**Breaker:** closed
