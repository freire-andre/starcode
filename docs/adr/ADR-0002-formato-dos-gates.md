# ADR-0002: Formato dos gates e dos artefatos de planejamento

- Status: aceito (Fase 2, 2026-11-03, SC-9)
- Base: tlc-spec-driven 4.1.0 (Felipe Rodrigues, CC-BY-4.0), adaptado (D24, D25)
- Evidência: `scripts/gates/`, `tests/test_gates.py`, fixtures em `tests/fixtures/gates/`

## Contexto

A D24 escolheu o tlc-spec-driven como base dos gates: `spec.md` + `tasks.md`, duas aprovações, checks
com prova. O StarCode muda o template da spec (seção 4.5), põe o briefing de 5 blocos dentro de cada
tarefa (D19), exige o rodapé `Refs: <ID>` nos commits e tira as regras de captura de tela (D25).

## Decisão

Gates em `scripts/gates/`, só com a stdlib do Python, mensagens em PT-BR, marcadores em inglês (D16).

| Gate | Quando | O que exige |
|---|---|---|
| `validate_spec.py` | antes de mostrar a spec | `**Size**:`; template completo (LARGE/COMPLEX) ou breve (MEDIUM); requisitos `R<n>` em EARS com `SHALL`; `Open Questions` vazia; decision map com status fechado; `## Checks` só na spec MEDIUM; `--approved` exige a aprovação nas palavras do usuário |
| `validate_tasks.py` | antes de mostrar as tasks | `## Gate Commands`, `## Tasks`, `## Checks`; por tarefa: `Depends on`, `Requirements`, `Tests`, `Gate` e os 5 blocos; `May change`; tarefas independentes sem caminho em comum; arquivo sensível exige `Runs alone`; um check por requisito; `--execute` exige as duas aprovações; `--published` exige o ID do Linear em cada tarefa |
| `check_commit.py` | antes de cada commit | Conventional Commits + `Refs: <ID>` (`--expect-ref` fixa o ticket) |
| `run_gates.py` | sempre | roda os gates da etapa (`spec`, `tasks`, `publish`, `execute`, `commit`) e imprime o VEREDITO primeiro |
| `tasks_export.py` | publicação | corpo de cada issue (o briefing), relações `blocks` e gravação dos IDs no `tasks.md` |

O que mudou em relação ao tlc:

| tlc | StarCode | Motivo |
|---|---|---|
| Seções Problem Statement, User Stories, Requirement Traceability, Assumptions | Template 4.5 (Context … Open Questions), IDs `R<n>` | plano 4.5 |
| Spec curta sem marcador de tamanho | `**Size**:` decide o template | o gate precisa saber qual template cobrar |
| Execution Plan com diagrama e checagem diagrama × `Depends on` | só `Depends on`; ciclo e dependência inexistente são erro | o diagrama duplicava a informação; as relações `blocks` do Linear saem do `Depends on` |
| `Where` com aviso de granularidade | `May change` nos BOUNDARIES, com sobreposição entre tarefas independentes como erro | D19 (dono de arquivo) e Frota |
| Test Coverage Matrix obrigatória | `## Gate Commands` obrigatória; o `Gate` de cada tarefa precisa existir nela | menos cerimônia; a matriz virou julgamento do Data |
| Regras de captura (`captures/`, `screens.md`) | removidas | D25 |
| `check_commit` sem rodapé | `Refs: <ID>` obrigatório | D24 |
| `validate_tasks --execute` roda o `Build` uma vez | não roda nesta fase | entra na Fase 3 junto com o `check_proofs.py` |

`check_proofs.py` e `validate_verification.py` são adaptados na Fase 3. O parser de `## Checks`
(`gates_common.read_checks`) já é o que eles vão usar.

## Consequências

- O `## Handoff` vive no artefato mais avançado da feature (F2-3); os gates ignoram essa seção.
- O selftest do StarCode é `tests/test_gates.py` (unittest), não o `selftest.py` do tlc, que testava
  seções que não existem mais.
- Mudar um gate exige entrada no `DECISIONS.md` (D30) e um teste novo.
