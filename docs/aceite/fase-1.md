# Aceite da Fase 1 (SC-8): núcleo, configuração, hooks e Picard (Claude)

Data: 2026-11-03. Ramo: `freireandrem/sc-8-fase-1-nucleo-configuracao-hooks-e-picard-claude`.
Versões: Claude Code 2.1.317, Orca 1.4.247, Python 3.14.8. Plugin `starcode` 0.1.0.

## Entregas

| Item do plano | Onde |
|---|---|
| `src/crew.yaml` (modelos da seção 3.2), `src/context/STARCODE.md`, `tools/build.py` | `src/`, `tools/build.py` (+ `tools/miniyaml.py`, F1-5) |
| Configs `schemaVersion: 1` + validador stdlib + fixtures | `scripts/config/validate_config.py`, `schemas/config.md`, `tests/fixtures/config/` |
| Hooks do Claude: `git_guard.py`, `secret_scan.py`, `banner.py` | `hooks/scripts/`, registrados em `dist/claude/hooks/hooks.json` |
| Skills `engajar` e `setup` | `skills/engajar/`, `skills/setup/` |
| Referências `git-modes`, `linear-contract`, `crew-voice`, `risk-sizing` | `skills/engajar/references/` |
| `evals/risk-sizing/` e `evals/routing/` | `evals/` (README com os comandos) |
| `conflicts.py` (D31) no setup e no banner | `scripts/conflicts.py` |
| Modo Git por worktree, autorização de merge | `scripts/git_mode.py` (F1-1, F1-3) |
| Gate do `DECISIONS.md` (D30) | `scripts/check_decisions.py` |

## Critérios de aceite

| Critério | Resultado | Evidência |
|---|---|---|
| `build.py --check` passa | ✅ | `python tools/build.py --check` → `OK, dist/ em dia`; `test_build.test_repo_dist_is_up_to_date` |
| `claude plugin validate dist/claude --strict` | ✅ | "Validation passed" (plugin e marketplace) |
| `claude plugin eval`: 100% dos casos com gatilho, ≥90% no total | ✅ 12/12 casos, 24/24 execuções | `--tag risk-sizing --ablation none`: os 8 casos `trigger` nunca saíram PEQUENA, e os 4 `no-trigger` saíram PEQUENA. Custo US$ 2,65 |
| Evals de roteamento, incluindo as frases negativas | ✅ 10/10 | 5 positivos disparam `starcode:engajar`/`starcode:setup`; 5 negativos não disparam nenhuma skill do StarCode |
| Hooks bloqueiam os casos de teste sem falso positivo | ✅ | `tests/test_git_guard.py`: 30 comandos sempre bloqueados, 23 comandos normais liberados, regras por modo, ramo base e autorização. `tests/test_secret_scan.py`: 8 tipos de segredo falso bloqueados, 11 textos parecidos liberados, allowlist, `.env`, lockfile, `commit -a` |
| Hooks no Claude real | ✅ | `claude -p --plugin-dir dist/claude` num repo temporário: `git reset --hard` negado pelo hook, mesmo com `--allowedTools`; `git commit` com token falso negado pelo `secret_scan`; `git push` negado no modo 2; banner "Diário do Capitão" recebido no início da sessão |
| Validador recusa config inválido com mensagem clara e nunca grava parcial | ✅ | `tests/test_validate_config.py`: 8 fixtures inválidas, cada uma com a mensagem esperada; `--write` não cria nem altera o arquivo quando o conteúdo é inválido |
| Setup aponta uma skill concorrente plantada | ✅ (script) | `tests/test_support.ConflictsTests`: skill `to-spec` plantada → "disputa com Spock" + ação para desativar; skills `orca-*` e de outros domínios não são apontadas; a descrição de terceiros nunca é ecoada |
| `setup` grava os dois configs válidos (sessão real) | ✅ | Sessão de 2026-11-03: `map-states` sem ambiguidade (SC: Todo / In Progress / Done; review e blocked nulos); `.starcode/config.json` e `~/.starcode/config.json` (`{"schemaVersion": 1}`) gravados via `validate_config.py --write` → "OK"; 12 labels `crew:*` criadas no time SC pelo Linear MCP após busca de duplicatas (time e workspace) e confirmação, `missing-labels` → `[]`; `conflicts.py` → "Nenhuma skill ou plugin concorrente encontrado"; banner → ambos os configs "✅ válido" |
| `engajar` pergunta o modo, lista time e estados e roteia (sessão real) | ✅ | Mesma sessão: banner completo, preflight (config ausente → recomenda setup), pergunta do modo com as 4 opções (modo 2 gravado por `git_mode.py set 2`), tabela de time e estados, dimensionamento da SC-9 (GRANDE) e parada correta: regra de avanço não cumprida e Troi/Spock/Data não instalados, sem fazer o trabalho deles |

Suíte completa: `python -m unittest discover -s tests` (stdlib).

## Observações da sessão real
1. Com "manter padrões", o passo 4 do setup não grava `~/.starcode/config.json` (só guarda diferenças) e o banner continua "ausente". O arquivo mínimo foi gravado à parte. Ajuste sugerido: gravar `{"schemaVersion": 1}` quando não houver diferenças.
2. O config do repositório foi recusado no setup e gravado depois, no preflight do engajar, sempre pelo validador.
