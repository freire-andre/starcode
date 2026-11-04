# Exportar relatórios em CSV: Tasks

**Spec**: `.specs/features/export-csv/spec.md`
**Status**: Approved
**Approved**: 2026-11-03 - user: "tasks aprovadas"
**Integration branch**: `feature/export-csv`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | tarefa só com testes unitários | `pytest tests/unit -q` |
| full | tarefa com rota HTTP | `pytest -q` |

## Tasks

### T1: Serializador CSV das vendas
**Depends on**: none
**Requirements**: R2
**Tests**: unit
**Gate**: quick

#### TASK
Criar `app/reports/csv_export.py` com `sales_to_csv(rows)` que gera o CSV com `;` e cabeçalho.

#### CONTEXT
Spec: `.specs/features/export-csv/spec.md` (R2). Checks: C2.
Siga o padrão dos serializadores em `app/reports/`.

#### BOUNDARIES
May change: `app/reports/csv_export.py`, `tests/unit/test_csv_export.py`
Do not touch: `app/routes/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>". Nunca segredos. Sem deploy, push ou merge.

#### DELIVERY
Commits na branch do worktree. Relatório final: o que mudou, gates com resultado, pendências.

### T2: Rota de download com validação do intervalo
**Depends on**: T1
**Requirements**: R1, R3
**Tests**: integration
**Gate**: full

#### TASK
Criar `GET /reports/sales.csv` em `app/routes/reports.py` usando `sales_to_csv`.

#### CONTEXT
Spec: `.specs/features/export-csv/spec.md` (R1, R3). Checks: C1, C3.

#### BOUNDARIES
May change: `app/routes/reports.py`, `tests/integration/test_reports_csv.py`
Do not touch: `app/reports/csv_export.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 2.
Commit: Conventional Commits + "Refs: <ID-LINEAR>".

#### DELIVERY
Commits na branch do worktree. Relatório final em até 5 linhas.

## Checks

**Build**: `ruff check .`; `mypy app`
**Run unit**: `pytest tests/unit -v`
**Run api**: `pytest tests/integration -v`

**C1** - `GET /reports/sales.csv` responde 200 com `text/csv; charset=utf-8` (R1)
Proof: run api | test_reports_csv.py::test_download_ok PASSED

**C2** - A primeira linha é `data;cliente;valor` (R2)
Proof: run unit | test_csv_export.py::test_header PASSED

**C3** - Intervalo de 367 dias responde 422 (R3)
Proof: run api | test_reports_csv.py::test_range_limit PASSED

## Handoff

**Phase:** tasks-approved
**Next:** publicar no Linear (confirmação pendente)
