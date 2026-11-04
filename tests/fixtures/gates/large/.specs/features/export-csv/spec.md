# Exportar relatórios em CSV: Spec

**Size**: LARGE
**Risk triggers**: contrato público (formato de arquivo), chamadas externas
**Status**: Approved
**Approved**: 2026-11-03 - user: "aprovado, pode seguir para as tasks"

## Context

Os gestores copiam os relatórios da tela para planilhas à mão. Um CSV baixado direto do relatório
acaba com o retrabalho e com os erros de digitação.

## Scope

- Botão "Exportar CSV" no relatório de vendas.
- Endpoint `GET /reports/sales.csv` com os mesmos filtros da tela.

## Non-Goals

- Exportar para Excel (.xlsx) ou PDF.
- Agendar exportações por e-mail.

## Requirements

- **R1** - WHEN o usuário pede `GET /reports/sales.csv` com filtros válidos THEN o sistema SHALL responder 200 com `Content-Type: text/csv; charset=utf-8` e uma linha por venda filtrada.
- **R2** - The sistema SHALL usar `;` como separador e a primeira linha como cabeçalho `data;cliente;valor`.
- **R3** - IF o filtro de datas tiver mais de 366 dias THEN o sistema SHALL responder 422 com a mensagem `intervalo máximo: 366 dias`.

## Data & Contracts

| Campo | Tipo | Origem |
|---|---|---|
| data | AAAA-MM-DD | `sales.created_at` |
| cliente | texto | `customers.name` |
| valor | decimal com vírgula | `sales.total` |

## States

N/A - endpoint de download sem tela intermediária; o botão só dispara o download.

## Edge Cases

- Nenhuma venda no intervalo: arquivo só com o cabeçalho.
- Nome de cliente com `;`: campo entre aspas.

## Decisions

| Item | Opções | Status |
|---|---|---|
| Separador | `,` (padrão RFC) · `;` (Excel pt-BR abre direto) | approved - user: "ponto e vírgula" |

## Open Questions

None.
