# Execute: Ciclo pós-Q, review e texto do PR

Variables and preconditions: see `execute.md` (sections 0 and 1).

## 5. Post-Q cycle (4.6) and the end
- Open findings → **one** LaForge dispatch in the worktree of `I` with **all findings in one brief**,
  generated with `python "P/scripts/dispatch.py" fix-brief <slug> --out <file>` (open `Closed` rows of
  `verification.md`, the feature's `May change`, `## Lessons` and the fixed rules; exit 2 with
  `nada a corrigir: <slug> sem achados abertos` when none is open); each fix is a commit with `Refs: <ID>` citing the finding. Then close each finding with
  `python "P/scripts/dispatch.py" close-finding <slug> <n> --commit <sha> --cover <C<n>|test_name>` (no hand-editing of the `Closed` cell; it checks the commit and the coverage).
- Screens (R28): the `fix-brief` covers only the Q findings: the Picard adds the `differs` rows of `screens.md`, when it exists, to the same brief; when only screen divergences remain, `fix-brief` exits 2 and the Picard writes the brief by hand from `screens.md`. After the
  fix, dispatch the judge again with `dispatch.py screens-brief ... --round 2` (only the pictures and `differs` rows;
  there is no round 3). What still differs after round 2 goes to the user with the evidence.
- Rerun `run_gates.py proofs <slug>` and `run_gates.py done <slug>` on the new HEAD. **There is no second
  Q.** The Q is dispatched again only if a fix changes a requirement of the spec: then stop, propose the
  spec change, and dispatch the Q again only after the new approval.
- A finding still open after the cycle goes to the user with the finding and the evidence; the issues do
  not move to review.
- `run_gates.py done <slug>` green → the Picard invokes the Guinan (retro, `skills/guinan`; lessons go to
  `.specs/LESSONS.md`) **before the PR**; only then continue below (R20).
- `run_gates.py done <slug>` green → move the issues to the `review` state of the config or, without one,
  comment "pronto para revisão" with HEAD, the proofs result and the Q verdict.
- Degraded (`self-verified`, `degraded`, same family or mode 1) → comment "verificação degradada" with the
  reason on the issues; the banner shows `Verificação: degradada (<slug>)`.
- `completed` only with the user's explicit confirmation in this session, with `run_gates.py done` green,
  and **never in mode 1**. Modes 3/4: push and PR follow `git-modes.md` (each confirmed right before).
- **Modes 3/4:** right after the PR is open, `python "P/scripts/handoff.py" set <slug> --phase pr-review` (the
  feature is still in progress during the Worf rounds); `--phase done` comes only after the merge, or after the
  user's explicit refusal of the merge (section "Review (Worf)").
- **Modes 1/2 (no PR):** right after the Guinan, `--phase done` and
  `python "P/scripts/crew_live.py" progress <slug> --phase done` (100%).

## Review (Worf)
After opening the PR (modes 3/4) and before asking for the merge authorization, the Picard invokes the
Worf (`skills/worf`): on Claude, a subagent with the model from `crew.yaml`; on the other CLIs, the
session itself (R17).
- `REQUEST_CHANGES`, or `COMMENT` with an open `should-fix` → **one LaForge dispatch** with all open
  findings in a single brief, then the next Worf round.
- After each LaForge fix is integrated, run `python "P/scripts/gates/run_gates.py" proofs <slug>` and
  `python "P/scripts/gates/run_gates.py" done <slug>` on the new HEAD **before** the next Worf round.
- After each round record `python "P/scripts/handoff.py" set <slug> --report "Worf r<N> <verdict>"`.
- After round 3 with findings still open, the Picard stops and shows the findings and the evidence,
  without asking for the merge (R18).
- Publishing the review (PR comments) always needs the user's confirmation.
- **Lessons only.** When the last Worf round ends (APPROVE, or round 3) and `review.md` has a `blocker` or
  `should-fix` finding fixed or confirmed in any round, the Picard invokes the Guinan in lessons-only mode
  (`skills/guinan`): it records the `review_finding` lessons through `lessons.py` and does not rewrite
  `retro.md`. Without such a finding the Guinan is not invoked. Not on a PEQUENA (no Guinan there).
- **Commit the review and the lessons.** Before the merge is asked, commit on the PR branch `review.md`,
  `review.json` and the lessons (`.specs/lessons.json` and `.specs/LESSONS.md`) with the message
  `docs(specs): review e lições (<slug>)` and the `Refs` footer, and push with the user's confirmation
  (`git-modes.md`).
- Then, only when the last round leaves no `blocker` or `should-fix` open (a finding the user sent to a
  follow-up issue does not count as open), the merge authorization is asked
  (`git-modes.md`). `--phase done` is written only after the merge, or
  after the user's explicit refusal of the merge, and right then (modes 3/4 as well as 1/2) run
  `python "P/scripts/crew_live.py" progress <slug> --phase done` (100%).

## Text for the PR and the Linear comments (Uhura)
Whenever you open a PR or comment on Linear (start, integrated, blocked, cancelled, done), have the text
drafted by the `uhura` skill instead of writing it yourself, from `skills/uhura/references/pr-body.md` and
`skills/uhura/references/linear-comments.md`, handing it the facts (issue ID, diff summary, gate results,
Q verdict).
- **Claude:** a subagent with Uhura's model (`crew.yaml`) that follows the skill.
- **Other CLIs:** the session itself follows the skill.
In both cases Uhura returns text only: you confirm it and run `gh pr create` and `orca linear comment`
yourself, as `git-modes.md` requires.
