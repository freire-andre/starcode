# Evals do StarCode

Rodados com `claude plugin eval` contra o plugin gerado (`dist/claude`). O `tools/build.py` copia esta
pasta para `dist/claude/evals/`; os resultados ficam em `dist/claude/evals/results/` (fora do Git).

| Suíte | Casos | Aceite (Fase 1) |
|---|---|---|
| `risk-sizing/` | 12 tarefas com a classe esperada (tag `trigger`: 8 com gatilho de risco; `no-trigger`: 4) | 100% dos casos `trigger` (nunca PEQUENA) e ≥90% no total |
| `routing/` | 24 frases: 14 que devem disparar `engajar`/`setup`/`troi`/`spock`/`data`/`laforge`/`mccoy`/`q`/`uhura`/`scotty`/`nova-missao` e 10 que não devem disparar nenhuma skill do StarCode | todas passam (Fases 1, 2 e 3) |

```
python tools/build.py
claude plugin eval dist/claude --tag risk-sizing --ablation none --trust-plugin --no-publish
claude plugin eval dist/claude --tag routing --ablation none --trust-plugin --no-publish
```

`--ablation none` é necessário nos evals de roteamento: no modo com/sem plugin, um grader
`tool_used: Skill` vira só indicador e não conta na nota.
