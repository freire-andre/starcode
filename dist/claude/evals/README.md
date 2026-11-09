# Evals do StarCode

Rodados com `claude plugin eval` contra o plugin gerado (`dist/claude`). O `tools/build.py` copia esta
pasta para `dist/claude/evals/`; os resultados ficam em `dist/claude/evals/results/` (fora do Git).

| Suíte | Casos | Aceite (Fase 1) |
|---|---|---|
| `risk-sizing/` | 12 tarefas com a classe esperada (tag `trigger`: 8 com gatilho de risco; `no-trigger`: 4) | 100% dos casos `trigger` (nunca PEQUENA) e ≥90% no total |
| `routing/` | 33 frases: 20 que devem disparar `engajar`/`setup`/`troi`/`spock`/`data`/`laforge`/`mccoy`/`q`/`uhura`/`scotty`/`nova-missao`/`worf`/`guinan`/`diagnostico` e 13 que não devem disparar nenhuma skill do StarCode | todas passam (Fases 1, 2, 3, 8 e 9) |

Fase 9: 9 casos novos de roteamento em `routing/` (R33), 2 positivos e 1 negativo por skill:

| Skill | Positivos | Negativo |
|---|---|---|
| `worf` | `pos-worf-review-pr`, `pos-worf-security` | `neg-worf-fix-code` |
| `guinan` | `pos-guinan-lessons`, `pos-guinan-retro` | `neg-guinan-review-pr` |
| `diagnostico` | `pos-diagnostico-harness`, `pos-diagnostico-level` | `neg-diagnostico-setup` |

```
python tools/build.py
claude plugin eval dist/claude --tag risk-sizing --ablation none --trust-plugin --no-publish
claude plugin eval dist/claude --tag routing --ablation none --trust-plugin --no-publish
```

`--ablation none` é necessário nos evals de roteamento: no modo com/sem plugin, um grader
`tool_used: Skill` vira só indicador e não conta na nota.
