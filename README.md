# StarCode

Plugin de desenvolvimento orientado a especificação (SDD) com uma tripulação de agentes Star Trek,
para Claude Code, Codex, Antigravity CLI e OpenCode dentro da Orca IDE, com o Linear como base dos tickets.

Estado: **v1.0**, com os 4 CLIs suportados (Claude Code, Codex, Antigravity CLI e OpenCode). A matriz de
compatibilidade está em [`docs/compatibilidade.md`](docs/compatibilidade.md). O plano completo está em
`PLANO_STARCODE.md`; as decisões, em `DECISIONS.md`; o aceite de cada fase, em `docs/aceite/`.

Repositório privado. Star Trek é marca de seus titulares; os nomes são usados só como homenagem.

## Pré-requisitos

- Acesso ao repositório privado `freire-andre/starcode`: rode `gh auth login` ou use uma credencial Git
  com acesso a ele.
- Python 3 no PATH.
- Orca e Linear.

## Instalação

### Claude Code

```
/plugin marketplace add freire-andre/starcode
/plugin install starcode@starcode
```

### Codex

```
codex plugin marketplace add freire-andre/starcode
codex plugin add starcode@starcode
```

Depois, abra `/hooks` no Codex e aprove (trust) os hooks do StarCode. Só você pode aprovar.

### Antigravity CLI

Clone em um caminho sem espaço (o instalador recusa caminhos com espaço):

```
git clone https://github.com/freire-andre/starcode.git
cd starcode
python tools/install_local.py --cli antigravity
```

### OpenCode

```
git clone https://github.com/freire-andre/starcode.git
cd starcode
python tools/install_local.py --cli opencode
```

O instalador copia o pacote para `~/.config/opencode/starcode` e aponta o `opencode.json` para essa cópia: o clone pode trocar de ramo sem afetar o OpenCode. Para atualizar, rode o comando de novo.

## Primeiros passos

Em cada repositório, rode o setup (configura Linear, estados e labels) e depois engaje (inicia ou retoma o
trabalho com a tripulação):

| CLI | Setup | Engajar |
| --- | --- | --- |
| Claude Code | `/starcode:setup` | `/starcode:engajar` |
| Codex | a skill `setup` do StarCode | a skill `engajar` do StarCode |
| Antigravity CLI | a skill `setup` do StarCode | a skill `engajar` do StarCode |
| OpenCode | `/sc-setup` | `/sc-engajar` |

Para ver todas as ferramentas do StarCode com uma linha sobre cada uma, chame o menu: `/starcode:menu`
(Claude Code), `/sc-menu` (OpenCode) ou a skill `menu` do StarCode (Codex e Antigravity).

Para tocar uma feature inteira com uma entrevista só, use `/starcode:piloto-automatico` (`/sc-piloto-automatico`
no OpenCode): a Troi entrevista você a fundo, você aprova a spec e o Picard decide o resto por você, registrando
cada pergunta e decisão em `.specs/features/<slug>/piloto.md`. Push, PR, merge e deploy continuam pedindo o seu sim.

Para escolher o modelo de cada tripulante conforme as assinaturas que você tem, use `/starcode:config`
(`/sc-config` no OpenCode, a skill `config` no Codex e no Antigravity). O StarCode sugere o modelo por
papel e custo (ex.: Haiku para as tarefas repetitivas) e você aceita ou troca linha por linha. Qualquer modelo do
OpenCode (Muse Spark, GLM, Kimi...) é analisado pelo catálogo do models.dev antes da escolha, e a escolha pode
valer para todos os projetos ou só para o repositório atual (`.starcode/config.local.json`, fora do Git).

## Painel ao vivo

O StarCode mantém dois arquivos pequenos para um painel visual, em `.starcode/live/` no worktree principal
(a pasta se ignora sozinha no Git; a escrita é atômica):

```json
// crew.json: quem está trabalhando (1) ou parado (0)
{"picard": 1, "spock": 0, "troi": 0, "data": 0, "laforge": 1, "mccoy": 0, "q": 0}

// progress.json: tickets integrados / total por feature
{"export-csv": {"done": 2, "total": 5, "percent": 40, "phase": "execute", "updatedAt": "2026-11-07T15:00:00+00:00"}}
```

`python <plugin>/scripts/crew_live.py reset` zera o status se uma sessão cair no meio.

**Statusline do Claude Code.** `scripts/statusline.py` mostra os tripulantes ativos e a barra de progresso
(degradê #C5DBFF → #75C3FF → #0028B3). Como statusline inteira, no `~/.claude/settings.json`:

```json
"statusLine": {"type": "command", "command": "python <plugin>/scripts/statusline.py"}
```

Numa statusline própria em Python, importe o arquivo e chame `segment(cwd)` (devolve `""` quando não há o que
mostrar).

## Painel Ponte (Orca)

A Ponte é um painel da Orca com a tripulação e o progresso do StarCode. Ela exige Orca 1.4.248 ou mais nova e
não depende do CLI de agente. Não há catálogo: instale do repositório.

```
python tools/build.py                           # gera dist/orca
python tools/install_local.py --cli orca        # instala o plugin da Orca localmente
```

Depois, aprove o plugin na Orca (a aprovação é sempre sua; nenhum script aprova por você) e abra a barra
lateral direita (`sidebar.right.toggle`) para ver a Ponte.

## Desenvolvimento

```
python tools/build.py            # gera dist/<cli>/ a partir da fonte (nunca edite dist/ à mão)
python tools/build.py --check    # falha se dist/ estiver desatualizado
python -m unittest discover -s tests
python scripts/check_decisions.py
```

O CI (GitHub Actions, `.github/workflows/ci.yml`) roda os checks e a conferência de release; o eval só roda sob demanda (`workflow_dispatch`, exige o secret `ANTHROPIC_API_KEY`).
O release é feito por `tools/release.py` (`check --tag vX.Y.Z` confere a tag; `create --yes` cria o release).

Evals: ver `evals/README.md`.
