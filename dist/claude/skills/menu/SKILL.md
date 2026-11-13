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

• /starcode:engajar · 🛸 Picard: Começa ou retoma uma missão: dimensiona a tarefa e conduz a tripulação.
• /starcode:setup · 🛸 Picard: Configura o StarCode no repositório e na máquina (Linear, estados, labels).
• /starcode:config · 🛸 Picard: Escolhe o modelo de cada tripulante conforme as assinaturas que você tem.
• /starcode:piloto-automatico · 🛸 Picard: Entrevista você a fundo, você aprova a spec e ele decide o resto por você, registrando tudo.
• /starcode:troi · 💜 Troi: Descoberta: entrevista você e escreve o context.md da feature.
• /starcode:spock · 🖖 Spock: Escreve ou revisa a spec.md da feature e roda o gate da spec.
• /starcode:data · 🤖 Data: Quebra a spec em tasks.md e publica os tickets no Linear.
• /starcode:laforge · 🔧 LaForge: Implementa um ticket com TDD, dentro do escopo, e commita.
• /starcode:mccoy · 🧪 McCoy: Diagnostica bug ou teste que não passa, com teste de regressão antes.
• /starcode:q · ✨ Q: Verificação independente da feature pronta (verification.md).
• /starcode:worf · 🛡️ Worf: Review de PR (correção e segurança); publica só com sua confirmação.
• /starcode:guinan · 🍸 Guinan: Retrospectiva: registra as lições da feature e escreve o retro.md.
• /starcode:uhura · 📡 Uhura: Cache da documentação da stack (Context7) e texto de PR e Linear.
• /starcode:scotty · ⚙️ Scotty: Perfil de stack, scaffold e limpeza de bancos efêmeros de teste.
• /starcode:nova-missao · 🚀 Kirk: Cria um projeto novo do zero numa pasta vazia, a partir de um perfil.
• /starcode:diagnostico · 🔧 LaForge: Diagnóstico do harness do repositório (nível L0–L4); só relatório.
• /starcode:menu · 🖖 StarCode: Mostra este menu.

Fluxo típico: engajar → Troi → Spock → Data → LaForge → Q → Worf → Guinan.
Para começar: /starcode:engajar
```
