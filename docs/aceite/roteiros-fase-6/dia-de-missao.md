# Roteiro do dia de missão (F6-1)

Uma feature GRANDE no `F:\Projetos\starcode-sandbox`, **modo Git 2**, do engajar ao gate `done`. O sandbox substitui um "projeto real" (decisão F6-1, escolha do usuário em 2026-11-06). Use o Claude Code com o `starcode` 1.0.0 já instalado (roteiro `claude.md`). Nunca use modelo pago no OpenCode; o trust do Codex é dado só pelo usuário.

## Passos

1. `/starcode:engajar` no sandbox; escolha o modo Git 2 quando o Picard perguntar.
2. Descreva uma feature GRANDE (várias tasks, mais de um arquivo por task) e deixe o Picard classificar o tamanho.
3. Troi (descoberta), Spock (spec, com a sua aprovação), Data (tasks e publicação no Linear, com a sua confirmação).
4. LaForge implementa cada ticket; o Picard integra os ramos de ticket no ramo da feature.
5. Q verifica a feature de forma independente.
6. Gate `done` verde: `python scripts/gates/run_gates.py done <slug>`.

## O que registrar

- Slug da feature, versão do StarCode e do CLI, data.
- Tamanho classificado e modo Git.
- Número de tasks e de tickets no Linear; tarefas que precisaram de McCoy.
- Veredito do Q (`VEREDITO: ...`) e saída do gate `done`.
- Problemas encontrados (cada um vira ticket ou decisão) e `**Resultado**: aprovado` ou `reprovado (<passo>)`.
