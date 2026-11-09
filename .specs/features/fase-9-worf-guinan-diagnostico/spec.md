# Fase 9: Worf, Guinan e diagnóstico (v1.3): Spec

**Approved**: 2026-11-09 - user: "sim"

**Size**: LARGE
**Risk triggers**: Segurança (gates de review e portão de evidência dos achados de segurança), Chamadas externas (`npx harness-score`, `gh` para o review do PR, juízes do harness-eval com custo)
**Status**: Approved

## Context

Até a v1.2 o review do PR é humano (plano §3). Também não há retro nem memória de lições entre as features, e não existe um jeito padronizado de medir a maturidade do harness de um repositório. Os achados do Q ficam no `verification.md` de cada feature, e erros repetidos voltam na feature seguinte (asserts fracos, exit code mascarado por pipe). A Fase 9 do plano (seções 3, 3.1, 3.2, 4 e 10) entrega três peças:
- **Worf** (`worf`): review de PR com os gates da §3.1 e o portão de evidência dos achados de segurança;
- **Guinan** (`guinan`): retro da feature e lições por repo, com `lessons.py`;
- **diagnóstico** (`diagnostico`, skill do LaForge): nível L0–L4 com `npx harness-score` e o Track A do harness-eval. Os Tracks B/C só rodam com aprovação de custo.

Sucesso:
- um review consolidado num PR de teste aponta um bypass plantado, que o `scan_bypasses.py` também detecta;
- uma lição fica registrada;
- existe um relatório L0–L4 do próprio repo.

Discovery: `.specs/features/fase-9-worf-guinan-diagnostico/context.md`. Issue: SC-16.

## Scope

- `scripts/review/` (novo, adaptado do the-judge 1.4.0): `scan_bypasses.py`, `review_gate.py`, `post_review.py`.
- `scripts/lessons.py` (novo, adaptado do `lessons.py` do tlc-spec-driven 4.1.0).
- `scripts/harness/` (novo, adaptado do harness-eval 1.8.3): `inventory_extract.py`, `track_a_correctness.py` e os auxiliares que esses dois importam; `merge_agreement.py`, `merge_usefulness.py`, `surfaces_extract.py`, `slim_fanin.py`, `doc_scope.py` para B/C.
- `scripts/diagnostico.py` (novo): roda o harness-score e o Track A e escreve o relatório.
- Skills novas: `skills/worf/` (com `references/review-standards.md`, `references/security-evidence.md`, `references/comment-voice.md`), `skills/guinan/` (com `references/retro.md`, `references/lessons.md`), `skills/diagnostico/` (com `references/judge-prompts.md` para B/C).
- Ajustes:
  - `skills/engajar/SKILL.md` e `references/execute.md`: Guinan depois do `done`, Worf depois do PR, antes da autorização de merge;
  - `scripts/dispatch.py`: lições confirmadas nos briefs do LaForge e do Q;
  - `src/crew.yaml`: `invocation: both` para `worf` e `guinan` e a skill `diagnostico` com dono `laforge`;
  - `src/context/STARCODE.md`: uma linha sobre review, retro e lições.
- `tools/build.py`: gera as 3 skills e copia os scripts novos nos 4 CLIs.
- Evals de roteamento para as 3 skills novas.
- Testes `unittest` de tudo acima, sem rede (`gh` e `npx` falsos).
- Registros:
  - `.gitignore`: `.harness-eval/`;
  - `CREDITS.md`: linhas do the-judge, harness-eval, tlc `lessons.py`, mattpocock `retro` e Cloudflare security-audit-skill;
  - `DECISIONS.md`: entradas F9-n;
  - `CHANGELOG.md`: seção `## [1.3.0] - não lançada`;
  - `docs/compatibilidade.md`: linha das 3 skills;
  - `dist/` regenerado.
- Aceite real em `docs/aceite/fase-9.md`. Inclui um PR rascunho de teste no `freire-andre/starcode` e `docs/diagnostico/<data>.md` do próprio repo.

## Non-Goals

- Painel Ponte (Fase 10), verificação de telas (Fase 11), snapshot e raio de impacto (Fase 12).
- Worf aprovando ou fazendo merge, ou mudando o código do PR. Worf só revisa. As correções vão para o LaForge.
- Instalar ferramentas no repositório revisado (linter, scanner) ou copiar o código do `harness-score` para o StarCode.
- Lições globais entre projetos (`~/.starcode`); lições de metodologia do próprio StarCode.
- Aplicar automaticamente cortes do Track B/C (Ship/Slim) ou sugestões da retro.
- Tag/release da v1.3.0 (fica para depois do aceite, com confirmação própria).

## Requirements

### Worf: varredura de bypass

- **R1** - WHEN `git diff <base>...<head> | python scripts/review/scan_bypasses.py` roda THEN the system SHALL imprimir uma linha `<arquivo>:<linha>\t<categoria>\t<conteúdo até 160 caracteres>` para cada linha adicionada com um marcador das categorias `suppression`, `test-dodge`, `hook-bypass`, `tls-bypass`, `type-bypass`, `error-swallow`, `unsafe-html`, `sync-hack`, com o número da linha no arquivo novo.
- **R2** - The system SHALL fazer o `scan_bypasses.py` ignorar linhas removidas e de contexto, imprimir `scan: <N> candidate(s)` no stderr e sair sempre com 0 (um detector nunca bloqueia o review).
- **R3** - The system SHALL tratar cada linha do `scan_bypasses.py` como candidata, não como achado. Uma supressão com justificativa e link de issue na mesma linha ou na anterior é aceita. Sem isso, vira achado `should-fix` (ou `blocker` se for `tls-bypass` ou `hook-bypass`).

### Worf: gate do review

- **R4** - WHEN `python scripts/review/review_gate.py <review.json>` roda THEN the system SHALL sair com 0 só se o JSON (Data & Contracts) cumprir todas as regras abaixo. Caso contrário, SHALL sair com 1 e listar uma linha `<local>: <regra>` por violação:
  - severidades só de `blocker`, `should-fix`, `nit`, `pre-existing`;
  - no máximo 5 `nit`;
  - todo `blocker` e `should-fix` com `evidence` não vazia, no formato `arquivo:linha` (interno), URL `https://` ou ID do Context7 (externo);
  - `summary` começando por `TL;DR:` com o veredito;
  - veredito igual ao mapeamento de R5.
- **R5** - The system SHALL calcular o veredito assim:
  - qualquer `blocker` → `REQUEST_CHANGES`;
  - nenhum `blocker` e nenhum `should-fix` → `APPROVE`;
  - o resto → `COMMENT`.

  Os emojis de severidade são 🔴 blocker, 🟠 should-fix, 🟡 nit, 🟣 pre-existing.
- **R6** - The system SHALL fazer o `review_gate.py` recusar, em PT-BR e em EN, palavras de bajulação e enchimento da lista do the-judge (ex.: "ótimo trabalho", "vale ressaltar", "great job"), comparadas sem acento e sem diferença de caixa. Cada uma vira uma violação `<local>: termo proibido "<termo>"`.
- **R7** - WHILE a rodada é 2 ou 3 the system SHALL fazer o `review_gate.py` recusar achado novo que não seja `blocker`, com `round <N>: só verificação de resolução e blockers novos`. IF a rodada passa de 3 THEN the system SHALL sair com 1 e `limite de 3 rodadas`.

### Worf: portão de evidência de segurança

- **R8** - The system SHALL exigir em todo achado com `category: security` os campos `attacker`, `entry`, `control`, `boundary`, `impact`, `proof` e `state`. `state` só pode ser `confirmed`, `needs-validation` ou `rejected`. O `review_gate.py` sai com 1 e `security: campo <nome> ausente` quando falta um campo.
- **R9** - IF `state` é `needs-validation` THEN the system SHALL exigir `missing_fact` não vazio. IF é `rejected` THEN SHALL exigir `reason` não vazio e nunca contar o achado no veredito. IF é `needs-validation` THEN a severidade máxima permitida é `should-fix`.
- **R10** - The system SHALL aceitar `hardening: true` num achado de segurança (falta de uma camada quando outra já barra o ataque). Esse achado vai só para o resumo, fora da contagem e do veredito.

### Worf: fluxo do review

- **R11** - WHEN o Worf revisa um PR ou um intervalo `<base>...<head>` THEN the system SHALL seguir esta ordem: (1) rodar os comandos de gate do repo (`**Build**`/`**Run**` dos tasks.md, ou o perfil do Scotty, ou o CI) e registrar o resultado, deixando o que eles pegam fora dos comentários; (2) rodar o `scan_bypasses.py`; (3) pesquisar cada superfície externa tocada pelo diff (dependência nova ou atualizada, API externa) no Context7, ou na documentação oficial quando o Context7 não está disponível, e registrar cada URL ou ID consultado; (4) revisar só o diff, os arquivos tocados e os chamadores diretos; (5) escrever o `review.json`; (6) rodar o `review_gate.py` até sair com 0.
- **R12** - The system SHALL rebaixar a pergunta, ou remover, todo achado sobre comportamento externo sem URL ou ID consultado na própria revisão, e todo achado interno cujo `arquivo:linha` não foi lido.
- **R13** - WHEN o `review_gate.py` sai com 0 THEN the system SHALL gravar `.specs/features/<slug>/review.md`. O arquivo tem `**Round**: <N>`, `**Verdict**: <veredito>`, `**Reviewer**: <cli> · <modelo>`, o TL;DR, uma tabela de achados (`| ID | Severity | Where | Finding | Evidence | State |`, IDs `W<n>` estáveis entre rodadas), o resultado da escada determinística e o registro da pesquisa.
- **R14** - The system SHALL publicar no PR só depois da confirmação do usuário nesta sessão, com `python scripts/review/post_review.py <review.json> --pr <N>`. O script SHALL recusar publicar (sai com 3 e não chama o `gh`) quando o `review_gate.py` não sai com 0. Também SHALL recusar quando o `review.md` da mesma rodada já tem a linha `**Posted**:`.
- **R15** - WHEN o autor do PR é o mesmo usuário autenticado no `gh` THEN `post_review.py` SHALL publicar como `COMMENT` e acrescentar ao fim do resumo `Veredito pretendido: <veredito> (o GitHub não aceita <veredito> no próprio PR)`.
- **R16** - IF o `gh` falha ao publicar (sem login, sem rede, erro HTTP) THEN the system SHALL manter o `review.md` intacto, sair com 2, mostrar `gh falhou: <motivo>` e não gravar `**Posted**:`. WHEN publica com sucesso THEN SHALL gravar `**Posted**: <data> - <URL do review>` no `review.md`.

### Worf no fluxo do Picard

- **R17** - WHEN o Picard abre o PR de uma feature (modos 3/4) THEN the system SHALL invocar o Worf antes de pedir a autorização de merge. No Claude, o Worf roda como subagente com o modelo do `crew.yaml`; nos outros CLIs, na própria sessão.
- **R18** - IF o veredito é `REQUEST_CHANGES` ou `COMMENT` com `should-fix` aberto THEN the system SHALL despachar **um** LaForge com todos os achados abertos num brief só. Depois roda a rodada seguinte do Worf (só verificação, R7). Após a rodada 3 com achados abertos, SHALL parar e mostrar os achados e a evidência, sem pedir o merge.
- **R19** - The system SHALL nunca fazer o Worf aprovar merge, fazer merge ou editar arquivos fora do `review.md` e do `review.json`.

### Guinan

- **R20** - WHEN `run_gates.py done <slug>` fica verde THEN the system SHALL invocar a Guinan antes do PR. A Guinan também pode ser chamada pelo usuário a qualquer momento para uma feature.
- **R21** - The system SHALL fazer a Guinan registrar uma lição por achado, com `python scripts/lessons.py add --feature <slug> --signal <sinal> --source <ref> --text "<frase>"`. Fontes:
  - achado do `verification.md` (`weak_test`, `spec_precision_gap`, `ac_gap`, `spec_deviation`);
  - linha vermelha do `proofs.md` (`gate_fail`);
  - achado `confirmed` `blocker`/`should-fix` do `review.md` (`review_finding`).

  Feature sem achado nenhum não ganha lição.
- **R22** - IF `lessons.py add` recebe `--signal` fora da lista, `--source` vazio ou `--text` vazio ou com mais de 300 caracteres THEN the system SHALL sair com 2 e uma mensagem com o campo, sem gravar nada.
- **R23** - The system SHALL fazer o `lessons.py` manter `.specs/lessons.json` (só o script escreve) e renderizar `.specs/LESSONS.md` a cada escrita. Regras:
  - lição de texto igual (comparado sem acento, caixa e pontuação) conta recorrência em vez de duplicar;
  - `candidate` vira `confirmed` quando aparece em 2 features distintas;
  - `penalize` move uma `confirmed` para `quarantined`.
- **R24** - The system SHALL fazer a Guinan escrever a retro em `.specs/features/<slug>/retro.md`. A retro tem até 7 sugestões de ambiente, ordenadas por severidade, nas categorias navegação, checagens automáticas, regras do revisor, AGENTS/CLAUDE.md, economia de ferramentas, instruções sem efeito e acesso a informação. Cada sugestão cita a evidência da feature (commit, linha do Handoff, achado). As sugestões nunca são aplicadas nem viram lição sozinhas.

### Lições nos briefs

- **R25** - WHEN `dispatch.py brief` ou `dispatch.py q-brief` gera um brief e existem lições `confirmed` THEN the system SHALL acrescentar uma seção `## Lessons` com até as 10 mais recentes (`L<n>: <texto>`). Sem lição confirmada ou sem `.specs/lessons.json`, a seção não aparece e o brief fica igual ao de hoje.

### Diagnóstico

- **R26** - WHEN `python scripts/diagnostico.py run [--root <repo>]` roda THEN the system SHALL executar `npx --yes harness-score@<versão> --json <repo>` com a versão fixada em `scripts/diagnostico.py` (lida do registro npm quando o script foi escrito). Depois roda o Track A (`inventory_extract.py` + `track_a_correctness.py`) com saída em `<repo>/.harness-eval/runs/<data>-diag/`.
- **R27** - The system SHALL escrever `docs/diagnostico/<YYYY-MM-DD>.md` no repo, com:
  - `**Level**: L<n> · <nome>` e `**Score**: <pontos>/<total>`;
  - uma tabela de dimensões com a porcentagem de cada uma;
  - a linha "Próximo degrau" (`To reach L<n+1>: ...` do harness-score);
  - o resumo do Track A (total de referências quebradas e os 5 primeiros grupos);
  - `**Tracks B/C**: não executados` ou o resultado.

  Rodar duas vezes no mesmo dia sobrescreve o arquivo do dia.
- **R28** - IF o `npx` não existe, falha ou não responde em 120 s THEN the system SHALL escrever no relatório `**Level**: não executado - <motivo>`, rodar o Track A mesmo assim e sair com 0. IF o Track A falha THEN SHALL sair com 2 com `track A falhou: <motivo>`.
- **R29** - The system SHALL rodar o Track B e/ou o Track C só depois de mostrar ao usuário a estimativa (número de juízes e de afirmações) e receber a aprovação nesta execução. A aprovação nunca é gravada em config. Sem aprovação, o relatório diz `**Tracks B/C**: não executados (sem aprovação de custo)`.
- **R30** - WHERE Track B ou C roda the system SHALL usar dois juízes independentes (o segundo sem acesso às notas do primeiro nem às chaves das armadilhas), gravar `model: <id>` de cada juiz e seguir o portão das armadilhas do harness-eval. Os cortes (Ship/Slim) são só relatório e nunca são aplicados.

### Registro e distribuição

- **R31** - The system SHALL gerar `worf`, `guinan` e `diagnostico` e copiar `scripts/review/`, `scripts/harness/`, `scripts/lessons.py` e `scripts/diagnostico.py` em cada `dist/<cli>/` por `tools/build.py`. `build.py --check` SHALL passar.
- **R32** - The system SHALL ter `worf` e `guinan` com `invocation: both` no `src/crew.yaml`, e `diagnostico` como skill com dono `laforge` e `invocation: user`.
- **R33** - The system SHALL ter evals de roteamento: ao menos 2 casos positivos e 1 negativo por skill nova (`worf`, `guinan`, `diagnostico`).
- **R34** - The system SHALL ter no `CREDITS.md` uma linha por fonte adaptada, com licença e arquivos:
  - the-judge 1.4.0 (CC-BY-4.0);
  - harness-eval 1.8.3 (CC-BY-4.0);
  - tlc-spec-driven 4.1.0 `lessons.py` (CC-BY-4.0);
  - mattpocock/skills `retro` (MIT);
  - Cloudflare security-audit-skill (MIT);
  - harness-score (MIT, só executado via `npx`).

  Cada arquivo adaptado SHALL ter no topo um comentário de origem e licença.
- **R35** - The system SHALL ter `.harness-eval/` no `.gitignore` do repo. O `diagnostico` SHALL avisar, em uma linha, quando o repo alvo não ignora essa pasta.

### Aceite

- **R36** - The system SHALL ter `docs/aceite/fase-9.md` com os resultados reais de quatro itens:
  - (1) um PR rascunho no `freire-andre/starcode`, num ramo descartável, com um bypass plantado: o `scan_bypasses.py` o lista e o `review.md`/review publicado o aponta com `arquivo:linha`;
  - (2) a publicação confirmada pelo usuário e o fallback de `COMMENT` do próprio PR;
  - (3) uma lição registrada pela Guinan em `.specs/LESSONS.md`;
  - (4) o relatório `docs/diagnostico/<data>.md` do próprio StarCode, com nível L0–L4.

  O PR de teste é fechado sem merge no fim.

## Data & Contracts

`review.json` (entrada do `review_gate.py` e do `post_review.py`):

```json
{
  "round": 1,
  "verdict": "REQUEST_CHANGES",
  "summary": "TL;DR: REQUEST_CHANGES - 1 blocker (TLS desligado)",
  "findings": [
    {"id": "W1", "severity": "blocker", "path": "src/x.py", "line": 12,
     "body": "...", "evidence": "src/x.py:12", "category": "security",
     "attacker": "...", "entry": "...", "control": "...", "boundary": "...",
     "impact": "...", "proof": "...", "state": "confirmed"}
  ],
  "carryover": {"W3": "resolved"},
  "research": ["https://...", "/context7/lib-id"],
  "ladder": [{"cmd": "python -m unittest", "result": "ok"}]
}
```

`lessons.json`: `{"schemaVersion": 1, "promote_threshold": 2, "lessons": [{"id": "L1", "text": "...", "signal": "weak_test", "status": "candidate|confirmed|quarantined", "features": ["<slug>"], "sources": ["<ref>"], "scope": "", "created": "<data>", "updated": "<data>"}]}`.

Sinais do `lessons.py`: `weak_test`, `spec_precision_gap`, `ac_gap`, `spec_deviation`, `gate_fail`, `review_finding`.

Códigos de saída:
- `review_gate.py`: 0 ok, 1 violação;
- `post_review.py`: 0 publicado, 2 falha do `gh`, 3 recusado pelo gate ou rodada já publicada;
- `lessons.py`: 0 ok, 2 entrada inválida;
- `diagnostico.py`: 0 ok (mesmo com harness-score não executado), 2 Track A falhou.

## States

- Review: `rodada N gravada` → `publicada` (`**Posted**:`) → rodada N+1 (até 3) → `aberto após 3 rodadas` (parada para o usuário).
- Achado de segurança: `confirmed` | `needs-validation` (com `missing_fact`) | `rejected` (com `reason`); `hardening` fora da contagem.
- Lição: `candidate` → `confirmed` (2 features) → `quarantined` (penalize).
- Diagnóstico: harness-score `executado` | `não executado - <motivo>`; Tracks B/C `não executados` | `executados (<modelos>)`.

## Edge Cases

- Diff vazio, ramo inexistente ou PR inexistente: o Worf para com `nada para revisar: <alvo>`, sem `review.md`.
- Diff só de arquivos mecânicos (`dist/`, lockfiles): eles são listados no resumo e ficam fora do review. O veredito é `APPROVE` se não houver outros achados.
- Bypass com justificativa e link de issue: candidato aceito (R3) e listado só no resumo.
- Repo sem linter ou testes: a escada registra `sem ferramentas determinísticas` e segue. Nada é instalado.
- `gh` sem login: o review fica só no arquivo (R16).
- `lessons.json` corrompido: `lessons.py` sai com 2 e `lessons.json inválido: <motivo>`, sem sobrescrever.
- Repo alvo sem `AGENTS.md`/`CLAUDE.md`: o harness-score devolve L0 normalmente, e o relatório mostra isso.
- Windows: os scripts leem e escrevem em UTF-8 explícito, sem depender do `PYTHONIOENCODING`.

## Decisions

| Item | Options | Status |
|---|---|---|
| Entrega do review | arquivo + gh confirmado · só arquivo · publica direto | approved - user: "Arquivo + gh confirmado (Recommended)" |
| PR de teste do aceite | PR rascunho no starcode · repo GitHub para o sandbox · só ramo local | approved - user: "PR rascunho no starcode (Recommended)" |
| Worf no fluxo | automático após o PR · só sob demanda | approved - user: "Automático após o PR (Recommended)" |
| Alcance das lições | por repo lidas nos briefs · por repo só registro · repo + global | approved - user: "Por repo, lidas nos briefs (Recommended)" |
| Guinan, retro, relatório, custo B/C, rodadas | defaults da descoberta (context.md, Gray Areas) | approved - user: defaults apresentados na descoberta, sujeitos a esta aprovação |
| Local dos scripts | `scripts/review/`, `scripts/harness/`, `scripts/lessons.py`, `scripts/diagnostico.py` (convenção de `scripts/gates/`) · dentro de cada skill | approved - user: decisão interna do Spock, sujeita a esta aprovação |

## Open Questions
None.

## Sources

- the-judge 1.4.0 (`docs/reference/the-judge.zip`): binding para os gates e scripts do Worf.
- harness-eval 1.8.3 (`docs/reference/harness-eval.zip`): binding para o Track A e o protocolo B/C.
- tlc-spec-driven 4.1.0 `scripts/lessons.py` e `references/lessons.md`: binding para o mecanismo de lições.
- harness-score (`docs/reference/harness-score-main.zip`, npm 1.8.4): binding para os níveis L0–L4.
- mattpocock/skills `retro`: non-binding - a retro segue as categorias, adaptada para a feature StarCode.
- Plano §3.1: binding.

## Differences from the Source

- the-judge publica direto no PR; aqui a publicação exige a confirmação do usuário (R14), por ser escrita externa (D29).
- the-judge abre rodadas pela listagem dos reviews no GitHub; aqui a rodada e o livro de achados ficam no `review.md` da feature (R13).
- the-judge não tem portão de evidência de segurança estruturado; aqui ele entra pela §3.1 (R8–R10).
- tlc: lições alimentadas só pelo verificador; aqui também pelos achados confirmados do Worf (sinal `review_finding`, R21).
- harness-eval é skill autônoma; aqui o Track A roda junto do harness-score num relatório só (R26, R27).
