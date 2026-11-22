# Retro: versao-1-9-0

| # | Severidade | Categoria | Evidência | Ação proposta | Estado |
|---|---|---|---|---|---|
| 1 | alta | automatic checks | Handoff `--attempt proofs-timeout=fail` (2x): o gate proofs estourou 1800 s no F: e a suíte filha seguiu rodando como órfã, o que fez a execução seguinte no C: estourar também. Com a máquina limpa, ficou verde em 784 s | Ao estourar o tempo, o `check_proofs.py` encerra a árvore inteira do processo da prova (no Windows, `taskkill /T /F`, ou grupo de processos no POSIX), e um teste prova que nenhum filho sobra. | aberto |

## Talvez

Ficam fora da tabela pela regra de no máximo uma ação por retro. Nenhuma foi aplicada.

- **information access**: 23 testes procuravam entradas só em `[Unreleased]` e quebraram na troca de versão. Resolvido nesta feature com o `changelog_recent` (commit ba05d26). Uma linha no `AGENTS.md` sobre como fechar uma versão (arquivos com a versão fixa, o helper, onde rodar a suíte) evitaria redescobrir isso na 1.10.0.
- **information access**: o R2 exigia `version` no marketplace do Codex, que não tem esse campo (achado 1, `tools/build.py:455`). A lição L94 cobre o lado da spec.
- **tool economy**: uma troca de versão levou duas rodadas do Q (4 e 3 achados, todos de teste frouxo, mais o erro de spec). A pergunta que fica é se uma troca de versão pode seguir como PEQUENA quando os arquivos extras são só testes e manifestos gerados.
