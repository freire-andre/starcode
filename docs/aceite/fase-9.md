# Aceite da Fase 9 (SC-113): Worf, Guinan e diagnóstico

Executado em 2026-11-09 com os scripts de `dist/claude` do ramo de integração `feature/fase-9-worf-guinan-diagnostico` em `022a690`. O PR de teste é aberto pelo Picard (push e PR exigem a confirmação do usuário) e fechado sem merge no fim; o ramo `teste/worf-bypass` não entra no ramo de integração.

## Varredura do bypass

**Resultado**: aprovado

Ramo local `teste/worf-bypass` (commit `456b371`, sem push), a partir de `022a690`, com `tests/fixtures/review/planted/planted_bypass.py` (`verify=False` numa chamada HTTP e `@unittest.skip` sem justificativa).

Comando: `git diff 022a690...teste/worf-bypass | python dist/claude/scripts/review/scan_bypasses.py`

```
tests/fixtures/review/planted/planted_bypass.py:8	tls-bypass	return requests.get(url, verify=False)
tests/fixtures/review/planted/planted_bypass.py:12	test-dodge	@unittest.skip("")
scan: 2 candidate(s)
```

## Review do PR de teste

**Resultado**: aprovado

PR rascunho #22 (https://github.com/freire-andre/starcode/pull/22), `teste/worf-bypass` (`456b371`) → `feature/fase-9-worf-guinan-diagnostico`. Review do Worf, rodada 1, por claude · claude-opus-5-5, seguindo `dist/claude/skills/worf`.

- Escada determinística no head: `build.py --check`, `check_decisions.py` e `claude plugin validate dist/claude --strict` com exit 0; `python -m unittest discover -s tests` com exit 0 e 571 testes.
- Varredura: 2 candidatos; os 2 viraram achados.
- Pesquisa: Context7 `/websites/requests_readthedocs_io` e https://requests.readthedocs.io/en/latest/user/advanced/.
- `review_gate.py docs/aceite/fase-9-pr22/review.json`: exit 0.
- **Veredito**: REQUEST_CHANGES.

| ID | Severity | Where | Finding |
|---|---|---|---|
| W1 | 🔴 blocker | tests/fixtures/review/planted/planted_bypass.py:8 | `tls-bypass`: `verify=False` sem justificativa nem issue |
| W2 | 🟠 should-fix | tests/fixtures/review/planted/planted_bypass.py:12 | `test-dodge`: `@unittest.skip("")` sem motivo nem issue |

Arquivos: `docs/aceite/fase-9-pr22/review.json` e `docs/aceite/fase-9-pr22/review.md`.

## Publicação e fallback COMMENT

**Resultado**: aprovado

Publicado com a confirmação do usuário em 2026-11-09 ("Sim, publicar"): `post_review.py review.json --pr 22 --review-md review.md`, exit 0.

- Review: https://github.com/freire-andre/starcode/pull/22#pullrequestreview-5831172888
- Estado no GitHub: `COMMENTED` (autor do PR = usuário do `gh`), com 2 comentários inline (linhas 8 e 12).
- O corpo termina com `Veredito pretendido: REQUEST_CHANGES (o GitHub não aceita REQUEST_CHANGES no próprio PR)`.
- O `review.md` ganhou `**Posted**: 2026-11-09 - https://github.com/freire-andre/starcode/pull/22#pullrequestreview-5831172888`.

## Lição registrada

**Resultado**: aprovado

A Guinan rodou depois do `done` (`ad12592`): `scripts/lessons.py` gravou 3 lições candidatas em `.specs/lessons.json` e `.specs/LESSONS.md`. Todas vêm de achados reais do Q e das provas. A retro está em `.specs/features/fase-9-worf-guinan-diagnostico/retro.md`, com 7 sugestões.

- L1 (`weak_test`, `scripts/review`): exigir string não vazia após strip (fonte: `scripts/review/review_gate.py:72`).
- L2 (`weak_test`): comparar a linha exata no teste (fonte: `tests/test_review_post.py`, `tests/test_acceptance_doc_f9.py`).
- L3 (`gate_fail`): registrar a decisão no `DECISIONS.md` no mesmo ciclo (fonte: `proofs.md`, `check_decisions` após `9e7679a`).

## Relatório L0–L4

**Resultado**: aprovado

Comando: `python dist/claude/scripts/diagnostico.py run --root .` (exit 0).

- **Nível**: L0 · Unharnessed
- **Pontuação**: 44/105
- **Relatório**: `docs/diagnostico/2026-11-09.md`
- **Track A**: 0 quebrados; Tracks B/C não executados (sem aprovação de custo).
