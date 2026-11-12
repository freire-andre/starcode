# Fixtures de aceite

Apps de exemplo que o StarCode usa para o aceite real de uma fase. Cada pasta é uma fixture: os fontes de um projeto completo, sem `node_modules`, `target` nem `.git`. Hoje existe `telas/`, o app Tauri da Fase 11 (tela de saudação com mockup vinculante).

## Como usar

```sh
python tools/aceite.py listar
python tools/aceite.py preparar telas            # diretório novo no temporário
python tools/aceite.py preparar telas --destino ~/aceite-telas
```

O comando copia a fixture para fora do repositório, roda `git init` (com `core.autocrlf false`), faz um commit inicial e imprime os próximos passos: `npm ci` e `orca repo add <caminho>`. Recusa destino dentro do repositório StarCode ou que não esteja vazio.

## O que precisa instalado

- Node (com npm)
- Rust e as dependências do Tauri para o seu sistema
- Orca (para `orca repo add` e para o navegador do juiz de telas)
- Python 3 e Git

## Linear

A `.starcode/config.json` da fixture aponta para o Linear do mantenedor (time PROJ). Quem baixar o repositório do GitHub deve rodar o setup do StarCode (`starcode:setup`) na cópia de trabalho para usar o próprio Linear.

## Distribuição

`aceite/` fica só no repositório: o `tools/build.py` não a leva ao `dist/`, então o plugin instalado pelo marketplace não traz a fixture. Só quem clona o repositório a recebe.
