# Lições com recorrência por ID: Spec

**Approved**: 2026-11-15 - user: "Sim"

**Size**: MEDIUM
**Risk triggers**: dados persistidos
**Status**: Approved
**Linear**: SC-183
**May change**: scripts/lessons.py, skills/guinan/SKILL.md, tests/test_lessons.py, tests/test_guinan_skill.py, .specs/lessons.json, .specs/LESSONS.md, DECISIONS.md, dist/

## Context
Item N.1 de `starcode-triagem-v2-2026-11-13.md` (seção 7, fora do Git), passo 10 do primeiro corte. Discovery em `context.md`. A recorrência de uma lição só conta quando o texto normalizado é idêntico (`scripts/lessons.py:190-191`), e a Guinan escreve uma frase nova a cada retro. Por isso, 36 das 40 lições seguem `candidate`, fora dos briefs (`scripts/dispatch.py:417-424`). Sucesso: a Guinan registra a recorrência pelo ID e as repetições atuais são reprocessadas uma vez.

## Scope
- `lessons.py add --id L<n>`: registra a recorrência numa lição existente, sem depender do texto.
- `skills/guinan/SKILL.md`, seção 1: listar as lições antes de escrever e reusar o ID quando o achado é o mesmo.
- Reprocessamento único de `.specs/lessons.json` com `add --id`, nos grupos abaixo.
- Grupos do reprocessamento (canônica = menor ID; confirmados na aprovação da spec):
  - G1 **L2** ← L18, L21, L24, L26, L37, L38 (asserção pelo texto inteiro, não por trecho).
  - G2 **L10** ← L29, L31 (cada afirmação ou item do requisito com teste próprio).
  - G3 **L32** ← L34, L39 (entrada de registro: asserte cada termo e campo exigido).
  - Fora: L20 (já `confirmed`, mesmo tema de G1; juntar não muda os briefs); L27, L9, L22, L30, L17, L23, L4, L35 (temas vizinhos, mas com causa ou correção diferente).
  - Resultado esperado: L2 com 9 features (ganha ponte-missao-ativa, fase-12-robustez, manutencao-retros-f11, ajustes-review-pr39, snapshot-restauracao-segura, impacto-seleciona-real); L10 confirmed com fase-11-telas, despacho-media-escopo, q-familia-revendedor; L32 confirmed com q-familia-revendedor, setup-grava-config, impacto-seleciona-real. O `--signal` de cada chamada é o da canônica.

## Non-Goals
- Mudar `promote_threshold` (2), a janela de poda (45 dias), o formato do `lessons.json` ou a seção de lições do brief.
- Apagar as lições repetidas: elas ficam como candidatas até a poda (decisão do usuário).
- Qualquer comando, subcomando ou skill novo (congelamento D-i); `--id` é uma opção do `add`, prevista na triagem.

## Requirements
- **R1** - WHEN `lessons.py add --id L<n> --feature <f> --signal <s> --source <ref>` roda e `L<n>` existe com status `candidate` ou `confirmed` THEN the system SHALL acrescentar `<f>` a `features` e `<ref>` a `sources` (cada um só se ainda não estiver lá), gravar `updated` com a hora atual, manter `text`, `signal`, `scope` e `created`, e sair com 0.
- **R2** - WHEN o `add --id` deixa uma lição `candidate` com `len(features) >= promote_threshold` THEN the system SHALL mudar o status para `confirmed` e imprimir `atualizada L<n> (features=<k>, status=confirmed) - promovida a confirmed`; sem promoção, SHALL imprimir `atualizada L<n> (features=<k>, status=<status>)`.
- **R3** - The system SHALL aceitar o ID do `--id` sem diferença de maiúsculas (`l3` encontra `L3`), como o `penalize`.
- **R4** - IF `--id` não corresponde a nenhuma lição THEN the system SHALL imprimir em stderr `id inválido: nenhuma lição <id>`, sair com 2 e deixar `lessons.json` e `LESSONS.md` com os mesmos bytes.
- **R5** - IF a lição do `--id` está `quarantined` THEN the system SHALL imprimir em stderr `id inválido: <L<n>> está quarantined; recorrência não tira da quarentena`, sair com 2 e deixar os dois arquivos com os mesmos bytes.
- **R6** - WHILE `--id` está presente the system SHALL tornar `--text` opcional e ignorá-lo (o texto gravado não muda, e o limite de 300 caracteres não se aplica); `--feature`, `--signal` e `--source` continuam obrigatórios e validados como hoje.
- **R7** - IF `add` roda sem `--id` e sem `--text` THEN the system SHALL imprimir em stderr `text inválido: vazio` e sair com 2, sem criar nem mudar arquivo.
- **R8** - WHEN o mesmo `add --id` (mesma feature, mesma fonte) roda duas vezes THEN the system SHALL manter `features` e `sources` sem repetição.
- **R9** - The system SHALL ter na seção `## 1. Lessons` de `skills/guinan/SKILL.md` (e nas cópias de `dist/<cli>/skills/guinan/SKILL.md`, com o caminho do plugin resolvido) o passo de listar antes de escrever, com o comando `python "<plugin-root>/scripts/lessons.py" list --status all`, antes do passo que escreve a lição; e o passo de recorrência com o comando `python "<plugin-root>/scripts/lessons.py" add --id L<n> --feature <slug> --signal <signal> --source "<file:line or id>"`, dizendo que, quando uma lição `candidate` ou `confirmed` já descreve o mesmo achado (mesma causa e mesma correção, mesmo com outras palavras), a Guinan registra a recorrência pelo ID em vez de escrever uma frase nova.
- **R10** - The system SHALL ter `.specs/lessons.json`, depois do reprocessamento, com L2, L10 e L32 em `confirmed` e com as features e fontes dos grupos da seção Scope. Cada fonte acrescentada tem o formato `<ID da repetida> (<primeira fonte da repetida>)`. As repetidas continuam como estão.
- **R11** - The system SHALL ter no `DECISIONS.md` a entrada `### SC-183:` com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**, citando `--id`, `recorrência` e `D-i`.

## Decisions

| Decisão | Opções | Resposta |
|---|---|---|
| Destino das repetidas no reprocessamento | (a) ficam como candidatas até a poda; (b) remover já (comando novo ou JSON à mão) | approved - user: "Ficam até a poda" |


## Edge Cases
- `--id` de lição que já tem a feature: só a fonte nova entra, sem promoção (C1).
- `--id` em minúscula: R3 (C2).
- `--id` inexistente e `--id` de lição `quarantined`: R4, R5 (C3).
- `--id` com `--text` de 301 caracteres: aceito e ignorado (C2).
- `add` sem `--id` e sem `--text`: R7 (C4).
- Mesmo `add --id` repetido: R8 (C1).
- `--id` com `--signal` fora da lista: sai com 2 como hoje (C3).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Store temporário com L1 `candidate` na feature `f1`: `add --id L1 --feature f1 --source b:2` mantém 1 feature, junta a fonte, imprime exatamente `atualizada L1 (features=1, status=candidate)` e não muda `text`, `signal`, `scope` nem `created`; depois `add --id L1 --feature f2 --source c:3` imprime exatamente `atualizada L1 (features=2, status=confirmed) - promovida a confirmed`; repetir a última chamada deixa `features == ["f1", "f2"]` e `sources == ["a:1", "b:2", "c:3"]`, sem repetição (R1, R2, R8)
Proof: run unit | test_lessons_add_id_registra_recorrencia_e_promove ... ok

**C2** - `add --id l1` (minúscula) com `--text` de 301 caracteres sai com 0 e o `text` gravado de L1 é igual ao de antes; `add --id L1` sem `--text` também sai com 0 (R3, R6)
Proof: run unit | test_lessons_add_id_sem_caixa_e_text_ignorado ... ok

**C3** - `add --id L99` sai com 2 e o stderr é exatamente `id inválido: nenhuma lição L99\n`; com L1 em `quarantined` (via `penalize`), `add --id L1` sai com 2 e o stderr é exatamente `id inválido: L1 está quarantined; recorrência não tira da quarentena\n`; `add --id L1 --signal inventado` sai com 2 e `signal inválido:`; nos três casos os bytes de `lessons.json` e `LESSONS.md` são iguais aos de antes (R4, R5, R6)
Proof: run unit | test_lessons_add_id_invalido_ou_quarentena_sai_2 ... ok

**C4** - `add` sem `--id` e sem `--text` sai com 2, o stderr é exatamente `text inválido: vazio\n` e `.specs/lessons.json` não existe depois (R7)
Proof: run unit | test_lessons_add_sem_id_exige_text ... ok

**C5** - Em `skills/guinan/SKILL.md` e em cada `dist/<cli>/skills/guinan/SKILL.md`, dentro da seção `## 1. Lessons`: há uma linha com `scripts/lessons.py" list --status all` antes da linha com `scripts/lessons.py" add --feature`, e há uma linha com `scripts/lessons.py" add --id L<n> --feature <slug> --signal <signal> --source "<file:line or id>"` no mesmo passo que contém `candidate`, `confirmed` e `recorrência` (R9)
Proof: run unit | test_guinan_lista_licoes_e_reusa_id ... ok

**C6** - O `.specs/lessons.json` do repositório tem L2, L10 e L32 com status `confirmed`; as features de L2 contêm as 9 da seção Scope, as de L10 contêm `fase-11-telas`, `despacho-media-escopo` e `q-familia-revendedor`, e as de L32 contêm `q-familia-revendedor`, `setup-grava-config` e `impacto-seleciona-real`; as fontes de cada canônica contêm, para cada repetida do grupo, uma fonte que começa por `<ID da repetida> (` (R10)
Proof: run unit | test_licoes_reprocessadas_n1 ... ok

**C7** - A entrada `### SC-183:` do `DECISIONS.md` contém `**Problema**`, `**Decisão**`, `**Motivo**` e `**Por que não é bug**`, cada um asserido dentro da entrada, mais `--id`, `recorrência` e `D-i` (R11)
Proof: run unit | test_decisions_licoes_recorrencia_por_id ... ok

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** Q verifica
**Linear:** SC-183
**Integration branch:** feature/licoes-recorrencia-por-id
**Last integrated:** 15aaf96
**Dispatched:** none
**Settled:** 2026-11-15: 2026-11-15: aprovação da spec e issue: "Sim"
**Attempts:** none
**Reports:** 2026-11-15: T1: add --id, Guinan lista e reusa ID, reprocessamento L2/L10/L32, SC-183 em DECISIONS; 921 OK; ticket gate verde; 8fcdf56, dcfab00
**Breaker:** closed
