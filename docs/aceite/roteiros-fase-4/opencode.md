# Roteiro de aceite da Fase 4: OpenCode

Roteiro autossuficiente para o worker automático (R26). Sandbox: `F:\Projetos\starcode-sandbox` (projeto Python `tarefas`, stdlib, `python -m unittest -v`). Time do Linear: **PROJ**, nunca o time SC.

## Missão

Exportar para Markdown: `exportar-md ARQ` grava as tarefas num arquivo Markdown.

Fluxo: `setup` → `engajar` → Troi → Spock → Data (publica no Linear, time PROJ) → 2 a 3 tickets no modo 2 → `run_gates.py done` em VEREDITO VERDE.

## Respostas

Respostas da Troi escritas de antemão (o worker não pergunta ao usuário):

- Problema: levar a lista para fora do programa.
- Entrada: `exportar-md ARQ` (caminho do arquivo; recusa sobrescrever sem aviso).
- Saída: arquivo com um item `- [ ]` ou `- [x]` por tarefa.
- Fora do escopo: importação, outros formatos.

## Aprovações

Todas gravadas como `user (roteiro pré-aprovado em 2026-11-05): "sim"`:

- dimensionamento do Picard (feature PEQUENA/MÉDIA);
- spec do Spock;
- tasks e publicação no Linear (time PROJ);
- modo Git 2 (ramo de integração `feature/<slug>`, sem push);
- custo do lote.

Marca obrigatória: `roteiro pré-aprovado em 2026-11-05`.

## Tripulação

- Picard, Troi, Spock, Data e LaForge: OpenCode, modelo `openrouter/deepseek/deepseek-v4-pro`.
- Q: no codex (outra família).

## Relatório esperado

No `worker_done` (3 frases): o que rodou, os achados e o que falta. Deve conter:

- resultado do `setup` e do `engajar` neste CLI;
- IDs das issues PROJ criadas e caminho de publicação usado (Projeto e Documento pelo MCP, ou issue-mãe pelo `orca linear`);
- commits dos 2 a 3 tickets e a saída final de `run_gates.py done` (VEREDITO VERDE);
- modelo efetivo de cada papel e CLI do Q;
- em falha do núcleo comum: CLI reprovado com a linha exata do erro (R29).
