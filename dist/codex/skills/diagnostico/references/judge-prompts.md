# Protocolo dos juízes B/C

Adaptado do harness-eval, `references/judge-prompts.md` e `SKILL.md` passos 4–10 (licença CC-BY-4.0,
créditos em `CREDITS.md`). Carregue este arquivo só depois da aprovação de custo desta execução.

Substitua: `REPO` = raiz do repositório; `RUN_DIR` = `$REPO/.harness-eval/runs/<run-id>`;
`MODEL_ID` = id do modelo (não rápido, sem `*-fast`) usado por aquele juiz.

## Regras do protocolo
1. **Dois juízes independentes por track.** Cada um roda num subagente próprio.
2. **O segundo juiz é cego**: não lê as notas do primeiro, nem `trap-key.json`, nem
   `usefulness-trap-key.json`, nem `claims.jsonl`, nem `surfaces.json`, nem os relatórios de acordo.
3. **Cada juiz grava `model: <id>`** no cabeçalho do arquivo. Prefira o mesmo modelo nos dois juízes do
   track C (a utilidade depende do modelo).
4. **Armadilhas (plants).** O portão das armadilhas segue o harness-eval: se falhar (trap FAIL), nada é
   Ship nem Slim; corrija as armadilhas e rejulgue antes de fundir.
5. **Ship e Slim são só relatório (R30).** Nunca aplique. Slim com `slim-fanin-blocked` vira Hold.
6. README fica fora do escopo como superfície e como evidência. Na dúvida: KEEP/UNCLEAR.

## Track B: redundância
Passos: Juiz 1 grava `05-redundancy-j1.md`; Juiz 2 (cego) grava `06-blind-scores.md`; depois:

```
python "<plugin-root>/scripts/harness/merge_agreement.py" --run-dir <RUN_DIR>
```

Saída: `07-agreement.md` (Ship/Review/Hold). Ship só com trap PASS, os dois juízes REDUNDANT e custo do
Juiz 2 ≤ 1.

Cabeçalho da tabela (exigido pelo merge): `| ID | Cost | Class | Evidence | Confidence | Trim suggestion |`.
Classes: `REDUNDANT-CODE`, `REDUNDANT-GENERAL`, `KEEP-POLICY`, `KEEP-CAVEAT`, `KEEP-ROUTING`,
`KEEP-COMPRESSED`, `UNCLEAR`. Custo ≥ 2 nunca é REDUNDANT-*.

### Juiz 1 (B)
```
You are Judge1 for a stack-agnostic harness redundancy audit.
Score EVERY claim row in: <RUN_DIR>/claims.md. Follow the rubric in that file exactly.
Rules: verify rediscovery against the live repo; README is OUT OF SCOPE; cost >= 2 never REDUNDANT-*;
default KEEP/UNCLEAR when unsure; score ALL IDs including P00x (you do not know which are plants).
You MAY read <RUN_DIR>/inventory.json. Do NOT read trap-key.json or claims.jsonl.
Write ONLY to <RUN_DIR>/05-redundancy-j1.md, starting with:
# Redundancy Judge1
> run: <run-id>
> model: <MODEL_ID>
Then a short counts summary and the full table covering every ID.
```

### Juiz 2 (B, cego)
```
You are Judge2 (BLIND second scorer) for a stack-agnostic harness redundancy audit.
Score EVERY claim row in: <RUN_DIR>/claims.md. Follow the rubric in that file exactly.
Do NOT read: trap-key.json, claims.jsonl, 05-redundancy-j1.md, 07-agreement.md, or any prior
agreement/redundancy report.
Rules: verify against the live repo; README out of scope; cost >= 2 never REDUNDANT-*; default
KEEP/UNCLEAR; score ALL IDs including P00x.
Write ONLY to <RUN_DIR>/06-blind-scores.md, starting with:
# Blind scores Judge2
> run: <run-id>
> model: <MODEL_ID>
Then a counts summary and the full table.
```

## Track C: utilidade
Antes: `python "<plugin-root>/scripts/harness/surfaces_extract.py" --root <REPO> --run-id <run-id>`.
Juiz 1 grava `08-usefulness-j1.md`; Juiz 2 (cego) grava `09-usefulness-j2.md`; depois:

```
python "<plugin-root>/scripts/harness/merge_usefulness.py" --run-dir <RUN_DIR>
python "<plugin-root>/scripts/harness/slim_fanin.py" --root <REPO> --path <caminho>
```

Saída: `10-usefulness-agreement.md` (Slim/Keep-core/Mixed/Hold), `11-mixed-apply.md`, `slim-fanin.json`.
Slim só com trap PASS, os dois juízes SLIM/ROUTING-ONLY e fan-in PASS. Nunca esvazie um caminho que
outra superfície do harness carrega como fonte de verdade.

Cabeçalho da tabela: `| ID | Overall | Keep-core | Slim | Overlap cites | Evidence | Confidence |`.
Overall: `KEEP-CORE`, `MIXED`, `SLIM`, `ROUTING-ONLY`, `UNCLEAR`. Em MIXED, as células Keep-core e Slim
nomeiam o que manter e o que cortar.

### Juiz 1 (C)
```
You are Usefulness Judge1 for a stack-agnostic harness audit (Track C).
Score EVERY surface in: <RUN_DIR>/surfaces.md. Read the rubric at its top; open the real file when the
preview is truncated.
Question: if this surface were deleted, and an agent could still list the repo and open 1-2 canonical
examples (and any other surface that mandates loading this path still runs), would behavior change?
Rules: evidence-or-zero (cite harness paths and example code paths); README out of scope; OVERLAP must
cite another harness surface; if another skill/doc hard-loads this path, prefer KEEP-CORE or MIXED over
SLIM; default UNCLEAR when unsure; score ALL IDs including S9xx.
Do NOT read usefulness-trap-key.json, surfaces.json, 09-usefulness-j2.md or 10-usefulness-agreement.md.
Write ONLY to <RUN_DIR>/08-usefulness-j1.md, starting with:
# Usefulness Judge1
> run: <run-id>
> model: <MODEL_ID>
Then a counts summary by Overall class and the full table.
```

### Juiz 2 (C, cego)
```
You are Usefulness Judge2 (BLIND) for a stack-agnostic harness audit (Track C).
Score EVERY surface in: <RUN_DIR>/surfaces.md, with the same counterfactual and evidence rules as Judge1.
Do NOT read: usefulness-trap-key.json, surfaces.json, 08-usefulness-j1.md,
10-usefulness-agreement.md, or the Track B files (05/06/07).
README out of scope; default UNCLEAR when unsure; score ALL IDs including S9xx.
Write ONLY to <RUN_DIR>/09-usefulness-j2.md, starting with:
# Usefulness Judge2 (blind)
> run: <run-id>
> model: <MODEL_ID>
Then a counts summary and the full table.
```
