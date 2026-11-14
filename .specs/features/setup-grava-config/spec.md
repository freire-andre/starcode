# Setup grava o config do usuário: Spec

**Approved**: 2026-11-14 - user: "SIM"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-172
**May change**: skills/setup/SKILL.md, tests/test_config_skill.py, DECISIONS.md, dist/

## Context
Item C.2 de `starcode-triagem-v2-2026-11-13.md` (fora do Git). A seção `## 4. User config` de `skills/setup/SKILL.md:60` manda seguir `skills/config/SKILL.md` nos "steps 1–5". A gravação do config do usuário é a seção `## 6. Write` da skill `config` desde `1266819`. Resultado: no primeiro setup, o `~/.starcode/config.json` não é gravado. A tarefa é PEQUENA (sem gatilho); usa a spec curta porque o `dispatch.py` só despacha com `spec.md` (item 3.5 da triagem, aberto). Sucesso: o setup cita o intervalo que termina na gravação, e um teste impede que os dois arquivos voltem a divergir.

## Scope
- Corrigir o intervalo citado na seção `## 4. User config` da skill `setup`.
- Teste que deriva o fim do intervalo dos títulos numerados da skill `config`.
- Entrada no `DECISIONS.md` (gate D30) e `dist/` regerado.

## Non-Goals
- Mudar a skill `config` (títulos, ordem ou texto).
- Qualquer skill, comando ou perfil novo (congelamento D-i).
- Outros itens da triagem (C.3 a C.9).

## Requirements
- **R1** - The system SHALL citar, na seção `## 4. User config` de `skills/setup/SKILL.md`, a skill `config` com o intervalo `(steps 1–6)`.
- **R2** - WHEN o teste lê os títulos `## <N>. <título>` de `skills/config/SKILL.md` THEN the system SHALL exigir que o fim do intervalo `steps 1–<M>` citado na seção `## 4. User config` do setup seja igual ao `<N>` do título `Write`, de modo que renumerar a skill `config` sem atualizar o setup reprove o teste.
- **R3** - The system SHALL ter os quatro `dist/<cli>/skills/setup/SKILL.md` (claude, codex, antigravity, opencode) com `(steps 1–6)` e sem `(steps 1–5)`, regerados por `python tools/build.py`.
- **R4** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-172:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug** citando o teste de R2.

## Edge Cases
- A skill `config` sem título `Write`: o teste de R2 falha com mensagem que nomeia o título ausente (C2).
- Hífen comum em vez de travessão (`1-6`): o teste de R2 aceita `–` e `-` no intervalo (C2).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `assertIn("(steps 1–6)", sec)` na seção `## 4. User config` de `skills/setup/SKILL.md` (R1)
Proof: run unit | test_setup_cita_intervalo_ate_a_gravacao ... ok

**C2** - O teste extrai `M` de `steps 1[–-](\d+)` na seção do setup e `N` do título `## N. Write` da skill `config`, e faz `assertEqual(M, N)`; com uma cópia da skill `config` renumerada em memória (`## 7. Write`), a mesma função de comparação devolve diferença (R2)
Proof: run unit | test_intervalo_do_setup_acompanha_titulo_write ... ok

**C3** - Para cada CLI em `claude`, `codex`, `antigravity`, `opencode`: `assertIn("(steps 1–6)", t)` e `assertNotIn("(steps 1–5)", t)` em `dist/<cli>/skills/setup/SKILL.md` (R3)
Proof: run unit | test_dist_setup_cita_steps_1_6 ... ok

**C4** - `DECISIONS.md` tem `### SC-172:` com `steps 1–6` e `Por que não é bug` citando `test_intervalo_do_setup_acompanha_titulo_write` (R4)
Proof: run unit | test_decisions_setup_grava_config ... ok

## Handoff

**Phase:** review
**Size:** PEQUENA
**Git mode:** 3
**Next:** provas e done
**Linear:** SC-172
**Integration branch:** feature/setup-grava-config
**Last integrated:** 6334872
**Dispatched:** none
**Settled:** 2026-11-14: aprovação da spec: "SIM"
**Attempts:** none
**Reports:** 2026-11-14: T1: setup cita (steps 1–6), 4 testes em test_config_skill.py, SC-172 no DECISIONS.md, dist regerado; commit 648cd43; 2026-11-14: Q: codex · gpt-6-luna · FAIL, 2 achados (C2 sem Write/duplicado; C4 sem campos de R4); suíte 862 OK; 2026-11-14: T1-fix: b9acdde (C2), 137d33b (C4)
**Breaker:** closed
