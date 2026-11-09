---
name: diagnostico
description: StarCode harness diagnosis. Use when the user asks for a harness diagnosis of a repository ("diagnóstico do harness", "nível L0–L4", "harness score", "qual o nível do meu harness", "diagnostique o harness"). Runs the maturity score and the deterministic Track A, writes docs/diagnostico/<data>.md, and offers the LLM judge Tracks B/C only after showing the cost estimate and getting approval for this run. Report only; never applies Ship or Slim. Not for configuring StarCode, setup or fixing code.
license: CC-BY-4.0
metadata:
  origin: Tracks B/C adapted from harness-eval (CC-BY-4.0); maturity score from harness-score
---

# Diagnóstico do harness

Plugin root: `<plugin-root>` in this skill means {{PLUGIN_ROOT}}. All output to the user is PT-BR.

## 1. Run (cheap, always)
Run `python "<plugin-root>/scripts/diagnostico.py" run` (add `--root <repo>` when the target is not the
current folder). It writes `docs/diagnostico/<data>.md`. Exit 2 means Track A failed: show the line
`track A falhou: <motivo>` and stop.

Show the result in at most **5 lines**: the level (L0–L4), the score (`earned/max`), the next step
(`Próximo degrau`), the Track A count of broken items and the report path. Nothing else.

## 2. Tracks B/C: cost approval (R29)
Tracks B (redundancy) and C (usefulness) spend model tokens. Never start them without approval.

1. Show the **estimate first**: the number of claims in `.harness-eval/runs/<run-id>/claims.jsonl`
   (count its lines) and that each track uses **2 judges** (2 × claims for B; 2 × surfaces for C, which
   costs the most).
2. Only then ask: `B`, `C`, `B+C` or `só A`.
3. The approval is valid **only for this run**. Never write it to any config, memory or file, and never
   reuse it in a later run: ask again every time.
4. No approval (or `só A`): the report keeps `não executados (sem aprovação de custo)` and you stop.

## 3. Judges
With approval, follow `references/judge-prompts.md`: two independent judges per track, the second blind,
each recording `model: <id>`, then merge with `scripts/harness/merge_agreement.py` (B),
`scripts/harness/merge_usefulness.py` (C) and check fan-in with `scripts/harness/slim_fanin.py`. Append
the outcome (trap gate, Ship/Review/Hold, Slim/Keep-core/Mixed/Hold, the model ids) to the same
`docs/diagnostico/<data>.md`, in PT-BR.

## 4. Never (R30)
Ship and Slim are **report only**. Never delete, stub, trim or rewrite any harness file because of them.
If the user wants to apply one, that is a separate task they ask for explicitly.
