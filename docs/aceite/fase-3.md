# Aceite da Fase 3 (SC-10): execução sequencial e verificação (LaForge, McCoy, Q)

Data: 2026-11-05. Ramo: `freireandrem/sc-10-fase-3-execucao-sequencial-e-verificacao-laforge-mccoy-q`.
Versões: Claude Code 2.1.318, codex-cli 0.166.0, Python 3.14.8. Plugin `starcode` 0.1.0 (lido de `dist/claude`).
Repositório de teste: `F:\Projetos\starcode-sandbox`, time PROJ do Linear (nenhum projeto de teste no time SC).
Tripulação efetiva: Picard nesta sessão (claude-opus-5-5); LaForge `claude · claude-sonnet-5-5`;
Q `codex · padrão do CLI` (modelo efetivo não confirmado pelo Orca; `config.toml` do Codex: `gpt-6-luna`).

## Entregas

| Item do plano | Onde |
|---|---|
| Gates de execução: provas, verificação, escopo do ticket | `scripts/gates/check_proofs.py`, `validate_verification.py`, `check_scope.py`; estágios `ticket`, `proofs` e `done` em `run_gates.py` |
| Handoff de execução e disjuntor (D27, D28) | `scripts/handoff.py` (`--dispatched`, `--integration-branch`, `--last-integrated`, `--report`, `--attempt`, `--breaker`) e o banner |
| Skills LaForge, McCoy e Q; briefing do Q | `skills/laforge/`, `skills/mccoy/`, `skills/q/`, `src/briefs/q-verify.md` |
| Despacho sequencial | `scripts/dispatch.py` (`next`, `brief`, `q-brief`, `family`) e `skills/engajar/references/execute.md` |
| Evals de roteamento | `evals/routing/` (18 casos, 18/18 com nota 1.00) |
| Decisões F3-1 a F3-7 | `DECISIONS.md` |

## Roteiro 1: modo 2

**Resultado**: ✅
Feature GRANDE `task-priority` (PROJ-7, PROJ-8, PROJ-9), ramo de integração `feature/task-priority`.

**Evidência**:
- Três workers LaForge (claude-sonnet-5-5), um por ticket, em sequência e cada um no seu worktree filho
  (`tp-t1`, `tp-t2`, `tp-t3`). `dispatch.py next` liberou T2 só depois de T1 integrada e T3 só depois de T2.
  - T1: commit `afb676c`, integrado em `1459954`.
  - T2: commit `4c11554`, integrado em `5ff8603`.
  - T3: commit `41ed821`, integrado em `e5112f9`.
  - `run_gates.py ticket` deu `VEREDITO: VERDE` (check_scope e check_commit) nos três antes de cada
    `merge --no-ff`.
- Cada despacho foi gravado no Handoff antes do envio, com o dispatch id e o modelo. Linear: In Progress
  com `crew:laforge`, worktree ligado à issue, comentário "integrado em `feature/task-priority`" com o hash.
- Achado plantado pelo coordenador do aceite em `2f081ae`: o `list` desempata pelo título, mas a spec
  manda desempatar pelo id. Os testes continuaram verdes porque, nos dados do teste, a ordem dos títulos
  e a dos ids coincidem.
- Provas: `proofs.md` em `3932c93`, 23 pass, 0 fail.
- Q no Codex, de outra família (`dispatch.py family` deu `different`), recebeu um briefing sem histórico.
  Ele escreveu só o `verification.md` (commit `e6acbf2`) com **Verdict: FAIL** e 3 achados:
  - o achado plantado (R17/C21), reproduzido com ids 1 `zulu` e 2 `alfa`;
  - C1 testando uma tarefa só;
  - C19 com `assertIn` no stderr.
- Rodada única de correção: um LaForge no worktree de integração recebeu todos os achados num briefing só.
  Os commits foram `7d4427c` (desempate pelo id; o teste novo falhou antes da correção), `ab53422` e
  `ed3a66a`, cada um citado na coluna `Closed`.
- Provas refeitas em `eb343a8`: 23 pass. `run_gates.py done task-priority` deu `VEREDITO: VERDE` em
  `fb3dc61`. Não houve segundo Q.
- PROJ-7, PROJ-8 e PROJ-9 receberam o comentário "pronto para revisão" (o time PROJ não tem estado de
  revisão). Done só com confirmação do usuário.

## Roteiro 2: modo 1

**Resultado**: ✅
Feature MÉDIA `limpar-concluidas` (PROJ-10), num único worktree (`tp-mode1`), sem ramo de integração e sem commits.

**Evidência**:
- Um LaForge implementou R1–R7 só na árvore de trabalho, sem nenhum commit. O HEAD ficou em `fb3dc61`
  e o `git status` mostra os 4 arquivos de `May change` alterados.
- `run_gates.py proofs` gravou `**Tree**: dirty (modo 1)` com 8 pass e saiu VERMELHO, como manda o R3:
  as provas não valem para o HEAD.
- O briefing do Q recebeu a linha do modo 1 (`git diff main` da árvore). O Q deu FAIL com 4 achados de
  teste, todos corrigidos numa rodada única de LaForge sem commits (36 testes).
- O `verification.md` traz `**Verification:** degraded` e cada achado foi fechado com
  `degradada (modo 1)`. `run_gates.py done` deu `VEREDITO: VERDE` com os avisos de árvore suja e de
  verificação degradada.
- Comentário "verificação degradada" na PROJ-10, que continua fora de Done (R31: nunca no modo 1).

## Roteiro 3: verificação degradada

**Resultado**: ✅

**Evidência**: clone descartável do sandbox no ramo `feature/task-priority`.
- `dispatch.py family claude:claude-sonnet-5-5 --compare claude:claude-opus-5-5` respondeu `same`.
- Com `**Verification:** degraded (Q na mesma família: claude)` no `verification.md`:
  - `run_gates.py done task-priority` deu `VEREDITO: VERDE` com o aviso "verificação degradada";
  - `run_gates.py done task-priority --strict` deu `VEREDITO: VERMELHO`;
  - o banner mostrou `⚠️ Verificação: degradada (task-priority)`.
- O caminho real de verificação degradada (modo 1) está no roteiro 2.

## Roteiro 4: disjuntor

**Resultado**: ✅

**Evidência**: mesmo clone.
- Três `handoff.py set --attempt gate-T3=fail` gravaram `**Attempts:** gate-T3=3` e
  `**Breaker:** open (gate-T3, attempts 3/3)`. O banner mostrou `⚠️ Disjuntor aberto: task-priority (gate-T3)`.
- Com `worker-T3`: `fail` e depois `ok` zera a contagem. Na 3ª falha seguida apareceu
  `DISJUNTOR ABERTO: open (worker-T3, attempts 3/3) (D27): pare e ofereça as duas saídas`.
- Defeito encontrado e corrigido em `802908d`: `--breaker closed` não zerava o contador, e a primeira
  falha depois da escolha do usuário reabria o disjuntor (`attempts 4/3`). Agora fechar o disjuntor dá 3
  tentativas novas ao erro (teste `test_closing_breaker_resets_its_counter`).

## Roteiro 5: escritor único

**Resultado**: ✅

**Evidência**: mesmo clone.
- Um commit simulando um worker que muda o `## Handoff` do `tasks.md` e o `.specs/STATE.md` (`Refs: PROJ-9`).
- `run_gates.py ticket task-priority T3 feature/task-priority..rogue` deu `VEREDITO: VERMELHO` com:
  - `ERRO .specs/STATE.md alterado: só o Picard escreve nele (D28)`;
  - `ERRO ## Handoff alterado em .specs/features/task-priority/tasks.md: só o Picard escreve nele (D28)`.
- Pelo `execute.md` passo 3, esse ticket nunca é integrado. Nos workers reais dos roteiros 1 e 2, nenhum
  tocou `.specs/STATE.md` nem o Handoff; o Q tocou só o `verification.md`.

## Testes, build e validação

| Item | Resultado |
|---|---|
| `python -m unittest discover -s tests` | OK |
| `python tools/build.py --check` · `claude plugin validate dist/claude --strict` · `scripts/check_decisions.py` | OK |
| Evals de roteamento (`claude plugin eval dist/claude --tag routing`) | 18/18, nota 1.00, US$ 1,73 |

## Observações e correções feitas durante o aceite

1. O banner lia `**Phase:**` e `**Breaker:**` em trechos do `tasks.md` que só citavam `## Handoff`. Na
   abertura da sessão, ele mostrou uma fase sem sentido e um disjuntor aberto falso. Corrigido em `ea4f973`:
   só vale a seção real.
2. O briefing do worker mandava rodar `run_gates.py` sem caminho, e um worker sem a skill `laforge` não
   acharia o script. Corrigido em `9fb60e8`: o caminho do plugin vai no briefing.
3. Disjuntor reaberto logo depois de fechado (roteiro 4), corrigido em `802908d`.
4. O Picard rodou nesta sessão no repositório do StarCode, e os workers rodaram no sandbox. Para isso:
   - o ramo de integração foi criado a partir de `chore/starcode-specs`, onde estão as specs aprovadas
     (o `baseBranch` do sandbox é `main`);
   - os worktrees dos tickets foram criados com `--worktree new-child --repo path:<sandbox>`;
   - o worktree de integração foi criado com `git worktree add` e aceito pelo Orca via `--worktree path:`.
5. O Handoff do sandbox fica no worktree principal (`chore/starcode-specs`). `proofs.md` e
   `verification.md` ficam no ramo de integração. É o desenho do D28 (o Picard grava no seu worktree), mas
   na Fase 4 convém o Picard rodar no worktree de integração.
6. O Orca não informou o modelo efetivo do Q no Codex (`worker-read` não traz o modelo). Ficou registrado
   como `effective unconfirmed`, com o modelo do `config.toml` (F0-2).
7. Ao preencher a coluna `Closed`, o coordenador criou uma coluna vazia a mais na tabela, e o gate `done`
   recusou. Corrigido em `fb3dc61`: o gate cumpriu o papel dele.
8. Para MÉDIA, o `dispatch.py brief` não monta o briefing a partir do `## Checks` da spec (só a partir do
   `tasks.md`). O briefing foi montado à mão, como diz o `execute.md` seção 8. Pendência para a próxima fase.
