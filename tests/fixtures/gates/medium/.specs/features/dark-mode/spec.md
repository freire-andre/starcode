# Preferência de tema escuro: Spec

**Size**: MEDIUM
**Risk triggers**: dados persistidos
**Linear**: SC-40
**Approved**: 2026-11-03 - user: "ok, manda ver"

## Context

Usuários pedem tema escuro e querem que a escolha valha em todos os dispositivos.

## Scope

- Campo `theme` no perfil (`light` | `dark`), salvo no servidor.

## Non-Goals

- Tema automático pelo sistema operacional.

## Requirements

- **R1** - WHEN o usuário salva `theme=dark` THEN o sistema SHALL persistir o valor no perfil.
- **R2** - IF `theme` tiver outro valor THEN o sistema SHALL responder 400.

## Edge Cases

- Perfil antigo sem o campo: vale `light`.

## Open Questions

## Checks

**Build**: `npm run lint`; `npx tsc --noEmit`
**Run unit**: `npx vitest run src/profile --reporter=verbose`

**C1** - Salvar `dark` grava no perfil (R1)
Proof: run unit | ✓ profile > saves dark theme

**C2** - Valor inválido responde 400 (R2)
Proof: run unit | ✓ profile > rejects invalid theme
