# AGENTS.md, CLAUDE.md e README: Context

**Size**: SMALL
**Risk triggers**: none
**Source request**: "proximo passo" (itens 1.5 e 1.7 da triagem v2; aprovação: "Sim (Recomendado)")
**Linear**: SC-189
**May change**: AGENTS.md, CLAUDE.md, README.md, docs/diagnostico/

## Inline checks
1. `AGENTS.md` na raiz, em PT-BR e curto (até ~60 linhas), com estes itens:
   - os comandos de build e teste do CI (`python tools/build.py --check`, `python -m unittest discover -s tests -v`, `python scripts/check_decisions.py`, `claude plugin validate dist/claude --strict`);
   - a regra do `dist/`: gerado por `python tools/build.py`, nunca editado à mão, fonte em `skills/`, `scripts/`, `hooks/`, `src/`;
   - a regra do `DECISIONS.md` (D30): toda mudança em `skills/`, `scripts/` ou `hooks/` ganha uma entrada no mesmo commit ou depois, e o `check_decisions.py` confere isso;
   - a regra "toda mudança passa pelo fluxo StarCode (`/starcode:engajar`) e ganha decisão";
   - o estilo de commit: tipo convencional, assunto em minúsculas e PT-BR, `Refs SC-<n>`;
   - a limitação: `orca plugin test`/`check` só roda com o plugin no mesmo drive da instalação da Orca (retro `ponte-missao-ativa`, item 1).
2. `CLAUDE.md` na raiz com uma linha de import `@AGENTS.md` e nada que repita o conteúdo.
3. `README.md:6`: a linha de estado diz **v1.8.0** no lugar de **v1.0**, sem mudar o resto do parágrafo.
4. `python scripts/diagnostico.py run`, com o resultado gravado em `docs/diagnostico/<data>.md`. Se o `npx` falhar, registre a falha no relatório e não invente pontuação.
5. A suíte inteira, `python tools/build.py --check` e `python scripts/check_decisions.py` passam.

## Handoff

**Phase:** execute
**Size:** PEQUENA
**Git mode:** 3
**Next:** LaForge implementa (SC-189)
**Linear:** SC-189
**Integration branch:** feature/agents-readme
**Last integrated:** none
**Dispatched:** T1 · SC-189 · base 2384af8 · claude:claude-sonnet-5-5 · 2026-11-17T10:59:51Z · ctx_572763709288
**Settled:** 2026-11-17: issue + despacho: "Sim (Recomendado)"
**Attempts:** none
**Reports:** none
**Breaker:** closed
