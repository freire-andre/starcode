# Manutenção das retros da Fase 11 e do patch v1.5.1: Spec

**Size**: LARGE
**Risk triggers**: concorrência e estado (despachos paralelos e o campo `Dispatched`)
**Approved**: 2026-11-13 - user: "sim"
**Status**: Approved
**Linear**: SC-148

## Context
As retros da Fase 11 (`.specs/features/fase-11-telas/retro.md`) e do patch v1.5.1 (`.specs/features/ponte-missao-ativa/retro.md`) apontaram nove atritos que custaram rodadas extras ao Picard e aos workers. A SC-148 junta as sugestões aprovadas pelo usuário em 2026-11-12. Sucesso: cada item vira um comportamento testado ou um texto verificável, sem regressão na suíte.

## Scope
- Item 1: `dispatch.py brief` acrescenta `DECISIONS.md` ao May change de ticket que mexe em `scripts/`.
- Item 2: `proofs.md` gravado em LF.
- Item 3: comandos `dispatch.py start` e `dispatch.py settle`, e o `execute.md` passa a usá-los.
- Item 4: o brief do Q exige comando e saída literal na Evidence dos achados vindos de sondagem.
- Item 5: o gate das tasks recusa arquivo citado no TASK fora do May change; o brief de ticket repete a regra de assinatura de commits.
- Item 6: `handoff.py set --report` não duplica a data.
- Item 7: nota em `docs/compatibilidade.md` e rascunho do relato à Orca.
- Item 8: os testes da Ponte falham quando o host recusa uma chamada.
- Item 9: comandos `worker-read`/`worker-show` do `execute.md` com `--dispatch` e onde ler o modelo efetivo.

## Non-Goals
- O teste da linha Build do tauri (entregue pela SC-143).
- Um comando para fechar achados no `verification.md`.
- Enviar o relato à Orca: o usuário envia; nenhum comando publica nada fora do repositório.
- Mudar o formato do `verification.md` ou o gate `validate_verification.py`.
- Mover a issue para Done ou comentar no Linear dentro do `settle` (continua no fluxo do Picard).

## Requirements

### Item 1: DECISIONS.md no brief
- **R1** - WHEN `dispatch.py brief <slug> <T>` monta o brief de um ticket cujo May change tem algum caminho que começa com `scripts/` e não tem `DECISIONS.md` THEN the system SHALL acrescentar `DECISIONS.md` ao fim da linha `May change:` do brief.
- **R2** - IF o May change do ticket já tem `DECISIONS.md` ou não tem caminho que começa com `scripts/` THEN the system SHALL manter a linha `May change:` do brief igual ao `tasks.md`, sem duplicar entrada.
- **R3** - WHEN `dispatch.py batch` compara os May change de dois tickets THEN the system SHALL contar o `DECISIONS.md` acrescentado pelo R1 como caminho compartilhado, deixando fora do mesmo lote dois tickets que mexem em `scripts/`.

### Item 2: proofs.md em LF
- **R4** - WHEN `run_gates.py proofs <slug>` grava `proofs.md` THEN the system SHALL gravar o arquivo só com LF (nenhum byte `\r`), em qualquer sistema operacional.

### Item 3: dispatch.py start e settle
- **R5** - WHEN `dispatch.py start <slug> <T> --cli <cli> --model <model>` roda com o ticket válido THEN the system SHALL executar, nesta ordem: gerar o brief num arquivo temporário; `handoff.py set --dispatch-add "<T> · <ID> · base <sha curto de feature/<slug>> · <cli>:<model> · <hora UTC ISO>"`; mover a issue para o estado `started` do repo config; pôr a label `crew:laforge`; `orca orchestration worker-start --agent <cli> --model <model> --worktree new-child --base-branch feature/<slug> --spec-file <brief> --task-title "<T>: <título>" --json`.
- **R6** - WHEN o `worker-start` do `start` termina com sucesso THEN the system SHALL regravar a entrada com `--dispatch-add`, acrescentando ` · <dispatch id>` e trocando `<cli>:<model>` pelo campo `model` do recibo quando ele existir, e rodar `orca worktree set --worktree <workspace do recibo> --linear-issue <ID>`.
- **R7** - WHERE `--cli opencode` the system SHALL criar antes o worktree com `orca worktree create --name <T> --base-branch feature/<slug> --json` e passar esse worktree ao `worker-start` no lugar de `new-child`.
- **R8** - IF o ticket não existe no `tasks.md`, não tem `**Linear**:`, já tem entrada em `Dispatched` ou o Handoff não tem `**Integration branch:**` THEN the system SHALL sair com 2 e a mensagem `start recusado: <motivo>`, sem gravar nada nem chamar a Orca.
- **R9** - IF o `worker-start` falha THEN the system SHALL rodar `--dispatch-remove <T>`, imprimir `worker-start falhou: <primeira linha do erro>` e sair com 1.
- **R10** - IF mover a issue, pôr a label ou o `orca worktree set` falha THEN the system SHALL imprimir `aviso: <passo>: <primeira linha do erro>` e seguir para o passo seguinte.
- **R11** - WHEN `dispatch.py start` termina com sucesso THEN the system SHALL imprimir uma linha por passo e, com `--json`, um objeto `{"ticket","issue","base","dispatch","worktree","model"}`, saindo com 0.
- **R12** - WHEN `dispatch.py settle <slug> <T> --branch <ramo do ticket>` roda no worktree de `feature/<slug>` THEN the system SHALL rodar `run_gates.py ticket <slug> <T> <base da entrada>..<ramo do ticket>` antes de qualquer merge.
- **R13** - WHEN o gate do `settle` fica verde THEN the system SHALL rodar `git merge --no-ff <ramo do ticket> -m "merge: integra <T> (<ID>) em feature/<slug>" -m "Refs: <ID>"`, depois `handoff.py set --dispatch-remove <T> --last-integrated <sha> --attempt worker-<T>=ok`, imprimir `integrado <T> em feature/<slug>: <sha curto>` e sair com 0.
- **R14** - IF o gate do `settle` fica vermelho THEN the system SHALL imprimir `gate vermelho: <T>` com as linhas de erro do gate, não fazer merge, manter a entrada em `Dispatched` e sair com 1.
- **R15** - IF o merge do `settle` tem conflito THEN the system SHALL rodar `git merge --abort`, imprimir `conflito no merge de <T>: <arquivos>`, manter a entrada em `Dispatched` e sair com 1.
- **R16** - IF não há entrada de `<T>` em `Dispatched` ou o ramo atual não é `feature/<slug>` THEN the system SHALL sair com 2 e a mensagem `settle recusado: <motivo>`, sem rodar gate nem merge.
- **R17** - WHILE há entradas de outros tickets em `Dispatched` the system SHALL preservá-las em `start` e `settle`: um `start` de T2 com T1 aberto deixa as duas entradas, e um `settle` de T1 remove só a de T1.
- **R18** - The system SHALL descrever nas seções 2, 2F e 3 do `skills/engajar/references/execute.md` o despacho por `dispatch.py start` e a integração por `dispatch.py settle`, no lugar da sequência manual de `--dispatched`/`--dispatch-add`, Linear, `worker-start`, gate, merge e `--dispatch-remove`.

### Item 4: evidência das sondagens do Q
- **R19** - The system SHALL dizer no brief do Q (`src/briefs/q-verify.md`) que um achado vindo de sondagem (passo 2) traz na coluna Evidence o comando exato entre crases e a saída literal que ele imprimiu, e que `<arquivo>:<linha>` sozinho só vale para achados de leitura de código (passos 1 e 3).

### Item 5: arquivos citados no TASK e assinatura de commits
- **R20** - WHEN `run_gates.py tasks <slug>` encontra no bloco `#### TASK` de uma tarefa um caminho entre crases, sem espaço nem `<`, `>`, `*`, `{`, `}`, terminado em uma das extensões `.py .md .json .ts .tsx .js .mjs .toml .yaml .yml .txt .sh .ps1 .rs .css .html .lock`, que nenhuma entrada do May change cobre THEN the system SHALL falhar com `T<n>: o TASK cita <caminho>, fora do May change: acrescente ao May change ou cite em CONTEXT`.
- **R21** - The system SHALL considerar coberto pelo May change o caminho igual a uma entrada, o caminho dentro de uma entrada que é pasta (termina em `/`), e o nome de arquivo sem pasta igual ao último segmento de uma entrada.
- **R22** - The system SHALL incluir nas regras fixas do worker (`WORKER_RULES` de `scripts/dispatch.py`) a linha `Nunca desligue a assinatura de commits (commit.gpgsign false, --no-gpg-sign) em código de produto; só repositórios Git temporários de teste podem fazê-lo.`

### Item 6: data no --report
- **R23** - IF o texto de `handoff.py set --report` começa com uma data ISO (`AAAA-MM-DD`, com ou sem hora) THEN the system SHALL acrescentá-lo ao `Reports` sem prefixar a data de hoje.
- **R24** - WHEN o texto de `--report` não começa com data ISO THEN the system SHALL manter o comportamento atual: `<data de hoje>: <texto>`.

### Item 7: limitação do orca plugin test/check
- **R25** - The system SHALL registrar em `docs/compatibilidade.md` que `orca plugin test` e `orca plugin check` (Orca 1.4.257) só rodam com o plugin no mesmo drive da instalação da Orca, com o sintoma (o harness não acha o `orca-runtime.mjs`) e o contorno (rodar a partir de um worktree no drive da Orca).
- **R26** - The system SHALL ter o rascunho do relato em `docs/relatos/orca-plugin-test-drive.md`, em inglês, com versão da Orca, sistema operacional, passos para reproduzir, resultado esperado, resultado observado e contorno.

### Item 8: recusas do host nos testes da Ponte
- **R27** - The system SHALL fazer cada teste de `src/orca/src/worker.test.ts` que cria um `mockHost` verificar, ao final, que `host.refusals` está vazio.
- **R28** - WHEN um teste cria o `mockHost` com `capabilities` sem `agent:launch` e aciona o "Iniciar Picard" THEN the system SHALL encontrar em `host.refusals` uma recusa do método `agent.launch` com código `capability_denied`.

### Item 9: exemplos do execute.md
- **R29** - The system SHALL escrever no `execute.md` os comandos como `orca orchestration worker-read --dispatch <id> --source auto` e `orca orchestration worker-show --dispatch <id>`, sem a forma posicional `<dispatch>`.
- **R30** - The system SHALL dizer no `execute.md` que o modelo efetivo do worker é o campo `model` do recibo do `worker-start` (`--json`), registrado na entrada de `Dispatched`.

### Registros
- **R31** - The system SHALL registrar em `DECISIONS.md` uma entrada F12-n para cada mudança de comportamento em `scripts/` (itens 1, 2, 3, 5 e 6) e regenerar o `dist/` (`tools/build.py --check` verde).

## Data & Contracts
```
dispatch.py start <slug> <T> --cli <cli> --model <model> [--root DIR] [--json]
  exit 0 sucesso · 1 worker-start falhou · 2 recusado (R8)
dispatch.py settle <slug> <T> --branch <ramo do ticket> [--root DIR]
  exit 0 integrado · 1 gate vermelho ou conflito · 2 recusado (R16)
Entrada de Dispatched (já usada pela Frota):
  "<T> · <ID> · base <sha7> · <cli>:<model> · <AAAA-MM-DDTHH:MM:SSZ>[ · <dispatch id>]"
```
Chamadas à Orca, ao Git e ao `run_gates.py` passam por um `runner` injetável, como em `tools/install_local.py`, para os testes não tocarem Linear nem Orca.

## States
N/A - os comandos são de linha única, sem estado próprio além das entradas do Handoff.

## Edge Cases
- `start` com a Orca ausente no PATH: R9 (falha do `worker-start`), com a entrada removida.
- `start` duas vezes do mesmo ticket: a segunda cai no R8 (já em `Dispatched`).
- `settle` com o ramo do ticket inexistente: o gate falha (R14).
- `--report "2026-11-13T10:00Z: T1 ok"`: sem prefixo (R23); `--report "T1 em 2026-11-13"`: com prefixo (R24).
- TASK com `` `1.6.0` `` ou `` `os.environ` ``: não conta como caminho (extensão fora da lista do R20).
- TASK que cita `` `snapshot.py` `` com `scripts/snapshot.py` no May change: coberto (R21).
- Ticket que só tem `dist/` e `scripts/x.py`: o brief acrescenta `DECISIONS.md` (R1); dois tickets assim não entram no mesmo lote (R3).

## Decisions
| Item | Options | Status |
|---|---|---|
| Arquivo citado no TASK fora do May change | gate das tasks recusa · brief acrescenta sozinho | approved - user: "Gate das tasks recusa (Recomendado)" |
| `settle` roda o gate do ticket | sim, gate antes do merge · não, só merge | approved - user: "Sim, gate antes (Recomendado)" |
| Relato à Orca | rascunho para o usuário · issue via gh · só documentar | approved - user: "Rascunho para você (Recomendado)" |
| `DECISIONS.md` implícito no lote da Frota (R3) | conta como compartilhado (tickets de `scripts/` em série, sem conflito no `DECISIONS.md`) · ignora (mais paralelismo, conflito provável no merge) | approved - user: "Conta, roda em série (Recomendado)" |
| Idioma do rascunho do relato (R26) | inglês (projeto externo) · PT-BR | approved - user: "Inglês (Recomendado)" |
| Item 8: como o mock recusa | usar o `refusals` que o `mockHost` da Orca já registra (capacidades vêm do `orca-plugin.json`, `orca-testing.d.ts` da Orca 1.4.258) · escrever um mock próprio | approved - user: "Usar o refusals da Orca (Recomendado)" |

## Open Questions
None.
