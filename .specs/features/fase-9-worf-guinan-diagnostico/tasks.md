# Fase 9: Worf, Guinan e diagnóstico (v1.3): Tasks

**Approved**: 2026-11-09 - user: "sim"

**Spec**: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md`
**Status**: Approved
**Integration branch**: `feature/fase-9-worf-guinan-diagnostico`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only, no generator change | `python -m unittest discover -s tests -v` |
| full | task that changes `skills/`, `scripts/`, `hooks/`, `src/`, `schemas/`, `evals/` or `tools/build.py` (F3-1: `dist/` regenerated in the same commit) | `python tools/build.py && python tools/build.py --check && python -m unittest discover -s tests -v` |
| build | records task, or after the last code task | `python tools/build.py && python tools/build.py --check && claude plugin validate dist/claude --strict && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |

## Tasks

### T1: Varredura de bypass (scan_bypasses.py)
**Linear**: SC-102
**Depends on**: none
**Requirements**: R1, R2
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/review/scan_bypasses.py` (só stdlib), adaptado de `the-judge/scripts/scan_bypasses.py` (the-judge 1.4.0, CC-BY-4.0, Felipe Rodrigues). O arquivo começa com um comentário de origem e licença.
- Lê um diff unificado do stdin, ou de `--diff <arquivo>`. Para cada linha **adicionada** com marcador, imprime `<arquivo>:<linha>\t<categoria>\t<conteúdo, strip, até 160 caracteres>`, com o número da linha no arquivo novo (cabeçalho `@@ ... +N ... @@`).
- Categorias e padrões: os do the-judge (`suppression`, `test-dodge`, `hook-bypass`, `tls-bypass`, `type-bypass`, `error-swallow`, `unsafe-html`, `sync-hack`). Um marcador por linha (o primeiro que casar).
- Ignora linhas removidas, de contexto, `\ No newline` e cabeçalhos `---`/`+++`.
- No stderr, `scan: <N> candidate(s)`. Sai **sempre** com 0, inclusive com diff vazio ou inválido.
- Leitura e escrita em UTF-8 explícito (`sys.stdin.reconfigure(encoding="utf-8")` ou leitura binária), sem depender do `PYTHONIOENCODING`.
- Adicione `ROOT / "scripts" / "review"` ao `sys.path` em `tests/helpers.py`.

Testes em `tests/test_review_scan.py` com diffs de fixture em `tests/fixtures/review/`. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R1, R2). Checks: C1, C2.
Fonte: `docs/reference/the-judge.zip` (o zip é ignorado pelo Git, mas está na pasta do repo principal `F:/Projetos/StarCode/docs/reference/`). Extraia numa pasta temporária fora do repo. Os scripts do repo são stdlib puro, testados com `unittest` (veja `tests/helpers.py` e `tests/test_dispatch.py`). `tools/build.py` copia `scripts/` inteiro para `dist/<cli>/scripts/`.

#### BOUNDARIES
May change: `scripts/review/scan_bypasses.py`, `tests/test_review_scan.py`, `tests/fixtures/review/`, `tests/helpers.py`, `dist/`
Do not touch: `skills/`, `src/`, `tools/build.py`, `scripts/dispatch.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T2: Gate do review e portão de evidência de segurança (review_gate.py)
**Linear**: SC-103
**Depends on**: T1
**Requirements**: R4, R5, R6, R7, R8, R9, R10
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/review/review_gate.py` (só stdlib, sem rede), adaptado de `the-judge/scripts/review_gate.py` (CC-BY-4.0, comentário de origem no topo). O formato de entrada é o `review.json` de Data & Contracts da spec. `python review_gate.py <review.json>` sai com 0 sem violações. Com violações, sai com 1 e imprime uma linha `<local>: <regra>` por violação (`<local>` = `summary`, `verdict`, `round` ou `W<n>`). Regras:
- severidade só em `blocker`, `should-fix`, `nit`, `pre-existing`; no máximo 5 `nit` (`nits: <N> acima do limite de 5`);
- `blocker` e `should-fix` com `evidence` não vazia, no formato `arquivo:linha`, URL `https://...` ou ID do Context7 (`/org/lib` ou `/org/lib/versão`);
- `summary` começa com `TL;DR:` e contém o token do veredito;
- veredito calculado (R5): algum `blocker` contável → `REQUEST_CHANGES`; nenhum `blocker` nem `should-fix` contável → `APPROVE`; senão `COMMENT`. Divergência → `verdict: esperado <X>, recebido <Y>`. Não contam: achado `rejected`, `hardening: true` e `pre-existing`;
- termos proibidos (lista do the-judge em PT-BR e EN, mais "ótimo trabalho", "excelente", "vale ressaltar", "great job"), comparados sem acento e sem caixa em `summary` e em cada `body`: `<local>: termo proibido "<termo>"`;
- `round` 2 ou 3: achado cujo `id` não está em `carryover` e não é `blocker` → `round <N>: só verificação de resolução e blockers novos`; `round` > 3 → `round: limite de 3 rodadas`;
- `category: security`: exige `attacker`, `entry`, `control`, `boundary`, `impact`, `proof` e `state` (`security: campo <nome> ausente`); `state` só em `confirmed`, `needs-validation`, `rejected`; `needs-validation` exige `missing_fact` e severidade no máximo `should-fix`; `rejected` exige `reason`.
- Exporte `compute_verdict(findings) -> str` e `EMOJI = {"blocker": "🔴", "should-fix": "🟠", "nit": "🟡", "pre-existing": "🟣"}`.

Testes em `tests/test_review_gate.py`, com JSONs de fixture em `tests/fixtures/review/`. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R4–R10; `review.json` e os códigos de saída em Data & Contracts). Checks: C3–C9.
Fonte: `docs/reference/the-judge.zip` (`scripts/review_gate.py`, `SKILL.md` seção "Severity and Verdict"). O portão de segurança vem do plano §3.1, adaptado da Cloudflare security-audit-skill (MIT). Escreva as regras do zero, a partir do texto da §3.1. O `scan_bypasses.py` (T1) já existe em `scripts/review/`.

#### BOUNDARIES
May change: `scripts/review/review_gate.py`, `tests/test_review_gate.py`, `tests/fixtures/review/`, `dist/`
Do not touch: `scripts/review/scan_bypasses.py`, `skills/`, `src/`, `tools/build.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T3: Publicação do review no PR (post_review.py)
**Linear**: SC-104
**Depends on**: T2
**Requirements**: R14, R15, R16
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/review/post_review.py` (só stdlib), adaptado de `the-judge/scripts/post_review.py` (CC-BY-4.0, comentário de origem no topo). Uso: `python post_review.py <review.json> --pr <N> --review-md <caminho do review.md>`.
- Antes de qualquer chamada ao `gh`, roda `review_gate.py` no JSON. Também lê o `review.md`: gate diferente de 0 → sai com 3 e `recusado: review_gate falhou`; `**Posted**:` já presente para a mesma `**Round**` → sai com 3 e `recusado: rodada <N> já publicada`. Nos dois casos, nenhuma chamada ao `gh`.
- Autor do PR (`gh pr view <N> --json author`) igual ao usuário do `gh api user --jq .login` → publica com evento `COMMENT` e acrescenta ao fim do corpo `Veredito pretendido: <veredito> (o GitHub não aceita <veredito> no próprio PR)`. Senão usa o veredito como evento.
- Publica um review consolidado com comentários inline (`gh api repos/{owner}/{repo}/pulls/<N>/reviews` com o JSON num arquivo temporário UTF-8). `pre-existing` e `hardening` vão só no corpo.
- Falha do `gh` (exit ≠ 0, ausente do PATH) → sai com 2 e `gh falhou: <motivo>`, sem tocar no `review.md`.
- Sucesso → acrescenta `**Posted**: <YYYY-MM-DD> - <html_url do review>` ao `review.md` e sai com 0.

Testes em `tests/test_review_post.py` com um `gh` falso (script Python num PATH temporário, com `gh.cmd` no Windows, como em `tests/test_ephemeral_db.py`), que registra as chamadas. Nunca o `gh` real. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R14–R16; códigos de saída em Data & Contracts). Checks: C10, C11, C12.
Fonte: `docs/reference/the-judge.zip` (`scripts/post_review.py`). O padrão de executável falso no Windows está em `tests/test_ephemeral_db.py` (docker falso).

#### BOUNDARIES
May change: `scripts/review/post_review.py`, `tests/test_review_post.py`, `tests/fixtures/review/`, `dist/`
Do not touch: `scripts/review/scan_bypasses.py`, `scripts/review/review_gate.py`, `skills/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T4: Skill do Worf e evals de roteamento
**Linear**: SC-105
**Depends on**: T3
**Requirements**: R3, R11, R12, R13, R19
**Tests**: unit
**Gate**: full

#### TASK
Criar `skills/worf/SKILL.md` (EN, saída PT-BR, frontmatter `name: worf` e `description` com gatilhos como "Worf, revise o PR", "review do PR", "revise esse PR"; não usar para corrigir código) e as referências:
- `references/review-standards.md`: passes do review, severidades e emojis, regra dos bypasses (R3: candidato com justificativa e link de issue aceito; sem isso `should-fix`, ou `blocker` para `tls-bypass`/`hook-bypass`), arquivos mecânicos (`dist/`, lockfiles) fora do review, convergência em até 3 rodadas;
- `references/security-evidence.md`: o portão de evidência (quem ataca, por onde entra, controle, fronteira, impacto, prova; estados; `hardening`; severidade nunca acima do impacto demonstrado), com crédito à Cloudflare security-audit-skill (MIT);
- `references/comment-voice.md`: voz dos comentários em PT-BR, sem bajulação, uma ideia por comentário.

O `SKILL.md` define o fluxo de R11, nesta ordem:
1. escada determinística: `**Build**`/`**Run**` dos `tasks.md`, ou `scaffold.py checks`, ou o CI;
2. `git diff <base>...<head> | python "<plugin-root>/scripts/review/scan_bypasses.py"`;
3. pesquisa das superfícies externas (Context7 `resolve-library-id` + `query-docs`; sem Context7, documentação oficial com URL);
4. revisão do diff, dos arquivos tocados e dos chamadores diretos;
5. o `review.json`;
6. `review_gate.py` até sair com 0.

Também define:
- R12: achado sem evidência é rebaixado ou removido;
- R13: o `review.md`, com `**Round**`, `**Verdict**`, `**Reviewer**`, TL;DR, a tabela `| ID | Severity | Where | Finding | Evidence | State |`, a escada e a pesquisa;
- a publicação só com confirmação, via `post_review.py`;
- R19: nunca aprova merge, faz merge ou edita fora do `review.md`/`review.json`;
- alvo vazio ou inexistente: `nada para revisar: <alvo>`.

Persona só no chat, e o header vem do hook no Claude (`crew_live.py` nos outros CLIs, como nas skills existentes).

Evals de roteamento: `evals/routing/pos-worf-review-pr/`, `evals/routing/pos-worf-security/`, `evals/routing/neg-worf-fix-code/` (formato dos `case.yaml` existentes). Testes de conteúdo em `tests/test_worf_skill.py` (fonte e os 4 CLIs). Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R3, R11–R13, R19). Checks: C13–C17.
Fonte: `docs/reference/the-judge.zip` (`SKILL.md`, `references/review-standards.md`, `references/comment-voice.md`; CC-BY-4.0, adapte com crédito). Modelo de skill: `skills/uhura/SKILL.md` e `tests/test_uhura_skill.py`. O Worf já está declarado em `src/crew.yaml` (`subagent: true`, Opus 5.5, voz "Hoje é um bom dia para revisar."). `tools/build.py` gera toda skill de `skills/` declarada no crew.yaml.

#### BOUNDARIES
May change: `skills/worf/`, `evals/routing/pos-worf-review-pr/`, `evals/routing/pos-worf-security/`, `evals/routing/neg-worf-fix-code/`, `tests/test_worf_skill.py`, `dist/`, `tests/test_build.py` (ampliado pelo Picard em 2026-11-09: a asserção de que `worf` não está em `available` passa a `assertIn`)
Do not touch: `scripts/`, `src/`, `skills/engajar/`, `tools/build.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T5: Lições por repo (lessons.py)
**Linear**: SC-106
**Depends on**: T4
**Requirements**: R22, R23
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/lessons.py` (só stdlib), adaptado de `tlc-spec-driven/scripts/lessons.py` (4.1.0, CC-BY-4.0, Felipe Rodrigues; comentário de origem no topo). Subcomandos: `init`, `add`, `penalize`, `list`, `prune`, `status`, com `--root` (padrão: pasta atual).
- `add --feature <slug> --signal <s> --source <ref> --text "<frase>" [--scope <s>]`. Sinais: `weak_test`, `spec_precision_gap`, `ac_gap`, `spec_deviation`, `gate_fail`, `review_finding`. Sinal fora da lista, `--source` vazio, `--text` vazio ou com mais de 300 caracteres → sai com 2 e `<campo> inválido: <motivo>`, sem gravar.
- Estado em `.specs/lessons.json` (formato de Data & Contracts da spec; só o script escreve). A cada escrita, renderiza `.specs/LESSONS.md` com as seções `## Confirmed`, `## Candidates`, `## Quarantined`.
- Texto igual, comparado sem acento, caixa e pontuação, soma a feature e a fonte à lição existente. Não duplica. A mesma feature não conta duas vezes.
- `candidate` → `confirmed` quando `features` tem 2 slugs distintos (`promote_threshold`).
- `penalize --id L<n>`: `confirmed` → `quarantined`.
- `list --status confirmed|candidate|quarantined|all [--limit N] [--json]`: as mais recentes primeiro (por `updated`).
- `lessons.json` inválido → sai com 2 e `lessons.json inválido: <motivo>`, sem sobrescrever.
- UTF-8 explícito em toda leitura e escrita.

Testes em `tests/test_lessons.py` (pasta temporária, nunca o `.specs/` do repo). Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R22, R23; `lessons.json` em Data & Contracts). Checks: C18, C19, C20.
Fonte: `docs/reference/tlc-spec-driven.zip` (`scripts/lessons.py` e `references/lessons.md`). Siga o mecanismo, com o sinal novo `review_finding` e o limite de 300 caracteres.

#### BOUNDARIES
May change: `scripts/lessons.py`, `tests/test_lessons.py`, `dist/`
Do not touch: `scripts/review/`, `scripts/dispatch.py`, `skills/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T6: Skill da Guinan (retro e lições) e evals de roteamento
**Linear**: SC-107
**Depends on**: T5
**Requirements**: R21, R24
**Tests**: unit
**Gate**: full

#### TASK
Criar `skills/guinan/SKILL.md` (EN, saída PT-BR, `name: guinan`, `description` com gatilhos como "Guinan, faça a retro", "retrospectiva da feature", "registre as lições"; não usar para revisar PR). Referências:
- `references/lessons.md`: a tabela achado → sinal; uma lição por achado, numa frase acionável e geral do código; nada de lição de metodologia; feature sem achado não ganha lição;
- `references/retro.md`: as 7 categorias (navegação, checagens automáticas, regras do revisor, AGENTS/CLAUDE.md, economia de ferramentas, instruções sem efeito, acesso a informação), com crédito a mattpocock/skills `retro` (MIT).

O `SKILL.md` define:
- R21: lê `verification.md`, `proofs.md` e `review.md` da feature e chama `python "<plugin-root>/scripts/lessons.py" add ...` por achado. A tabela de sinais inclui `review_finding` para achado `confirmed` `blocker`/`should-fix` do Worf.
- R24: escreve `.specs/features/<slug>/retro.md` com até 7 sugestões ordenadas por severidade. Cada uma tem categoria, evidência (commit, linha do Handoff ou achado) e ação proposta. As sugestões nunca são aplicadas nem viram lição sozinhas.
- Relatório ao Picard em até 5 linhas: lições gravadas com ID e as 3 sugestões principais.

Evals: `evals/routing/pos-guinan-retro/`, `evals/routing/pos-guinan-lessons/`, `evals/routing/neg-guinan-review-pr/`. Testes de conteúdo em `tests/test_guinan_skill.py` (fonte e os 4 CLIs). Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R21, R24). Checks: C21, C22.
Fontes: `docs/reference/tlc-spec-driven.zip` (`references/lessons.md`) e `docs/reference/skills-main.zip` (`skills/engineering/retro/SKILL.md`). A Guinan já está declarada em `src/crew.yaml` (Haiku 5.5, voz "Sente-se. Conte."). `scripts/lessons.py` vem da T5.

#### BOUNDARIES
May change: `skills/guinan/`, `evals/routing/pos-guinan-retro/`, `evals/routing/pos-guinan-lessons/`, `evals/routing/neg-guinan-review-pr/`, `tests/test_guinan_skill.py`, `dist/`
Do not touch: `scripts/`, `src/`, `skills/engajar/`, `skills/worf/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T7: Lições confirmadas nos briefs (dispatch.py)
**Linear**: SC-108
**Depends on**: T6
**Requirements**: R25
**Tests**: unit
**Gate**: full

#### TASK
Em `scripts/dispatch.py`, `worker_brief` (subcomando `brief`) e `q_brief` (subcomando `q-brief`) passam a acrescentar no fim uma seção `## Lessons` quando `<repo>/.specs/lessons.json` tem lições `confirmed`. A seção traz até as 10 mais recentes (por `updated`), uma por linha: `- L<n>: <texto>`. Leia o JSON com o módulo `lessons` (T5) ou diretamente, sem duplicar a regra de status.
- Sem arquivo, sem lição `confirmed` ou com JSON inválido: o brief sai idêntico ao de hoje, sem a seção. JSON inválido não quebra o despacho: imprime um aviso de uma linha no stderr.

Testes em `tests/test_dispatch_lessons.py` (repo temporário com `TempRepoCase`). Os testes existentes de `tests/test_dispatch.py` continuam verdes sem mudança. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R25). Checks: C23, C24.
`scripts/dispatch.py` tem `worker_brief(slug, ticket, root)` e `q_brief(slug, root, base, head)`. O brief do Q vem de `src/briefs/q-verify.md`.

#### BOUNDARIES
May change: `scripts/dispatch.py`, `tests/test_dispatch_lessons.py`, `dist/`
Do not touch: `scripts/lessons.py`, `src/briefs/`, `tests/test_dispatch.py`, `skills/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T8: Diagnóstico: harness-score e Track A (diagnostico.py)
**Linear**: SC-109
**Depends on**: T7
**Requirements**: R26, R27, R28, R35
**Tests**: unit
**Gate**: full

#### TASK
- Copiar para `scripts/harness/` os scripts do harness-eval 1.8.3 (CC-BY-4.0, Tech Leads Club). Cada arquivo leva um comentário de origem no topo. Ficam assim:
  - `inventory_extract.py`, `track_a_correctness.py`, `doc_scope.py`, `surfaces_extract.py`, `merge_agreement.py`, `merge_usefulness.py`, `slim_fanin.py`;
  - os auxiliares que eles importam;
  - `references/PROTOCOL.md`, `GLOSSARY.md`, `claims.schema.json` em `scripts/harness/references/`.

  Ajuste só o necessário: imports locais e UTF-8 explícito no Windows.
- Criar `scripts/diagnostico.py` (só stdlib), com o subcomando `run [--root <repo>] [--date YYYY-MM-DD]`:
  - executa `npx --yes harness-score@1.8.4 --json <repo>` (versão fixada numa constante `HARNESS_SCORE_VERSION = "1.8.4"`, lida do registro npm em 2026-11-09), com timeout de 120 s;
  - roda `inventory_extract.py` e `track_a_correctness.py` com `--root <repo> --run-id <data>-diag` (saída em `<repo>/.harness-eval/runs/<data>-diag/`);
  - escreve `<repo>/docs/diagnostico/<data>.md` (R27): `**Level**: L<n> · <nome>`, `**Score**: <pontos>/<total>`, a tabela `| Dimensão | % |`, a linha `Próximo degrau: <texto To reach ...>`, o resumo do Track A (total de quebrados e os 5 primeiros grupos) e `**Tracks B/C**: não executados (sem aprovação de custo)` por padrão. A mesma data sobrescreve o arquivo.
  - `npx` ausente, exit ≠ 0, JSON inválido ou timeout: grava `**Level**: não executado - <motivo>`, roda o Track A mesmo assim e sai com 0 (R28). Track A falhou: sai com 2 e `track A falhou: <motivo>`.
  - Quando `<repo>/.gitignore` não tem `.harness-eval/`, imprime `aviso: .harness-eval/ não está no .gitignore de <repo>` (R35).
- O nome do campo de nível e de dimensões no JSON vem do `harness-score` real. Confira com `npx --yes harness-score@1.8.4 --json .` uma vez e salve uma amostra como fixture.

Testes em `tests/test_diagnostico.py` com um `npx` falso (PATH temporário, `npx.cmd` no Windows) que devolve a fixture JSON, falha ou demora. Repo temporário com um `AGENTS.md` mínimo para o Track A. Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R26–R28, R35; códigos de saída em Data & Contracts). Checks: C25, C26, C27, C28.
Fontes: `docs/reference/harness-eval.zip` (`scripts/`, `references/`, `SKILL.md` passos 2 e 3) e `docs/reference/harness-score-main.zip` (`packages/cli/README.md`: `--json`, `--md`, `--min-level`; níveis L0 Unharnessed, L1 Documented, L2 Guided, L3 Sensing, L4 Self-correcting). `harness-score` 1.8.4 no npm (MIT, sem rede em tempo de execução).

#### BOUNDARIES
May change: `scripts/harness/`, `scripts/diagnostico.py`, `tests/test_diagnostico.py`, `tests/fixtures/diagnostico/`, `dist/`, `.gitignore` (ampliado pelo Picard em 2026-11-09: C28 checa `.harness-eval/` no .gitignore; antes só na T11)
Do not touch: `scripts/review/`, `scripts/lessons.py`, `scripts/dispatch.py`, `skills/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T9: Skill diagnostico (Tracks B/C com aprovação de custo) e evals
**Linear**: SC-110
**Depends on**: T8
**Requirements**: R29, R30, R32
**Tests**: unit
**Gate**: full

#### TASK
- `src/crew.yaml`: declarar a skill `diagnostico` em `skills:` com `owner: laforge`, `invocation: user`, `release: "1.3"`.
- Criar `skills/diagnostico/SKILL.md` (EN, saída PT-BR, `name: diagnostico`, gatilhos como "diagnóstico do harness", "nível L0–L4", "harness score"). Conteúdo:
  - roda `python "<plugin-root>/scripts/diagnostico.py" run`;
  - mostra nível, pontuação e próximo degrau em até 5 linhas;
  - pergunta sobre B/C só depois de mostrar a estimativa (número de afirmações em `claims.jsonl` e 2 juízes por track) (R29);
  - a aprovação vale só para esta execução e nunca vai para config;
  - sem aprovação, o relatório mantém `não executados (sem aprovação de custo)`.
- `skills/diagnostico/references/judge-prompts.md`: protocolo B/C adaptado do harness-eval (`references/judge-prompts.md`, CC-BY-4.0). Dois juízes independentes; o segundo é cego (sem as notas do primeiro e sem as chaves das armadilhas). Cada juiz grava `model: <id>`. O portão das armadilhas segue o harness-eval, com merge por `scripts/harness/merge_agreement.py` / `merge_usefulness.py` / `slim_fanin.py`. Ship/Slim são só relatório, nunca aplicados (R30).

Evals: `evals/routing/pos-diagnostico-harness/`, `evals/routing/pos-diagnostico-level/`, `evals/routing/neg-diagnostico-setup/`. Testes em `tests/test_diagnostico_skill.py` (fonte e os 4 CLIs; crew.yaml com a skill e o dono). Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R29, R30, R32). Checks: C29, C30, C31.
Fonte: `docs/reference/harness-eval.zip` (`SKILL.md` passos 4–10, questionário Q2; `references/judge-prompts.md`). `tools/build.py` recusa skill não declarada no crew.yaml (`crew.*.skill` ou `skills.*`). Modelo de declaração: a skill `setup` em `src/crew.yaml`.

#### BOUNDARIES
May change: `src/crew.yaml`, `skills/diagnostico/`, `evals/routing/pos-diagnostico-harness/`, `evals/routing/pos-diagnostico-level/`, `evals/routing/neg-diagnostico-setup/`, `tests/test_diagnostico_skill.py`, `dist/`
Do not touch: `scripts/`, `skills/engajar/`, `skills/worf/`, `skills/guinan/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T10: Worf e Guinan no fluxo do Picard
**Linear**: SC-111
**Depends on**: T9
**Requirements**: R17, R18, R20, R32
**Tests**: unit
**Gate**: full

#### TASK
- `src/crew.yaml`: `worf` e `guinan` com `invocation: both`.
- `skills/engajar/references/execute.md`, seção 5:
  - depois de `run_gates.py done` verde e antes do PR, o Picard invoca a Guinan (R20);
  - nova seção `## Review (Worf)`: depois de abrir o PR (modos 3/4) e antes de pedir a autorização de merge, o Picard invoca o Worf (no Claude, subagente com o modelo do crew.yaml; nos outros CLIs, a própria sessão) (R17);
  - com `REQUEST_CHANGES`, ou `COMMENT` com `should-fix` aberto, vai **um** despacho do LaForge com todos os achados abertos num brief só, e depois a rodada seguinte do Worf. Após a rodada 3 com achados abertos, o Picard para e mostra os achados e a evidência, sem pedir merge (R18);
  - a publicação do review sempre com confirmação.
- `skills/engajar/SKILL.md`: na rota GRANDE/COMPLEXA, a linha de fluxo termina com `→ Guinan → PR → Worf → autorização de merge`.
- `src/context/STARCODE.md`: uma linha em "State, handoff and stops" sobre o review (Worf), a retro (Guinan) e `.specs/LESSONS.md`.

Testes em `tests/test_flow_worf_guinan.py` (fonte e os 4 CLIs). Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R17, R18, R20, R32). Checks: C32, C33, C34.
`skills/engajar/references/execute.md` seção 5 ("Post-Q cycle (4.6) and the end") e a seção "Text for the PR and the Linear comments (Uhura)" mostram onde entram o PR e o `done`. O teste `tests/test_uhura_skill.py` checa trechos do execute.md: não quebre o cabeçalho `## Text for the PR and the Linear comments (Uhura)`.

#### BOUNDARIES
May change: `src/crew.yaml`, `skills/engajar/references/execute.md`, `skills/engajar/SKILL.md`, `src/context/STARCODE.md`, `tests/test_flow_worf_guinan.py`, `dist/`
Do not touch: `skills/worf/`, `skills/guinan/`, `skills/diagnostico/`, `scripts/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T11: Build nos 4 CLIs, créditos e registros da fase
**Linear**: SC-112
**Depends on**: T10
**Requirements**: R31, R33, R34, R35
**Tests**: unit
**Gate**: build

#### TASK
- `tests/test_build.py`: `worf`, `guinan`, `diagnostico`, `scripts/review/`, `scripts/harness/`, `scripts/lessons.py` e `scripts/diagnostico.py` presentes nos 4 `dist/<cli>/`. Ajuste `tools/build.py` só se algo não for gerado. `build.py --check` verde.
- `evals/README.md`: contagem e lista dos 9 casos novos (R33). `tests/test_evals_f9.py` confere ao menos 2 positivos e 1 negativo por skill nova.
- `CREDITS.md`: as linhas de R34 (the-judge 1.4.0, harness-eval 1.8.3, tlc `lessons.py`, mattpocock `retro`, Cloudflare security-audit-skill, harness-score via `npx`), com licença e arquivos. Atualize as linhas "v1.3" existentes em vez de duplicar. `tests/test_credits_f9.py` confere cada fonte e que cada arquivo adaptado em `scripts/review/`, `scripts/harness/` e `scripts/lessons.py` tem o comentário de origem.
- `.gitignore`: `.harness-eval/` (R35).
- `DECISIONS.md`: F9-n:
  - review com publicação confirmada;
  - rodada no `review.md`;
  - portão de evidência de segurança;
  - lições por repo nos briefs e sinal `review_finding`;
  - Guinan antes do PR e Worf depois do PR;
  - harness-score fixado via `npx` e Track A junto;
  - B/C com aprovação por execução;
  - scripts em `scripts/review/` e `scripts/harness/`.
- `CHANGELOG.md`: `## [1.3.0] - não lançada`. `docs/compatibilidade.md`: linha das 3 skills por CLI. `tests/test_release_docs_f9.py`: as F9-n e a seção do CHANGELOG existem.

Regenere o `dist/`.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R31, R33–R35). Checks: C35, C36, C37, C38.
`scripts/check_decisions.py` é o gate da CI para o `DECISIONS.md` (D30). Modelo: a T12 da fase 8 (`.specs/features/fase-8-uhura-scotty-kirk/tasks.md`) e `tests/test_release_docs_f8.py`.

#### BOUNDARIES
May change: `tools/build.py`, `tests/test_build.py`, `evals/README.md`, `tests/test_evals_f9.py`, `CREDITS.md`, `tests/test_credits_f9.py`, `.gitignore`, `DECISIONS.md`, `CHANGELOG.md`, `docs/compatibilidade.md`, `tests/test_release_docs_f9.py`, `dist/`
Do not touch: `scripts/`, `skills/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T12: Aceite real (PR de teste com bypass, lição e relatório L0–L4)
**Linear**: SC-113
**Depends on**: T11
**Requirements**: R36
**Tests**: unit
**Gate**: build

#### TASK
Com os scripts de `dist/claude` deste ramo de integração:
1. Criar o ramo local `teste/worf-bypass` a partir do ramo de integração. Nele vai um commit com um arquivo de exemplo `tests/fixtures/review/planted/planted_bypass.py`, que tem um bypass plantado (`verify=False` numa chamada HTTP e um `@unittest.skip` sem justificativa). Rodar `git diff <integração>...teste/worf-bypass | python dist/claude/scripts/review/scan_bypasses.py` e registrar as linhas. **Não faça push nem PR**: o Picard abre o PR rascunho com a confirmação do usuário e roda o Worf. Deixe no relatório o nome do ramo e o hash.
2. Rodar `python dist/claude/scripts/diagnostico.py run --root <repo>`. O resultado é `docs/diagnostico/2026-11-<dd>.md` do próprio StarCode, com o nível L0–L4.
3. Escrever `docs/aceite/fase-9.md` com as seções:
   - `Varredura do bypass`: preencha com as linhas reais;
   - `Review do PR de teste` e `Publicação e fallback COMMENT`: deixe `**Resultado**: pendente (Picard)`;
   - `Lição registrada`: `**Resultado**: pendente (Guinan)`;
   - `Relatório L0–L4`: o nível, a pontuação e o caminho do relatório.

   Cada seção concluída leva `**Resultado**: aprovado` ou `reprovado`.

Testes: `tests/test_acceptance_doc_f9.py` com `test_fase9_acceptance_sections`, que confere as 5 seções e, nas concluídas, `**Resultado**`. Depois que o Picard preencher as pendentes, o teste também exige `aprovado` em todas. Use a variável `STARCODE_F9_FINAL=1` para o modo final; sem ela, `pendente` é aceito.

#### CONTEXT
Spec: `.specs/features/fase-9-worf-guinan-diagnostico/spec.md` (R36). Checks: C39.
Aceites anteriores: `docs/aceite/fase-8.md` (formato) e `tests/test_acceptance_doc_f8.py`. O PR de teste é aberto pelo Picard (push e PR exigem a confirmação do usuário) e fechado sem merge no fim. O ramo `teste/worf-bypass` não entra no ramo de integração.

#### BOUNDARIES
May change: `docs/aceite/fase-9.md`, `docs/diagnostico/`, `tests/test_acceptance_doc_f9.py`, `tests/fixtures/review/planted/`
Do not touch: `scripts/`, `skills/`, `src/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - O scan imprime `<arquivo>:<linha>\t<categoria>\t<conteúdo>` com a linha do arquivo novo para cada uma das 8 categorias (R1)
Proof: run unit | test_scan_reports_each_category_with_new_line_number ... ok

**C2** - O scan ignora linhas removidas e de contexto, imprime `scan: N candidate(s)` no stderr e sai com 0 mesmo com diff vazio ou inválido (R2)
Proof: run unit | test_scan_ignores_removed_context_and_always_exits_zero ... ok

**C3** - O gate recusa severidade desconhecida, 6 nits e blocker sem evidência no formato aceito (R4)
Proof: run unit | test_gate_rejects_severity_nits_and_missing_evidence ... ok

**C4** - O gate exige `TL;DR:` com o token do veredito no summary (R4)
Proof: run unit | test_gate_requires_tldr_with_verdict ... ok

**C5** - `compute_verdict`: blocker → REQUEST_CHANGES; nenhum blocker/should-fix → APPROVE; senão COMMENT; rejected, hardening e pre-existing não contam (R5)
Proof: run unit | test_compute_verdict_mapping ... ok

**C6** - O gate recusa termos de bajulação em PT-BR e EN, sem acento e sem caixa (R6)
Proof: run unit | test_gate_rejects_banned_terms_accent_insensitive ... ok

**C7** - Nas rodadas 2 e 3, achado novo não blocker é recusado; rodada 4 sai com 1 e `limite de 3 rodadas` (R7)
Proof: run unit | test_gate_round_convergence_rules ... ok

**C8** - Achado de segurança sem um dos 7 campos sai com 1 e `security: campo <nome> ausente`; state fora da lista é recusado (R8)
Proof: run unit | test_gate_security_fields_required ... ok

**C9** - `needs-validation` exige `missing_fact` e no máximo should-fix; `rejected` exige `reason` e não conta; `hardening` fica fora do veredito (R9, R10)
Proof: run unit | test_gate_security_states_and_hardening ... ok

**C10** - `post_review.py` sai com 3 sem chamar o `gh` quando o gate falha ou a rodada já tem `**Posted**:` (R14)
Proof: run unit | test_post_refuses_without_gate_or_when_already_posted ... ok

**C11** - No próprio PR publica como COMMENT com a linha `Veredito pretendido: <veredito> ...` (R15)
Proof: run unit | test_post_own_pr_falls_back_to_comment ... ok

**C12** - Falha do `gh` sai com 2 sem tocar no review.md; sucesso grava `**Posted**: <data> - <url>` (R16)
Proof: run unit | test_post_gh_failure_and_success_marks_posted ... ok

**C13** - A skill worf existe na fonte e nos 4 CLIs com a ordem dos 6 passos de R11 e os comandos de scan e gate (R11)
Proof: run unit | test_worf_skill_review_flow_order ... ok

**C14** - A skill worf exige evidência e rebaixa achado sem URL/ID ou sem `arquivo:linha` lido (R12)
Proof: run unit | test_worf_skill_evidence_or_silence ... ok

**C15** - A skill worf define o review.md com Round, Verdict, Reviewer, TL;DR e a tabela de achados `W<n>` (R13)
Proof: run unit | test_worf_skill_review_md_contract ... ok

**C16** - A referência de padrões trata bypass com justificativa e link como aceito e sem isso como should-fix/blocker (R3)
Proof: run unit | test_worf_review_standards_bypass_rule ... ok

**C17** - A skill worf proíbe aprovar merge, fazer merge e editar fora do review.md/review.json (R19)
Proof: run unit | test_worf_skill_never_merges ... ok

**C18** - `lessons.py add` com sinal inválido, source vazio ou texto acima de 300 caracteres sai com 2 sem gravar (R22)
Proof: run unit | test_lessons_add_rejects_invalid_input ... ok

**C19** - Texto igual sem acento/caixa/pontuação soma recorrência sem duplicar e vira confirmed em 2 features distintas (R23)
Proof: run unit | test_lessons_dedupe_and_promote_on_two_features ... ok

**C20** - `penalize` move confirmed para quarantined; LESSONS.md é renderizado a cada escrita; JSON inválido sai com 2 sem sobrescrever (R23)
Proof: run unit | test_lessons_penalize_render_and_corrupt_store ... ok

**C21** - A skill guinan mapeia achados de verification.md, proofs.md e review.md para os 6 sinais e não grava lição sem achado (R21)
Proof: run unit | test_guinan_skill_signals_and_no_finding_no_lesson ... ok

**C22** - A skill guinan escreve retro.md com até 7 sugestões nas 7 categorias, com evidência, nunca aplicadas (R24)
Proof: run unit | test_guinan_skill_retro_contract ... ok

**C23** - Com lições confirmed, os briefs do LaForge e do Q ganham `## Lessons` com até 10, as mais recentes primeiro (R25)
Proof: run unit | test_briefs_include_up_to_ten_confirmed_lessons ... ok

**C24** - Sem lessons.json, sem confirmed ou com JSON inválido, o brief fica idêntico ao de hoje (R25)
Proof: run unit | test_briefs_unchanged_without_confirmed_lessons ... ok

**C25** - `diagnostico.py run` chama `npx --yes harness-score@1.8.4 --json` e roda o Track A em `.harness-eval/runs/<data>-diag/` (R26)
Proof: run unit | test_diagnostico_runs_harness_score_and_track_a ... ok

**C26** - O relatório tem Level, Score, tabela de dimensões, Próximo degrau, resumo do Track A e Tracks B/C; mesma data sobrescreve (R27)
Proof: run unit | test_diagnostico_report_contract ... ok

**C27** - `npx` ausente, falho ou com timeout grava `**Level**: não executado - <motivo>` e sai com 0; Track A falho sai com 2 (R28)
Proof: run unit | test_diagnostico_failures ... ok

**C28** - Sem `.harness-eval/` no .gitignore do alvo o diagnóstico avisa em uma linha; o .gitignore do repo tem `.harness-eval/` (R35)
Proof: run unit | test_diagnostico_gitignore_warning ... ok

**C29** - A skill diagnostico só roda B/C depois de mostrar a estimativa e receber aprovação nesta execução, nunca gravada (R29)
Proof: run unit | test_diagnostico_skill_cost_approval ... ok

**C30** - O protocolo B/C exige 2 juízes, o segundo cego, `model: <id>` de cada um, e nunca aplica Ship/Slim (R30)
Proof: run unit | test_diagnostico_judge_protocol ... ok

**C31** - crew.yaml declara `diagnostico` com dono laforge e invocation user (R32)
Proof: run unit | test_crew_declares_diagnostico_skill ... ok

**C32** - crew.yaml tem worf e guinan com `invocation: both` (R32)
Proof: run unit | test_crew_worf_guinan_invocation_both ... ok

**C33** - execute.md chama o Worf depois do PR e antes da autorização de merge, com um despacho do LaForge por rodada e parada após a rodada 3 (R17, R18)
Proof: run unit | test_execute_review_worf_after_pr ... ok

**C34** - execute.md chama a Guinan depois do `done` verde e antes do PR (R20)
Proof: run unit | test_execute_guinan_after_done ... ok

**C35** - As 3 skills e os scripts novos estão nos 4 `dist/<cli>/` (R31)
Proof: run unit | test_build_fase9_skills_and_scripts_in_all_clis ... ok

**C36** - Os evals têm ao menos 2 positivos e 1 negativo para worf, guinan e diagnostico (R33)
Proof: run unit | test_evals_f9_routing_cases ... ok

**C37** - CREDITS.md tem as 6 fontes com licença e cada arquivo adaptado tem comentário de origem (R34)
Proof: run unit | test_credits_f9_sources_and_headers ... ok

**C38** - DECISIONS.md tem as F9-n e o CHANGELOG tem `## [1.3.0] - não lançada` (R31)
Proof: run unit | test_release_docs_f9 ... ok

**C39** - docs/aceite/fase-9.md tem as 5 seções do aceite com `**Resultado**` (R36)
Proof: run unit | test_fase9_acceptance_sections ... ok

## Handoff

**Phase:** done
**Size:** GRANDE
**Git mode:** 3
**Next:** release 1.3.0 (quando o usuário pedir)
**Linear:** SC-16, SC-102..SC-113; PR #21 https://github.com/freire-andre/starcode/pull/21; PR rascunho #22 https://github.com/freire-andre/starcode/pull/22
**Integration branch:** feature/fase-9-worf-guinan-diagnostico
**Last integrated:** worf-r1 (f97ce19, fe552a2) via bc42aa8
**Dispatched:** worf-r1 · SC-109, SC-104 · base b2fa8f5 · dispatch ctx_ef2c24da3412 · model claude-sonnet-5-5
**Settled:** 2026-11-09: 2026-11-09: spec aprovada: user "sim"; 2026-11-09: 2026-11-09: tasks aprovadas e publicadas: user "sim"; 2026-11-09: 2026-11-09: push e PRs (feature + rascunho de teste): user "Sim, os dois (Recommended)"; 2026-11-09: push e rodada 2: Push e publicar (Recommended); 2026-11-09: merge do PR #21: Sim, autorizo o merge; 2026-11-09: publicar review do PR #22: Sim, publicar (Recommended); 2026-11-09: publicar review do PR #21 (rodada 1): Sim, publicar (Recommended); 2026-11-09: encerrar: Done + commit e push (Recommended)
**Attempts:** none
**Reports:** 2026-11-09: 2026-11-09: T1: scan_bypasses.py + testes + dist; 528 testes; commit b72a50e; integrado em 761cf11; 2026-11-09: 2026-11-09: T2: review_gate.py + testes + dist; worker commitou direto no ramo de integração (worktree errado), sem merge; check_commit, gate do ticket, build --check e suíte 536 OK em 9f6d2e5; aceito; 2026-11-09: 2026-11-09: T3: post_review.py + testes com gh falso + dist; suíte 539 OK; commit cda0b2d; integrado em 7cb21e7; 2026-11-09: 2026-11-09: T4: skill worf + 3 referências + 3 evals + test_worf_skill; test_build ajustado (May change ampliado); suíte 544 OK; commit 713ea76; integrado em 2fe2850; 2026-11-09: 2026-11-09: T5: lessons.py + test_lessons + dist; suíte 548 OK; commit 0e597d4; integrado em c0c9ae2; 2026-11-09: 2026-11-09: T6: skill guinan + lessons.md + retro.md + 3 evals + test_guinan_skill; suíte 551 OK; commit 655fdda; integrado em b954128; 2026-11-09: 2026-11-09: T7: lessons_section em dispatch.py + test_dispatch_lessons; suíte 553 OK; commit 5560f7e; integrado em 85eb60c; 2026-11-09: 2026-11-09: T8: diagnostico.py + scripts/harness + fixtures + .gitignore (May change ampliado); suíte 557 OK; commit 95dec9d; integrado em bc0d909; 2026-11-09: 2026-11-09: T9: skill diagnostico + judge-prompts + 3 evals + crew.yaml (também worf/guinan invocation both, adiantando C32 da T10); suíte 561 OK; commit 4abefc5; integrado em 8c78b8a; 2026-11-09: 2026-11-09: T10: Review (Worf) e Guinan no execute.md, fluxo no engajar, STARCODE.md, test_flow_worf_guinan; suíte 565 OK; commit 6b97f6b; integrado em 311a81b; 2026-11-09: 2026-11-09: T11: testes de build/evals/créditos/registros; CREDITS, evals/README, DECISIONS F9-1..8, CHANGELOG 1.3.0, compatibilidade; gate build verde; suíte 571 OK; commit f528f1a; integrado em 022a690; 2026-11-09: 2026-11-09: T12: aceite: ramo teste/worf-bypass 456b371 (scan: 2 candidatos), diagnóstico L0 44/105, docs/aceite/fase-9.md; suíte 572 OK; commit 8b47cdb; integrado em 153071a; 2026-11-09: 2026-11-09: proofs verdes em 153071a (39 checks); 2026-11-09: 2026-11-09: Q (codex · GPT-6-Luna medium) FAIL: 38/39 checks sustentam; achados: R8 aceita campo de segurança não textual vazio (attacker: []) em review_gate.py:72; asserts fracos em C11 e C39; 2026-11-09: 2026-11-09: pós-Q: 9e7679a (R8) e 6e26b43 (C11/C39); sonda do Picard: attacker [] {} 0 espaço recusados; proofs vermelho só em check_decisions (falta F9-9); 2026-11-09: 2026-11-09: F9-9 em 8ad073e; proofs verdes; achados do Q fechados (9e7679a, 6e26b43); 2026-11-09: 2026-11-09: gate done verde; achados do Q fechados; 2026-11-09: 2026-11-09: Guinan: lições L1, L2 (weak_test) e L3 (gate_fail) como candidate; retro.md com 7 sugestões (worktree errado, zips de referência, require_text, AGENTS.md L0, May change, ramo renomeado, --help); 2026-11-09: W1 e W2 corrigidos; 573 testes; test_diagnostico verde no Linux (WSL); 2026-11-09: CI do PR #21 verde (ubuntu e windows); 2026-11-09: PR #21 mergeado na main (9887e7f); PR #22 fechado sem merge
**Breaker:** closed
