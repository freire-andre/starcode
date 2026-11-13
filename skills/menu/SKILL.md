---
name: menu
description: StarCode menu. Use when the user asks what StarCode can do or which commands, skills or crew members it has ("menu do StarCode", "#menu", "StarCode, menu", "quais são as ferramentas do StarCode", "o que o StarCode faz", "lista os comandos do StarCode"). Shows a fixed list of every StarCode skill with how to invoke it and one line on what it does. Read only; runs nothing. Not for starting work (that is engajar) or for setup.
---

# StarCode: menu

Show the block below to the user **verbatim** (it is already PT-BR), as your whole reply. Do not run any
tool, do not read any file, do not add a header, a summary or a closing line. If the user asked about one
specific item, show the block anyway and then answer that question in at most 2 lines.

```text
🖖 StarCode · Menu

• {{CMD:engajar}} · 🛸 Picard: Começa ou retoma uma missão: dimensiona a tarefa e conduz a tripulação.
• {{CMD:setup}} · 🛸 Picard: Configura o StarCode na máquina e no repositório (Linear, labels, modelos).
• {{CMD:troi}} · 💜 Troi: Descoberta: entrevista você e escreve o context.md da feature.
• {{CMD:spock}} · 🖖 Spock: Escreve ou revisa a spec.md da feature e roda o gate da spec.
• {{CMD:data}} · 🤖 Data: Quebra a spec em tasks.md e publica os tickets no Linear.
• {{CMD:laforge}} · 🔧 LaForge: Implementa um ticket com TDD, dentro do escopo, e commita.
• {{CMD:mccoy}} · 🧪 McCoy: Diagnostica bug ou teste que não passa, com teste de regressão antes.
• {{CMD:q}} · ✨ Q: Verificação independente da feature pronta (verification.md).
• {{CMD:worf}} · 🛡️ Worf: Review de PR (correção e segurança); publica só com sua confirmação.
• {{CMD:guinan}} · 🍸 Guinan: Retrospectiva: registra as lições da feature e escreve o retro.md.
• {{CMD:uhura}} · 📡 Uhura: Cache da documentação da stack (Context7) e texto de PR e Linear.
• {{CMD:scotty}} · ⚙️ Scotty: Perfil de stack, scaffold e limpeza de bancos efêmeros de teste.
• {{CMD:nova-missao}} · 🚀 Kirk: Cria um projeto novo do zero numa pasta vazia, a partir de um perfil.
• {{CMD:diagnostico}} · 🔧 LaForge: Diagnóstico do harness do repositório (nível L0–L4); só relatório.
• {{CMD:menu}} · 🖖 StarCode: Mostra este menu.

Fluxo típico: engajar → Troi → Spock → Data → LaForge → Q → Worf → Guinan.
Para começar: {{CMD:engajar}}
```
