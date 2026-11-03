# StarCode

Plugin de desenvolvimento orientado a especificação (SDD) com uma tripulação de agentes Star Trek,
para Claude Code, Codex, Antigravity CLI e OpenCode dentro da Orca IDE, com o Linear como base dos tickets.

Estado: **Fase 1** (núcleo, configuração, hooks e Picard no Claude Code). O plano completo está em
`PLANO_STARCODE.md`; as decisões, em `DECISIONS.md`; a matriz de compatibilidade, em
`docs/compatibilidade.md`; o aceite de cada fase, em `docs/aceite/`.

Repositório privado. Star Trek é marca de seus titulares; os nomes são usados só como homenagem.

## Instalação (Claude Code)

```
/plugin install starcode --marketplace freire-andre/starcode
```

Depois, em cada repositório: `/starcode:setup` (configura Linear, estados e labels) e
`/starcode:engajar` (inicia ou retoma o trabalho com a tripulação).

## Desenvolvimento

```
python tools/build.py            # gera dist/<cli>/ a partir da fonte (nunca edite dist/ à mão)
python tools/build.py --check    # falha se dist/ estiver desatualizado
python -m unittest discover -s tests
python scripts/check_decisions.py
```

Evals: ver `evals/README.md`.
