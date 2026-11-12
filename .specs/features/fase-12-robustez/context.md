# Fase 12 - Robustez: Context

**Size**: LARGE
**Risk triggers**: Irreversibilidade
**Source request**: "inicie a fase 12" (Fase 12 do PLANO_STARCODE.md: "Snapshot no modo 1: antes de cada ticket, um snapshot da árvore de trabalho guardado num ref próprio (`git stash create` + `git update-ref refs/starcode/snapshots/<ticket>`), sem commit no branch e sem mexer na árvore. É o 'último ponto bom' do disjuntor no modo 1; restaurar pede confirmação. Testes por raio de impacto: McCoy e Q escolhem os testes de regressão a partir dos dependentes reversos do que mudou (grafo de imports por linguagem do perfil). Se não conseguir mapear a mudança, roda tudo; nunca devolve um conjunto vazio. Aceite: o disjuntor no modo 1 restaura o snapshot do ticket com confirmação, sem perder arquivos fora do ticket; numa mudança numa função compartilhada, os testes escolhidos incluem os dos chamadores indiretos, e numa mudança fora do grafo o veredito é 'rodar tudo'.")

## Problem
No modo 1 não há commits, e a saída (b) do disjuntor ("voltar ao último ponto bom", `execute.md` seção 6) só existe para quem tem commit integrado. Quando o disjuntor abre no modo 1, hoje não há ponto bom para onde voltar. Além disso, McCoy e Q escolhem os testes de regressão no olho: podem rodar tudo (lento) ou esquecer os chamadores indiretos de uma função compartilhada.

## Users
- Picard, que tira o snapshot antes de cada ticket no modo 1 e oferece a restauração quando o disjuntor abre.
- O usuário, que confirma a restauração.
- McCoy e Q, que pedem o conjunto de testes do raio de impacto para os arquivos que mudaram.

## Success
- No modo 1, cada ticket tem um snapshot em `refs/starcode/snapshots/<ticket>` tirado antes do despacho, sem commit no branch e sem alterar a árvore nem o índice.
- Com o disjuntor aberto no modo 1, a saída (b) restaura o snapshot do ticket depois da confirmação do usuário. Arquivos fora do `May change` do ticket ficam intactos.
- Uma mudança numa função compartilhada seleciona também os testes dos chamadores indiretos (dependentes reversos transitivos).
- Uma mudança que o grafo não mapeia devolve o veredito "rodar tudo". O conjunto nunca sai vazio.

## Constraints
- Scripts só com a stdlib do Python (D20, padrão do repo).
- O `git_guard` bloqueia `checkout -- .`, `restore .`, `reset --hard` e `clean -f` (`hooks/scripts/git_guard.py`). A restauração não pode depender desses comandos nem contornar o hook: trabalha caminho por caminho, limitada ao `May change`.
- Só o Picard escreve o Handoff (D28). O snapshot e a restauração são registrados por ele.
- Modo 1 continua sendo verificação degradada. O snapshot não muda isso.

## Scope Notes
- Dentro: snapshot do modo 1 antes de cada ticket; restauração com confirmação como saída (b) do disjuntor no modo 1; seleção de testes por raio de impacto usada por McCoy e Q.
- Usuário: snapshot montado com índice temporário, cobrindo também arquivos não rastreados não ignorados (desvio consciente do `git stash create` do plano).
- Usuário: restaurar volta só os caminhos do `May change` do ticket.
- Usuário: grafo de imports para Python e TS/JS; Rust sempre "rodar tudo".
- Usuário: seleção só para McCoy e Q; os gates continuam rodando a suíte inteira.
- Fora: modos 2–4 (já têm o commit integrado como ponto bom); grafo para Rust; reduzir a suíte dos gates.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Como montar o snapshot | índice temporário com rastreados + não rastreados não ignorados / `git stash create` como no plano | Índice temporário | 2026-11-12 |
| Escopo da restauração | só caminhos do `May change` que mudaram, arquivo novo dentro dele removido / tudo que difere do snapshot | Só o May change | 2026-11-12 |
| Linguagens do grafo | Python + TS/JS / + Rust / só Python | Python + TS/JS | 2026-11-12 |
| Onde a seleção vale | só McCoy e Q / também nos gates do ticket | Só McCoy e Q | 2026-11-12 |
| Retenção dos snapshots | apagar em `--phase done` / manter os N últimos / nunca apagar | apagar os refs da feature quando ela chega a `done`; antes disso um novo snapshot do mesmo ticket substitui o anterior - default (não perguntado) | 2026-11-12 |
| Árvore sem mudanças no snapshot | sem snapshot / snapshot igual ao HEAD | grava o snapshot apontando para a árvore do HEAD, para a restauração ter sempre um alvo - default (não perguntado) | 2026-11-12 |
| Profundidade do raio | só dependentes diretos / transitivos completos | transitivos completos, com proteção contra ciclos - default (não perguntado) | 2026-11-12 |
| Arquivo de teste alterado | ignorar / incluir o próprio teste | o próprio teste entra no conjunto - default (não perguntado) | 2026-11-12 |
| Formato da saída | texto / JSON | texto legível por padrão e `--json` para o Picard e os briefs - default (não perguntado) | 2026-11-12 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | ID do ticket validado antes de virar nome de ref (`git check-ref-format`); caminhos do `May change` normalizados e confinados à raiz do repo; arquivos binários e grandes entram no snapshot como blobs sem leitura no Python. |
| Failure and partial failure | falha ao gravar o snapshot impede o despacho do ticket (registro que falha interrompe o fluxo, STARCODE.md). Na restauração, falha num caminho para e lista o que já foi restaurado e o que faltou, sem seguir às cegas. Erro de parse num arquivo do grafo → aquele arquivo vira "não mapeado" → "rodar tudo". |
| Retries, idempotency and duplicates | tirar o snapshot de novo para o mesmo ticket substitui o ref; restaurar duas vezes dá o mesmo resultado. |
| Authorization boundaries and rate limits | restauração só depois de uma confirmação explícita do usuário para aquela ação (flag `--yes` só passada pelo Picard depois do sim). Rate limit: N/A because é tudo local. |
| Concurrency and ordering | modo 1 roda tickets em sequência num único worktree; o índice temporário fica num arquivo próprio e nunca toca o `.git/index` real. Restaurar com worker rodando é recusado (o Picard checa `**Dispatched:**`). |
| Data lifecycle | refs em `refs/starcode/snapshots/<ticket>`, removidos quando a feature chega a `done`; nunca enviados no push (ref fora de `refs/heads`). |
| Observability | snapshot e restauração imprimem uma linha (ref, hash, quantidade de caminhos); o Picard registra o snapshot no Handoff. A seleção imprime o motivo de cada teste ou o motivo do "rodar tudo". |
| External dependency failure | N/A because só usa `git` local e a stdlib; sem rede. |
| State-transition rules | a restauração só é oferecida com `**Breaker:** open` e modo 1; depois dela o Picard grava `--breaker closed` e o próximo passo. |

## Facts Found
- Plano: `PLANO_STARCODE.md` seção 10 "Fase 12" e linha 295 (disjuntor no modo 1 volta ao snapshot "quando existir").
- Disjuntor: `scripts/handoff.py` (`BREAKER_LIMIT = 3`, `apply_attempt`, imprime `DISJUNTOR ABERTO`); saídas (a)/(b) em `skills/engajar/references/execute.md` seção 6; modo 1 na seção 7 (um worktree, sem commits, `git status` comparado antes e depois de cada worker).
- `hooks/scripts/git_guard.py` bloqueia checkout/restore da árvore inteira, `reset --hard`, `clean -f`.
- `git stash create` não inclui arquivos não rastreados (comportamento documentado do Git), daí a decisão do índice temporário.
- McCoy (`skills/mccoy/SKILL.md`): reproduz, escreve teste de regressão, roda o gate do ticket. Q (`skills/q/SKILL.md`, `briefs/q-verify.md`): roda exemplos não citados como testes descartáveis.
- Perfis (`profiles/*/profile.yaml`): `python-flask` (pytest), `typescript` (vitest), `tauri` (vitest + cargo), `rust` e `gpui` (cargo). O próprio StarCode usa Python com `tests/test_*.py`.
- `**May change**:` de cada ticket fica em `tasks.md` (briefing de 5 blocos) e já é lido pelo `scripts/gates/check_scope.py`.
