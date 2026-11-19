# Escrita concorrente dos arquivos de sessão: Spec

**Approved**: 2026-11-19 - user: "Sim"

**Size**: MEDIUM
**Risk triggers**: concorrência
**Status**: Approved
**Linear**: SC-202
**May change**: scripts/starcode_common.py, scripts/crew_live.py, scripts/git_mode.py, tests/test_sessions_concorrente.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Esta spec cobre o item 3.4 da triagem v2. O discovery e a reprodução estão em `.specs/features/sessions-concorrente/context.md`. Com 16 processos e 64 escritas, o `sessions.json` perdeu de 51 a 55 entradas, e o `write_session` falhou com `PermissionError` em até 11 escritas.

## Scope
- Trava de SO e escrita atômica com temporário único, num helper só, em `starcode_common.py`.
- `update_sessions`, `set_progress`, `write_session` e o `git_mode.py` passam a ler, mudar e gravar sob a trava.

## Non-Goals
- Os escritores do `.specs/` (Handoff, lições) e o `validate_config.py`, que já usa `mkstemp`.
- Mudar o formato de qualquer arquivo.

## Decisions
None. Os defaults técnicos (trava de SO, 5 s, hook silencioso, temporário único) estão no `context.md` e valem com a aprovação desta spec.

## Requirements
- **R1** - The `starcode_common.py` SHALL ter `locked(path, timeout=5.0)`, um gerenciador de contexto que segura uma trava exclusiva do SO no arquivo vizinho `<path>.lock` (`msvcrt.locking` no Windows, `fcntl.flock` no POSIX) e levanta `TimeoutError` quando não a obtém em `timeout` segundos. Ele SHALL ter também `write_json_atomic(path, data)`: temporário único na mesma pasta (`tempfile.mkstemp`), `os.replace` com até 5 novas tentativas em `PermissionError`, e o temporário apagado se a escrita falhar.
- **R2** - WHEN 16 processos chamam `update_sessions` ao mesmo tempo, cada um com uma chave diferente, 64 vezes no total THEN o `sessions.json` SHALL terminar com as 64 entradas, e o `crew.json` SHALL contar as 64.
- **R3** - WHEN 16 processos chamam `set_progress` ao mesmo tempo com slugs diferentes (64 no total) THEN o `progress.json` SHALL terminar com os 64 slugs.
- **R4** - The `starcode_common.py` SHALL ter `update_session(cwd, mutate)`, que lê, aplica `mutate` e grava o `session.json` sob `locked`. O `write_session` e as três escritas do `git_mode.py` SHALL usar esse caminho. WHEN 16 processos gravam ao mesmo tempo chaves diferentes (64 no total) THEN nenhuma escrita SHALL falhar e o `session.json` SHALL ter as 64 chaves. Nenhum arquivo `session.tmp` de nome fixo SHALL ser criado.
- **R5** - IF a trava esgota o tempo dentro do hook (`update_sessions` chamado pelo hook) THEN o hook SHALL pular a escrita sem saída e sem erro. IF ela esgota em `crew_live.py start|stop|set|progress` ou no `git_mode.py` THEN o comando SHALL sair com 2 e a mensagem `trava ocupada: <arquivo> (tente de novo)`.
- **R6** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-<n>:` com **Problema** (com os números da reprodução), **Decisão** (`locked`, `write_json_atomic`, `update_session`, os 5 s, o hook silencioso e a saída 2), **Motivo** e **Por que não é bug** (com os testes), mais uma linha em `CHANGELOG.md` `[Unreleased]`.

## Edge Cases
- Processo morto com a trava: o SO a solta, e o próximo escritor segue (R1).
- `sessions.json` ilegível com `strict=True`: continua levantando como hoje, agora dentro da trava (R2).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - `locked` dá exclusão entre processos, solta ao sair e levanta `TimeoutError` com a trava presa por outro processo; `write_json_atomic` usa temporário único e não deixa temporário depois de falha (R1)
Proof: run unit | test_locked_e_escrita_atomica (test_sessions_concorrente.SessionsConcorrenteTests.test_locked_e_escrita_atomica) ... ok

**C2** - 16 processos e 64 chaves em `update_sessions`: 64 entradas no `sessions.json` e no `crew.json` (R2)
Proof: run unit | test_update_sessions_paralelo (test_sessions_concorrente.SessionsConcorrenteTests.test_update_sessions_paralelo) ... ok

**C3** - 16 processos e 64 slugs em `set_progress`: 64 slugs no `progress.json` (R3)
Proof: run unit | test_set_progress_paralelo (test_sessions_concorrente.SessionsConcorrenteTests.test_set_progress_paralelo) ... ok

**C4** - 16 processos e 64 chaves em `update_session`: nenhuma falha, 64 chaves, nenhum `session.tmp`; o `git_mode.py` usa `update_session` (R4)
Proof: run unit | test_update_session_paralelo (test_sessions_concorrente.SessionsConcorrenteTests.test_update_session_paralelo) ... ok

**C5** - Trava esgotada: o hook pula a escrita em silêncio; `crew_live.py set` e `git_mode.py set` saem com 2 e a mensagem exata (R5)
Proof: run unit | test_trava_esgotada (test_sessions_concorrente.SessionsConcorrenteTests.test_trava_esgotada) ... ok

**C6** - Entrada no `DECISIONS.md` com os quatro campos, os números da reprodução, os termos da Decisão, os testes e a linha no CHANGELOG (R6)
Proof: run unit | test_decisions_sessions_concorrente (test_sessions_concorrente.SessionsConcorrenteTests.test_decisions_sessions_concorrente) ... ok

## Handoff

**Phase:** review
**Size:** MEDIUM
**Git mode:** 3
**Next:** Guinan; PR; Worf
**Linear:** SC-202
**Integration branch:** feature/sessions-concorrente
**Last integrated:** 4e9283c
**Dispatched:** none
**Settled:** 2026-11-19: spec aprovada: Sim; issue SC-202 criada
**Attempts:** none
**Reports:** 2026-11-19: Q r1 FAIL: 4 achados (write_session substitui o arquivo inteiro; C1, C5 e C6 frouxos); 2026-11-19: pós-Q: f616de4; achados fechados com close-finding; 2026-11-19: done --strict verde
**Breaker:** closed
