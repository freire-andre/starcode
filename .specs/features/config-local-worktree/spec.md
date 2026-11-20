# Config local nos worktrees: Spec

**Approved**: 2026-11-20 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: none
**Status**: Approved
**Linear**: SC-206
**May change**: scripts/starcode_common.py, scripts/config/validate_config.py, scripts/setup_helpers.py, hooks/scripts/banner.py, skills/config/SKILL.md, tests/test_model_info.py, tests/test_config_local_worktree.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Itens C.3, C.5 e C.7 da triagem v2 (seção 10.1), missão 1 do passo 4. Discovery e reprodução em `.specs/features/config-local-worktree/context.md`. Num worktree ligado, `load_local_config` devolve `None` e a tripulação volta à config do usuário em silêncio. No principal, a mescla campo a campo produz `antigravity · zai/glm-5.3`.

## Scope
- Leitura da config local com queda para o worktree principal; entrada local inteira.
- Validação de `model` e leitura do `@`; aviso no banner sobre o arquivo local versionado.
- `suggest` partindo do que já está configurado.

## Non-Goals
- Mudar a semântica da config do usuário (entrada parcial continua herdando do padrão).
- Copiar a config local para os worktrees.

## Decisions
| Item | Options | Status |
|---|---|---|
| Entrada local parcial | exigir `cli` e `model` · herdar o CLI do padrão | approved - user: "Exigir CLI e modelo (Recomendado)" |
| `suggest` com config existente | manter o membro configurado · propor tudo e marcar diferenças | approved - user: "Manter o configurado (Recomendado)" |
| Arquivo local nos dois worktrees | o do worktree atual vence · o do principal vence | approved - user: "você decide" (o do worktree atual vence; default registrado no context.md) |

## Requirements
- **R1** - WHEN `.starcode/config.local.json` não existe no worktree atual AND existe no worktree principal (pasta-mãe de `git rev-parse --path-format=absolute --git-common-dir`) THEN `local_config_path` SHALL apontar para o arquivo do principal. WHEN existe no worktree atual THEN SHALL usar o do worktree atual. IF o `git` falhar ou a pasta não for um repositório THEN SHALL manter a leitura atual, sem erro. `crew_at`, `dispatch.py`, `setup_helpers.py` e o banner SHALL obter o mesmo resultado num worktree ligado e no principal.
- **R2** - The validador (`--kind local`) SHALL recusar uma entrada de `crew` sem `cli` e `model` juntos, com a mensagem `<caminho>: a entrada local precisa de cli e model juntos`. The `effective_crew` SHALL usar a entrada local inteira (CLI e modelo da local, nunca o CLI do usuário com o modelo local).
- **R3** - The validador SHALL recusar, em toda fonte de modelo das configs (o `crew` do usuário, o `crew` local e a parte do modelo de cada item de `fleet.workers` do usuário; a config do repositório não tem modelo), um `model` vazio, com espaço, começando com `-` ou com caractere fora de `[A-Za-z0-9._:/+@-]`, com a mensagem `<caminho>: modelo inválido <valor>`. The `parse_model_arg` (`setup_helpers.py`) SHALL separar o `@<nível>` só quando o sufixo é um nível de custo conhecido; nos demais casos o `@` fica no id do modelo.
- **R4** - IF o arquivo local está versionado (`git ls-files --error-unmatch`) ou não está ignorado (`git check-ignore`) THEN o banner SHALL mostrar a linha `⚠️ config local versionado ou fora do .gitignore: <caminho>`.
- **R5** - WHEN `suggest` recebe a config atual THEN cada membro já configurado (config do usuário ou local) com CLI entre os disponíveis SHALL ficar como está, e a saída SHALL listar os mantidos na linha `mantidos: <nomes>`. Só os membros sem config ou com CLI indisponível SHALL receber proposta. The CLI `suggest` SHALL ler a config atual sozinho.
- **R6** - The `skills/config/SKILL.md` SHALL dizer que a entrada local leva `cli` e `model` juntos e que ela vale também nos worktrees ligados. The `DECISIONS.md` SHALL ter a entrada `### SC-<n>:` com **Problema** (com a reprodução), **Decisão**, **Motivo** e **Por que não é bug** (com os testes), e o `CHANGELOG.md` uma linha em `[Unreleased]`.

## Edge Cases
- Worktree principal sem o arquivo: nenhuma config local, como hoje (R1).
- Config local inválida no principal, lida de um worktree ligado: o banner a mostra como inválida, como faria no principal (R1).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Num worktree ligado sem o arquivo, a config local vem do principal, e `crew_at` dá o mesmo resultado nos dois; com arquivo no worktree atual, vale o dele; fora de repositório, nada muda (R1)
Proof: run unit | test_local_no_worktree_ligado (test_config_local_worktree.ConfigLocalWorktreeTests.test_local_no_worktree_ligado) ... ok
Proof: run unit | test_consumidores_no_worktree_ligado (test_config_local_worktree.ConfigLocalWorktreeTests.test_consumidores_no_worktree_ligado) ... ok

**C2** - O validador recusa entrada local parcial com a mensagem exata, e `effective_crew` usa a entrada local inteira (R2)
Proof: run unit | test_entrada_local_inteira (test_config_local_worktree.ConfigLocalWorktreeTests.test_entrada_local_inteira) ... ok

**C3** - Tabela de modelos válidos e inválidos no `crew` do usuário, no `crew` local e em `fleet.workers`, com a mensagem exata; `parse_model_arg` com `@` de nível e `@` dentro do id (R3)
Proof: run unit | test_modelo_valido (test_config_local_worktree.ConfigLocalWorktreeTests.test_modelo_valido) ... ok

**C4** - O banner mostra a linha exata quando o arquivo local está versionado ou fora do `.gitignore`, e não mostra quando está ignorado (R4)
Proof: run unit | test_aviso_local_versionado (test_config_local_worktree.ConfigLocalWorktreeTests.test_aviso_local_versionado) ... ok

**C5** - `suggest` mantém os membros configurados com CLI disponível, lista os mantidos e só propõe os demais (R5)
Proof: run unit | test_suggest_mantem_configurado (test_config_local_worktree.ConfigLocalWorktreeTests.test_suggest_mantem_configurado) ... ok

**C6** - A skill `config` traz as duas frases e a entrada no `DECISIONS.md` tem os quatro campos, a reprodução, os termos da Decisão e os testes, mais a linha no CHANGELOG (R6)
Proof: run unit | test_skill_e_decisions (test_config_local_worktree.ConfigLocalWorktreeTests.test_skill_e_decisions) ... ok

## Handoff

**Phase:** review
**Size:** MEDIUM
**Git mode:** 3
**Next:** proofs e done --strict; Guinan; PR
**Linear:** SC-206
**Integration branch:** feature/config-local-worktree
**Last integrated:** 41e0458
**Dispatched:** none
**Settled:** 2026-11-20: sim
**Attempts:** none
**Reports:** 2026-11-20: provas verdes (6/6); 2026-11-20: Q r1 FAIL: 5 achados; R3 precisado (fontes de modelo: crew do usuário, crew local, fleet.workers; o repo não tem modelo); 2026-11-20: pós-Q: d4221d6..41e0458; achados fechados com close-finding; C1 ganhou a prova test_consumidores_no_worktree_ligado
**Breaker:** closed
