# Retro: licoes-recorrencia-por-id

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | instructions without effect | `verification.md` achados 3, 4 e 5 (C4, C5, C6): asserção por trecho ou incompleta, embora L2 e L20 (confirmed) estivessem na seção `## Lessons` do brief do T1 | Fazer o LaForge conferir cada teste citado contra as lições do brief antes do `worker_done`, com uma linha por lição no relatório (`L2: ok` ou o motivo) |
| 2 | alta | tool economy | Handoff: o T1 e o T1-fix foram despachados à mão (`--dispatch-add` e `worker-start` direto), porque o `dispatch.py start` lê `tasks.md` e a feature MÉDIA não tem esse arquivo | Fazer o `dispatch.py start` aceitar uma feature MÉDIA, usando o `**May change**:` e os `## Checks` da spec como ticket único `T1` (execute.md, seção 8) |
| 3 | média | information access | Handoff, relatório do Q: o `dispatch.py q-check` não existe no plugin instalado (1.8.0); foi preciso rodar o `scripts/dispatch.py` do repositório | Publicar uma versão com o `q-check` antes do passo 12, ou dizer no execute.md de onde rodar o comando enquanto o cache não tiver a versão nova |
| 4 | média | automatic checks | `verification.md`, seção Limits: o `--dispatched "Q · 856e012"` gravado depois do commit das provas deixou `spec.md` modificado, e o `q-check` apontou esse arquivo como fora da lista | Gravar o `--dispatched` do Q antes do commit do Handoff, ou fazer o `q-check` ignorar uma mudança só na linha `**Dispatched:**` do Handoff |
| 5 | baixa | automatic checks | Commit `ee2e48d`: o check_commit avisou que o cabeçalho tem 99 caracteres | Incluir no brief do worker o limite do cabeçalho do commit, ou transformar o aviso em erro no gate do ticket |
