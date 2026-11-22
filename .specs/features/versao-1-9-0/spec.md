# Versão 1.9.0: Spec

**Approved**: 2026-11-22 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-214
**May change**: VERSION, src/orca/orca-plugin.json, tests/test_build.py, tests/test_versao_1_9_0.py, README.md, CHANGELOG.md, .claude-plugin/marketplace.json, .agents/plugins/marketplace.json, dist/

## Context
Os agentes instalados estão na 1.8.0 de 2026-11-13 (OpenCode em 1.6.1), sem as 24 mudanças de `[Unreleased]`. O Claude Code guarda o plugin pela versão, então a atualização exige uma versão nova. Discovery em `.specs/features/versao-1-9-0/context.md`.

## Scope
- Versão 1.9.0 no `VERSION`, no `src/orca/orca-plugin.json`, no teste de versão e no `README.md`.
- `CHANGELOG.md`: os itens de `[Unreleased]` passam para `## [1.9.0] - 2026-11-22`.
- `dist/` e manifestos regenerados por `python tools/build.py`.

## Non-Goals
- Tag e release no GitHub (ficam para depois de 01/12, quando o Actions tiver minutos).
- Qualquer mudança de comportamento em `skills/`, `scripts/` ou `hooks/`.
- A reinstalação nos agentes: é passo do Picard depois do merge, fora do código.

## Requirements
- **R1** - The `VERSION` SHALL conter `1.9.0`, e o `src/orca/orca-plugin.json` SHALL ter `"version": "1.9.0"`.
- **R2** - WHEN `python tools/build.py` roda THEN the system SHALL gravar `1.9.0` em `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `dist/claude/.claude-plugin/plugin.json`, `dist/codex/.codex-plugin/plugin.json`, `dist/antigravity/plugin.json`, `dist/orca/orca-plugin.json` e nos `dist/*/crew.json`; e `python tools/build.py --check` SHALL dizer `OK`.
- **R3** - The teste de versão de `tests/test_build.py` SHALL exigir `1.9.0` no `VERSION`, no marketplace do Claude e nos três manifestos de `dist/`.
- **R4** - The `CHANGELOG.md` SHALL ter `## [Unreleased]` vazio, seguido de `## [1.9.0] - 2026-11-22` com todos os itens que estavam em `[Unreleased]`, nas mesmas seções (`### Alterado`, `### Corrigido`), e `python tools/release.py notes` (ou a função `_notes`) SHALL achar a seção 1.9.0.
- **R5** - The `README.md` SHALL dizer `Estado: **v1.9.0**` na linha que hoje diz `Estado: **v1.8.0**`.

## Edge Cases
- Um item de `[Unreleased]` perdido na mudança de seção: o check do R4 compara a lista de itens antes e depois.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `VERSION`, marketplace do Claude e os três manifestos de `dist/` em 1.9.0 (R1, R2, R3)
Proof: run unit | test_version_is_1_2_0_in_all_manifests (test_build.BuildTests.test_version_is_1_2_0_in_all_manifests) ... ok

**C2** - `src/orca/orca-plugin.json`, `dist/orca/orca-plugin.json`, `.agents/plugins/marketplace.json` e os `dist/*/crew.json` em 1.9.0 (R1, R2)
Proof: run unit | test_versao_1_9_0_em_todos_os_manifestos (test_versao_1_9_0.Versao190Tests.test_versao_1_9_0_em_todos_os_manifestos) ... ok

**C3** - `[Unreleased]` vazio; a seção `[1.9.0] - 2026-11-22` tem 24 itens (`- ` no início da linha), citando exatamente as 22 issues que estavam em `[Unreleased]` (SC-186, SC-187, SC-188, SC-190, SC-195 a SC-200, SC-202 a SC-213), e `release._notes` acha a seção (R4)
Proof: run unit | test_changelog_fecha_1_9_0 (test_versao_1_9_0.Versao190Tests.test_changelog_fecha_1_9_0) ... ok

**C4** - `README.md` com `Estado: **v1.9.0**` e sem `v1.8.0` na linha de estado (R5)
Proof: run unit | test_readme_estado_1_9_0 (test_versao_1_9_0.Versao190Tests.test_readme_estado_1_9_0) ... ok

## Handoff

**Phase:** spec-approved
**Size:** MEDIUM
**Git mode:** 3
**Plugin:** none yet
**Next:** LaForge T1
**Linear:** SC-214
**Integration branch:** not created
**Last integrated:** none
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
