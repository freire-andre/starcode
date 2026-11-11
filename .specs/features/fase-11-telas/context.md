# Fase 11 — Verificação de telas: Context

**Size**: LARGE
**Risk triggers**: none
**Source request**: "siga para a proxima fase, lembre de atualizar o Linear" (Fase 11 do PLANO_STARCODE.md: "Reintroduzir as regras de captura do tlc e o subagente de telas usando `orca snapshot`/`orca screenshot`. Aceite: uma feature Tauri com mockup vinculante tem as telas capturadas no tamanho do mockup e julgadas, com `screens.md` aceito pelo `validate_verification`.")

## Problem
Desde a D25 o StarCode não verifica telas: a adaptação dos gates removeu as regras de captura do tlc (`captures/`, `screens.md`, rodadas) e a skill do Spock avisa que mockups não são verificados. Uma feature com tela pode passar no gate final sem que ninguém compare a tela rodando com o mockup aprovado.

## Users
O dono do repositório (único usuário do StarCode), em features com interface (Tauri, web) dentro da Orca.

## Success
- Uma spec pode citar um mockup vinculante (`captures/<tela>.png`); o gate final exige, para cada mockup citado, uma captura da tela rodando no mesmo tamanho (1x/2x/3x) e um `screens.md` com veredito `matches` em todas as linhas.
- Um juiz de telas independente do autor tira as próprias capturas no navegador da Orca no tamanho do mockup, faz o inventário e escreve `screens.md` (no máximo 2 rodadas).
- Aceite: feature Tauri real com mockup vinculante passa no `validate_verification` com `screens.md`.

## Constraints
- Orca 1.4.256. Captura só pelo navegador da Orca (`orca tab create`, `orca exec --command "set viewport W H"`, `orca screenshot`, `orca snapshot`).
- `orca computer` no Windows não move nem redimensiona janela nativa (`windows.moveResize: false`): a janela nativa do Tauri não pode ser posta no tamanho do mockup.
- Atribuição CC-BY-4.0 do tlc nos arquivos adaptados (como os outros gates).
- Q e juiz de telas fora da família de modelo do LaForge (D17).

## Scope Notes
- Entra (plano): regras de captura do tlc, subagente de telas, `screens.md` no `validate_verification`, aceite com feature Tauri.
- Fora (plano): nada além do aceite Tauri; Fase 12 (robustez) fica para depois.

## Gray Areas
| Item | Options | User answer | Date |
|---|---|---|---|
| Captura de tela Tauri | frontend (Vite) no navegador da Orca com viewport do mockup e `mockIPC` / janela nativa via `orca computer` | Frontend no navegador | 2026-11-11 |
| Quem julga as telas | worker de telas próprio na família do Q / dentro do worker do Q | Worker próprio | 2026-11-11 |
| Mockup do aceite | gerado por nós (HTML → PNG 1x, aprovado pelo usuário) / fornecido pelo usuário | Nós geramos | 2026-11-11 |
| Projeto do aceite | app Tauri novo criado pelo Scotty numa pasta nova, Linear no time PROJ / `starcode-sandbox` | Novo no sandbox | 2026-11-11 |
| Formato do mockup vinculante | PNG em `captures/` / também HTML ou Figma | PNG (ou JPEG/WebP) em `.specs/features/<slug>/captures/`, citado entre crases num critério da spec — default (não perguntado) | |
| Paridade nos 4 CLIs | só Claude / os 4 | gate e regras nos 4 pelo build; a captura usa o navegador da Orca, igual em todos — default (não perguntado) | |
| Sem navegador da Orca disponível | falhar / julgar a foto do autor | julga a foto do autor e grava `pictures: author's` (verificação degradada, aviso no gate) — default (não perguntado) | |
| Rodadas | 1 / 2 | 2, como no tlc; o que ainda difere na rodada 2 vai para o usuário — default (não perguntado) | |

## Implicit Requirements
| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | Imagem citada que não existe, ilegível ou fora de PNG/JPEG/WebP vira ERRO do gate com o caminho; tamanho lido do cabeçalho da imagem, sem dependência externa. |
| Failure and partial failure | Uma tela que falha na captura (página não desenha frame, servidor fora) é registrada no `screens.md` com o motivo, nunca como `matches`. |
| Retries, idempotency and duplicates | Captura refeita sobrescreve `captures/<tela>.running.png`; no máximo 2 rodadas do juiz. |
| Authorization boundaries and rate limits | N/A because só lê arquivos locais e usa o navegador da Orca em `127.0.0.1`. |
| Concurrency and ordering | Uma aba por tela, identificada por `--page`; abas de teste fechadas ao final. |
| Data lifecycle | Capturas `.running.png` ficam versionadas na pasta da feature como evidência; os PNGs temporários da Orca (expiram em ~24 h) são copiados para lá. |
| Observability | `screens.md` traz rodada, verificador, fonte das fotos (`running` ou `author's`) e o inventário de cada tela. |
| External dependency failure | Orca sem navegador ou servidor de desenvolvimento fora do ar: o juiz grava o motivo e a verificação fica degradada; o gate avisa. |
| State-transition rules | Rodada 1 → correção → rodada 2 → usuário; linhas `same` da rodada 1 não são reabertas. |

## Facts Found
- tlc de referência: `docs/reference/tlc-spec-driven.zip` → `references/verify-screens.md` (juiz, inventário, critérios `controls/arrangement/copy/drawing/render`, 2 rodadas) e `scripts/validate_verification.py` (`_screen_evidence`, `_picture_sizes` 1x/2x/3x, `_screens_verdicts`, `**Round**:`, `**Walked:**`, prova `browser`).
- O que foi removido e por quê: `docs/adr/ADR-0002-formato-dos-gates.md` (linha das regras de captura), `DECISIONS.md` D25; aviso na `skills/spock/SKILL.md:43`.
- Gate atual: `scripts/gates/validate_verification.py` (sem regras de tela).
- Testado em 2026-11-11: `orca tab create --url http://127.0.0.1:8765/` + `orca exec --page <id> --command "set viewport 800 600"` + `orca screenshot --page <id>` gerou PNG 800×600 (deviceScaleFactor 1). Com URL `data:` o screenshot expira ("page did not draw a frame").
- Perfil Tauri: `profiles/tauri/profile.yaml` (Tauri 2, Vite 8, `@tauri-apps/api` 2); o frontend roda no servidor do Vite.
