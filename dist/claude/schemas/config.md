# StarCode config: field reference (schemaVersion 1)

Validated by `scripts/config/validate_config.py` (Python stdlib, D20). **Unknown key = error.** A
`schemaVersion` newer than the plugin blocks and asks for an update. A field never exists in both
levels: project settings live in the repo config, personal preferences in the user config. No secrets
in either file.

## User config: `~/.starcode/config.json` (not versioned; `STARCODE_HOME` overrides the folder)

| Key | Type | Required | Values |
|---|---|---|---|
| `schemaVersion` | integer | yes | `1` |
| `outputLanguage` | text | no | `pt-BR` (default), `en` |
| `crew` | object | no | keys: `picard`, `spock`, `troi`, `data`, `laforge`, `mccoy`, `q`, `uhura`, `scotty`, `kirk`, `worf`, `guinan`. Keep only what differs from `src/crew.yaml` |
| `crew.<member>.cli` | text | no | `claude`, `codex`, `antigravity`, `opencode` |
| `crew.<member>.model` | text | no | model ID accepted by that CLI (never invented) |
| `qStrategy` | list | no | ordered, unique, ≥1: `opencode-subagent`, `orca-worker`, `self-verified`. `opencode-subagent` is accepted but skipped by `q-cli` (not implemented yet) |
| `fleet.maxBatch` | integer | no | 1–10 (default 3, v1.1) |
| `fleet.timeoutMinutes` | integer | no | 1–1440 (default 30, v1.1) |
| `fleet.workers` | list of text | no | 1–10 unique `<cli>:<model>` items; `<cli>` is `claude`, `codex`, `antigravity` or `opencode`; the model may contain `/` and `:` (split at the first `:`), e.g. `opencode:openrouter/nvidia/x:free` |

```json
{
  "schemaVersion": 1,
  "outputLanguage": "pt-BR",
  "crew": {
    "laforge": { "cli": "claude", "model": "claude-opus-5-5" },
    "q": { "cli": "opencode", "model": "<id confirmado pelo setup>" }
  },
  "qStrategy": ["opencode-subagent", "orca-worker", "self-verified"],
  "fleet": { "maxBatch": 3, "timeoutMinutes": 30, "workers": ["claude:claude-sonnet-5-5", "opencode:openrouter/nvidia/x:free"] }
}
```

## Local config: `<repo>/.starcode/config.local.json` (not versioned)

Personal crew models for **this repository only** (e.g. a paid OpenCode model in one project). It wins over
the user config, member by member. `validate_config.py --kind local --write` also adds `config.local.json` to
`<repo>/.starcode/.gitignore`. Written by `/starcode:config`.

| Key | Type | Required | Values |
|---|---|---|---|
| `schemaVersion` | integer | yes | `1` |
| `crew` | object | no | same keys and entries as the user config `crew` |

Precedence of a crew member's cli/model: session override (Handoff) > local config > user config > `src/crew.yaml`.

## Repo config: `<repo>/.starcode/config.json` (versioned)

| Key | Type | Required | Values |
|---|---|---|---|
| `schemaVersion` | integer | yes | `1` |
| `linear.workspace` | text | yes | workspace id (from `orca linear team list --json`) |
| `linear.team` | text | yes | team key or id |
| `linear.states.unstarted` | text | yes | exact state name |
| `linear.states.started` | text | yes | exact state name |
| `linear.states.review` | text or null | yes | exact state name, or `null` if the team has none |
| `linear.states.completed` | text | yes | exact state name |
| `linear.states.blocked` | text or null | yes | exact state name, or `null` |
| `linear.states.verifiedAt` | date | yes | `YYYY-MM-DD`, when the mapping was checked |
| `baseBranch` | Git branch name | yes | e.g. `main` |
| `stack` | list | no | unique: `python-flask`, `rust`, `tauri`, `typescript`, `postgresql`, `mysql` |
| `sensitiveFiles` | list | no | extra path patterns that make a ticket run alone (Fleet, v1.1) |

```json
{
  "schemaVersion": 1,
  "linear": {
    "workspace": "<id>",
    "team": "SC",
    "states": {
      "unstarted": "Todo",
      "started": "In Progress",
      "review": null,
      "completed": "Done",
      "blocked": null,
      "verifiedAt": "2026-11-03"
    }
  },
  "baseBranch": "main",
  "stack": ["python-flask", "postgresql"]
}
```

## Session state (not a config)
`<git-dir>/starcode/session.json` holds the Git mode of the worktree (`scripts/git_mode.py`). It lives
inside the Git directory, so it is never committed and each worktree has its own.
