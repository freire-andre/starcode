# Créditos

O StarCode é privado ("All rights reserved", ver `LICENSE`). Os itens abaixo são de terceiros e mantêm as próprias licenças. Cada arquivo adaptado recebe uma linha nesta tabela quando entrar no repositório.

| Origem | Licença | Uso no StarCode | Arquivos |
|---|---|---|---|
| tlc-spec-driven 4.1.0 (Felipe Rodrigues, github.com/felipfr) | CC-BY-4.0 | Base dos gates e das práticas de spec/tasks/retomada, adaptada (D24, D25, ADR-0002) | `scripts/gates/gates_common.py`, `validate_spec.py`, `validate_tasks.py`, `check_commit.py`, `check_proofs.py`, `validate_verification.py` (Fase 3); práticas reescritas em `skills/troi`, `skills/spock`, `skills/data`, `skills/q`, `src/briefs/q-verify.md` (a partir do `references/validate.md`), `skills/engajar/references/state-format.md`; Fase 9: `scripts/lessons.py` (adaptado do `lessons.py`, com o sinal `review_finding` novo) e a tabela de lições em `skills/guinan/` |
| mattpocock/skills | MIT | Fluxo de trabalho de referência (D5); categorias da skill `retro` adaptadas na Guinan (Fase 9) | a partir da Fase 2; `skills/guinan/references/retro.md` |
| the-judge 1.4.0 (Felipe Rodrigues) | CC-BY-4.0 | Gates do review do Worf, adaptados (formato `review.json`, só stdlib) | `scripts/review/review_gate.py`, `post_review.py`, `scan_bypasses.py`; `skills/worf/` |
| harness-eval 1.8.3 (Tech Leads Club) | CC-BY-4.0 | Track A e protocolo do diagnóstico, copiados com ajuste de UTF-8 | `scripts/harness/` (`doc_scope.py`, `inventory_extract.py`, `merge_agreement.py`, `merge_usefulness.py`, `slim_fanin.py`, `surfaces_extract.py`, `track_a_correctness.py`, `references/`) |
| Cloudflare security-audit-skill | MIT | Portão de evidência dos achados de segurança do Worf (inspiração, reescrito) | `scripts/review/review_gate.py`, `skills/worf/references/security-evidence.md` |
| harness-score | executado via `npx`, não copiado (versão fixada no script) | Pontuação de maturidade do diagnóstico | `scripts/diagnostico.py` |
| superpowers | MIT | Práticas genéricas, escritas do zero (tabela "desculpa × realidade") | `skills/engajar/references/gate-excuses.md` |

Star Trek e os nomes dos personagens pertencem aos seus donos. O StarCode só usa os nomes como apelidos dos papéis, sem nenhuma afiliação.

Material de terceiros com licença que proíbe reuso (por exemplo, o plugin Genesis) **não** é copiado, parafraseado nem incorporado.
