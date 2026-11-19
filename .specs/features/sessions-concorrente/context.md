# Escrita concorrente dos arquivos de sessão: Context

**Size**: MEDIUM
**Risk triggers**: concorrência (escritas simultâneas de processos diferentes)
**Source request**: "Prossiga" (lote 3 da triagem v2, item 3.4: "Escrita concorrente de `sessions.json` [...] `scripts/starcode_common.py:147` ainda usa `.tmp` de nome fixo; não há trava em nenhum script [...] Continua *reproduzir*"; triagem v1: "Teste com escritas simultâneas não perde entrada; temporários têm nome único")

## Problem
Reproduzido em 2026-11-19, no Windows 11, com 16 processos e 64 escritas, em três rodadas:
- `crew_live.update_sessions` lê o arquivo, aplica a mudança e regrava sem trava. As 64 escritas saem com sucesso, mas o `sessions.json` termina com 9, 11 e 13 entradas: as outras se perdem.
- `starcode_common.write_session` grava num `session.tmp` de nome fixo. De 64 escritas, 10, 6 e 11 falharam com `PermissionError`.
- `set_progress` (`progress.json`) e o `git_mode.py` (ler, mudar e gravar o `session.json`) têm o mesmo ciclo sem trava.
A Ponte e o painel leem esses arquivos enquanto as sessões e os workers da Frota escrevem.

## Users
O dono e os workers paralelos da Frota (hooks a cada chamada de ferramenta).

## Success
Escritas simultâneas não perdem entrada nem falham. Os temporários têm nome único, e os hooks continuam silenciosos.

## Constraints
- Só biblioteca padrão, Windows e POSIX.
- O hook nunca derruba uma chamada de ferramenta.
- Entrada no `DECISIONS.md` (D30). O `dist/` é regenerado.

## Scope Notes
- Dentro: `sessions.json` e `crew.json` (`update_sessions`), `progress.json` (`set_progress`), `session.json` (`write_session` e o ler-mudar-gravar do `git_mode.py`).
- Fora: os demais itens do lote 3 e o `.specs/` (escrito só pelo Picard).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Mecanismo de trava | `.lock` com `msvcrt.locking`/`fcntl.flock` / arquivo criado com `O_EXCL` | Trava de SO num arquivo vizinho `<arquivo>.lock` (`msvcrt` no Windows, `fcntl` no POSIX): o SO solta a trava se o processo morrer: default (não perguntado) | 2026-11-19 |
| Tempo máximo de espera | 2 s / 5 s / 10 s | 5 s; depois disso, `TimeoutError`: default (não perguntado) | 2026-11-19 |
| Hook com trava esgotada | falhar / pular a escrita | O hook pula a escrita em silêncio (o painel se corrige na próxima chamada); os comandos de CLI (`crew_live.py`, `git_mode.py`) saem com 2 e a mensagem: default (não perguntado) | 2026-11-19 |
| Temporário | nome fixo / único | Único (`tempfile.mkstemp` na mesma pasta), com a mesma nova tentativa do `write_json` no `os.replace`: default (não perguntado) | 2026-11-19 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Concurrency and ordering | Ler, mudar e gravar sob a mesma trava |
| Failure and partial failure | O temporário de uma escrita que falhou é apagado; o arquivo final nunca fica pela metade |
| demais dimensões | N/A para este escopo |

## Facts Found
- `scripts/starcode_common.py:142-149` (`write_session`, `session.tmp` fixo).
- `scripts/crew_live.py:87-98` (`write_json`, já com `mkstemp`), `:163-187` (`update_sessions`) e `:252-264` (`set_progress`).
- `scripts/git_mode.py:55-65` (três chamadas de `write_session` depois de `read_session`).
