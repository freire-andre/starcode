# Paridade declarada: nível de suporte de cada CLI: Spec

**Size**: SMALL
**Linear**: SC-204
**May change**: README.md, docs/compatibilidade.md, tests/test_paridade_declarada.py, DECISIONS.md, CHANGELOG.md

## Scope
- Item 3.8 da triagem v2 (decisão D-d). O `README.md` troca "com os 4 CLIs suportados" pelos níveis: Claude Code **principal**, Codex **secundário completo**, Antigravity CLI e OpenCode **melhor esforço**, com uma linha por nível: principal = todo recurso nasce e é aceito aqui; secundário completo = paridade de recursos, com aceite em sessão real; melhor esforço = funciona pelo mesmo pacote gerado, sem lógica própria nova, e problema só é corrigido quando bloqueia o fluxo. O `docs/compatibilidade.md` ganha, antes de `## Matriz`, a seção `## Nível de suporte` com a tabela `| CLI | Nível | O que significa |` (quatro linhas) e a lista `Pendências do dono`, com o aceite das Fases 8 e 9 em sessão real no Codex (notas 14 e 15: hoje a prova é de build). Entrada `### SC-204:` no `DECISIONS.md` (**Problema**, **Decisão**, **Motivo**, **Por que não é bug**) e linha no `CHANGELOG.md` `[Unreleased]`.

## Checks
**Build**: `python tools/build.py --check`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - O README não diz mais "com os 4 CLIs suportados" e traz os três níveis com o CLI de cada um e a linha do que cada nível significa
Proof: run unit | test_readme_niveis (test_paridade_declarada.ParidadeDeclaradaTests.test_readme_niveis) ... ok

**C2** - A matriz tem `## Nível de suporte` antes de `## Matriz`, a tabela com as quatro linhas exatas e a pendência do dono das Fases 8 e 9 no Codex
Proof: run unit | test_matriz_niveis (test_paridade_declarada.ParidadeDeclaradaTests.test_matriz_niveis) ... ok

**C3** - Entrada `### SC-204:` com os quatro campos, citando a D-d, os três níveis e os testes, e a linha no CHANGELOG
Proof: run unit | test_decisions_paridade (test_paridade_declarada.ParidadeDeclaradaTests.test_decisions_paridade) ... ok

## Handoff

**Phase:** pr-review
**Size:** SMALL
**Git mode:** 3
**Next:** publicar r1, push do review, merge (confirmação)
**Linear:** SC-204
**Integration branch:** feature/paridade-declarada
**Last integrated:** 2a31040
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** 2026-11-19: provas e done --strict verdes; Q dispensado (PEQUENA); 2026-11-19: PR aberto; 2026-11-19: Worf r1 APPROVE (sem achados)
**Breaker:** closed
