# Retro: suite-e-execute

| # | Severidade | Categoria | Evidência | Ação proposta | Estado |
|---|---|---|---|---|---|
| 1 | alta | automatic checks | commit d2a62c1 (May change ampliado durante o T1: 6 testes que liam o `execute.md` ou exigiam o `piloto-automatico/SKILL.md` igual ao da main; o worker parou com 34 falhas) | Ao mover ou renomear um arquivo de `skills/`, o `run_gates.py spec` lista os testes que leem esse caminho (busca pelo nome do arquivo em `tests/`) e avisa os que faltam no `**May change**`. | aberto |

## Talvez

Ficam fora da tabela pela regra de no máximo uma ação por retro. Nenhuma foi aplicada.

- **automatic checks**: L2, L20, L32 e L10 voltaram nesta feature (achados C3, C6, C8, C10 do `verification.md`) e já somam de 10 a 19 features cada. Isso reforça o gate contra teste frouxo, candidato para depois da pausa.
- **information access**: o check C4 só ficou conferível depois que a saída bruta da medição foi guardada (commit fc40824, `medicao-durations.txt`). Um check sobre um valor medido pode exigir, no template da spec, o arquivo com a saída bruta.
- **automatic checks**: `test_roteamento_worf_mccoy.test_descricao_piloto` comparava o `SKILL.md` inteiro, em bytes, com a main e quebrava em qualquer mudança legítima (relatório do worker do T1). Guardas desse tipo podem comparar só o campo protegido.
- **information access**: a mesma suíte levou 731 s no C: (`medicao-durations.txt`, 1.100 testes) e 1.519 s no F: (linha de base de 2026-11-21, 1.083 testes). Rodar a suíte inteira no C: pode virar uma nota no `AGENTS.md`.
