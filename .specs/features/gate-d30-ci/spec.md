# Gate D30 no CI e decisões da 1.8.0: Spec

**Approved**: 2026-11-13 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-168
**May change**: .github/workflows/ci.yml, scripts/check_decisions.py, DECISIONS.md, tests/test_check_decisions.py, tests/test_ci_workflow.py, dist/

## Context
O gate D30 (`scripts/check_decisions.py`) nunca falha no CI: o `actions/checkout@v4` sem `fetch-depth` faz clone de profundidade 1, e aí o último commit em `skills/`/`scripts/`/`hooks/` e o último no `DECISIONS.md` são o mesmo, então o script responde "OK (atualizado no mesmo commit)". Assim a 1.8.0 saiu sem nenhuma entrada no `DECISIONS.md`, com o CI verde. Fonte: itens 0.1 e 0.2 de `starcode-triagem-v2-2026-11-13.md` (fora do Git). Sucesso: o CI avalia o gate sobre o histórico completo, o script recusa clone raso e o `DECISIONS.md` registra as decisões da 1.8.0.

## Scope
- `fetch-depth: 0` no checkout do job `checks` (0.1).
- `check_decisions.py` detecta repositório raso e sai com 2 antes de comparar commits (0.1).
- Entradas `V18-1` a `V18-5` no `DECISIONS.md` com as decisões da 1.8.0, e uma entrada `SC-168` para a mudança do gate (0.2).
- `dist/` só por `python tools/build.py`, nunca à mão.

## Non-Goals
- Mudar a regra D30 (D-e): continua comparando commits de `skills/`, `scripts/`, `hooks/` e `DECISIONS.md`.
- Corrigir o piloto (itens 0.4 a 0.7, decisões D-g e D-h) e o Q sobre o diff da 1.8.0 (0.3).
- Registrar agora as decisões D-g a D-k: cada uma entra quando o item dela for implementado.
- Jobs `eval` e `release-check` do CI.

## Requirements
- **R1** - The system SHALL ter, no job `checks` de `.github/workflows/ci.yml`, o passo `actions/checkout@v4` com `with: fetch-depth: 0`.
- **R2** - IF `git rev-parse --is-shallow-repository` imprime `true` THEN `check_decisions.py` SHALL sair com código 2 e a mensagem `check_decisions: repositório raso; o gate D30 precisa do histórico completo (use fetch-depth: 0 no actions/checkout ou rode git fetch --unshallow)`, sem comparar commits.
- **R3** - IF a saída de `git rev-parse --is-shallow-repository` não é exatamente `true` nem `false` (comando falhou ou git antigo) THEN `check_decisions.py` SHALL sair com código 2 e a mensagem `check_decisions: não foi possível confirmar que o clone é completo (git rev-parse --is-shallow-repository)`.
- **R4** - WHEN o repositório não é raso THEN `check_decisions.py` SHALL manter os resultados de hoje (0, 1 ou 2, com as mesmas mensagens) para os casos já cobertos em `tests/test_check_decisions.py`.
- **R5** - The system SHALL ter no `DECISIONS.md` a entrada `### V18-1` (piloto automático) com **Problema**, **Decisão**, **Motivo** e **Por que não é bug**, dizendo que, depois da aprovação da spec, o Picard responde às paradas da lista D29 e aprova as tasks pelo mandato, que a spec continua com o usuário, e listando o que nunca é delegado conforme a seção 5 de `skills/piloto-automatico/SKILL.md`.
- **R6** - The system SHALL ter a entrada `### V18-2` (aprovação `piloto:`) dizendo que `**Approved**: <data> - piloto: "D<n> ..."` só é aceito no `tasks.md`, com piloto `ativo` e `**Mandato confirmado:**` do usuário, e que `spec.md` exige aprovação do usuário.
- **R7** - The system SHALL ter a entrada `### V18-3` (skill `config` e `model_info.py`) citando o catálogo do models.dev como fonte, o cache de 7 dias e as faixas de custo `$`, `$$` e `$$$` por papel.
- **R8** - The system SHALL ter a entrada `### V18-4` (config local) citando `.starcode/config.local.json` fora do Git e a precedência sessão > config local do repositório > config do usuário > padrão do `crew.yaml`.
- **R9** - The system SHALL ter a entrada `### V18-5` (skill `menu`) dizendo que ela só lê, não roda ferramentas, e que um teste garante que o menu cita todas as skills de `skills/`.
- **R10** - The system SHALL ter a entrada `### SC-168` (gate raso) descrevendo R1 a R3 e citando os testes que falham sem eles.
- **R11** - WHEN `check_decisions.py` roda num clone completo do ramo da feature THEN the system SHALL sair com 0.

## Edge Cases
- Clone raso com `DECISIONS.md` e código no mesmo commit: hoje dá "OK"; passa a dar 2 (R2).
- Git sem `--is-shallow-repository` (anterior à 2.15) ecoa o argumento: cai em R3, nunca em OK.
- O teste do clone raso usa `git clone --depth 1 file://<repo temporário>`, sem rede, e roda em Linux e Windows.
- O passo do CI que pula a validação da Orca fica como está (item C.9, fora deste escopo).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - O job `checks` tem `actions/checkout@v4` com `fetch-depth: 0` (R1)
Proof: run unit | test_ci_checkout_historico_completo ... ok

**C2** - Num clone `--depth 1` de um repositório com `DECISIONS.md` e `skills/` no mesmo commit, `check()` devolve 2 e a mensagem de R2 (R2)
Proof: run unit | test_clone_raso_sai_2 ... ok

**C3** - Com a saída de `--is-shallow-repository` igual a `--is-shallow-repository` (git antigo) ou com o comando falhando, `check()` devolve 2 e a mensagem de R3 (R3)
Proof: run unit | test_raso_indeterminado_sai_2 ... ok

**C4** - Os casos existentes continuam com os mesmos códigos num repositório completo (R4)
Proof: run unit | test_flow ... ok

**C5** - `DECISIONS.md` tem `V18-1` com D29, aprovação das tasks, spec com o usuário e "Por que não é bug" (R5)
Proof: run unit | test_decisions_v18_1_piloto ... ok

**C6** - `DECISIONS.md` tem `V18-2` com `tasks.md`, `Mandato confirmado` e `spec.md` (R6)
Proof: run unit | test_decisions_v18_2_aprovacao_piloto ... ok

**C7** - `DECISIONS.md` tem `V18-3` com `models.dev`, `7 dias` e `$$$` (R7)
Proof: run unit | test_decisions_v18_3_config_model_info ... ok

**C8** - `DECISIONS.md` tem `V18-4` com `config.local.json` e a ordem de precedência (R8)
Proof: run unit | test_decisions_v18_4_config_local ... ok

**C9** - `DECISIONS.md` tem `V18-5` sobre a skill `menu` (R9)
Proof: run unit | test_decisions_v18_5_menu ... ok

**C10** - `DECISIONS.md` tem a entrada do gate raso com `fetch-depth`, `is-shallow-repository` e "Por que não é bug" (R10)
Proof: run unit | test_decisions_gate_raso ... ok

**C11** - `check_decisions.py` sai com 0 no ramo da feature, em clone completo (R11)
Proof: `python scripts/check_decisions.py`

## Handoff

**Phase:** review
**Size:** MÉDIA
**Git mode:** 3
**Next:** PR com confirmação, depois Worf
**Linear:** SC-168
**Integration branch:** feature/gate-d30-ci
**Last integrated:** 8e1547f
**Dispatched:** LaForge pós-Q · fcb0394
**Settled:** none
**Attempts:** none
**Reports:** 2026-11-13: SC-168: fetch-depth 0, check_decisions sai 2 em clone raso/indeterminado, V18-1..V18-5 e SC-168 no DECISIONS.md, 8 testes, dist regerado; gate ticket verde; suíte completa não conferida pelo worker; 2026-11-13: Q (codex · effective gpt-6-luna): FAIL, 8 achados (R3 aceita ' false '; C4-C10 com asserções fracas); suíte 820 ok; 2026-11-13: LaForge pós-Q: achado 1 em 7c24202, achados 2-8 em 6369977; 26 testes ok; usou git checkout no próprio arquivo de teste (sem perda)
**Breaker:** closed
