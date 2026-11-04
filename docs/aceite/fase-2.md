# Aceite da Fase 2 (SC-9): planejamento com Troi, Spock e Data (Claude)

Data: 2026-11-04. Ramo: `freireandrem/sc-9-fase-2-planejamento-troi-spock-data-claude`.
Versões: Claude Code 2.1.318, Python 3.14.8. Plugin `starcode` 0.1.0.
Repositório de teste: `F:\Projetos\starcode-sandbox`. Time do Linear: PROJ ("Projetos / Teste"), para não
criar projetos no time SC.

## Entregas

| Item do plano | Onde |
|---|---|
| Gates adaptados do tlc-spec-driven (ADR-0002) | `scripts/gates/` (`validate_spec`, `validate_tasks`, `check_commit`, `run_gates`, `tasks_export`, `gates_common`) |
| Skills Troi, Spock e Data | `skills/troi/`, `skills/spock/` (+ template da spec), `skills/data/` (+ template das tasks, publicação no Linear) |
| Handoff e STATE.md (D28, F2-3) | `skills/engajar/references/state-format.md`, `scripts/handoff.py` (F2-10), banner lê os três artefatos |
| Tabela desculpa × realidade dos gates | `skills/engajar/references/gate-excuses.md` |
| Evals de roteamento das três skills | `evals/routing/` (15 casos) |
| Decisões F2-1 a F2-12 | `DECISIONS.md` |

## Critérios de aceite

| Critério | Resultado | Evidência |
|---|---|---|
| (a) feature GRANDE até as tasks aprovadas, gates verdes, 2 aprovações com as palavras do usuário, Projeto, Documento e issues criados após confirmação | ✅ | `csv-import-export`: projeto P-PROJ-4 com o Documento da spec, issues PROJ-2..6 com relações `blocks`; `task-priority`: P-PROJ-5, PROJ-7..9. Aprovações gravadas em `spec.md`/`tasks.md` com as palavras do usuário; `run_gates.py publish` VERDE nas duas |
| (b) feature MÉDIA com spec breve, `## Checks` e 1 aprovação, usando uma única issue | ✅ | `limpar-concluidas`: classificada MÉDIA (1 gatilho: dados persistidos), Troi com 1 rodada, spec breve com R1–R7 e C1–C7, uma pergunta "Aprovo a spec e crio a issue no Linear?" → "sim", issue PROJ-10, commit `b51d4a3` com `Refs: PROJ-10`; `run_gates.py execute` VERDE |
| (c) interrupção simulada retomada pelo Handoff | ✅ | Sessão nova (`/clear`) retomou `csv-import-export` pelo Handoff e pelas linhas de aprovação, sem refazer passos |
| Testes, build e validação | ✅ | `python -m unittest discover -s tests` (128 testes), `build.py --check` OK, `claude plugin validate dist/claude --strict` OK, roteamento 15/15 |

## Observações das sessões reais e correções
1. O Spock gravou uma decisão como aprovada sem a resposta do usuário; o gate da spec pegou e o agente corrigiu. É o comportamento esperado do gate.
2. Commits dos `.specs/` improvisados, sem `Refs:` → F2-7 (commit nos marcos aprovados, sem perguntar).
3. Paradas demais, turnos longos, quase tudo GRANDE, Troi sem limite de rodadas → F2-8 a F2-11. A sessão da MÉDIA, já com elas, terminou em ~3 min com 3 interações do usuário.
4. Na sessão da MÉDIA, o Handoff ainda foi editado à mão, o Settled recebeu respostas de antes da aprovação, e houve perguntas desnecessárias na retomada → F2-12. Conferir na primeira sessão da Fase 3.
5. Os commits do sandbox ficaram no ramo `chore/starcode-specs`, criado na primeira sessão (antes da F2-7); as sessões seguintes respeitaram o ramo atual.
