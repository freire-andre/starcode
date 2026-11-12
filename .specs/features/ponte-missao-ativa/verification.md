# ponte-missao-ativa verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 751ebe8
**HEAD**: 751ebe8
**Verifier**: codex · requested padrão do CLI · effective unconfirmed · rodada 2 (R7 mudou com aprovação do usuário)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_ponte.py` `test_elsewhere_picks_newest_active_worktree` | yes |
| C2 | `tests/test_ponte.py` `test_elsewhere_null_when_local_active` | yes |
| C3 | `tests/test_ponte.py` `test_elsewhere_worktree_errors_do_not_break_snapshot` | yes |
| C4 | `tests/test_ponte.py` `test_elsewhere_snapshot_is_read_only` | yes |
| C5 | `src/orca/src/panel.test.tsx` `painel mostra a missão ativa de outro worktree` | yes |
| C6 | `src/orca/src/worker.test.ts` `barra de status indica missão em outro worktree` | yes |
| C7 | `src/orca/src/worker.test.ts` `atalho foca o worktree da missão ativa`; `src/orca/src/panel.test.tsx` `painel mostra a missão ativa de outro worktree` | yes |
| C8 | `tests/test_ponte.py` `test_decisions_records_p151_2_elsewhere` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C4: a comparação anterior de tamanho e mtime não detectava toda alteração; corrigida com comparação de lista e bytes. | `tests/test_ponte.py:367-389`; commit `31953b4` adiciona comparação por conteúdo e lista | Comparar nomes e bytes dos arquivos antes e depois da execução. | `31953b4` — teste agora compara conteúdo e lista de arquivos. |
| R1: o desempate por slug não estava especificado, embora o código já o aplicasse; resolvido ao fixar o maior slug na spec e no teste. | `scripts/ponte.py:169-187`; `tests/test_ponte.py:307-320`; commit `9680f1e` | Definir o desempate de mtime igual na spec e cobri-lo no teste. | `9680f1e` — spec fixa maior slug e o teste cobre empate e ordem da listagem. |
| R7: a versão anterior tentava usar `notifications.show`, capacidade ausente no manifesto; agora a resposta exibe a mensagem no painel e não chama notificação. | `src/orca/src/worker.ts:520-541`; `src/orca/src/panel.test.tsx:270-287`; commit `751ebe8` | Retornar a mensagem e renderizá-la junto ao atalho, sem chamada de notificação. | `751ebe8` — worker retorna a mensagem e teste do painel verifica sua exibição. |
| `same_path` iguala caminhos Windows diferentes: remove a barra final e transforma `C:/` em `c:`, que designa o diretório raiz da unidade e um caminho relativo à unidade, respectivamente. Isso pode excluir um workspace distinto ou escolher o workspace errado. | `scripts/ponte.py:236-239`; comando `python -c "import importlib.util; s=importlib.util.spec_from_file_location('ponte','scripts/ponte.py'); p=importlib.util.module_from_spec(s); s.loader.exec_module(p); print(p.same_path('C:/','c:'))"` → `True`; `PureWindowsPath('C:/') == PureWindowsPath('c:')` → `False` | Normalizar caixa e separadores sem colapsar raiz absoluta em caminho relativo à unidade; acrescentar caso de teste. | `e8d79b0` (+ `7400f47` P151-3) — `same_path('C:/','c:')` agora False; `test_same_path_preserva_raiz_do_drive` falhou antes e passa. |
| C5 verifica partes do aviso por substring, não a composição/valores exatos do texto; alterações extras ou repetidas ainda passam. | `src/orca/src/panel.test.tsx:256-257` | Comparar o texto completo do aviso com ramo, fase, progresso e contagem esperados. | `1d87e72` — o teste compara o texto completo do aviso (branch, fase, `2/3`, "e mais 1"). |

## Limits

Não repeti a suíte; aceitei os resultados registrados em `proofs.md` para o HEAD 751ebe8.
Os probes foram de comparação de caminhos; não executei a Orca real para abrir workspaces.
