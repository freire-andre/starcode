# Roteiro de aceite da Fase 4: Antigravity

Roteiro autossuficiente para o worker automático (R26). Sandbox: `F:\Projetos\starcode-sandbox` (projeto Python `tarefas`, stdlib, `python -m unittest -v`). Time do Linear: **PROJ**, nunca o time SC.

## Missão

Busca por texto: `buscar TERMO` lista as tarefas cujo título contém o termo.

Fluxo: `setup` → `engajar` → Troi → Spock → Data (publica no Linear, time PROJ) → 2 a 3 tickets no modo 2 → `run_gates.py done` em VEREDITO VERDE.

## Respostas

Respostas da Troi escritas de antemão (o worker não pergunta ao usuário):

- Problema: achar tarefas numa lista longa.
- Entrada: `buscar TERMO` (sem diferenciar maiúsculas; termo vazio é recusado).
- Saída: as tarefas que contêm o termo, ou a mensagem `nenhuma tarefa encontrada`.
- Fora do escopo: expressões regulares, busca por data.

## Aprovações

Todas gravadas como `user (roteiro pré-aprovado em 2026-11-05): "sim"`:

- dimensionamento do Picard (feature PEQUENA/MÉDIA);
- spec do Spock;
- tasks e publicação no Linear (time PROJ);
- modo Git 2 (ramo de integração `feature/<slug>`, sem push);
- custo do lote.

Marca obrigatória: `roteiro pré-aprovado em 2026-11-05`.

## Tripulação

- Picard, Troi, Spock, Data e LaForge: Antigravity, modelo `gemini-3.8-flash-high`.
- Q: no codex (outra família).

## Relatório esperado

No `worker_done` (3 frases): o que rodou, os achados e o que falta. Deve conter:

- resultado do `setup` e do `engajar` neste CLI;
- IDs das issues PROJ criadas e caminho de publicação usado (Projeto e Documento pelo MCP, ou issue-mãe pelo `orca linear`);
- commits dos 2 a 3 tickets e a saída final de `run_gates.py done` (VEREDITO VERDE);
- modelo efetivo de cada papel e CLI do Q;
- em falha do núcleo comum: CLI reprovado com a linha exata do erro (R29).
