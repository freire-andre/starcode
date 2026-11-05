# Linear publication (plan 5.0, D2, D13)

Rules from `<plugin-root>/skills/engajar/references/linear-contract.md` apply. Team, workspace and the
exact state names come from `.starcode/config.json` (`linear.team`, `linear.workspace`,
`linear.states.unstarted`). If the repo config is missing, stop and recommend `{{CMD:setup}}`.

## 1. Plan, shown with the tasks (one message, F2-9)

    python "<plugin-root>/scripts/gates/tasks_export.py" plan <slug>

It writes one body file per task (the 5-block briefing) to a temp folder and prints the plan. Before
any write, check duplicates:
- Project: `orca linear project list --query "<feature name>" --workspace <workspace> --json` (or the
  Linear MCP project search).
- Issues: `orca linear search "<feature name>" --workspace <workspace> --json`.

The plan goes in the **same message** as the tasks summary (Data skill, step 3): Project name and team,
Document title (`Spec: <feature>`), issue count with state (`linear.states.unstarted`) and label
`crew:data`, the number of `blocks` relations, and any duplicate found (recommendation: reuse it). The
single question "Aprovo as tasks e publico no Linear? (sim / só aprovar / ajustes)" covers approval 2
and this confirmation. No answer, "só aprovar", or anything but a yes means nothing is written.

## 2. Writes, in order (only after the yes)

1. **Project** via the Linear MCP project tool (e.g. `save_project`): name = feature title, team = the
   repo team, description = Context of the spec in 2–3 lines + repo path of the spec. Reuse an existing
   project if the user chose to.
2. **Document** via the Linear MCP document tool (e.g. `save_document`): parent = the project,
   title `Spec: <feature>`, content = spec.md as is. If the MCP is unavailable, say so: the spec stays only
   in `.specs/` and the repo path goes in the project description (fallback in plan 5.0).
3. **Issues** via `orca linear` (run `orca skills get orca-linear` and `orca linear create --help` first):

        orca linear create --title "<T1: title>" --body-file "<body file>" --team <team> \
          --project "<project name or id>" --state "<linear.states.unstarted>" --label "crew:data" --json

   One per task, in task order. Keep each returned identifier.
4. **Relations**: for each `blocker → blocked` in the plan:

        orca linear relation add <blocker ID> --related <blocked ID> --type blocks --json

5. **Record** the IDs in tasks.md and gate it:

        python "<plugin-root>/scripts/gates/tasks_export.py" record <slug> T1=<ID> T2=<ID> ...
        python "<plugin-root>/scripts/gates/run_gates.py" publish <slug>

6. Comment once on the project or first issue only if useful; never paste secrets.

## Failures

- A write that fails: stop there, report the exact command and error, and list what was already created
  (with IDs) so nothing is created twice on retry. `orca linear create` may return `--write-id` for an
  unconfirmed write: retry with it, never with a fresh create.
- MCP not available for the Project: show the fields for the user to create it by hand and continue
  with the issues without a project, after saying so.
- A state name rejected by the CLI: stop and recommend `{{CMD:setup}}` (the mapping is stale).
