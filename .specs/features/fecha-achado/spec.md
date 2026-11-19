# Fechamento de achado do Q com commit e cobertura: Spec

**Approved**: 2026-11-19 - user: "Sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-199
**May change**: scripts/dispatch.py, scripts/gates/validate_verification.py, src/briefs/q-verify.md, skills/engajar/references/execute.md, tests/test_fecha_achado.py, tests/test_validate_verification.py, tests/test_validate_verification_screens.py, tests/test_q_skill.py, tests/test_acceptance_doc_f11.py, tests/test_dispatch_screens.py, tests/test_pequena_minima.py, tests/test_piloto.py, tests/test_worf_skill.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Esta spec cobre o item 3.7 da triagem v2 e a decisão do dono D-c. O discovery está em `.specs/features/fecha-achado/context.md`. Hoje o gate `done` só confere o commit na célula `Closed` (`scripts/gates/validate_verification.py:276-289`), e a célula é preenchida à mão. Nesta sessão, uma célula a mais (`||`) e pipes sem escape na evidência do Q deixaram o `done` vermelho com a mensagem "sem commit em `Closed`", que não apontava a causa.

## Scope
- Subcomando `dispatch.py close-finding` que preenche a célula `Closed` conferindo o commit e a cobertura.
- Gate `done`: exige commit e cobertura em cada achado e acusa linha com número errado de células.
- Brief do Q: pipe dentro de célula escrito como `&#124;`.
- `execute.md`: o fechamento passa a usar o subcomando.

## Non-Goals
- Segundo Q (D-c: continua sem).
- Revalidar os `verification.md` de features já fechadas.
- Mudar o fechamento do modo 1 (`degradada (modo 1)`).

## Decisions
| Item | Options | User answer |
|---|---|---|
| O que vale como cobertura | `C<n>` ou teste existente / só `C<n>` / teste que passou no proofs.md | approved - user: "C<n> ou teste existente (Recomendado)" |

## Requirements
- **R1** - WHEN o Picard roda `dispatch.py close-finding <slug> <n> --commit <sha> --cover <C<n>|test_nome>` THEN o comando SHALL gravar na célula `Closed` do n-ésimo achado da tabela `## Findings` do `verification.md` o texto `<sha curto de 7> · <cobertura>`, e sair com 0. Opções repetidas (`--commit` e `--cover` mais de uma vez) SHALL virar uma lista separada por `, ` em cada lado do `·`.
- **R2** - IF o commit não existe no repositório, a cobertura não é um `C<n>` dos checks da feature (`tasks.md` ou, sem ele, `spec.md`) nem um `test_<nome>` definido como `def test_<nome>` em algum arquivo de `tests/` no HEAD, `n` está fora da faixa, ou a tabela `## Findings` tem uma linha com número de células diferente do cabeçalho THEN o comando SHALL sair com 2, com uma mensagem que nomeia o problema, sem gravar nada.
- **R3** - The `close-finding` SHALL reescrever só a célula `Closed` da linha escolhida e manter todos os outros bytes do arquivo iguais.
- **R4** - WHEN o gate `done` lê um achado sem `degradada (modo 1)` THEN ele SHALL exigir na célula `Closed` ao menos um commit do repositório e ao menos uma cobertura válida, pela mesma regra do R2. Sem a cobertura, o erro SHALL ser `` achado '<nome>': `Closed` sem cobertura (C<n> ou test_<nome>): use dispatch.py close-finding ``.
- **R5** - IF uma linha das tabelas `## Checks` ou `## Findings` do `verification.md` tem número de células diferente do cabeçalho THEN o gate `done` SHALL dar o erro `verification.md:<linha>: <m> células, o cabeçalho tem <k> (escape pipe como &#124;)` e não SHALL dar, para essa linha, o erro de commit ausente.
- **R6** - The `src/briefs/q-verify.md` SHALL mandar escrever todo pipe dentro de uma célula como `&#124;`, inclusive dentro de crases. The `execute.md` (seção 5) SHALL mandar fechar cada achado com `dispatch.py close-finding`, no lugar de editar a célula.
- **R7** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-<n>:` desta issue com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**. A **Decisão** SHALL citar a D-c, o `close-finding`, o formato `<sha> · <cobertura>`, a regra da cobertura e o erro de células. O **Por que não é bug** SHALL citar os testes. SHALL ter também uma linha em `CHANGELOG.md` `[Unreleased]`.

## Edge Cases
- `&#124;` dentro da célula não conta como separador (R2, R5).
- Achado já fechado: o `close-finding` substitui a célula (R1).
- `C<n>` que não existe na feature, ou `test_` que só aparece num comentário: recusado (R2).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `close-finding` grava `<sha7> · C<n>` e a lista com opções repetidas, e sai com 0 (R1)
Proof: run unit | test_close_finding_grava (test_fecha_achado.FechaAchadoTests.test_close_finding_grava) ... ok

**C2** - Commit inexistente, cobertura inválida, `n` fora da faixa e tabela malformada saem com 2 e a mensagem, sem mudar os bytes (R2)
Proof: run unit | test_close_finding_recusa (test_fecha_achado.FechaAchadoTests.test_close_finding_recusa) ... ok

**C3** - Só a célula `Closed` muda; o resto do arquivo fica igual em bytes, inclusive com `&#124;` na evidência (R3)
Proof: run unit | test_close_finding_preserva_bytes (test_fecha_achado.FechaAchadoTests.test_close_finding_preserva_bytes) ... ok

**C4** - O `done` recusa `Closed` só com commit, com a mensagem exata, e aceita commit com `C<n>` ou com teste existente (R4)
Proof: run unit | test_done_exige_cobertura (test_fecha_achado.FechaAchadoTests.test_done_exige_cobertura) ... ok

**C5** - O `done` acusa a linha com células a mais ou a menos, com a mensagem exata e o número da linha, sem o erro de commit (R5)
Proof: run unit | test_done_acusa_celulas (test_fecha_achado.FechaAchadoTests.test_done_acusa_celulas) ... ok

**C6** - O brief do Q manda `&#124;` e o `execute.md` manda `close-finding` (R6)
Proof: run unit | test_textos_close_finding (test_fecha_achado.FechaAchadoTests.test_textos_close_finding) ... ok

**C7** - Entrada no `DECISIONS.md` com os quatro campos, os termos da Decisão, os testes citados e a linha no CHANGELOG (R7)
Proof: run unit | test_decisions_fecha_achado (test_fecha_achado.FechaAchadoTests.test_decisions_fecha_achado) ... ok

## Handoff

**Phase:** spec-approved
**Size:** MEDIUM
**Git mode:** 3
**Next:** LaForge implementa T1 (SC-199)
**Linear:** SC-199
**Integration branch:** feature/fecha-achado
**Last integrated:** none
**Dispatched:** none
**Settled:** 2026-11-19: spec aprovada: Sim; issue SC-199 criada
**Attempts:** none
**Reports:** none
**Breaker:** closed
