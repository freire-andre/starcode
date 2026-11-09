# Fase 9: Worf, Guinan e diagnóstico (v1.3): Context

**Size**: LARGE
**Risk triggers**: Segurança (gates de review e portão de evidência dos achados de segurança), Chamadas externas (`npx harness-score`, `gh` para o review do PR, juízes do harness-eval com custo)
**Source request**: "inicia a fase 9, lembre de atualizar o Linear" (Fase 9 do PLANO_STARCODE.md, issue SC-16: "`worf` com os gates da seção 3.1, incluindo o portão de evidência dos achados de segurança; `guinan` (retro + `lessons.py`); `diagnostico` (`npx harness-score` + harness-eval opcional: Track A sempre, B/C só com aprovação de custo). Aceite: review consolidado num PR de teste, incluindo um bypass plantado que o `scan_bypasses.py` detecta e o review aponta; lição registrada; relatório L0–L4 do próprio repo.")

## Problem

Até a v1.2 o review do PR é humano (plano §3), não há retro nem memória de lições entre features, e não existe um jeito padronizado de medir a maturidade do harness de um repositório. Os achados do Q morrem no `verification.md` de cada feature e erros repetidos (ex.: asserts fracos, exit code mascarado por pipe) voltam na feature seguinte.

## Users

O dono do repositório (usuário solo) usando StarCode no Claude Code, Codex, Antigravity e OpenCode dentro da Orca, com o fluxo GRANDE e o modo Git 3 (PR no GitHub).

## Success

- Worf revisa um PR com os gates da §3.1 e produz um review consolidado; um bypass plantado é detectado pelo `scan_bypasses.py` e apontado no review.
- Guinan faz a retro da feature e registra ao menos uma lição via `lessons.py`.
- `diagnostico` gera o relatório L0–L4 do próprio repo StarCode com `npx harness-score` e roda o Track A do harness-eval; B/C só com aprovação de custo.

## Constraints

- Fontes adaptáveis com crédito no `CREDITS.md`: the-judge 1.4.0 (CC-BY-4.0, Felipe Rodrigues: `scan_bypasses.py`, `review_gate.py`, `post_review.py`), harness-eval 1.8.3 (CC-BY-4.0, Tech Leads Club: scripts do Track A), tlc-spec-driven 4.1.0 `lessons.py` (CC-BY-4.0), mattpocock/skills `retro` (MIT), Cloudflare security-audit-skill (MIT, portão de evidência). Material do Genesis nunca.
- `harness-score` é ferramenta externa (npm 1.8.4, MIT, zero dependências, sem rede): roda via `npx`, não é copiada.
- Modelos padrão (plano §3.2): Worf claude Opus 5.5 (opção codex para segundo olhar), Guinan claude Haiku 5.5; diagnóstico como skill do LaForge (plano §3, linha "LaForge (diagnóstico)").
- Skills em EN, saída em PT-BR, persona só no chat; núcleo comum nos 4 CLIs via `tools/build.py`; sem bajulação (Worf em especial).
- Publicar review no GitHub é escrita externa: confirmação na hora (D29 item 6).
- Track B/C do harness-eval gastam tokens de modelo: só com aprovação de custo explícita.

## Scope Notes

- Escopo é a Fase 9 do plano inteira, numa feature GRANDE (mesmo modelo da Fase 8): `worf`, `guinan`, `diagnostico`.
- Fora: painel Ponte (Fase 10), verificação de telas (Fase 11), snapshot e raio de impacto (Fase 12), deploy.

## Gray Areas

| Item | Options | User answer | Date |
|---|---|---|---|
| Entrega do review do Worf | arquivo + gh confirmado / só arquivo / publica direto | Arquivo + gh confirmado: `review.md` na pasta da feature; publicação no PR via `gh` só após o sim do usuário | 2026-11-09 |
| PR de teste do aceite | PR rascunho no starcode / repo GitHub para o sandbox / só ramo local | PR rascunho no starcode: ramo descartável no próprio repo, PR draft fechado sem merge | 2026-11-09 |
| Worf no fluxo | automático após o PR / só sob demanda | Automático após o PR: Picard chama o Worf depois de abrir o PR e antes de pedir a autorização de merge | 2026-11-09 |
| Alcance das lições | por repo lidas nos briefs / por repo só registro / repo + global | Por repo, lidas nos briefs: `.specs/lessons.json` + `.specs/LESSONS.md`; as `confirmed` entram nos briefs do LaForge e do Q | 2026-11-09 |
| Quando a Guinan roda | automático no fim da feature / sob demanda | Automático: Picard chama a Guinan depois do `done` (antes do PR) e também sob demanda; default (não perguntado) | 2026-11-09 |
| Fonte das lições | só achados do Q / Q + retro | Achados do `verification.md` e linhas vermelhas de `proofs.md` (sinais do tlc) e achados do Worf; a retro vira lista de sugestões de ambiente para o usuário, nunca lição automática; default (não perguntado) | 2026-11-09 |
| Relatório do diagnóstico | arquivo no repo / só chat | `docs/diagnostico/<data>.md` com nível L0–L4, pontuação por dimensão, próximo degrau e resumo do Track A; default (não perguntado) | 2026-11-09 |
| Aprovação de custo B/C | por execução / gravada na config | por execução, com estimativa mostrada antes; nunca gravada; default (não perguntado) | 2026-11-09 |
| Rodadas do Worf | máximo 3 (§3.1) | rodada 1 completa; 2 e 3 só verificam resolução e blockers novos; depois disso o Picard para e mostra o que ficou aberto; default (não perguntado) | 2026-11-09 |

## Implicit Requirements

| Dimension | Requirement or N/A because ... |
|---|---|
| Input validation and limits | Worf recusa alvo inexistente (PR, ramo ou diff vazio) com mensagem clara; `review_gate.py` limita 5 nits, exige evidência em blocker/should-fix e TL;DR com veredito; `lessons.py add` recusa lição sem sinal e sem referência a um achado real |
| Failure and partial failure | falha do `gh` ao publicar não perde o review: `review.md` fica gravado e o erro é mostrado; `npx harness-score` indisponível (sem Node ou sem rede para baixar) marca o relatório como "não executado" com o motivo, e o Track A roda mesmo assim |
| Retries, idempotency and duplicates | republicar o review no mesmo PR na mesma rodada é recusado (marcador da rodada no `review.md`); `lessons.py add` de lição já existente conta recorrência em vez de duplicar |
| Authorization boundaries and rate limits | publicar review e qualquer chamada `gh` que escreve exigem confirmação; Track B/C exigem aprovação de custo; Worf nunca aprova merge nem faz merge |
| Concurrency and ordering | N/A because Worf, Guinan e diagnóstico rodam em sequência na sessão do Picard, um por vez; `lessons.json` só é escrito pelo script |
| Data lifecycle (retention, deletion) | `lessons.py` faz poda e quarentena (lição que falhou ao ser aplicada); runs do harness-eval ficam em pasta ignorada pelo Git; o ramo e o PR de teste do aceite são fechados/removidos no fim, com a exclusão remota feita pelo usuário |
| Observability | cada passo informa no chat em uma linha (veredito, contagem de achados por severidade, nível L0–L4); o Handoff registra rodada do Worf, lições gravadas e o relatório do diagnóstico |
| External dependency failure | Context7 indisponível: achado externo sem URL/ID é rebaixado a pergunta ou removido (evidência ou silêncio); `gh` sem login: review fica só no arquivo e o motivo é mostrado |
| State-transition rules | estados do achado de segurança: `confirmed`, `needs-validation` (com o fato exato que falta), `rejected` (com o motivo); estados da lição: `candidate` → `confirmed` (recorrência em 2 features) → `quarantined`; severidade nunca acima do impacto demonstrado |

## Facts Found

- Fontes já no repo: `docs/reference/the-judge.zip` (SKILL.md, `scripts/scan_bypasses.py`, `review_gate.py`, `post_review.py`, `references/review-standards.md`, `comment-voice.md`), `docs/reference/harness-eval.zip` (Track A: `track_a_correctness.py`, `inventory_extract.py`, `surfaces_extract.py`, `doc_scope.py`; B/C: `merge_agreement.py`, `merge_usefulness.py`, `slim_fanin.py`), `docs/reference/harness-score-main.zip` (níveis L0 Unharnessed … L4 Self-correcting, `--min-level`, saída JSON/markdown), `docs/reference/tlc-spec-driven.zip` (`scripts/lessons.py`, `references/lessons.md`: `.specs/lessons.json` + `.specs/LESSONS.md`, sinais `weak_test`/`spec_precision_gap`/`ac_gap`/`spec_deviation`/`gate_fail`, candidate→confirmed por recorrência em 2 features), `docs/reference/skills-main.zip` (`skills/engineering/retro/SKILL.md`).
- `harness-eval` não existe no npm (404): é skill, adaptada a partir do zip.
- `CREDITS.md` já reserva linhas para the-judge e Cloudflare security-audit-skill (v1.3).
- Plano §3.1 define os gates do Worf (evidência ou silêncio, pesquisa obrigatória, escada determinística, `scan_bypasses.py`, `review_gate.py` com no máximo 5 nits, convergência em até 3 rodadas, portão de evidência com estados `confirmed`/`needs-validation`/`rejected`).
- Plano §4 fluxo: "review (Worf a partir da v1.3; antes, humano) → merge só com autorização separada"; "Retro (Guinan a partir da v1.3) → concluído só com critérios atendidos e evidência".
- O sandbox `F:\Projetos\starcode-sandbox` não tem remoto no GitHub; o repo `freire-andre/starcode` tem remoto e CI.
- Estrutura das fases anteriores: skills em `skills/<nome>/`, scripts em `scripts/`, gates em `scripts/gates/`, briefs em `src/briefs/`, gerado em `dist/<cli>/` por `tools/build.py`; modelo de context em `.specs/features/fase-8-uhura-scotty-kirk/context.md`.
