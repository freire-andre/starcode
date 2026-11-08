# Fase 8: Uhura, Scotty e Kirk (v1.2): Context

**Size**: LARGE
**Risk triggers**: Chamadas externas (registro de pacotes, Context7), Irreversibilidade (containers locais e criação de projeto)
**Source request**: "Siga para próxima fase, lembre de atualizar o Linear" (Fase 8 do PLANO_STARCODE.md, issue SC-15: "Uhura, Scotty e Kirk: Context7, perfis das 5 stacks, scaffolding e `nova-missao`; banco efêmero local nos perfis com banco. Aceite: `nova-missao` cria Flask+PostgreSQL e Tauri+TS com versões do registro de pacotes, docs dessas versões no cache do Context7 e gates verdes na primeira execução.")

## Problem

Até a v1.1 o StarCode só trabalha em repositórios que já existem. Não há como começar um projeto novo dentro do fluxo, os gates (`**Build**`/`**Run**` nos tickets) são escritos à mão pelo Data a cada feature, e as regras do Context7 e do corpo do PR vivem só como texto no núcleo comum (`STARCODE.md`), sem um tripulante responsável nem cache padronizado em `.specs/stack/`.

## Users

O dono do repositório (usuário solo) usando StarCode no Claude Code, Codex, Antigravity e OpenCode dentro da Orca, nas stacks do plano: Python/Flask, Rust, Tauri, TypeScript, PostgreSQL/MySQL.

## Success

- `nova-missao` cria um projeto Flask+PostgreSQL e um Tauri+TS com versões vindas do registro de pacotes, o cache `.specs/stack/` só das dependências principais, e os gates do perfil verdes na primeira execução.
- Perfis com banco sobem um banco efêmero local para os gates de integração e para o Q, e o removem no fim.
- Uhura grava e renova o cache do Context7 e redige o corpo do PR e os comentários do Linear.
- Scotty aplica um perfil num repositório (scaffolding, gates padrão para o Data).

## Constraints

- Versões nunca do Context7: só manifesto/lockfile ou registro de pacotes (`npm view`, `pip index versions`/`uv`, `cargo search`) (plano §6).
- Templates trazem estrutura e convenções, não versões (plano §7).
- Banco efêmero nunca aponta para banco real; em `127.0.0.1`, porta livre, dados fictícios, removido no fim; sem Docker o gate de integração fica "não executado" com o motivo (plano, Fase 8).
- Skills em EN, saída em PT-BR; persona só no chat; núcleo comum nos 4 CLIs via `tools/build.py`.
- Modelos padrão já definidos em `src/crew.yaml`: Uhura Haiku 5.5, Scotty e Kirk Sonnet 5.5.
- Nenhum texto do Genesis copiado ou parafraseado (D da rev. 4.2).

## Scope Notes

- Usuário: uma feature GRANDE só para a fase toda ("Uma feature GRANDE"), com um PR e um aceite.
- Templates: "Arquivos fixos + script": cada perfil traz uma pasta de template e um script copia, preenche nomes e grava as versões lidas do registro.
- Tauri: "Vanilla TS + Vite" apenas nesta versão.
- Kirk: "Pasta + git init + setup": cria a pasta, scaffold, `git init` com commit inicial e oferece o `/starcode:setup`. Repo no GitHub fica fora.
- Ferramentas: "uv + npm".
- Fora: Worf, Guinan, diagnóstico (Fase 9), painel Ponte (Fase 10), verificação de telas (Fase 11), deploy.

## Gray Areas

| Item | Options | User answer | Date |
|---|---|---|---|
| Divisão da fase | uma feature GRANDE / três features | Uma feature GRANDE | 2026-11-08 |
| Geração dos templates | arquivos fixos + script / modelo gera | Arquivos fixos + script | 2026-11-08 |
| Frontend do Tauri | vanilla+Vite / +React / +Svelte | Vanilla TS + Vite | 2026-11-08 |
| Alcance do Kirk | pasta+git+setup / +repo GitHub / só scaffold | Pasta + git init + setup | 2026-11-08 |
| Ferramentas Python/Node | uv+npm / pip+npm / uv+pnpm | uv + npm | 2026-11-08 |
| Perfis com template | os 5 perfis com template / só os 2 do aceite | os 5 perfis com template; aceite real só nos 2 combos, os outros 3 cobertos por testes e por uma geração com gates quando a ferramenta existe na máquina; default (não perguntado) | 2026-11-08 |
| Banco efêmero | só Docker / Docker ou instalação local | só Docker (`docker run` com nome `starcode-eph-<id>`, removido no fim); sem Docker = gate "não executado" com motivo; default (não perguntado) | 2026-11-08 |
| Uhura no fluxo | Picard chama Uhura para PR/comentários / Uhura só sob demanda | Picard usa Uhura (subagente onde houver, senão a própria sessão) para o corpo do PR e os comentários do Linear; o cache `.specs/stack/` é escrito pela Uhura no bootstrap e sob demanda; default (não perguntado) | 2026-11-08 |
| Combinação de perfis | um perfil por projeto / combinação (app + banco) | combinação: perfil de app + perfil de banco opcional (ex.: `python-flask` + `postgresql`); default (não perguntado) | 2026-11-08 |

## Implicit Requirements

| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | nome do projeto e pasta validados (minúsculas-hífen, pasta inexistente ou vazia); perfil e combinação desconhecidos são recusados com a lista válida |
| Failure and partial failure | falha no meio do scaffold não deixa projeto pela metade sem aviso: a pasta criada nesta execução é removida ou o relatório diz exatamente o que ficou; falha de um gate na primeira execução é reportada, nunca escondida |
| Retries, idempotency and duplicates | rodar o scaffold de novo numa pasta não vazia é recusado; renovar o cache `.specs/stack/` sobrescreve a entrada da mesma lib, sem duplicar |
| Authorization boundaries and rate limits | N/A because não há usuários nem permissões; consultas ao registro e ao Context7 só para as dependências principais do perfil |
| Concurrency and ordering | dois bancos efêmeros ao mesmo tempo (Frota/Q) usam nomes e portas distintos; a porta é escolhida livre na hora |
| Data lifecycle | banco efêmero e seu volume removidos no fim do gate, também em erro; containers `starcode-eph-*` órfãos são listados pelo banner ou removidos com confirmação |
| Observability | o relatório do scaffold lista perfil, versões com a fonte (registro e data), entradas do cache criadas e o resultado de cada gate |
| External dependency failure | registro de pacotes fora do ar → para e informa, sem inventar versão; sem Context7 → cache marcado "não verificada" com a doc oficial; sem Docker → gate de integração "não executado" |
| State-transition rules | N/A because não há máquina de estados nova; o fluxo do Picard (fases do Handoff) não muda |

## Facts Found

- Personas, papéis, `release: "1.2"` e modelos de Uhura, Scotty e Kirk já estão em `src/crew.yaml` (Kirk com skill `nova-missao`, `invocation: user`, sem subagente).
- `tools/build.py` recusa pasta em `skills/` sem a skill declarada em `src/crew.yaml`; gera `dist/<cli>/skills/`.
- Gates por ticket vêm das linhas `**Build**` e `**Run <name>**` do `tasks.md` (`skills/data/references/tasks-template.md`, `scripts/gates/check_proofs.py`).
- Regras do Context7 e das versões estão em `src/context/STARCODE.md` e no plano §6; perfis no plano §7.
- `schemas/config.md` já aceita `uhura`, `scotty` e `kirk` na chave `crew`.
- Máquina: Docker 29.7.2 (daemon ativo), cargo/rustc 1.99.1, Node 24.22.1/npm 12.2.0, Python 3.14.8, uv 0.9.3; sem psql/mysql locais.
- Aceites reais anteriores usam o sandbox `F:\Projetos\starcode-sandbox` e o time PROJ no Linear (nunca o time SC).
