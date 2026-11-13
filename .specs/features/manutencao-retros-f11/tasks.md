# Manutenção das retros da Fase 11 e do patch v1.5.1: Tasks

**Approved**: 2026-11-13 - user: "sim"

**Spec**: `.specs/features/manutencao-retros-f11/spec.md`
**Status**: Approved
**Integration branch**: `feature/manutencao-retros-f11`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only, no generator change | `python -m unittest discover -s tests -v` |
| full | task that changes `scripts/`, `src/`, `skills/`, `tools/` or `tests/` (F3-1: `dist/` regenerated in the same commit) | `python tools/build.py && python tools/build.py --check && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |
| plugin | task that changes `src/orca/` | `orca plugin validate src/orca --json && orca plugin test src/orca && orca plugin check src/orca --json && python tools/build.py && python tools/build.py --check && python -m unittest discover -s tests -v` |

## Tasks

### T1: handoff.py --report sem data duplicada
**Linear**: SC-157
**Depends on**: none
**Requirements**: R23, R24, R31
**Tests**: unit
**Gate**: full
May change: `scripts/handoff.py`, `tests/test_handoff_report_date.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/dispatch.py`, `scripts/gates/`, `skills/`, `src/`, `hooks/`

#### TASK
Em `scripts/handoff.py`, o `--report` deixa de prefixar a data de hoje quando o texto já começa com uma data ISO:
- Texto que casa `^\d{4}-\d{2}-\d{2}` (com ou sem hora depois, ex.: `2026-11-13: T1 ok`, `2026-11-13T10:00Z: T1 ok`) entra no `Reports` como veio (R23).
- Qualquer outro texto continua como `<data de hoje>: <texto>` (R24), inclusive `T1 em 2026-11-13` (data no meio).
- O `--settle` não muda (continua sempre com o prefixo).
- Entrada nova em `DECISIONS.md` (próximo número livre da série F12, hoje F12-9) descrevendo a regra (R31).
- Testes em `tests/test_handoff_report_date.py`, sem docstring, com os nomes: `test_report_com_data_iso_nao_prefixa`, `test_report_sem_data_prefixa_hoje`, `test_settle_continua_prefixando`.

#### CONTEXT
Spec: `.specs/features/manutencao-retros-f11/spec.md` (R23, R24, R31). Checks: C1, C2.
Hoje a função `append_item` (perto da linha 122) monta `f"{today or dt.date.today().isoformat()}: {text}"` para `--report` e `--settle`. Os testes existentes de handoff ficam em `tests/test_handoff.py` (só leitura) e usam `import helpers`.

#### BOUNDARIES
May change: `scripts/handoff.py`, `tests/test_handoff_report_date.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/dispatch.py`, `scripts/gates/`, `skills/`, `src/`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/manutencao-retros-f11`. Testes citados por check não têm docstring. Nunca desligue a assinatura de commits em código de produto.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T2: proofs.md gravado em LF
**Linear**: SC-158
**Depends on**: T1
**Requirements**: R4, R31
**Tests**: unit
**Gate**: full
May change: `scripts/gates/check_proofs.py`, `tests/test_check_proofs_lf.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/handoff.py`, `scripts/dispatch.py`, `skills/`, `src/`, `hooks/`

#### TASK
Em `scripts/gates/check_proofs.py`, gravar o proofs.md só com LF em qualquer sistema operacional (R4): `write_text(..., encoding="utf-8", newline="\n")` ou gravação em bytes. Entrada nova em `DECISIONS.md` (próximo F12 livre) (R31).
Teste em `tests/test_check_proofs_lf.py`, sem docstring: `test_proofs_md_gravado_sem_cr` gera um proofs.md numa feature temporária e confere que os bytes do arquivo não têm `\r` (no Windows ele falha antes da correção).

#### CONTEXT
Spec: R4, R31. Check: C3.
A gravação está perto da linha 203: `(fdir / "proofs.md").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")`. Veja como `tests/test_check_proofs.py` (só leitura) monta uma feature temporária e chama o gate.

#### BOUNDARIES
May change: `scripts/gates/check_proofs.py`, `tests/test_check_proofs_lf.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/handoff.py`, `scripts/dispatch.py`, `skills/`, `src/`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/manutencao-retros-f11`. Testes citados por check não têm docstring. Nunca desligue a assinatura de commits em código de produto.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T3: DECISIONS.md implícito no brief e no lote, e regra de assinatura
**Linear**: SC-159
**Depends on**: T2
**Requirements**: R1, R2, R3, R22, R31
**Tests**: unit
**Gate**: full
May change: `scripts/dispatch.py`, `tests/test_dispatch_decisions.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/handoff.py`, `scripts/gates/`, `skills/`, `src/`, `hooks/`

#### TASK
Em `scripts/dispatch.py`:
- `brief` (R1, R2): quando o May change do ticket tem algum caminho que começa com `scripts/` e não tem `DECISIONS.md`, a linha `May change:` do brief ganha `DECISIONS.md` no fim. Sem caminho de `scripts/`, ou com `DECISIONS.md` já presente, a linha fica igual à do tasks.md, sem duplicar. O tasks.md nunca é alterado.
- `batch` (R3): ao comparar caminhos compartilhados, usa o mesmo May change efetivo do brief; dois tickets prontos que mexem em `scripts/` não entram no mesmo lote (o segundo vai para os excluídos com o motivo de caminho compartilhado `DECISIONS.md`).
- `WORKER_RULES` (R22): acrescentar a linha `- Nunca desligue a assinatura de commits (commit.gpgsign false, --no-gpg-sign) em código de produto; só repositórios Git temporários de teste podem fazê-lo.`
- Entrada nova em `DECISIONS.md` (próximo F12 livre) (R31).
- Testes em `tests/test_dispatch_decisions.py`, sem docstring: `test_brief_acrescenta_decisions_com_scripts`, `test_brief_sem_scripts_ou_com_decisions_nao_muda`, `test_batch_separa_tickets_de_scripts`, `test_brief_traz_regra_de_assinatura`.

#### CONTEXT
Spec: R1, R2, R3, R22, R31. Checks: C4, C5, C6, C7.
A linha do brief é montada perto da linha 329 (`may = gc.split_paths(...)`); o lote calcula `reserved` e `paths` perto das linhas 216-224. Os testes existentes de dispatch ficam em `tests/test_dispatch.py` (só leitura, veja como montam um `tasks.md` temporário).

#### BOUNDARIES
May change: `scripts/dispatch.py`, `tests/test_dispatch_decisions.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/handoff.py`, `scripts/gates/`, `skills/`, `src/`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/manutencao-retros-f11`. Testes citados por check não têm docstring. Nunca desligue a assinatura de commits em código de produto.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T4: gate das tasks recusa arquivo citado no TASK fora do May change
**Linear**: SC-160
**Depends on**: T3
**Requirements**: R20, R21, R31
**Tests**: unit
**Gate**: full
May change: `scripts/gates/validate_tasks.py`, `tests/test_validate_tasks_citations.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/dispatch.py`, `scripts/handoff.py`, `skills/`, `src/`, `hooks/`

#### TASK
Em `scripts/gates/validate_tasks.py`, nova verificação por tarefa (R20, R21):
- Candidatos: trechos entre crases no bloco `#### TASK`, sem espaço nem `<`, `>`, `*`, `{`, `}`, terminados numa das extensões `.py .md .json .ts .tsx .js .mjs .toml .yaml .yml .txt .sh .ps1 .rs .css .html .lock`.
- Coberto: igual a uma entrada do May change; dentro de uma entrada que é pasta (termina em `/`); ou nome sem pasta igual ao último segmento de uma entrada.
- Não coberto → erro `T<n>: o TASK cita <caminho>, fora do May change: acrescente ao May change ou cite em CONTEXT`.
- Citações nos blocos CONTEXT, BOUNDARIES, RULES e DELIVERY não contam.
- Entrada nova em `DECISIONS.md` (próximo F12 livre) (R31).
- Testes em `tests/test_validate_tasks_citations.py`, sem docstring: `test_task_cita_arquivo_fora_do_may_change_falha`, `test_citacao_coberta_por_pasta_ou_nome`, `test_versao_e_atributo_nao_contam`, `test_citacao_em_context_nao_conta`.
- Rode o gate `tasks` nas features existentes de `.specs/features/` e diga no relatório quais ficariam vermelhas (não altere nenhuma).

#### CONTEXT
Spec: R20, R21, R31. Checks: C8, C9, C10, C34.
A função `evaluate` (perto da linha 133) já junta `errors` por tarefa; a classe da tarefa tem `may_change` e acesso aos blocos. Veja os testes existentes em `tests/test_validate_tasks.py` (só leitura) para montar um `tasks.md` e um `spec.md` temporários.

#### BOUNDARIES
May change: `scripts/gates/validate_tasks.py`, `tests/test_validate_tasks_citations.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/dispatch.py`, `scripts/handoff.py`, `skills/`, `src/`, `hooks/`, `.specs/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/manutencao-retros-f11`. Testes citados por check não têm docstring. Nunca desligue a assinatura de commits em código de produto.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T5: dispatch.py start
**Linear**: SC-161
**Depends on**: T4
**Requirements**: R5, R6, R7, R8, R9, R10, R11, R17, R31
**Tests**: unit
**Gate**: full
May change: `scripts/dispatch.py`, `tests/test_dispatch_start.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/handoff.py`, `scripts/gates/`, `skills/`, `src/`, `hooks/`

#### TASK
Novo subcomando `dispatch.py start <slug> <T> --cli <cli> --model <model> [--root DIR] [--json]` em `scripts/dispatch.py`:
- Recusa (R8): ticket inexistente no tasks.md, sem `**Linear**:`, já com entrada em `Dispatched`, ou Handoff sem `**Integration branch:**` → exit 2 e `start recusado: <motivo>`, sem gravar nada nem chamar a Orca.
- Passos, nesta ordem (R5): gera o brief (a mesma função do subcomando `brief`) num arquivo temporário; `handoff.py set <slug> --dispatch-add "<T> · <ID> · base <sha curto de feature/<slug>> · <cli>:<model> · <AAAA-MM-DDTHH:MM:SSZ>"`; `orca linear status set <ID> --to "<started>"` (estado `started` do repo config); `orca linear label add <ID> --label crew:laforge`; `orca orchestration worker-start --agent <cli> --model <model> --worktree new-child --base-branch feature/<slug> --spec-file <brief> --task-title "<T>: <título>" --json`.
- OpenCode (R7): com `--cli opencode`, antes `orca worktree create --name <T> --base-branch feature/<slug> --json` e esse worktree no lugar de `new-child`.
- Sucesso do worker-start (R6): `--dispatch-add` de novo com ` · <dispatch id>` no fim e `<cli>:<model>` trocado pelo campo `model` do recibo quando houver; depois `orca worktree set --worktree <workspace do recibo> --linear-issue <ID>`.
- Falha do worker-start (R9): `--dispatch-remove <T>`, imprime `worker-start falhou: <primeira linha do erro>`, exit 1.
- Falha no Linear ou no `worktree set` (R10): imprime `aviso: <passo>: <primeira linha do erro>` e segue.
- Saída (R11): uma linha por passo; com `--json`, `{"ticket","issue","base","dispatch","worktree","model"}`; exit 0.
- Paralelo (R17): um `start` de T2 com T1 aberto deixa as duas entradas em `Dispatched`.
- Todas as chamadas externas (orca, git, handoff) passam por um `runner` injetável (padrão `subprocess.run`); os testes nunca chamam a Orca nem o Linear de verdade.
- Entrada nova em `DECISIONS.md` (próximo F12 livre) (R31).
- Testes em `tests/test_dispatch_start.py`, sem docstring: `test_start_ordem_dos_passos`, `test_start_regrava_entrada_com_dispatch_e_modelo`, `test_start_opencode_cria_worktree_antes`, `test_start_recusa_sem_gravar`, `test_start_worker_falha_remove_entrada`, `test_start_linear_falha_vira_aviso`, `test_start_json`, `test_start_paralelo_preserva_outra_entrada`.

#### CONTEXT
Spec: R5–R11, R17, R31 e a seção Data & Contracts. Checks: C11–C18.
O passo a passo manual que este comando substitui está em `skills/engajar/references/execute.md`, seções 2 e 2F (só leitura nesta tarefa). O Handoff é escrito só por `scripts/handoff.py` (`--dispatch-add`, `--dispatch-remove`; só leitura nesta tarefa, chame por subprocesso ou import). Estado `started`: `linear.states.started` em `.starcode/config.json` do repositório. Padrão de runner injetável: `tools/install_local.py` (só leitura).

#### BOUNDARIES
May change: `scripts/dispatch.py`, `tests/test_dispatch_start.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/handoff.py`, `scripts/gates/`, `skills/`, `src/`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/manutencao-retros-f11`. Testes citados por check não têm docstring. Nunca desligue a assinatura de commits em código de produto.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T6: dispatch.py settle
**Linear**: SC-162
**Depends on**: T5
**Requirements**: R12, R13, R14, R15, R16, R17, R31
**Tests**: unit
**Gate**: full
May change: `scripts/dispatch.py`, `tests/test_dispatch_settle.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/handoff.py`, `scripts/gates/`, `skills/`, `src/`, `hooks/`

#### TASK
Novo subcomando `dispatch.py settle <slug> <T> --branch <ramo do ticket> [--root DIR]` em `scripts/dispatch.py`, rodado no worktree de `feature/<slug>`:
- Recusa (R16): sem entrada de `<T>` em `Dispatched`, ou ramo atual diferente de `feature/<slug>` → exit 2 e `settle recusado: <motivo>`, sem gate nem merge.
- Gate antes (R12): `run_gates.py ticket <slug> <T> <base da entrada>..<ramo do ticket>`.
- Verde (R13): `git merge --no-ff <ramo do ticket> -m "merge: integra <T> (<ID>) em feature/<slug>" -m "Refs: <ID>"`; depois `handoff.py set <slug> --dispatch-remove <T> --last-integrated <sha> --attempt worker-<T>=ok`; imprime `integrado <T> em feature/<slug>: <sha curto>`; exit 0.
- Vermelho (R14): imprime `gate vermelho: <T>` e as linhas de erro do gate; sem merge; entrada mantida; exit 1.
- Conflito (R15): `git merge --abort`, imprime `conflito no merge de <T>: <arquivos>`, entrada mantida, exit 1.
- Paralelo (R17): o `settle` de T1 remove só a entrada de T1.
- Mesmo `runner` injetável do `start`; os testes usam repositórios Git temporários de verdade para o merge e o conflito, e um gate falso.
- Entrada nova em `DECISIONS.md` (próximo F12 livre) (R31).
- Testes em `tests/test_dispatch_settle.py`, sem docstring: `test_settle_roda_gate_antes_do_merge`, `test_settle_verde_integra_e_remove_entrada`, `test_settle_gate_vermelho_nao_integra`, `test_settle_conflito_aborta`, `test_settle_recusa_sem_entrada_ou_ramo_errado`, `test_settle_paralelo_remove_so_o_seu`.

#### CONTEXT
Spec: R12–R17, R31 e Data & Contracts. Checks: C19–C24.
A integração manual que este comando substitui está em `skills/engajar/references/execute.md`, seção 3 e 2F passo 5 (só leitura nesta tarefa). A base é a gravada na entrada de `Dispatched` no despacho, nunca o HEAD atual do ramo de integração.

#### BOUNDARIES
May change: `scripts/dispatch.py`, `tests/test_dispatch_settle.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/handoff.py`, `scripts/gates/`, `skills/`, `src/`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge (o merge dentro dos repositórios temporários dos testes é permitido).
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/manutencao-retros-f11`. Testes citados por check não têm docstring. Nunca desligue a assinatura de commits em código de produto.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T7: execute.md com start, settle e worker-read --dispatch
**Linear**: SC-163
**Depends on**: T6
**Requirements**: R18, R29, R30
**Tests**: unit
**Gate**: full
May change: `skills/engajar/references/execute.md`, `tests/test_execute_doc_start_settle.py`, `dist/`
Do not touch: `scripts/`, `src/`, `hooks/`

#### TASK
Em `skills/engajar/references/execute.md`:
- Seções 2, 2F e 3 (R18): o despacho passa a ser `python "P/scripts/dispatch.py" start <slug> <T> --cli <cli> --model <model>` e a integração `python "P/scripts/dispatch.py" settle <slug> <T> --branch <ramo do ticket>`, no lugar da sequência manual (`--dispatched`/`--dispatch-add`, status e label no Linear, `worker-start`, gate, `git merge --no-ff`, `--dispatch-remove`). Mantenha o que os comandos não fazem: espera do `worker_done`, `--report`, crew_live.py, comentário "integrado", paradas do `nested_worker_depth_exceeded` e do `agent-hooks-review-prompt` (agora lidas na saída do `start`), timeouts, overdue e cancelamento.
- R29: todo `worker-read`/`worker-show` escrito como `orca orchestration worker-read --dispatch <id> --source auto` e `orca orchestration worker-show --dispatch <id>`.
- R30: uma frase dizendo que o modelo efetivo do worker é o campo `model` do recibo do `worker-start --json`, gravado na entrada de `Dispatched` pelo `start`.
- Testes em `tests/test_execute_doc_start_settle.py`, sem docstring: `test_execute_usa_start_e_settle`, `test_execute_sem_worker_show_posicional`, `test_execute_diz_onde_ler_o_modelo`.

#### CONTEXT
Spec: R18, R29, R30. Checks: C25, C26, C27.
Os comandos `start` e `settle` já existem em `scripts/dispatch.py` (T5, T6; só leitura): leia o `--help` deles. Formas posicionais hoje: linhas perto de 108, 149 e 204. O teste lê o arquivo de `skills/` (fonte), não o `dist/`.

#### BOUNDARIES
May change: `skills/engajar/references/execute.md`, `tests/test_execute_doc_start_settle.py`, `dist/`
Do not touch: `scripts/`, `src/`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/manutencao-retros-f11`. Testes citados por check não têm docstring. Nunca desligue a assinatura de commits em código de produto.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T8: brief do Q exige comando e saída literal nas sondagens
**Linear**: SC-164
**Depends on**: T7
**Requirements**: R19
**Tests**: unit
**Gate**: full
May change: `src/briefs/q-verify.md`, `tests/test_q_brief_evidence.py`, `dist/`
Do not touch: `scripts/`, `skills/`, `hooks/`, `src/orca/`

#### TASK
Em `src/briefs/q-verify.md` (R19): dizer, no passo 2 ("Examples nobody cited") e na explicação da tabela `## Findings`, que um achado vindo de sondagem traz na coluna Evidence o comando exato entre crases e a saída literal que ele imprimiu, e que `<arquivo>:<linha>` sozinho só vale para achados de leitura de código (passos 1 e 3). A linha de exemplo da tabela passa a mostrar as duas formas.
Teste em `tests/test_q_brief_evidence.py`, sem docstring: `test_q_brief_exige_comando_e_saida_na_sondagem` lê o brief gerado por `dispatch.py q-brief` numa feature temporária e confere as duas frases.

#### CONTEXT
Spec: R19. Check: C28.
O brief é montado por `scripts/dispatch.py q-brief` (só leitura) a partir de `src/briefs/q-verify.md`; veja `tests/test_dispatch_regression.py` (só leitura) para gerar um q-brief em teste.

#### BOUNDARIES
May change: `src/briefs/q-verify.md`, `tests/test_q_brief_evidence.py`, `dist/`
Do not touch: `scripts/`, `skills/`, `hooks/`, `src/orca/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/manutencao-retros-f11`. Testes citados por check não têm docstring. Nunca desligue a assinatura de commits em código de produto.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T9: testes da Ponte falham com recusa do host
**Linear**: SC-165
**Depends on**: T8
**Requirements**: R27, R28
**Tests**: unit
**Gate**: plugin
May change: `src/orca/src/worker.test.ts`, `dist/`
Do not touch: `src/orca/src/worker.ts`, `scripts/`, `skills/`, `hooks/`

#### TASK
Em `src/orca/src/worker.test.ts`:
- R27: cada teste que cria um `mockHost` (direto ou pelos auxiliares `hostFor` e `launchHost`) confere no fim `assert.deepEqual(host.refusals, [])`. Prefira um auxiliar único chamado no fim de cada teste a repetir o código.
- R28: novo teste `host recusa agent.launch sem a capacidade` cria o `mockHost` com `capabilities` sem `agent:launch`, aciona o "Iniciar Picard" e confere em `host.refusals` uma recusa com `method` `agent.launch` e `code` `capability_denied`.
- Se algum teste existente passar a falhar por uma recusa real, pare e relate o teste e a recusa (não mude o manifesto nem o worker).

#### CONTEXT
Spec: R27, R28. Checks: C29, C30.
O `mockHost` vem de `orca/testing`; pela tipagem da Orca 1.4.258 (`resources/plugins/types/orca-testing.d.ts` na instalação da Orca), `mockHost({ capabilities })` usa por padrão as capacidades do manifesto do plugin e `host.refusals` lista as chamadas recusadas (`capability_denied`, `not_permitted`, `invalid_params`, `unknown_method`). O manifesto é `src/orca/orca-plugin.json` (só leitura). `orca plugin test` e `orca plugin check` (Orca 1.4.257+) só rodam com o plugin no mesmo drive da instalação da Orca (C:); se o worktree estiver em outro drive, diga no relatório e rode os testes a partir de uma cópia no C:.

#### BOUNDARIES
May change: `src/orca/src/worker.test.ts`, `dist/`
Do not touch: `src/orca/src/worker.ts`, `scripts/`, `skills/`, `hooks/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/manutencao-retros-f11`. Testes citados por check não têm docstring. Nunca desligue a assinatura de commits em código de produto.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T10: registros, limitação da Orca e rascunho do relato
**Linear**: SC-166
**Depends on**: T9
**Requirements**: R25, R26, R31
**Tests**: unit
**Gate**: full
May change: `docs/compatibilidade.md`, `docs/relatos/orca-plugin-test-drive.md`, `CHANGELOG.md`, `tests/test_registros_retros_f11.py`, `dist/`
Do not touch: `scripts/`, `skills/`, `src/`, `hooks/`, `DECISIONS.md`

#### TASK
- `docs/compatibilidade.md` (R25): uma linha dizendo que `orca plugin test` e `orca plugin check` (Orca 1.4.257) só rodam com o plugin no mesmo drive da instalação da Orca, com o sintoma (o harness não acha o orca-runtime.mjs) e o contorno (rodar a partir de um worktree no drive da Orca).
- `docs/relatos/orca-plugin-test-drive.md` (R26): rascunho em inglês do relato à Orca, com as seções `## Orca version`, `## OS`, `## Steps to reproduce`, `## Expected`, `## Actual`, `## Workaround`. Não envie a lugar nenhum.
- `CHANGELOG.md`: em `## [Unreleased]`, uma linha por item entregue da SC-148 (itens 1 a 9).
- Teste em `tests/test_registros_retros_f11.py`, sem docstring: `test_compatibilidade_cita_limite_do_drive`, `test_relato_orca_tem_as_secoes`, `test_decisions_registra_os_itens_de_scripts` (o DECISIONS.md tem entradas F12 que citam handoff.py, check_proofs.py, dispatch.py brief, dispatch.py start, dispatch.py settle e validate_tasks.py; só leitura nesta tarefa).

#### CONTEXT
Spec: R25, R26, R31. Checks: C31, C32, C33.
O sintoma real: `orca-testing.mjs: cannot import "./orca-runtime.mjs"` no checkout do drive F:, enquanto a mesma árvore passou num worktree no C: (`.specs/features/ponte-missao-ativa/retro.md`, item 1). Versões: Orca 1.4.257 na época, 1.4.258 instalada hoje; Windows 11.

#### BOUNDARIES
May change: `docs/compatibilidade.md`, `docs/relatos/orca-plugin-test-drive.md`, `CHANGELOG.md`, `tests/test_registros_retros_f11.py`, `dist/`
Do not touch: `scripts/`, `skills/`, `src/`, `hooks/`, `DECISIONS.md`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/manutencao-retros-f11`. Testes citados por check não têm docstring. Nunca desligue a assinatura de commits em código de produto.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

## Checks

**Build**: `python tools/build.py --check`; `python scripts/check_decisions.py`; `orca plugin validate src/orca --json`; `orca plugin check src/orca --json`
**Run unit**: `python -m unittest discover -s tests -v`
**Run plugin**: `orca plugin test src/orca`

**C1** - `--report "2026-11-13: T1 ok"` e `--report "2026-11-13T10:00Z: T1 ok"` entram no Reports sem a data de hoje na frente (R23)
Proof: run unit | test_report_com_data_iso_nao_prefixa ... ok

**C2** - `--report "T1 em 2026-11-13"` vira `<hoje>: T1 em 2026-11-13`; `--settle` continua prefixando (R24)
Proof: run unit | test_report_sem_data_prefixa_hoje ... ok

**C3** - o `proofs.md` gerado pelo gate não tem nenhum byte `\r` (R4)
Proof: run unit | test_proofs_md_gravado_sem_cr ... ok

**C4** - ticket com `scripts/x.py` e `dist/` no May change: o brief traz `May change: scripts/x.py, dist/, DECISIONS.md` (R1)
Proof: run unit | test_brief_acrescenta_decisions_com_scripts ... ok

**C5** - ticket sem `scripts/`, e ticket com `DECISIONS.md` já listado: a linha do brief é igual à do tasks.md, com `DECISIONS.md` uma vez só (R2)
Proof: run unit | test_brief_sem_scripts_ou_com_decisions_nao_muda ... ok

**C6** - dois tickets prontos com `scripts/a.py` e `scripts/b.py`: o lote leva um só e exclui o outro por `DECISIONS.md` compartilhado (R3)
Proof: run unit | test_batch_separa_tickets_de_scripts ... ok

**C7** - o brief de ticket traz a linha exata da regra de assinatura de commits (R22)
Proof: run unit | test_brief_traz_regra_de_assinatura ... ok

**C8** - TASK que cita `` `scripts/y.py` `` fora do May change: gate vermelho com `T1: o TASK cita scripts/y.py, fora do May change: acrescente ao May change ou cite em CONTEXT` (R20)
Proof: run unit | test_task_cita_arquivo_fora_do_may_change_falha ... ok

**C9** - citação igual a uma entrada, dentro de pasta (`dist/x.json` com `dist/`) ou só pelo nome (`snapshot.py` com `scripts/snapshot.py`): gate verde (R21)
Proof: run unit | test_citacao_coberta_por_pasta_ou_nome ... ok

**C10** - `` `1.6.0` ``, `` `os.environ` `` e `` `<arquivo>.py` `` no TASK, e caminho fora do May change citado só em CONTEXT, não geram erro (R20)
Proof: run unit | test_versao_e_atributo_nao_contam ... ok

**C11** - `start` chama, nesta ordem: `--dispatch-add` com base e `cli:model`, status `started`, label `crew:laforge`, `worker-start` com os argumentos do R5 (R5)
Proof: run unit | test_start_ordem_dos_passos ... ok

**C12** - depois do `worker-start`, a entrada é regravada com ` · <dispatch id>` e o `model` do recibo, e o `worktree set --linear-issue <ID>` é chamado (R6)
Proof: run unit | test_start_regrava_entrada_com_dispatch_e_modelo ... ok

**C13** - com `--cli opencode`, `orca worktree create --name <T>` vem antes do `worker-start`, que recebe esse worktree (R7)
Proof: run unit | test_start_opencode_cria_worktree_antes ... ok

**C14** - ticket inexistente, sem Linear, já despachado ou sem ramo de integração: exit 2, `start recusado: <motivo>`, Handoff igual e nenhuma chamada à Orca (R8)
Proof: run unit | test_start_recusa_sem_gravar ... ok

**C15** - `worker-start` falhando: entrada removida, `worker-start falhou: <linha>` e exit 1 (R9)
Proof: run unit | test_start_worker_falha_remove_entrada ... ok

**C16** - status, label ou `worktree set` falhando: `aviso: <passo>: <linha>` e o `start` termina com 0 (R10, R11)
Proof: run unit | test_start_linear_falha_vira_aviso ... ok

**C17** - `--json` imprime as chaves `ticket`, `issue`, `base`, `dispatch`, `worktree`, `model` com os valores do recibo (R11)
Proof: run unit | test_start_json ... ok

**C18** - `start` de T2 com T1 aberto deixa as duas entradas; `settle` de T1 remove só a de T1 (R17)
Proof: run unit | test_start_paralelo_preserva_outra_entrada ... ok

**C19** - `settle` chama `run_gates.py ticket <slug> <T> <base da entrada>..<ramo>` antes de qualquer `git merge` (R12)
Proof: run unit | test_settle_roda_gate_antes_do_merge ... ok

**C20** - gate verde: commit de merge com as duas mensagens do R13, entrada removida, `Last integrated` = sha do merge, saída `integrado <T> em feature/<slug>: <sha curto>`, exit 0 (R13)
Proof: run unit | test_settle_verde_integra_e_remove_entrada ... ok

**C21** - gate vermelho: `gate vermelho: <T>`, HEAD do ramo igual, entrada mantida, exit 1 (R14)
Proof: run unit | test_settle_gate_vermelho_nao_integra ... ok

**C22** - conflito: merge abortado (árvore limpa, HEAD igual), `conflito no merge de <T>: <arquivo>`, entrada mantida, exit 1 (R15)
Proof: run unit | test_settle_conflito_aborta ... ok

**C23** - sem entrada em Dispatched ou fora de `feature/<slug>`: exit 2, `settle recusado: <motivo>`, sem gate nem merge (R16)
Proof: run unit | test_settle_recusa_sem_entrada_ou_ramo_errado ... ok

**C24** - `settle` de T1 com T2 aberto mantém a entrada de T2 (R17)
Proof: run unit | test_settle_paralelo_remove_so_o_seu ... ok

**C25** - o execute.md manda `dispatch.py start` nas seções 2 e 2F e `dispatch.py settle` nas seções 2F e 3, sem `--dispatched "<T>` nem `git merge --no-ff <ticket branch>` manuais (R18)
Proof: run unit | test_execute_usa_start_e_settle ... ok

**C26** - o execute.md não tem `worker-show <` nem `worker-read <` posicionais e tem `worker-read --dispatch` (R29)
Proof: run unit | test_execute_sem_worker_show_posicional ... ok

**C27** - o execute.md diz que o modelo efetivo é o campo `model` do recibo do `worker-start` (R30)
Proof: run unit | test_execute_diz_onde_ler_o_modelo ... ok

**C28** - o q-brief gerado exige comando entre crases e saída literal na Evidence de achado de sondagem e restringe `<arquivo>:<linha>` aos passos 1 e 3 (R19)
Proof: run unit | test_q_brief_exige_comando_e_saida_na_sondagem ... ok

**C29** - o mockHost sem `agent:launch` registra a recusa `agent.launch` / `capability_denied` ao acionar o "Iniciar Picard" (R28)
Proof: run plugin | ✔ host recusa agent.launch sem a capacidade

**C30** - os testes da Ponte conferem `host.refusals` vazio no fim (R27)
Proof: run plugin | ✔ atalho foca o worktree da missão ativa

**C31** - `docs/compatibilidade.md` cita `orca plugin test`, `orca plugin check`, `1.4.257`, o drive da instalação e o contorno (R25)
Proof: run unit | test_compatibilidade_cita_limite_do_drive ... ok

**C32** - o rascunho do relato existe, em inglês, com as seis seções (R26)
Proof: run unit | test_relato_orca_tem_as_secoes ... ok

**C33** - o `DECISIONS.md` tem entradas F12 que citam `handoff.py`, `check_proofs.py`, `dispatch.py brief`, `dispatch.py start`, `dispatch.py settle` e `validate_tasks.py` (R31)
Proof: run unit | test_decisions_registra_os_itens_de_scripts ... ok

**C34** - citação de caminho fora do May change feita só no CONTEXT não conta (R20)
Proof: run unit | test_citacao_em_context_nao_conta ... ok

## Handoff

**Phase:** published
**Size:** LARGE
**Git mode:** 3
**Next:** worktree de integração e T1
**Linear:** SC-148 (mãe); SC-157..SC-166; doc https://linear.app/cifren/document/spec-manutencao-das-retros-da-fase-11-e-do-patch-v151-2008cd0d7d29
**Integration branch:** not created
**Last integrated:** none
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
