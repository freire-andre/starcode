# Aceite da Fase 12 (SC-156): snapshot do modo 1 e raio de impacto

**Resultado**: aprovado

Rodado pelo LaForge (T8) em 2026-11-12, em repositórios temporários fora do StarCode (não commitados). R36 e R37 atendidos; as evidências estão nas seções abaixo.

## Snapshot (R36)

**Resultado**: aprovado

Repositório temporário com `.specs/features/aceite/tasks.md` mínimo (ticket `T1`, `May change: src/`), um commit e `src/app.py`, `notas.md`. Modo Git 1 gravado com `python scripts/git_mode.py --cwd <repo> set 1`.

Sequência e saídas relevantes:

```
$ python scripts/git_mode.py --cwd <repo> set 1
OK: modo Git 1 (somente código local (sem commit)) gravado em <repo>\.git\starcode\session.json
$ python scripts/snapshot.py take aceite T1 --root <repo>
snapshot aceite/T1 b2a734f (3 arquivos)
$ git rev-list --count HEAD
1
(altera src/app.py, cria src/novo.py, edita notas.md)
$ python scripts/handoff.py set aceite --attempt gate-x=fail --root <repo>     (3 vezes)
DISJUNTOR ABERTO: open (gate-x, attempts 3/3) (D27): pare e ofereça as duas saídas
$ python scripts/snapshot.py restore aceite T1 --root <repo>
plano aceite/T1 (May change: src/)
  voltar   src/app.py
  remover  src/novo.py
fora do ticket (não tocados):
  .specs/features/aceite/tasks.md
  notas.md
nada foi alterado: rode de novo com --yes depois da confirmação do usuário
$ python scripts/snapshot.py restore aceite T1 --yes --root <repo>
restaurado aceite/T1: 1 voltaram, 1 removidos
```

Hash do snapshot: `b2a734fc1db6d7da699fcf865de5b3cbfdcc5735`, guardado em `refs/starcode/snapshots/aceite/T1`.

Conferência depois do `--yes`:

- `src/app.py` voltou a `print("v1")`; `src/novo.py` foi removido (`ls src` mostra só `app.py`).
- `notas.md` manteve a edição do usuário (`notas v1` + `edição do usuário`).
- `git status --short`: só `notas.md` e o `tasks.md` (reescrito pelo handoff), ambos fora do `May change`; nenhum `src/`.
- `git rev-list --count HEAD`: `1`, igual ao de antes: nenhum commit criado.

Ocorrência: a primeira tentativa usou `## Tarefas` no `tasks.md` e o `restore` recusou com `ticket T1 não está no tasks.md de aceite`; o cabeçalho exigido é `## Tasks`. O repositório foi refeito e a sequência acima é a da segunda execução.

## Raio de impacto (R37)

**Resultado**: aprovado

No StarCode, `python scripts/impact.py select scripts/gates/gates_common.py` selecionou 20 testes, com cadeias de 3 ou mais elos, por exemplo:

```
selecionados 20 testes
  scripts/gates/gates_common.py <- dist/antigravity/scripts/dispatch.py <- dist/antigravity/scripts/crew_live.py <- dist/antigravity/scripts/ponte.py <- tests/test_ponte.py
  scripts/gates/gates_common.py <- tests/test_gates.py
```

Arquivo fora do grafo:

```
$ python scripts/impact.py select README.md
rodar tudo: fora do grafo: README.md
```

Na cópia preparada por `python tools/aceite.py preparar telas --destino <tmp>`:

```
$ python scripts/impact.py select src/greeting.ts --root <tmp>
selecionados 2 testes
  src/greeting.ts <- src/greeting.test.ts
  src/greeting.ts <- src/main.ts <- src/ui.test.ts
```

## Pendências

- Nenhuma.
