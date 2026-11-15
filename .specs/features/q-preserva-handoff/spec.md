# Q preserva o Handoff: Spec

**Approved**: 2026-11-15 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-181
**May change**: scripts/dispatch.py, src/briefs/q-verify.md, skills/engajar/references/execute.md, tests/test_dispatch.py, tests/test_dispatch_qcheck.py, tests/test_skills_exec.py, tests/test_q_skill.py, DECISIONS.md, dist/

## Context
Item 1.1 ampliado de `starcode-triagem-v2-2026-11-13.md` (seção 4, fora do Git). Discovery em `context.md`. Na fase 12, o Q restaurou o `tasks.md` e apagou o Handoff não commitado (retro `fase-12-robustez`, item 2). Hoje o brief do Q (`src/briefs/q-verify.md:22-24`) não cita o Handoff, o `execute.md` (seção 4) grava o Handoff depois do commit das provas e o Picard desfaz à mão as mudanças extras do Q. Sucesso: o Handoff está commitado quando o Q começa, o brief proíbe tocar nele e restaurar arquivos, e um comando diz se o Q mexeu em algo fora da lista.

## Scope
- Brief do Q: regra explícita sobre o `## Handoff` e sobre não restaurar nem descartar arquivos.
- `execute.md`: o Picard commita o Handoff antes de despachar o Q e roda o `q-check` depois do `worker_done`.
- Subcomando `dispatch.py q-check <slug> [--root <dir>]`, que só relata.

## Non-Goals
- Restaurar ou apagar arquivos automaticamente (o comando só relata).
- Outros itens da triagem.
- Qualquer outro comando, opção ou skill novo (congelamento D-i; o `q-check` é a exceção registrada).

## Requirements
- **R1** - The system SHALL gerar o brief do Q (`dispatch.py q-brief`) com a linha exata `Never touch the \`## Handoff\` section of any artifact, and never restore, revert, stash, check out or delete files: uncommitted changes you did not make are not yours.` dentro da seção `## Rules`.
- **R2** - WHEN `dispatch.py q-check <slug>` roda num repositório Git cujo `git status --porcelain --untracked-files=all` só lista caminhos permitidos (ou nenhum) THEN the system SHALL imprimir exatamente `q-check: só arquivos permitidos alterados` e sair com 0.
- **R3** - The system SHALL considerar permitidos só `.specs/features/<slug>/verification.md`, `.specs/features/<slug>/screens.md` e `.specs/features/<slug>/captures/<nome>.running.png`.
- **R4** - IF algum caminho listado não é permitido (rastreado modificado, apagado, no índice ou novo não rastreado) THEN the system SHALL imprimir uma linha `fora da lista: <XY> <caminho>` por caminho, em ordem, onde `<XY>` são os dois caracteres de estado do `git status --porcelain`, seguida da linha `q-check: <n> arquivo(s) fora da lista; desfaça com git restore (rastreados) ou apague (novos)`, e sair com 1.
- **R5** - The system SHALL NOT restaurar, apagar nem alterar nenhum arquivo ao rodar o `q-check`.
- **R6** - IF o `git status` falha (pasta fora de um repositório Git) THEN the system SHALL imprimir em stderr `ERRO: git status falhou em <pasta>: <motivo>` e sair com 2.
- **R7** - The system SHALL ter no `execute.md` (seção 4) o commit do Handoff (`handoff.py set <slug> --phase review` seguido do commit) antes do `orca orchestration worker-start` do Q, e no passo das mudanças extras o comando `python "P/scripts/dispatch.py" q-check <slug>` rodado logo após o `worker_done` do Q.
- **R8** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-181:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**, citando `q-check`, `Handoff` e a exceção ao `D-i`.

## Decisions

| Decisão | Opções | Resposta |
|---|---|---|
| Onde fica a checagem | subcomando `dispatch.py q-check` / regra no gate `done` / só texto | approved - user: "Subcomando dispatch.py q-check" |
| Arquivo fora da lista | só relata / desfaz sozinho | approved - user: "Só relata" |

## Edge Cases
- Árvore limpa: R2 (C2).
- Só `verification.md`, `screens.md` e `captures/x.running.png` alterados: R2, R3 (C2).
- `tasks.md` modificado, `spec.md` apagado e `notas.txt` novo: R4 (C3).
- `captures/x.png` (não `.running.png`) alterado: fora da lista (C3).
- Arquivo de outra feature (`.specs/features/outra/verification.md`): fora da lista (C3).
- Pasta fora de repositório Git: R6 (C4).
- O teste existente `test_q_brief_fills_placeholders` afirma hoje `assertNotIn("Handoff", text)`; muda de sentido por este item.

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `q_brief("demo", ...)` contém, como linha inteira dentro da seção `## Rules`, o texto de R1 (`assertIn` da linha completa entre as linhas do bloco `## Rules`); `test_q_brief_fills_placeholders` troca o `assertNotIn("Handoff", text)` por essa asserção (R1)
Proof: run unit | test_q_brief_proibe_tocar_no_handoff ... ok

**C2** - Repositório temporário com commit: árvore limpa, e depois só `verification.md`, `screens.md` e `captures/x.running.png` da feature `demo` alterados ou novos: nos dois casos `main(["q-check", "demo", "--root", repo])` sai com 0 e o stdout é exatamente `q-check: só arquivos permitidos alterados\n` (R2, R3)
Proof: run unit | test_q_check_so_permitidos_sai_0 ... ok

**C3** - Mesmo repositório com `verification.md` (permitido), `tasks.md` modificado, `spec.md` apagado, `notas.txt` novo, `captures/x.png` modificado e `.specs/features/outra/verification.md` novo: sai com 1 e o stdout é exatamente as linhas `fora da lista: <XY> <caminho>` dos cinco caminhos fora da lista, em ordem, mais a linha final com `q-check: 5 arquivo(s) fora da lista; desfaça com git restore (rastreados) ou apague (novos)`; depois do comando, `git status --porcelain` é idêntico ao de antes e os arquivos têm o mesmo conteúdo (R3, R4, R5)
Proof: run unit | test_q_check_fora_da_lista_sai_1_sem_tocar ... ok

**C4** - Pasta temporária sem Git: sai com 2 e o stderr começa por `ERRO: git status falhou em ` seguido da pasta (R6)
Proof: run unit | test_q_check_fora_de_repositorio_sai_2 ... ok

**C5** - No `execute.md`, seção 4: a posição do commit do Handoff (`--phase review` e o commit) vem antes da primeira linha `orca orchestration worker-start --agent codex`, e o texto contém exatamente uma vez `python "P/scripts/dispatch.py" q-check <slug>` (R7)
Proof: run unit | test_execute_commita_handoff_antes_do_q ... ok

**C6** - A entrada `### SC-181:` do `DECISIONS.md` contém `**Problema**`, `**Decisão**`, `**Motivo**` e `**Por que não é bug**`, cada um asserido dentro da entrada, mais `q-check`, `Handoff` e `D-i` (R8)
Proof: run unit | test_decisions_q_preserva_handoff ... ok

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** LaForge registra f5af811 no DECISIONS.md
**Linear:** SC-181
**Integration branch:** feature/q-preserva-handoff
**Last integrated:** e485a75
**Dispatched:** none
**Settled:** 2026-11-15: aprovação da spec e issue: "sim"
**Attempts:** gate-proofs=1
**Reports:** 2026-11-15: T1: q-check, regra do Handoff no brief, execute.md, C1-C6; ticket gate verde; 6330af4, e485a75; 2026-11-15: Q parado: provas vermelhas (test_skills_exec.test_execute_ref_q_dispatch e outra falha); Q despachado por engano e interrompido antes de escrever; 2026-11-15: T1-fix provas: 8061c88 (test_skills_exec), 62a1af9 (test_q_skill); 910 OK; ticket gate verde nos commits do LaForge; 2026-11-15: Q: codex · FAIL, 4 achados (renomeação entre permitidos dá fora da lista; C4 sem stderr integral; C5 ordem frouxa; C6 vínculos de R8); 910 OK; q-check após o Q: 0 (só verification.md); 2026-11-15: T1-fix: 2328e05, f5af811 (renomeação; C4-C6 estritos), e320c0e, c81bbba (dist); 2026-11-15: provas vermelhas: check_decisions (f5af811 mexeu em skills/ sem DECISIONS.md); Closed corrigido pelo Picard
**Breaker:** closed
