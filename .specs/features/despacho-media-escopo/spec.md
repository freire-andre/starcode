# Despacho da MÉDIA e escopo com DECISIONS.md: Spec

**Approved**: 2026-11-13 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: Concorrência e estado (entradas `Dispatched` do Handoff)
**Status**: Approved
**Linear**: SC-169
**May change**: scripts/dispatch.py, scripts/gates/check_scope.py, scripts/gates/gates_common.py, skills/engajar/references/execute.md, DECISIONS.md, tests/test_dispatch_start.py, tests/test_dispatch_settle.py, tests/test_dispatch_decisions.py, tests/test_check_scope.py, tests/test_execute_doc_start_settle.py, tests/test_skills_exec.py, dist/

## Context
Itens R.7 e R.6 de `starcode-triagem-v2-2026-11-13.md` (fora do Git). R.7: o brief de ticket da GRANDE acrescenta `DECISIONS.md` ao May change quando ele cita `scripts/` (`effective_may_change`, `scripts/dispatch.py:108`), mas o `check_scope` lê o May change sem esse acréscimo, então o gate do ticket reprova o que o brief mandou fazer. R.6: `dispatch.py start` e `settle` exigem `tasks.md`; numa feature MÉDIA o `FileNotFoundError` vira traceback com código 1, lido como falha do worker ou gate vermelho, e por isso a MÉDIA é despachada e integrada à mão. As mensagens de recusa do modo 1 e da nova tentativa não dizem o caminho certo. Decisão do usuário: o `start` e o `settle` aceitam a MÉDIA como ticket único lido da spec.

## Scope
- Uma regra única para o acréscimo de `DECISIONS.md`, usada pelo brief (GRANDE e MÉDIA) e pelo `check_scope` (GRANDE e MÉDIA).
- `start` e `settle` aceitam a feature MÉDIA como o ticket `T1`, com a issue do `**Linear**:` da spec.
- Falta de arquivo sai com 2 e mensagem em todos os subcomandos do `dispatch.py`.
- Mensagens de recusa do `start` para modo 1 e nova tentativa apontam o caminho certo.
- `execute.md` descreve o caminho da MÉDIA (seção 8), da nova tentativa (seção 3) e do modo 1 (seção 7).

## Non-Goals
- Caminho da PEQUENA (item 3.5).
- Outras falhas do `start`/`settle` (R.8: `orca` fora do PATH, recibo com texto antes do JSON, mensagem de merge, trava de arquivo).
- Opção ou subcomando novo (congelamento D-i).
- Mudar o comportamento da GRANDE além do acréscimo de `DECISIONS.md` no `check_scope`.

## Requirements
- **R1** - The system SHALL ter em `scripts/gates/gates_common.py` uma só função que devolve o May change efetivo (a lista dada mais `DECISIONS.md` quando algum caminho começa com `scripts/` e `DECISIONS.md` não está na lista), usada por `scripts/dispatch.py` e por `scripts/gates/check_scope.py`.
- **R2** - WHEN um ticket do `tasks.md` com `scripts/` no May change e sem `DECISIONS.md` altera `DECISIONS.md` THEN `check_scope` SHALL passar sem erro para `DECISIONS.md`.
- **R3** - WHEN o ticket de uma feature MÉDIA com `scripts/` no `**May change**:` da spec altera `DECISIONS.md` THEN `check_scope` SHALL passar sem erro para `DECISIONS.md`.
- **R4** - WHEN o brief de uma feature MÉDIA é gerado e o `**May change**:` da spec tem `scripts/` sem `DECISIONS.md` THEN a linha `May change:` do brief SHALL terminar com `, DECISIONS.md`.
- **R5** - WHEN a feature não tem `tasks.md`, a spec tem `**Linear**: <ID>` e o ticket pedido é `T1` ou `<ID>` THEN `dispatch.py start` SHALL despachar o ticket `T1` com a issue `<ID>`, gravando a entrada `T1 · <ID> · base <sha> · <cli>:<modelo> · <hora UTC>` e seguindo os mesmos passos da GRANDE.
- **R6** - IF a feature não tem `tasks.md` e a spec não tem `**Linear**:` com um ID THEN `dispatch.py start` SHALL sair com 2 e `start recusado: spec sem **Linear**:`, sem gravar o Handoff nem chamar a Orca.
- **R7** - IF a feature não tem `tasks.md` e o ticket pedido não é `T1` nem o `**Linear**:` da spec THEN `dispatch.py start` e `dispatch.py settle` SHALL sair com 2 e `<start|settle> recusado: ticket <ticket> não é desta feature MÉDIA (use <ID> ou T1)`.
- **R8** - WHEN a feature não tem `tasks.md` e `settle` roda com a entrada `T1` em `Dispatched` THEN `dispatch.py settle` SHALL rodar `run_gates.py ticket <slug> T1 <base>..<ramo>`, mesclar com `merge: integra T1 (<ID>) em feature/<slug>` e `Refs: <ID>`, remover só a entrada `T1` e gravar `Last integrated` e `worker-T1=ok`.
- **R9** - IF um subcomando do `dispatch.py` não encontra um arquivo que precisa ler (`FileNotFoundError`) THEN o comando SHALL sair com 2 e `dispatch: arquivo não encontrado: <caminho>`, sem traceback.
- **R10** - IF o Handoff não tem `**Integration branch:**` THEN `dispatch.py start` SHALL recusar com 2 e `start recusado: o Handoff não tem **Integration branch:** (modo 1: siga a seção 7 do execute.md, sem start)`.
- **R11** - IF o ticket já tem entrada em `Dispatched` THEN `dispatch.py start` SHALL recusar com 2 e `start recusado: <T> já tem entrada em Dispatched (nova tentativa: handoff.py set <slug> --dispatch-remove <T>)`.
- **R12** - The system SHALL ter na seção 3 de `skills/engajar/references/execute.md`, no caso de falha, o texto `--dispatch-remove <T>` antes do novo `dispatch.py start`.
- **R13** - The system SHALL ter na seção 8 de `execute.md` o despacho da MÉDIA por `dispatch.py start <slug> <ID> --cli <laforge cli> --model <laforge model> --json` e a integração por `dispatch.py settle <slug> <ID> --branch <ramo do ticket>`, com `<ID>` = `**Linear**:` da spec.
- **R14** - The system SHALL ter na seção 7 de `execute.md` a frase `No modo 1 não se usa dispatch.py start nem settle`.
- **R15** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-169` descrevendo R1 a R14, com **Problema**, **Decisão**, **Motivo** e **Por que não é bug** citando os testes.

## Edge Cases
- MÉDIA com `tasks.md` presente: vale o `tasks.md` (fluxo da GRANDE), como hoje.
- Spec com `**Linear**:` vazio: R6.
- `settle` da MÉDIA sem entrada `T1`: recusa com 2 como hoje (`T1 não tem entrada em Dispatched`).
- Ticket pedido como o ID em minúscula: comparação sem diferença de maiúsculas, como no `tasks.md`.
- O acréscimo de `DECISIONS.md` não duplica quando a lista já o tem (com ou sem crases ou `./`).

## Decisions
| Item | Options | Status |
|---|---|---|
| MÉDIA no `start`/`settle` | aceitar como ticket único lido da spec · recusar com código 2 e apontar o caminho manual | approved - user: "Aceitar a MÉDIA (Recommended)" |

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `check_scope` e o brief chamam a mesma função de `gates_common`; trocar a função muda os dois resultados (R1)
Proof: run unit | test_regra_decisions_compartilhada ... ok

**C2** - Ticket do `tasks.md` com May change `scripts/x.py` que altera `scripts/x.py` e `DECISIONS.md` passa no `check_scope` com 0 erros; o mesmo ticket alterando `README.md` dá erro só para `README.md` (R2)
Proof: run unit | test_scope_aceita_decisions_com_scripts ... ok

**C3** - Feature MÉDIA com `**May change**: scripts/x.py` que altera `DECISIONS.md` passa no `check_scope` com 0 erros (R3)
Proof: run unit | test_scope_media_aceita_decisions ... ok

**C4** - Brief da MÉDIA com `**May change**: scripts/x.py` tem a linha exata `May change: scripts/x.py, DECISIONS.md`; com `DECISIONS.md` já presente, a linha não muda (R4)
Proof: run unit | test_brief_media_acrescenta_decisions ... ok

**C5** - Na MÉDIA com `**Linear**: PROJ-9`, `start` com `PROJ-9` e com `T1` grava a entrada que começa com `T1 · PROJ-9 · base ` e chama `worker-start` (R5)
Proof: run unit | test_start_media_despacha_t1 ... ok

**C6** - Na MÉDIA sem `**Linear**:`, `start` sai com 2, a primeira linha é exatamente `start recusado: spec sem **Linear**:`, e não há gravação nem chamada à Orca (R6)
Proof: run unit | test_start_media_sem_linear_recusa ... ok

**C7** - Na MÉDIA com `**Linear**: PROJ-9`, `start PROJ-8` e `settle PROJ-8` saem com 2 e a mensagem exata de R7 (R7)
Proof: run unit | test_media_ticket_errado_recusa ... ok

**C8** - Na MÉDIA, `settle` com a entrada `T1` roda o gate `ticket <slug> T1 <base>..<ramo>` antes do merge, mescla com a mensagem exata de R8 e remove só a entrada `T1` (R8)
Proof: run unit | test_settle_media_integra_t1 ... ok

**C9** - `dispatch.py` com um caminho que não existe sai com 2 e a linha exata `dispatch: arquivo não encontrado: <caminho>`, sem `Traceback` na saída (R9)
Proof: run unit | test_main_arquivo_ausente_sai_2 ... ok

**C10** - Sem `**Integration branch:**`, `start` sai com 2 e a mensagem exata de R10 (R10)
Proof: run unit | test_start_sem_ramo_aponta_modo_1 ... ok

**C11** - Com entrada aberta, `start` sai com 2 e a mensagem exata de R11 (R11)
Proof: run unit | test_start_entrada_aberta_aponta_dispatch_remove ... ok

**C12** - Seção 3 do `execute.md` tem `--dispatch-remove <T>` antes do novo `dispatch.py start`; seção 8 tem os dois comandos exatos de R13; seção 7 tem a frase exata de R14 (R12, R13, R14)
Proof: run unit | test_execute_media_retry_e_modo_1 ... ok

**C13** - `DECISIONS.md` tem a entrada da issue com `effective`/função única, `T1`, `arquivo não encontrado`, `--dispatch-remove` e `Por que não é bug` citando os testes de C1 a C12 (R15)
Proof: run unit | test_decisions_despacho_media ... ok

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** PR com confirmação, depois Worf
**Linear:** SC-169
**Integration branch:** feature/despacho-media-escopo
**Last integrated:** ded8b31
**Dispatched:** LaForge pós-Q · 3caef6b
**Settled:** none
**Attempts:** none
**Reports:** 2026-11-13: T1: effective_may_change em gates_common, start/settle aceitam a MÉDIA (T1 ou ID), FileNotFoundError sai 2, recusas apontam modo 1 e --dispatch-remove, execute.md 3/7/8, SC-169 no DECISIONS.md; 98 testes e gate ticket verdes; 2026-11-13: Q (codex · effective gpt-6-luna): FAIL, 4 achados (C5, C9, C13 fracos; ID em minúscula sem teste); suíte 833 ok; 2026-11-13: LaForge pós-Q: achados 1-2 em 8c5fb8e, 3 em 0010fd1, 4 em e0a81e9; 44 testes ok
**Breaker:** closed
