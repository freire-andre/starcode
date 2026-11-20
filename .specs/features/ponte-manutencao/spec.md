# Manutenção da Ponte: Spec

**Approved**: 2026-11-20 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-207
**May change**: scripts/handoff.py, scripts/ponte.py, scripts/dispatch.py, src/orca/orca-plugin.json, src/orca/src/panel.tsx, src/orca/src/panel.test.tsx, src/orca/src/worker.ts, src/orca/src/worker.test.ts, .github/workflows/ci.yml, tests/test_handoff.py, tests/test_ponte.py, tests/test_orca_manifest.py, tests/test_ponte_manutencao.py, tests/fixtures/ponte/tasks-ativa.md, DECISIONS.md, CHANGELOG.md, dist/

## Context
Itens C.4, C.8 e C.9 da triagem v2 (seção 10.1), missão 2 do passo 4, sob a D-k (só manutenção, Cena congelada). Discovery em `.specs/features/ponte-manutencao/context.md`. O `start` grava `<Tn> · <issue> · base <sha> · <cli>:<modelo> · <UTC> [· <dispatch id>]`, e o `ponte.py` procura `dispatch <id> · model <m>`: o painel nunca mostra o modelo.

## Scope
- Um só leitor da entrada do `**Dispatched:**`, usado pelo `ponte.py` e pelo `dispatch.py`.
- Limpeza do plugin da Orca: capacidade sem uso, `issue.url`, casamento de agente, nome do worktree.
- Passo do `orca` no CI com pulo visível.

## Non-Goals
- Versionar os tipos da Orca, criar `package.json` ou rodar `tsc` no CI.
- Qualquer recurso novo no painel ou na Cena (D-k).
- Mudar o formato que o `start` grava.

## Decisions
| Item | Options | Status |
|---|---|---|
| Testes do painel no CI (C.9) | pulo visível (aviso + resumo) · versionar os tipos da Orca e rodar tsc | approved - user: "Pulo visível (Recomendado)" |
| Formato do modelo no painel | `<cli>:<modelo>` como gravado · só `<modelo>` | approved - user: "você decide" (`<cli>:<modelo>`; default registrado no context.md) |
| Entradas no formato antigo | continuar lendo · ignorar | approved - user: "você decide" (continuar lendo; default registrado no context.md) |
| `issue.url` fora do padrão | descartar (`null`) · montar pelo identificador | approved - user: "você decide" (descartar; default registrado no context.md) |

## Requirements
- **R1** - The `scripts/handoff.py` SHALL ter `parse_dispatch_entry(entry)`, que devolve `ticket`, `issues`, `base`, `model`, `at`, `dispatch` e `blocked` de uma entrada do `**Dispatched:**`. No formato do `start` (`<Tn> · <issues> · base <sha> · <cli>:<modelo> · <UTC> [· <dispatch id>] [· blocked]`), `model` SHALL ser `<cli>:<modelo>`, `at` o horário e `dispatch` o id quando houver. No formato antigo (`· dispatch <id> · model <m>`), SHALL ler `dispatch` e `model` desses campos. Campo ausente SHALL virar `None`, nunca exceção.
- **R2** - The `parse_dispatched` (`scripts/ponte.py`) e os leitores do `dispatch.py` (horário do `overdue` e base do `settle`) SHALL usar `parse_dispatch_entry`, sem mudar a saída nem os códigos de saída de hoje. WHEN o `start` acabou de gravar uma entrada THEN o estado da Ponte SHALL trazer o worker com `model` igual a `<cli>:<modelo>`, provado com fixture copiada de uma entrada real gravada pelo `start`.
- **R3** - The `src/orca/orca-plugin.json` SHALL deixar de declarar `storage:own`.
- **R4** - The worker (`src/orca/src/worker.ts`) SHALL aceitar o `issue.url` vindo da Orca só quando começa com `https://linear.app/`; nos demais casos SHALL usar `null`.
- **R5** - The `agentFor` (`src/orca/src/panel.tsx`) SHALL casar o rótulo e as issues do worker com o título do agente por token inteiro (delimitado por início, fim ou caractere não alfanumérico): `T1` SHALL casar com `LaForge T1` e SHALL NOT casar com `LaForge T10`.
- **R6** - The nome do worktree no diário (`worker.ts`) SHALL ser o último trecho do caminho separado por `/` ou `\`: `C:\x\meu-wt` e `/x/meu-wt/` SHALL dar `meu-wt`.
- **R7** - WHEN não há `orca` no PATH THEN o passo do `orca` no `.github/workflows/ci.yml` SHALL imprimir `::warning title=orca ausente::validação e testes do plugin da Ponte pulados` e acrescentar ao `$GITHUB_STEP_SUMMARY` a linha `- orca plugin validate: pulado (orca ausente)`. WHEN há `orca` THEN SHALL rodar `orca plugin validate src/orca --json` como hoje.
- **R8** - The `DECISIONS.md` SHALL ter a entrada `### SC-<n>:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug** (com os testes), e o `CHANGELOG.md` uma linha em `[Unreleased]`.

## Edge Cases
- Entrada com `blocked` no fim e sem dispatch id: `blocked` verdadeiro, `dispatch` `None` (R1).
- Entrada só com `<Tn>`: `ticket` preenchido, o resto `None` (R1).
- Agente sem título: nunca casa (R5).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`; `orca plugin validate src/orca --json`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`
**Run plugin**: `orca plugin test src/orca`

O `Run plugin` só roda num worktree no drive da Orca (`docs/compatibilidade.md:150`).

**C1** - `parse_dispatch_entry` com tabela de entradas: formato do `start` com e sem dispatch id, com `blocked`, formato antigo, só `<Tn>` (R1)
Proof: run unit | test_parse_dispatch_entry (test_ponte_manutencao.PonteManutencaoTests.test_parse_dispatch_entry) ... ok

**C2** - Entrada real do `start` mostra `<cli>:<modelo>` no estado da Ponte; `overdue` e `settle` seguem com a mesma saída (R2)
Proof: run unit | test_ponte_modelo_do_start (test_ponte_manutencao.PonteManutencaoTests.test_ponte_modelo_do_start) ... ok
Proof: run unit | test_dispatch_usa_leitor_unico (test_ponte_manutencao.PonteManutencaoTests.test_dispatch_usa_leitor_unico) ... ok

**C3** - O manifesto não declara `storage:own` (R3)
Proof: run unit | test_manifesto_sem_storage (test_ponte_manutencao.PonteManutencaoTests.test_manifesto_sem_storage) ... ok

**C4** - `issue.url` fora de `https://linear.app/` vira `null` (R4)
Proof: run plugin | ✔ issue.url fora do linear vira null

**C5** - `agentFor` casa `T1` com `LaForge T1` e não com `LaForge T10`; agente sem título nunca casa (R5)
Proof: run plugin | ✔ agentFor casa por token inteiro

**C6** - Nome do worktree com `\` e com `/` (R6)
Proof: run plugin | ✔ nome do worktree com barra invertida

**C7** - O passo do CI, rodado com bash sem `orca` no PATH e com `GITHUB_STEP_SUMMARY` num arquivo temporário, imprime o aviso exato e grava a linha exata; com um `orca` falso no PATH, chama `orca plugin validate src/orca --json` (R7)
Proof: run unit | test_ci_pulo_visivel (test_ponte_manutencao.PonteManutencaoTests.test_ci_pulo_visivel) ... ok

**C8** - Entrada do SC no `DECISIONS.md` com as quatro partes e linha no `CHANGELOG.md` (R8)
Proof: run unit | test_decisions_e_changelog (test_ponte_manutencao.PonteManutencaoTests.test_decisions_e_changelog) ... ok

## Handoff

**Phase:** spec-approved
**Size:** MEDIUM
**Git mode:** 3
**Next:** LaForge implementa T1
**Linear:** SC-207
**Integration branch:** feature/ponte-manutencao
**Last integrated:** 2b75935cc25b5107910787d3087a1023eec79c12
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
