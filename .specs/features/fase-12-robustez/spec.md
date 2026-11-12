# Fase 12 - Robustez (v1.6): Spec

**Approved**: 2026-11-12 - user: "Sim"
**Approved**: 2026-11-12 - user: "A" (revisão do R21: templates com `{{`)

**Size**: LARGE
**Risk triggers**: Irreversibilidade
**Status**: Approved

## Context

No modo Git 1 não há commits. A saída (b) do disjuntor (D27, `skills/engajar/references/execute.md` seção 6), "voltar ao último ponto bom", só existe hoje para quem tem commit integrado. Quando o disjuntor abre no modo 1, não há para onde voltar. A Fase 12 grava um snapshot da árvore de trabalho antes de cada ticket do modo 1, num ref próprio, sem commit no branch e sem mexer na árvore. A restauração depende da confirmação do usuário e só toca os caminhos do `May change` do ticket.

Além disso, McCoy e Q escolhem os testes de regressão no olho: ou rodam tudo (lento), ou esquecem os chamadores indiretos de uma função compartilhada. Um script novo monta o grafo de imports (Python e TS/JS) e devolve os testes que alcançam, direta ou indiretamente, os arquivos que mudaram. Quando não consegue mapear a mudança, devolve "rodar tudo". O conjunto nunca sai vazio.

Sucesso:
- o disjuntor no modo 1 restaura o snapshot do ticket com confirmação, sem perder arquivos fora do ticket;
- numa mudança numa função compartilhada, os testes escolhidos incluem os dos chamadores indiretos;
- numa mudança fora do grafo, o veredito é "rodar tudo".

Discovery: `.specs/features/fase-12-robustez/context.md`.

## Scope

- `scripts/snapshot.py` (novo, stdlib): `take`, `list`, `restore` e `drop` (R1–R13).
- `scripts/impact.py` (novo, stdlib): grafo de imports Python e TS/JS e seleção de testes (R14–R27).
- Fluxo:
  - `skills/engajar/references/execute.md` seções 6 e 7: snapshot antes de cada ticket no modo 1, saída (b) do disjuntor no modo 1 e `drop` no `done` (R28–R30);
  - `skills/mccoy/SKILL.md`: seleção por raio de impacto antes do gate (R31);
  - `src/briefs/q-verify.md` e `scripts/dispatch.py q-brief`: os testes de regressão escolhidos entram no brief do Q (R32–R33).
- `tools/build.py` nos 4 CLIs; testes `unittest` com repositórios Git temporários.
- Registros:
  - `DECISIONS.md` F12-n;
  - `PLANO_STARCODE.md`: o parágrafo do disjuntor no modo 1 e o texto da Fase 12;
  - `CHANGELOG.md` em `## [Unreleased]`;
  - `docs/compatibilidade.md`;
  - `dist/` regenerado.
- Aceite real em `docs/aceite/fase-12.md` (R36–R38).

## Non-Goals

- Snapshot nos modos 2–4: lá o ponto bom continua sendo o último commit integrado (`**Last integrated:**`).
- Grafo para Rust (`.rs`, `Cargo.toml`): mudança em Rust é sempre "rodar tudo".
- Reduzir a suíte dos gates: `run_gates.py` continua rodando os comandos inteiros do perfil. A seleção é só para McCoy e Q.
- Granularidade por função ou símbolo: o grafo é por arquivo. "Chamador indireto" é o arquivo que importa, direta ou transitivamente, o arquivo que mudou.
- Resolver aliases do TypeScript (`compilerOptions.paths`, `baseUrl`): com aliases em uso, a mudança em TS/JS vira "rodar tudo" (R22).
- Novo campo no Handoff ou mudança no banner e na Ponte.
- Enviar snapshots no push: os refs ficam fora de `refs/heads` e `refs/tags`.

## Requirements

### Snapshot (`snapshot.py`)

- **R1** - WHEN `python scripts/snapshot.py take <slug> <ticket> [--root DIR]` roda THEN the system SHALL montar um commit solto com a árvore de trabalho inteira: arquivos rastreados e não rastreados não ignorados pelo `.gitignore`. O commit tem como pai o HEAD e a mensagem `starcode snapshot <slug>/<ticket>`. O script grava o commit em `refs/starcode/snapshots/<slug>/<ticket>`, imprime `snapshot <slug>/<ticket> <hash curto> (<n> arquivos)` e sai com 0.
- **R2** - The system SHALL montar o snapshot com um índice temporário (`GIT_INDEX_FILE` num arquivo próprio, removido no fim, inclusive em erro). O `.git/index` real, a árvore de trabalho, o HEAD e os branches ficam iguais byte a byte antes e depois do `take`.
- **R3** - WHEN já existe snapshot para o mesmo `<slug>/<ticket>` THEN the system SHALL substituir o ref e imprimir `(substituído <hash curto antigo>)` ao fim da linha.
- **R4** - IF `<slug>` não casa `^[a-z0-9][a-z0-9-]*$`, ou `<ticket>` não casa `^[A-Za-z0-9][A-Za-z0-9._-]*$`, ou o nome do ref é recusado por `git check-ref-format` THEN the system SHALL sair com 2 e a mensagem `nome inválido para o snapshot: <valor>`, sem gravar nada.
- **R5** - IF a pasta não é um repositório Git, o repositório não tem HEAD (sem commits) ou um comando `git` falha THEN the system SHALL sair com 1 e uma linha `snapshot falhou: <passo>: <motivo>`, sem ref parcial gravado.
- **R6** - WHEN `snapshot.py list <slug> [--root DIR] [--json]` roda THEN the system SHALL listar os snapshots da feature: ticket, hash curto, data e quantidade de arquivos. Com `--json`, um array de objetos `{"ticket","commit","date","files"}`. Sem snapshots, imprime `nenhum snapshot de <slug>` (`[]` com `--json`) e sai com 0.

### Restauração

- **R7** - WHEN `snapshot.py restore <slug> <ticket> [--root DIR]` roda sem `--yes` THEN the system SHALL calcular o plano: cada caminho que casa com o `**May change**:` do ticket (em `tasks.md`; para MEDIUM, o da spec, mesma regra do `check_scope.py`) e que difere entre o snapshot e a árvore atual. O plano marca cada caminho como `voltar` (existe no snapshot) ou `remover` (não existe no snapshot). O script imprime o plano, a linha `nada foi alterado: rode de novo com --yes depois da confirmação do usuário` e sai com 0.
- **R8** - WHEN `restore` roda com `--yes` THEN the system SHALL gravar em cada caminho `voltar` o conteúdo e o bit executável do snapshot, apagar cada caminho `remover` e imprimir `restaurado <slug>/<ticket>: <v> voltaram, <r> removidos`. Caminhos fora do `May change` não são lidos para escrita nem apagados.
- **R9** - The system SHALL listar na saída do `restore` (com e sem `--yes`) os caminhos fora do `May change` que diferem do snapshot, sob o título `fora do ticket (não tocados):`. A lista tem no máximo 50 linhas mais `e mais N`.
- **R10** - IF o HEAD atual não é o pai do snapshot THEN the system SHALL sair com 1 e `HEAD mudou desde o snapshot (<pai> → <atual>): restauração recusada`, sem alterar nada.
- **R11** - IF não existe snapshot para `<slug>/<ticket>`, o ticket não está no `tasks.md` ou o `May change` dele está vazio THEN the system SHALL sair com 1 e a mensagem com o motivo, sem alterar nada.
- **R12** - IF a escrita de um caminho falha no meio do `--yes` THEN the system SHALL parar nesse caminho, imprimir os caminhos já restaurados, o caminho que falhou com o motivo e os que faltaram, e sair com 1. Rodar de novo com `--yes` termina a restauração (idempotente).
- **R13** - WHEN `snapshot.py drop <slug> [--root DIR]` roda THEN the system SHALL apagar todos os refs `refs/starcode/snapshots/<slug>/*`, imprimir `removidos <n> snapshots de <slug>` e sair com 0, inclusive com n = 0.

### Raio de impacto (`impact.py`)

- **R14** - WHEN `python scripts/impact.py select [--root DIR] [--json] (<arquivo>... | --diff <base>[..<head>])` roda THEN the system SHALL listar os arquivos do repositório com `git ls-files -co --exclude-standard`, montar o grafo de imports dos arquivos Python (`.py`) e TS/JS (`.ts`, `.tsx`, `.mts`, `.cts`, `.js`, `.jsx`, `.mjs`, `.cjs`) e devolver os testes que alcançam, direta ou transitivamente, algum arquivo mudado. Com `--diff`, os mudados são os de `git diff --name-only` do intervalo mais os não rastreados (sem `..<head>`, a árvore de trabalho contra `<base>`).
- **R15** - The system SHALL tratar como teste: em Python, `test_*.py`, `*_test.py` e qualquer `.py` sob uma pasta `tests/` ou `test/`; em TS/JS, `*.test.*`, `*.spec.*` e arquivos sob `__tests__/`.
- **R16** - The system SHALL resolver os imports Python com o `ast` da stdlib: `import a.b`, `from a.b import c` (também `a/b/c.py` quando `c` é módulo) e imports relativos (`from . import x`, `from ..m import y`) a partir da pasta do arquivo. Um nome absoluto casa com todo arquivo do repositório cujo caminho termina em `a/b.py` ou `a/b/__init__.py`. Com mais de um candidato, liga a todos (conservador, cobre `sys.path` montado em teste). Sem candidato, é externo (stdlib ou pacote) e fica fora do grafo.
- **R17** - The system SHALL resolver os imports TS/JS por expressão regular: `import ... from '<esp>'`, `import '<esp>'`, `export ... from '<esp>'`, `import('<esp>')` e `require('<esp>')`. Só especificadores relativos (`./`, `../`) viram arestas, testando o caminho exato, as extensões de R14 e `index.<ext>`. Especificador sem prefixo relativo é pacote externo.
- **R18** - WHEN um arquivo mudado é ele mesmo um teste THEN the system SHALL incluí-lo no conjunto.
- **R19** - The system SHALL seguir os dependentes reversos até o fecho transitivo, visitando cada arquivo uma vez (import circular não entra em loop), e registrar para cada teste escolhido uma cadeia mínima até o arquivo mudado.
- **R20** - IF algum arquivo mudado não é Python nem TS/JS, ou foi apagado, ou não está na lista do R14 THEN the system SHALL devolver o veredito `rodar tudo` com o motivo `fora do grafo: <arquivos>`.
- **R21** - IF algum arquivo Python ou TS/JS do repositório não pode ser lido ou analisado (erro de sintaxe, codificação, mais de 1 MiB) THEN the system SHALL devolver `rodar tudo` com o motivo `grafo incompleto: <arquivo>: <erro>`. Exceção: um `.py` com erro de sintaxe cujo conteúdo tem o marcador `{{` (template de perfil, não importável) fica fora do grafo, sem forçar `rodar tudo`.
- **R22** - IF há um `tsconfig.json` ou `jsconfig.json` com `compilerOptions.paths` ou `baseUrl`, ou algum arquivo importa um especificador que começa com `@/` ou `~/`, e algum arquivo mudado é TS/JS THEN the system SHALL devolver `rodar tudo` com o motivo `aliases do TypeScript não resolvidos`.
- **R23** - IF a busca termina sem nenhum teste THEN the system SHALL devolver `rodar tudo` com o motivo `nenhum teste alcança <arquivos>`. O resultado nunca é um conjunto vazio.
- **R24** - IF não há arquivo mudado (lista vazia ou diff vazio) THEN the system SHALL devolver `rodar tudo` com o motivo `nenhuma mudança informada`.
- **R25** - WHEN o veredito é uma seleção THEN the system SHALL imprimir em texto a linha `selecionados <n> testes` e um teste por linha com a cadeia (`tests/test_x.py <- scripts/a.py <- scripts/b.py`). No veredito `rodar tudo`, imprime `rodar tudo: <motivo>`. Nos dois casos sai com 0.
- **R26** - WHEN `--json` é usado THEN the system SHALL imprimir `{"verdict": "selected"|"run-all", "tests": [...], "chains": {"<teste>": [...]}, "reason": "<motivo ou vazio>", "changed": [...]}`. No `run-all`, `tests` é `[]` e `reason` não é vazio.
- **R27** - IF a pasta não é um repositório Git ou o `git` falha THEN the system SHALL sair com 1 e `impact falhou: <passo>: <motivo>`. Argumentos inválidos (nenhum arquivo e nenhum `--diff`, ou os dois juntos) saem com 2.

### Fluxo

- **R28** - The system SHALL descrever em `execute.md` seção 7 que, no modo 1, antes de cada despacho do LaForge, o Picard roda `snapshot.py take <slug> <ticket>` e registra a linha impressa com `handoff.py set --report`. Se o `take` falha, o ticket não é despachado (falha de registro interrompe o fluxo).
- **R29** - The system SHALL descrever em `execute.md` seção 6 que, no modo 1, a saída (b) do disjuntor é o snapshot do ticket que falhou. O Picard roda `restore` sem `--yes`, mostra o plano e a lista "fora do ticket" e pede um sim para essa restauração. Só então roda com `--yes` e grava `--breaker closed`. Com `**Dispatched:**` não fechado, a restauração não é oferecida antes do `worker-stop`.
- **R30** - The system SHALL descrever em `execute.md` seção 7 que, no modo 1, depois de `--phase done`, o Picard roda `snapshot.py drop <slug>`.
- **R31** - The system SHALL descrever em `skills/mccoy/SKILL.md` que, depois do teste de regressão e da correção, o McCoy roda `impact.py select --diff <base>` (base = `baseBranch` do config) e roda os testes escolhidos, ou a suíte inteira no `rodar tudo`, antes do gate do ticket. A linha do veredito entra no relatório dele.
- **R32** - WHEN `dispatch.py q-brief` roda THEN the system SHALL calcular `impact.py select --diff <base>..<head>` e preencher no brief do Q o bloco `{{regression}}`: a lista de testes com as cadeias, ou `rodar tudo: <motivo>`. Se o `impact.py` falha, o bloco diz `seleção indisponível: <motivo>; rode a suíte inteira`, e o brief é gerado assim mesmo.
- **R33** - The system SHALL acrescentar a `src/briefs/q-verify.md` uma regra: o Q roda os testes de regressão do bloco `{{regression}}` em HEAD (no `rodar tudo`, a suíte inteira) e registra o resultado em `## Limits`. O brief continua autocontido e não cita caminhos do plugin.

### Build e registros

- **R34** - WHEN `python tools/build.py` roda THEN the system SHALL levar `snapshot.py`, `impact.py` e o brief atualizado para os 4 CLIs. `build.py --check` falha se `dist/` divergir da fonte.
- **R35** - The system SHALL registrar: (1) as decisões F12-n em `DECISIONS.md`, entre elas o índice temporário no lugar do `git stash create` e o ref `refs/starcode/snapshots/<slug>/<ticket>`; (2) a atualização do texto da Fase 12 e do parágrafo do disjuntor no `PLANO_STARCODE.md`; (3) as entradas em `## [Unreleased]` no `CHANGELOG.md`; (4) as linhas de snapshot e raio de impacto em `docs/compatibilidade.md`.

### Aceite

- **R36** - WHEN o aceite do snapshot roda num repositório temporário fora do StarCode, no modo 1, com um ticket cujo `May change` é `src/` THEN the system SHALL mostrar a sequência: (1) `take` antes do ticket; (2) edições do "ticket" em `src/` (um arquivo alterado e um criado); (3) uma edição do usuário em `notas.md` (fora do ticket); (4) três `--attempt` com falha abrindo o disjuntor; (5) `restore` sem `--yes` mostrando o plano e `notas.md` em "fora do ticket"; (6) `restore --yes`. No fim, `src/` está igual ao snapshot (o arquivo criado foi removido), `notas.md` mantém a edição e o `git status` não mostra commit novo no branch.
- **R37** - WHEN o aceite do raio de impacto roda no próprio repositório StarCode THEN the system SHALL mostrar dois resultados. Uma mudança simulada numa função de `scripts/gates/gates_common.py` seleciona ao menos um teste que alcança o arquivo só por um importador intermediário (cadeia com 3 ou mais elos). Uma mudança num `.md` dá `rodar tudo: fora do grafo`. Na fixture `aceite/telas` (TS), uma mudança em `src/greeting.ts` seleciona `src/greeting.test.ts`.
- **R38** - The system SHALL registrar o aceite em `docs/aceite/fase-12.md`: comandos, saídas relevantes e os hashes dos snapshots. O arquivo traz `**Resultado**: aprovado` só quando R36 e R37 foram atendidos.

## Data & Contracts

- Ref do snapshot: `refs/starcode/snapshots/<slug>/<ticket>`. O plano escrevia `refs/starcode/snapshots/<ticket>`. O `<slug>` entra porque IDs de ticket (`T1`, `T2`) se repetem entre features, e porque o `drop` apaga por feature. Fica fora de `refs/heads`, então `git push` de branch não o envia.
- Commit do snapshot: árvore = árvore de trabalho (rastreados + não rastreados não ignorados); pai = HEAD no momento do `take`; mensagem `starcode snapshot <slug>/<ticket>`. Nenhum branch aponta para ele.
- Saída do `restore` (texto):

```
plano <slug>/<ticket> (May change: src/)
  voltar   src/app.py
  remover  src/novo.py
fora do ticket (não tocados):
  notas.md
nada foi alterado: rode de novo com --yes depois da confirmação do usuário
```

- Saída do `impact.py` (texto):

```
selecionados 2 testes
  tests/test_run_gates.py <- scripts/gates/run_gates.py <- scripts/gates/gates_common.py
  tests/test_gates.py <- scripts/gates/gates_common.py
```

  ou `rodar tudo: fora do grafo: README.md`. O JSON segue o R26.
- Bloco `{{regression}}` no brief do Q: a mesma saída em texto do `impact.py`.

## States

- `take`: sucesso (ref gravado), nome inválido (2), erro de Git (1, nada gravado).
- `restore`: plano (sem `--yes`, nada alterado), restaurado, recusado (HEAD mudou, sem snapshot, ticket sem `May change`), parcial (falha no meio, lista do que faltou).
- `impact`: `selected` (n ≥ 1), `run-all` (com motivo), erro (1 ou 2).

## Edge Cases

- Árvore de trabalho sem mudanças: o snapshot tem a árvore do HEAD e a restauração continua tendo alvo.
- Arquivo staged e depois alterado de novo: o snapshot guarda o conteúdo da árvore de trabalho, não o do índice.
- Arquivo ignorado pelo `.gitignore` dentro do `May change` (ex.: `src/__pycache__/`): não entra no snapshot nem no plano de restauração. Nunca é apagado.
- Bit executável mudado sem mudança de conteúdo: aparece como `voltar` no plano.
- Fim de linha: o conteúdo é gravado com os bytes do blob, sem conversão. Com `core.autocrlf` ativo, a diferença de fim de linha não conta como mudança no plano (comparação depois do filtro do Git, via `git diff`).
- Caminho com espaço ou acento: aceito; caminho que sai da raiz do repositório (`..`) no `May change` é ignorado com aviso.
- `__init__.py` mudado: os importadores do pacote entram no grafo pela regra `a/b/__init__.py` (R16).
- Import dinâmico (`importlib.import_module("x")`, `require(variavel)`): não é visto. O limite fica registrado em `docs/compatibilidade.md`. Os gates continuam rodando a suíte inteira, então a seleção nunca é a última barreira.
- Repositório muito grande: a varredura lê cada arquivo uma vez; arquivo acima de 1 MiB leva ao `rodar tudo` (R21).

## Decisions

| Item | Options | Status |
|---|---|---|
| Como montar o snapshot | índice temporário com rastreados + não rastreados não ignorados (cobre arquivos novos do ticket) · `git stash create` como no plano (perde arquivos novos) | approved - user: "Índice temporário (Recomendado)" |
| Escopo da restauração | só os caminhos do `May change` do ticket, arquivo novo dentro dele removido · tudo que difere do snapshot (arrisca desfazer edições do usuário) | approved - user: "Só o May change (Recomendado)" |
| Linguagens do grafo | Python + TS/JS, Rust = rodar tudo · + Rust (macros e re-exports erram o mapeamento) · só Python | approved - user: "Python + TS/JS (Recomendado)" |
| Onde a seleção vale | só McCoy e Q, gates com a suíte inteira · também nos gates do ticket (gate dependeria do grafo) | approved - user: "Só McCoy e Q (Recomendado)" |
| Templates com `{{` no grafo (R21) | fora do grafo, sem forçar rodar tudo (templates não são importáveis; sem isso o R37 falha no StarCode) · exclusão só por pasta `*/template/` · R21 estrito e R37 ajustado | approved - user: "A" |

## Open Questions
None.
