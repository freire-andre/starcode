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

• a skill `engajar` do StarCode · 🛸 Picard: Começa ou retoma uma missão: dimensiona a tarefa e conduz a tripulação.
• a skill `setup` do StarCode · 🛸 Picard: Configura o StarCode no repositório e na máquina (Linear, estados, labels).
• a skill `config` do StarCode · 🛸 Picard: Escolhe o modelo de cada tripulante conforme as assinaturas que você tem.
• a skill `piloto-automatico` do StarCode · 🛸 Picard: Entrevista você a fundo, você aprova a spec e ele decide o resto por você, registrando tudo.
• a skill `troi` do StarCode · 💜 Troi: Descoberta: entrevista você e escreve o context.md da feature.
• a skill `spock` do StarCode · 🖖 Spock: Escreve ou revisa a spec.md da feature e roda o gate da spec.
• a skill `data` do StarCode · 🤖 Data: Quebra a spec em tasks.md e publica os tickets no Linear.
• a skill `laforge` do StarCode · 🔧 LaForge: Implementa um ticket com TDD, dentro do escopo, e commita.
• a skill `mccoy` do StarCode · 🧪 McCoy: Diagnostica bug ou teste que não passa, com teste de regressão antes.
• a skill `q` do StarCode · ✨ Q: Verificação independente da feature pronta (verification.md).
• a skill `worf` do StarCode · 🛡️ Worf: Review de PR (correção e segurança); publica só com sua confirmação.
• a skill `guinan` do StarCode · 🍸 Guinan: Retrospectiva: registra as lições da feature e escreve o retro.md.
• a skill `uhura` do StarCode · 📡 Uhura: Cache da documentação da stack (Context7) e texto de PR e Linear.
• a skill `scotty` do StarCode · ⚙️ Scotty: Perfil de stack, scaffold e limpeza de bancos efêmeros de teste.
• a skill `nova-missao` do StarCode · 🚀 Kirk: Cria um projeto novo do zero numa pasta vazia, a partir de um perfil.
• a skill `diagnostico` do StarCode · 🔧 LaForge: Diagnóstico do harness do repositório (nível L0–L4); só relatório.
• a skill `menu` do StarCode · 🖖 StarCode: Mostra este menu.

Fluxo típico: engajar → Troi → Spock → Data → LaForge → Q → Worf → Guinan.
Para começar: a skill `engajar` do StarCode
```
