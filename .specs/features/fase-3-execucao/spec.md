# Fase 3 — Execução sequencial e verificação: Spec

**Approved**: 2026-11-04 - user: "sim"

**Size**: LARGE
**Risk triggers**: Concorrência e estado
**Status**: Approved

## Context

O StarCode planeja (Troi → Spock → Data) e publica no Linear, mas para em `published`. Esta fase entrega a execução no Claude Code: o Picard cria o ramo de integração, despacha um LaForge por ticket como worker da Orca com contexto limpo, integra cada ticket, roda `check_proofs`, despacha o Q em outra família de modelo, conduz o ciclo de correção pós-Q e fecha com `validate_verification`. Inclui o disjuntor, a lista fechada de paradas e o escritor único do Handoff. Sucesso: o roteiro de aceite da SC-10 passa no sandbox com a feature task-priority. Discovery: `.specs/features/fase-3-execucao/context.md`.

## Scope

- Gates novos em `scripts/gates/`: `check_proofs.py`, `validate_verification.py`, `check_scope.py`; estágios novos no `run_gates.py`.
- Skill `engajar` (Picard): ramo de integração, despacho sequencial, espera, vínculo com a issue, integração, Q, ciclo pós-Q, disjuntor, status e comentários no Linear.
- Skills novas `laforge`, `mccoy`, `q` e o briefing `src/briefs/q-verify.md`.
- `scripts/handoff.py` com os campos de execução; banner com disjuntor e verificação degradada.
- Build (`tools/build.py`), testes unitários, evals de roteamento das skills novas, `DECISIONS.md` (F3-*), `CREDITS.md` e `docs/aceite/fase-3.md`.

## Non-Goals

- Modo Frota / despacho paralelo (Fase 7).
- Paridade e hooks em Codex, Antigravity e OpenCode (Fases 4 e 5); só o Q roda no Codex, como worker, sem plugin StarCode.
- Review de PR (Worf, v1.3), retro (Guinan), verificação de telas (D25), snapshot do modo 1 (Fase 12).
- Push, PR e merge no ramo base automáticos: seguem o modo Git e as autorizações já existentes.
- Remover worktrees ou ramos dos tickets.
- Alterar as skills `troi`, `spock`, `data` além de apontar para o próximo passo.

## Requirements

Convenções: `<slug>` é a feature; `B` é o ramo base do config do repositório; `I` é o ramo de integração `feature/<slug>`; "relatório do worker" é o texto de até 5 linhas que o worker devolve no `worker_done`.

Gates:

- **R1** - WHEN `check_proofs.py <slug>` roda THEN the system SHALL executar cada comando `**Build**:`, cada `**Run <name>**:` uma vez e cada `Proof:` isolado do `## Checks` (do `tasks.md`, ou do `spec.md` na MÉDIA) e gravar `.specs/features/<slug>/proofs.md` com `**HEAD**:`, `**Tree**:`, `**Result**:` e uma linha `pass`/`fail` por check e por Build.
- **R2** - The system SHALL considerar uma prova `run <name> | <palavras>` aprovada só quando todas as palavras depois de `|` aparecem, nessa ordem, numa mesma linha da saída daquele run.
- **R3** - IF a árvore tem mudanças não commitadas quando `check_proofs.py` roda THEN the system SHALL gravar `**Tree**: dirty (modo 1)` no `proofs.md` e sair com código 1, mesmo com todas as provas `pass`.
- **R4** - WHEN `validate_verification.py <slug>` roda THEN the system SHALL sair com código 1 se faltar `proofs.md` ou `verification.md`, se o `proofs.md` for de outro commit que não o HEAD ou de árvore suja, se um check não tiver linha `pass` no `proofs.md` ou linha com teste no `## Checks` do `verification.md`, se um achado de `## Findings` não tiver commit na coluna `Closed`, ou se faltar a linha `**Approved**:` no `spec.md` ou no `tasks.md`.
- **R5** - IF o `verification.md` tem `**Verification:** degraded` ou `**Verification:** self-verified` THEN `validate_verification.py` SHALL imprimir o aviso `verificação degradada` e sair com código 0 só quando todo o resto passar, e com `--strict` SHALL sair com código 1.
- **R6** - WHEN `check_scope.py <slug> <ticket> <base>..<head>` roda THEN the system SHALL sair com código 1 e listar cada arquivo alterado no intervalo que esteja fora do `**May change**:` do ticket, ou que seja `.specs/STATE.md`, ou que altere a seção `## Handoff` de um artefato da feature.
- **R7** - The system SHALL aceitar em `run_gates.py` os estágios `ticket` (`check_scope` + `check_commit`), `proofs` (`check_proofs`) e `done` (`validate_verification`), imprimindo o VEREDITO primeiro como nos estágios existentes.

Picard — execução:

- **R8** - WHEN a feature GRANDE/COMPLEXA está `published` e o modo Git é 2, 3 ou 4 THEN the system SHALL criar `I` a partir de `B` (ou reutilizar `I` se já existir) e gravar `**Integration branch:** feature/<slug>` no Handoff antes do primeiro despacho.
- **R9** - The system SHALL despachar no máximo um LaForge por vez por feature, escolhendo o primeiro ticket do `tasks.md` cujas dependências estão integradas.
- **R10** - WHEN o Picard despacha um ticket THEN the system SHALL gravar `**Dispatched:**` (ticket, issue, HEAD de `I`) no Handoff antes de rodar `orca orchestration worker-start --agent <cli do laforge> --model <modelo do laforge> --worktree new-child --base-branch feature/<slug> --spec-file <briefing do ticket>`, e depois acrescentar o ID do despacho e o `model` do resultado.
- **R11** - WHEN o `worker-start` devolve o worktree novo THEN the system SHALL rodar `orca worktree set --worktree <novo> --linear-issue <ID>` antes de esperar o worker.
- **R12** - The system SHALL esperar o fim do worker com `orca orchestration check --wait --types worker_done --timeout-ms <limite>`, com limite padrão de 3.600.000 ms.
- **R13** - IF o worker termina com falha, termina sem relatório ou o limite de espera expira THEN the system SHALL não integrar o ticket, comentar na issue o motivo em uma linha e contar uma tentativa do disjuntor com o identificador `worker-<ticket>`.
- **R14** - WHEN o worker termina com sucesso THEN the system SHALL rodar `run_gates.py ticket <slug> <ticket>` no intervalo `<HEAD de I no despacho>..<HEAD do ramo do ticket>` e só com VEREDITO VERDE integrar o ramo do ticket em `I` com `git merge --no-ff`, sem pedir autorização (D11).
- **R15** - IF a integração em `I` tem conflito THEN the system SHALL abortar o merge (`git merge --abort`), deixar `I` no commit anterior e parar com a lista dos arquivos em conflito.
- **R16** - WHEN um ticket é integrado THEN the system SHALL gravar no Handoff `**Last integrated:**` com o commit, transcrever o relatório do worker, comentar na issue "integrado em `I`" com o hash curto do commit e só então despachar o próximo ticket, sem perguntar ao usuário.
- **R17** - IF já existe `**Dispatched:**` sem integração quando o Picard retoma THEN the system SHALL consultar o despacho com `orca orchestration worker-show` antes de qualquer novo despacho e nunca iniciar um segundo worker para o mesmo ticket enquanto o primeiro não estiver encerrado.
- **R18** - WHEN o último ticket é integrado THEN the system SHALL rodar `run_gates.py proofs <slug>` no HEAD de `I` e, com VEREDITO VERDE, gravar `**Phase:** review` no Handoff e despachar o Q.

Q — verificação independente:

- **R19** - The system SHALL despachar o Q com `orca orchestration worker-start --agent <cli do q> [--model <modelo do q>] --worktree <worktree de I> --spec-file <briefing>`, onde o briefing é `src/briefs/q-verify.md` preenchido com os caminhos de `spec.md`, `tasks.md`, `proofs.md`, o intervalo `<B>..<HEAD de I>` e o caminho de saída `verification.md`, sem o histórico da sessão.
- **R20** - The system SHALL usar como CLI do Q o `codex`; IF o despacho do `codex` falha THEN the system SHALL tentar o `antigravity` com um modelo Gemini e, se também falhar, rodar o Q como subagente de contexto limpo e marcar `**Verification:** self-verified`.
- **R21** - IF a família de modelo do Q (pela tabela `families` do `crew.yaml`, ou pelo prefixo do CLI quando o modelo é o padrão do CLI) é a mesma do LaForge THEN the system SHALL avisar o usuário em uma linha e gravar `**Verification:** degraded` no `verification.md`.
- **R22** - WHEN o Q termina THEN the system SHALL registrar no `verification.md` e no Handoff o CLI, o modelo pedido (campo `model` do resultado do `worker-start`) e o modelo efetivo lido com `worker-read`, ou `model: unconfirmed` quando a leitura não o mostra.
- **R23** - IF o diff do Q altera qualquer arquivo além de `.specs/features/<slug>/verification.md` THEN the system SHALL descartar essas alterações extras antes de commitar o `verification.md` e citar os arquivos no comentário de revisão.

Ciclo pós-Q (4.6):

- **R24** - WHEN o `verification.md` tem ao menos um achado aberto THEN the system SHALL despachar um único LaForge no worktree de `I` com todos os achados num só briefing, e cada correção SHALL ser um commit com `Refs: <ID>` que cita o achado.
- **R25** - WHEN o LaForge da correção termina THEN the system SHALL rodar de novo `run_gates.py proofs <slug>` e `run_gates.py done <slug>` no novo HEAD, sem despachar o Q outra vez.
- **R26** - IF uma correção exige mudar um requisito da spec THEN the system SHALL parar, propor a mudança da spec e despachar o Q de novo só depois da nova aprovação.
- **R27** - IF um achado continua aberto depois do ciclo THEN the system SHALL mostrar ao usuário o achado e a evidência e não mover a issue para revisão.

Status e Linear:

- **R28** - WHEN o LaForge começa um ticket THEN the system SHALL mover a issue para o estado mapeado como `started` e adicionar a label `crew:laforge`.
- **R29** - WHEN `run_gates.py done <slug>` sai VERDE THEN the system SHALL mover as issues da feature para o estado `review` do config ou, se não houver, comentar "pronto para revisão" com o HEAD, o resultado das provas e o veredito do Q.
- **R30** - IF a verificação é degradada (`self-verified`, `degraded` ou modo 1) THEN the system SHALL comentar "verificação degradada" com o motivo nas issues da feature e o banner SHALL mostrar a linha `Verificação: degradada (<slug>)`.
- **R31** - The system SHALL mover uma issue para `completed` só com confirmação explícita do usuário na mesma sessão, com `run_gates.py done` VERDE, e nunca no modo 1.

Modo 1:

- **R32** - WHILE o modo Git é 1 the system SHALL rodar a feature num único worktree, com os tickets em sequência na mesma árvore, sem ramo de integração e sem commits, e o Q SHALL receber `git diff <B>` da árvore de trabalho.
- **R33** - WHILE o modo Git é 1 the system SHALL fechar cada achado do Q com a marca de verificação degradada na coluna `Closed` e exibir o resultado como verificação degradada.

Disjuntor e paradas:

- **R34** - The system SHALL exigir que cada relatório de worker com falha traga um identificador estável do erro e o número da tentativa, e SHALL contar as tentativas por identificador no Handoff, zerando a contagem daquele identificador num sucesso.
- **R35** - WHEN o mesmo identificador falha pela 3ª vez THEN the system SHALL gravar `**Breaker:** open (<id>, attempts 3/3)`, não fazer uma 4ª tentativa e apresentar as 3 tentativas com duas saídas: (a) repensar a abordagem, (b) voltar ao último commit integrado de `I`.
- **R36** - WHEN uma sessão começa com `**Breaker:** open` no Handoff THEN o banner SHALL mostrar `Disjuntor aberto: <slug> (<id>)` e o Picard SHALL propor as duas saídas antes de qualquer despacho.
- **R37** - The system SHALL parar a execução só pelos motivos da lista fechada (D29) e SHALL seguir para o próximo ticket liberado sem perguntar quando o anterior foi integrado.

Escritor único:

- **R38** - The system SHALL proibir no briefing do LaForge, do McCoy e do Q a escrita em `.specs/STATE.md` e na seção `## Handoff`, e o Picard SHALL recusar a integração de um ticket cujo `check_scope.py` acuse essa escrita (R6).
- **R39** - The system SHALL gravar o Handoff só por `scripts/handoff.py set`, com campos para `--dispatched`, `--integration-branch`, `--last-integrated`, `--breaker` e `--report`.

Skills dos workers:

- **R40** - The `laforge` skill SHALL implementar só o ticket do briefing, alterar só os arquivos do `**May change**:`, escrever o teste antes do código (TDD), rodar as provas do ticket e fazer um commit por tarefa com Conventional Commits e o rodapé `Refs: <ID>` validado por `check_commit.py` (modos 2–4).
- **R41** - IF o LaForge precisa alterar um arquivo fora do `**May change**:` THEN the `laforge` skill SHALL parar e devolver no relatório o arquivo e o motivo, sem alterá-lo.
- **R42** - WHEN uma prova do ticket fica vermelha duas vezes com o mesmo identificador THEN the `laforge` skill SHALL acionar a skill `mccoy` na mesma sessão do worker antes da 3ª tentativa.
- **R43** - The `mccoy` skill SHALL reproduzir a falha com um teste de regressão antes de corrigir, alterar só arquivos do `**May change**:` e devolver no relatório o identificador do erro, a causa e o teste criado.
- **R44** - The `q` skill e o `src/briefs/q-verify.md` SHALL, para cada check, dizer se o teste falharia com a afirmação falsa, rodar exemplos não citados como testes descartáveis sem commitá-los, apontar asserções mais frouxas que o critério e escrever só o `verification.md` no formato de R4.
- **R45** - The system SHALL fazer cada worker terminar com um relatório de até 5 linhas: o que mudou, gates com resultado, commits, pendências e tentativas do disjuntor.

Entrega:

- **R46** - The system SHALL gerar `laforge`, `mccoy` e `q` em `dist/claude` pelo `tools/build.py`, com `build --check` e `claude plugin validate dist/claude --strict` verdes.
- **R47** - The system SHALL ter testes unitários para `check_proofs.py`, `validate_verification.py`, `check_scope.py`, os estágios novos do `run_gates.py`, os campos novos do `handoff.py` e as linhas novas do banner, e evals de roteamento com frases de disparo das três skills novas.
- **R48** - The system SHALL registrar em `DECISIONS.md` cada decisão da fase (F3-*), a origem dos gates adaptados em `CREDITS.md` e a evidência de cada roteiro de aceite da SC-10 em `docs/aceite/fase-3.md`.

## Data & Contracts

- `proofs.md`: `**HEAD**: <sha>`, `**Tree**: clean | dirty (modo 1)`, `**Result**: <n> pass, <m> fail`, tabela `| Check | Proof | Result |` com uma linha por check e uma `Build`, e `## Output` com a saída de cada run.
- `verification.md`: `**Verdict**: PASS | FAIL`, `**Proofs**: proofs.md at <sha>`, `**Verifier**: <cli> · requested <model> · effective <model | unconfirmed>`, `**HEAD**: <sha>`, opcional `**Verification:** degraded | self-verified`; `## Checks` (`| Check | Test | Holds |`) e `## Findings` (`| Finding | Evidence | Fix | Closed |`).
- Handoff (campos novos via `handoff.py`): `**Integration branch:**`, `**Last integrated:**`, `**Dispatched:** <ticket> · <issue> · base <sha> · dispatch <id> · model <pedido>`, `**Breaker:** closed | open (<id>, attempts 3/3)`, `**Attempts:** <id>=<n>, ...`, `**Reports:**` (um item por relatório).
- Briefing do worker: o bloco do ticket no `tasks.md` (5 blocos + `**May change**:`) acrescido das regras fixas do worker (R38, R45); passado por `--spec-file`.
- `src/briefs/q-verify.md`: modelo com marcadores `{{spec}}`, `{{tasks}}`, `{{proofs}}`, `{{range}}`, `{{output}}`, preenchido pelo Picard num arquivo temporário.

## States

- Feature: `published` → `execute` (despachos e integrações) → `review` (provas verdes, Q despachado e ciclo pós-Q) → `done`.
- Ticket: aguardando dependências → despachado → integrado | falhou (tentativa contada) | bloqueado (disjuntor).
- Verificação: normal | degradada (`self-verified`, `degraded` ou modo 1).
- Falha parcial: um ticket com falha não impede retomar os demais depois da decisão do usuário; nada é integrado sem `check_scope` verde.

## Edge Cases

- Orca indisponível no despacho: parada com a linha exata do erro (D29 item 3), sem contar tentativa.
- Codex com hooks sem trust (`agent-hooks-review-prompt`, F0-1): o Picard cai para o Antigravity (R20) e avisa.
- Modelo recusado pelo CLI: avisa e pergunta; não troca sozinho.
- `I` já existe com commits de outra sessão: reutiliza; a evidência do Git vence o Handoff.
- Worker que commita no ramo errado ou não commita nada: `check_scope` sem commits no intervalo conta como falha `worker-<ticket>`.
- Ticket cujo briefing não tem `**May change**:`: não é despachado (o gate `validate_tasks` já barra).
- Q que não escreve `verification.md`: falha do despacho, segue a cascata de R20.
- Prova de `run` cujo filtro não seleciona nenhum teste: reprovada por R2 (sem a linha com o marcador).
- Compactação no meio da execução: retoma pelo Handoff e por R17.
- Windows: comandos de prova rodam no bash do Git for Windows, como no tlc.

## Decisions

| Item | Options | Status |
|---|---|---|
| Publicação dos tickets desta fase | sub-issues da SC-10 (sem projeto novo) · projeto novo no time SC · não publicar | approved - user: "Sub-issues da SC-10" |
| Feature do aceite | task-priority (3 tickets, publicada) · csv-import-export (5 tickets) · feature nova | approved - user: "task-priority" |
| CLI do Q | codex com cascata para antigravity e self-verified (R20) · só codex · antigravity primeiro | approved - default do Spock (não perguntado; confirmado na aprovação da spec) |
| Onde roda o McCoy | skill dentro do worker do LaForge (sem custo de outro worker) · worker próprio (contexto limpo, mais caro) | approved - default do Spock (não perguntado; confirmado na aprovação da spec) |
| Espera pelo worker | `check --wait --types worker_done` com limite de 1 h (R12) · o usuário avisa quando o worker termina | approved - default do Spock (não perguntado; confirmado na aprovação da spec) |
| Integração do ticket | `merge --no-ff` (preserva o ramo do ticket) · squash (histórico curto, perde commits por tarefa) · rebase | approved - default do Spock (não perguntado; confirmado na aprovação da spec) |
| Escritor único verificado | `check_scope.py` antes da integração (determinístico) · só a regra no briefing | approved - default do Spock (não perguntado; confirmado na aprovação da spec) |
| Aceite do modo 1 | mesma feature num worktree novo a partir do base, sem commits · outra feature | approved - default do Spock (não perguntado; confirmado na aprovação da spec) |
| Achado plantado | o Picard planta uma asserção frouxa num commit de `I` antes do Q · o usuário planta | approved - default do Spock (não perguntado; confirmado na aprovação da spec) |

## Open Questions

None.

## Sources

- `PLANO_STARCODE.md` §4, §4.3, §4.6, §4.7, §9.2 e §10 (Fase 3): binding.
- `DECISIONS.md` D7, D11, D22, D23, D27, D28, D29, F0-1, F0-2, F0-5, F2-7, F2-10: binding.
- `docs/reference/tlc-spec-driven.zip` (`check_proofs.py`, `validate_verification.py`, `references/validate.md`): non-binding - user: "Adaptar os gates do tlc-spec-driven (ADR-0002, D24)" (plano, Fase 2/3).

## Differences from the Source

- Regras de captura de tela e `walk` do tlc removidas do `validate_verification.py` (D25).
- `check_scope.py` não existe no tlc: criado para o escritor único (D28) e o dono de arquivo (D19).
- `**Tree**: dirty (modo 1)` em vez de só `dirty`, para o modo 1 (D11).
