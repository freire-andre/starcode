# Retro: setup-grava-config

Lições registradas: L33 e L34 (novas).

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | instructions without effect | `verification.md` achado C4; mesma falha já apareceu em despacho-media-escopo (achado C5) e q-familia-revendedor (achado C9): teste de entrada do DECISIONS.md sem conferir os campos | Um helper de teste compartilhado (`tests/helpers.py`) que valida uma entrada `### <ID>:` com os quatro campos obrigatórios, usado por todo check de "entrada da issue"; a lição por texto (L34) não se promove sozinha (item N.1 da triagem). |
| 2 | média | automatic checks | `verification.md` achado C2: `interval_diff` dava `AttributeError` com o título ausente e aceitava duplicata; o edge case estava na spec, mas não no check C2 | Quando a spec lista um edge case com mensagem, o check correspondente cita o caso e a mensagem esperada, para o teste não cobrir só o caminho feliz. |
| 3 | média | information access | Relatório do worker T1-fix: `python -m unittest tests.test_config_skill`, citado no brief, falha por import de `helpers`; só roda com `discover -s tests` | Registrar no `AGENTS.md` (item 1.5) o comando de um módulo isolado que funciona (`python -m unittest discover -s tests -p test_config_skill.py -v`) e usá-lo nos briefs. |
| 4 | média | tool economy | Handoff `**Size:** PEQUENA` com spec curta: o `dispatch.py` só despacha com `spec.md` | Fechar o item 3.5 da triagem (caminho PEQUENA no `dispatch.py`) ou registrar no `execute.md` que PEQUENA usa a spec curta, para não haver decisão ad hoc a cada vez. |
| 5 | baixa | automatic checks | Primeira execução de `run_gates.py proofs` reprovou por `starcode-triagem-v2-2026-11-13.md` não rastreado na raiz, fora da feature | Documentar no `execute.md` que a árvore do worktree de integração precisa estar limpa de arquivos alheios (ou usar worktree próprio para `feature/<slug>`), antes das provas. |
