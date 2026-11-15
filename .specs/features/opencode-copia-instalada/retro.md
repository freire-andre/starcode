# Retro: opencode-copia-instalada

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | média | automatic checks | Ramo local `fix/opencode-copia-instalada` (commit `5d8450a`, 2026-11-13) ficou 275 commits atrás da `main` sem PR, e só apareceu numa revisão manual dos ramos | Fazer o banner do StarCode listar ramos locais com commits ausentes da base (`git cherry`) há mais de 1 dia |
| 2 | média | instructions without effect | `verification.md` achado 2 e Handoff: o check C5 foi acrescentado depois do Q, e a linha dele na verificação ficou como "não julgado pelo Q" | Quando a spec cita um comportamento em Requirements (o dry-run de R3), exigir no gate da spec que cada requisito tenha um check citando o teste correspondente |
| 3 | baixa | tool economy | Handoff: o gate da spec recusa `**Size**: SMALL` com spec, e a tarefa PEQUENA precisou de uma spec marcada como MEDIUM para ter `May change` e checks nos gates | Aceitar no gate uma spec PEQUENA mínima (`May change` + `## Checks`) ou ler os checks inline do Handoff |
