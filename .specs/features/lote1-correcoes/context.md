# Correções pontuais do lote 1: Context

**Size**: MEDIUM
**Risk triggers**: Segurança (o scanner de segredos decide o que é escaneado)
**Source request**: "proximo passo" (lote 1 da triagem v2, itens 1.2, 1.3 e 1.4; escolha do usuário: "1.2+1.3+1.4 agora")

## Problem
- 1.2: `skills/guinan/SKILL.md:20` usa `**Header first:**` sem `(F6-6)`. A regex `HEADER_PARAGRAPHS` de `tools/build.py` não casa com essa forma, e por isso o parágrafo chega intacto nos 4 `dist/*/skills/guinan/SKILL.md`.
- 1.3: `sees()` de `scripts/gates/check_proofs.py:78-84` casa `test_login` dentro de `test_login_extra`. Quando o teste tem docstring, o unittest verboso imprime o nome numa linha e a docstring com o `... ok` na seguinte, e a prova falha (retro `fase-10-ponte`, item 4). Além disso, `run()` chama `subprocess.run` sem `timeout`.
- 1.4: em `hooks/scripts/secret_scan.py:166`, `"Binary files" in diff` olha o diff inteiro, então um arquivo de texto com essa frase numa linha adicionada não é escaneado. O `except` de `:156-157` pula o arquivo sem avisar.

## Users
Picard e workers (gates de prova), qualquer usuário do hook de commit.

## Success
Os três defeitos fechados com teste. Nenhum `dist/*/skills/*/SKILL.md` contém `Header first`.

## Constraints
- Biblioteca padrão. `dist/` é regenerado pelo `tools/build.py`.
- `DECISIONS.md` e CHANGELOG no mesmo PR.

## Scope Notes
- Entra: 1.2, 1.3 e 1.4.
- Fica para depois: 1.5 e 1.7 numa missão de documentação, 1.6 por último (sobrepõe o N.2), e o helper único de `git` (N.6).

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Divisão do lote 1 | 1.2+1.3+1.4 agora / lote inteiro / um por missão | "1.2+1.3+1.4 agora (Recomendado)" | 2026-11-16 |
| Tempo limite por prova | 30 min fixo / 30 min ajustável / 10 min | "30 min fixo (Recomendado)" | 2026-11-16 |
| "Palavra inteira" em `sees()` | cada palavra esperada não pode ter caractere de palavra (`\w`) colado antes nem depois | default (não perguntado) |  |
| Docstring entre o nome e o `... ok` | o casamento pode atravessar duas linhas seguidas quando a 1ª é `<nome> (<id pontuado>)` do unittest; `test_x\n... ok` continua não casando | default (não perguntado) |  |
| Como reconhecer binário | linha do diff exatamente `Binary files ... differ` (cabeçalho do git), fora das linhas `+` | default (não perguntado) |  |
| Aviso de arquivo pulado | uma linha no stderr `StarCode hook: secret_scan pulou <arquivo> (<motivo>)`; não bloqueia | default (não perguntado) |  |
| Prova que estoura o tempo | linha `fail - tempo limite (1800 s)` no proofs.md | default (não perguntado) |  |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Failure and partial failure | Prova travada vira falha com mensagem; arquivo que o scanner não leu gera aviso |
| demais dimensões | N/A para este escopo |

## Facts Found
- `tools/build.py:222-225`: `HEADER_PARAGRAPHS` casa `**Header first (F6-6):**`. `tests/test_crew_hook.py:268-280` verifica uma lista fixa de skills, sem a Guinan.
- `scripts/gates/check_proofs.py:71-75` é `run()`; `:150-153` mostra que cada comando de `Run` roda uma vez; `:168-169` é a falha de prova. `tests/test_check_proofs.py:61-73` testa `sees()`, inclusive `test_x\n... ok` → False.
- `hooks/scripts/secret_scan.py:129-175` é `staged_findings`; o aviso do hook segue o formato `StarCode hook: secret_scan ...` (`:361`).
