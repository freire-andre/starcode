# Retro: the 7 categories

Adapted from the `retro` skill of mattpocock/skills (MIT, https://github.com/mattpocock/skills).

Read the feature's commits, the Handoff of `tasks.md`, `verification.md`, `proofs.md` and `review.md`. Look for
friction, then name the cheapest change that would have removed it. Each suggestion belongs to one category:

1. **navigation**: the agent wandered to find where things live; propose a map, an index or a rename.
2. **automatic checks**: a mistake a linter, type check or test could have caught; propose the check.
3. **reviewer rules**: a recurring Worf finding that a standing rule would prevent; propose the rule.
4. **AGENTS/CLAUDE.md**: a convention missing, stale or wrong in the repo instructions; propose the line.
5. **tool economy**: many calls or a large read for a small answer; propose a script, a filter or a skill.
6. **instructions without effect**: an instruction that exists but was not followed; propose to cut it or to make it checkable.
7. **information access**: the agent lacked a fact (doc, decision, env detail) and guessed; propose where it should live.

Output `.specs/features/<slug>/retro.md`, in PT-BR:

```
# Retro: <slug>

| # | Severidade | Categoria | Evidência | Ação proposta | Estado |
|---|---|---|---|---|---|
| 1 | alta | <category> | <commit, Handoff line or finding ID> | <action, not applied> | aberto |
```

Rules: at most 7 rows; ordered by severity (alta, média, baixa); every row has evidence; at most one row per
friction; no row for a category without friction. The last column is `Estado`: Guinan writes `aberto` in every new row. Valid values: `aberto`, `aberto: <issue>`,
`feito em <commit>` and `recusado: <motivo>`. Only the user or the Picard changes it later, through
`python scripts/retros.py estado <slug> <n> (--feito <commit> | --recusado <motivo> | --aberto [<issue>])`;
`python scripts/retros.py abertas` lists the open ones. The suggestions are never applied and never become a lesson on
their own.
