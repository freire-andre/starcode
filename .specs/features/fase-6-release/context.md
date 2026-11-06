# Fase 6: Empacotamento e distribuição (release v1.0): Context

**Size**: LARGE
**Risk triggers**: CI, release irreversível (tag v1.0), distribuição em 4 CLIs, dependência externa (GitHub privado `freire-andre/starcode`)
**Source request**: "vamos para a Fase 6, lembre de atualizar o Linear". Aqui, Fase 6 = Fase 6 do PLANO_STARCODE.md, issue SC-13: "CI: `build.py --check`, `claude plugin validate --strict`, `claude plugin eval` (risco e roteamento), selftest dos gates, testes dos hooks e do validador, `check_decisions.py` (D30). Marketplace privado e instruções de instalação nos 4 CLIs; changelog e versão sincronizada. Aceite: instalação limpa a partir do GitHub privado em cada CLI e um 'dia de missão' completo (feature GRANDE no modo 2) num projeto real. Tag v1.0." A SC-61 entra no escopo (decisão do usuário, 2026-11-06).

## Problem
Hoje o StarCode só se instala a partir de um clone local, com `tools/install_local.py` ou com o marketplace apontando para `F:/Projetos/StarCode`. Esses são os caminhos que as Fases 1–5 usaram.

Faltam várias peças para o release:
- Não há CI (`.github/` não existe), então nada impede um merge com o `dist/` desatualizado, um gate quebrado ou uma decisão sem registro.
- A versão é 0.1.0 em `VERSION` e em `.claude-plugin/marketplace.json`.
- Não há changelog.
- O README ainda diz "Fase 1" e só documenta o Claude.

Há também duas pendências da Fase 5 (SC-61) que atrapalham a instalação limpa:
- O `install_local --cli opencode` acumula entradas em `skills.paths`.
- O banner sugere `/starcode:setup` (comando do Claude) no Codex e no Antigravity.

## Users
- O dono do repositório, que instala o StarCode em máquinas novas e nos 4 CLIs a partir do GitHub privado.
- Quem mantém o StarCode e precisa que a CI barre regressões antes do merge.

## Success
- Um PR para `main` roda a CI e fica vermelho se alguma destas checagens falhar:
  - `build.py --check`;
  - `claude plugin validate --strict`;
  - a suíte `unittest`, que inclui o selftest dos gates, os hooks e o validador;
  - `check_decisions.py`.
- `claude plugin eval` (risk-sizing e routing) roda na CI só numa tag `v*` ou num disparo manual, com o secret `ANTHROPIC_API_KEY`.
- Em cada um dos 4 CLIs, numa pasta sem nenhuma instalação anterior do StarCode, a instalação pelas instruções do README a partir do GitHub privado funciona: o banner aparece, as skills carregam e os hooks bloqueiam onde a matriz diz `ok`.
- `VERSION`, `marketplace.json` e os manifestos gerados em `dist/` mostram a mesma versão, 1.0.0. Há um `CHANGELOG.md`.
- Um "dia de missão" completo, uma feature GRANDE no modo 2 do engajar ao gate `done`, roda no `starcode-sandbox`, com a evidência registrada em `docs/aceite/fase-6.md`.
- A tag anotada `v1.0.0` e um GitHub Release privado com as notas do CHANGELOG.
- SC-61 resolvida:
  - rodar o install do OpenCode duas vezes, de worktrees diferentes, deixa só as skills do `dist/opencode` atual em `skills.paths`;
  - `banner.py --cli <cli>` mostra o comando de setup e o de engajar no formato do CLI.

## Constraints
- `dist/` é gerado e versionado. Só se edita a fonte, e o `dist/` é regenerado no mesmo commit (F3-1).
- Push, PR, tag, Release e merge em `main` só com confirmação explícita do usuário (modo 3). A tag e o Release são irreversíveis na prática e pedem uma confirmação própria.
- Nunca usar modelo pago no OpenCode no aceite.
- O trust dos hooks no Codex é dado só pelo usuário. Nunca usar `--dangerously-bypass-hook-trust`.
- Escrita em pasta global do usuário só com confirmação (setup/install).
- Gate de CI de decisões (D30): bloqueia o release quando `skills/`, `scripts/` ou outras pastas mudam sem registro.
- O repositório é privado. A instalação a partir do GitHub exige que o usuário esteja autenticado no Git e no `gh`. O StarCode não guarda credenciais.

## Scope Notes
- Dentro (plano):
  - CI;
  - marketplace privado;
  - instruções de instalação nos 4 CLIs (Claude, Codex, Antigravity, OpenCode);
  - changelog;
  - versão sincronizada;
  - aceite de instalação limpa;
  - dia de missão;
  - tag v1.0.
- Dentro (usuário): SC-61, as duas pendências da Fase 5.
- Dentro (default): o README sai do "Fase 1" e passa a descrever o v1.0 e a instalação por CLI.
- Fora:
  - Modo Frota (Fase 7);
  - Uhura, Scotty e Kirk (Fase 8);
  - publicação em marketplace público;
  - instalador num comando só (o usuário escolheu clone + install_local).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Projeto do "dia de missão" | ApuraBolsa / OuveAI / Genesis_Aprimorado / starcode-sandbox | starcode-sandbox. Desvio do plano, que pede "projeto real": registrar em DECISIONS.md | 2026-11-06 |
| `claude plugin eval` na CI | só na tag e sob demanda / todo PR / só local | só na tag `v*` e no disparo manual, com secret `ANTHROPIC_API_KEY` | 2026-11-06 |
| Instalação no Antigravity e no OpenCode a partir do GitHub | clone + install_local / script único | clone + `install_local.py --cli <cli>`. Claude e Codex usam o marketplace por `owner/repo` | 2026-11-06 |
| O que sai no release | tag + GitHub Release / só tag | VERSION 1.0.0, tag anotada `v1.0.0` e GitHub Release privado com as notas do CHANGELOG | 2026-11-06 |
| SC-61 no escopo | entra / separada | entra | 2026-11-06 |
| Gatilhos da CI de PR | PR + push em main / só PR | PR para `main` e push em `main`. default (não perguntado) | 2026-11-06 |
| Plataforma da CI | ubuntu / windows / matriz | `ubuntu-latest` e `windows-latest` (o uso real é no Windows; os hooks já falharam só no Windows). default (não perguntado) | 2026-11-06 |
| Versão do Python na CI | 3.11 / 3.12 / matriz | 3.12. default (não perguntado) | 2026-11-06 |
| CLI na CI | instalar `claude` via npm / pular validate | instalar o Claude Code via npm para `plugin validate --strict` (não precisa de chave). default (não perguntado) | 2026-11-06 |
| Formato do CHANGELOG | Keep a Changelog / livre | Keep a Changelog, em PT-BR, com a entrada 1.0.0 resumindo as Fases 1–6. default (não perguntado) | 2026-11-06 |
| Fonte única da versão | VERSION / marketplace.json | `VERSION`. O build propaga para `marketplace.json` e para os manifestos do `dist/`, e o `--check` falha se divergirem. default (não perguntado) | 2026-11-06 |
| CLI do dia de missão | Claude / outro | Claude como Picard, LaForge como worker da Orca e Q no Codex, como nas Fases 3–5. default (não perguntado) | 2026-11-06 |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | `VERSION` precisa ser semver `X.Y.Z` (o build já valida). A tag precisa bater com `VERSION`, e o job de release falha se `v$(cat VERSION)` ≠ nome da tag. |
| Failure and partial failure | Cada passo da CI é um step separado com o nome da checagem, para que o vermelho diga qual falhou. Se a instalação falhar num CLI no aceite, o CLI fica marcado como reprovado no `fase-6.md`, sem bloquear o registro dos outros. A tag só é criada depois de todos os aceites aprovados. |
| Retries, idempotency and duplicates | O `install_local` é idempotente em todos os CLIs (SC-61: `skills.paths` sem duplicata nem entradas de outros clones do StarCode). Recriar uma tag existente é recusado; nunca usar `--force` em tag. |
| Authorization boundaries and rate limits | O secret `ANTHROPIC_API_KEY` só é lido no job de eval (tag e manual), nunca em PRs. O push da tag e a criação do Release pedem confirmação do usuário. |
| Concurrency and ordering | A CI usa `concurrency` por ramo, e um push novo cancela a execução anterior do mesmo PR. Ordem do release: merge em `main`, CI verde em `main`, tag e Release. |
| Data lifecycle | Os resultados do eval ficam como artefato do job (fora do Git, como hoje em `dist/claude/evals/results/`). Retenção: o padrão do GitHub. |
| Observability | O resumo do job de eval mostra a nota de cada suíte. O aceite registra a versão de cada CLI usada. |
| External dependency failure | A falha no `npm install` do Claude Code ou na API da Anthropic deixa o job vermelho com a mensagem do passo. Ela nunca vira verde por skip silencioso. |
| State-transition rules | Linear: a SC-13 vai para Done só depois da tag e do Release. A SC-61 vai para Done quando o ticket dela for integrado e o aceite confirmar. |

## Facts Found
- `tools/build.py`: lê `VERSION`, valida o semver e gera `dist/{claude,codex,antigravity,opencode}`. O `dist/` está versionado.
- `.claude-plugin/marketplace.json`: marketplace `starcode` com `source: ./dist/claude` e `version: 0.1.0` escrito à mão.
- `tools/install_local.py`:
  - Codex: `codex plugin marketplace add <root>`. O Codex 0.166 aceita `owner/repo[@ref]` e URL Git como fonte.
  - Antigravity: `agy plugin install dist/antigravity`.
  - OpenCode: cópia do plugin e `skills.paths` acumulando entradas, na linha ~101. Essa é a SC-61.
- `hooks/scripts/banner.py`: o texto fixo `/starcode:setup` aparece nas linhas 85, 200, 208 e 243 (SC-61).
- `evals/README.md`: comandos de `claude plugin eval` e critérios (risk-sizing ≥90% e 100% dos casos com gatilho; routing com todos os casos).
- `scripts/check_decisions.py`: o gate D30 já existe e roda local.
- `README.md`: diz "Estado: Fase 1" e só tem a instalação no Claude.
- Repositório GitHub: `freire-andre/starcode`, PRIVATE. Não há `.github/` nem CHANGELOG.
- `F:/Projetos/starcode-sandbox`: repositório de testes já usado nas Fases 2–4 (features task-priority, csv-import-export, limpar-concluidas).
- `tests/`: 277 testes, incluindo os gates (`test_gates.py`, `test_run_gates_exec.py`), os hooks (`test_git_guard.py`, `test_secret_scan.py`) e o validador (`test_validate_config.py`, `test_validate_verification.py`).
