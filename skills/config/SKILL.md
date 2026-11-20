---
name: config
description: StarCode crew model config. Use when the user wants to choose or change which AI model or CLI each StarCode crew member uses, for all projects or only this repository, wants advice on a model (Muse Spark, GLM, Kimi, OpenRouter...), or says they do not have some subscription ("configurar os agentes", "trocar o modelo do LaForge", "qual modelo cada agente usa", "usar o Kimi neste projeto", "não tenho ChatGPT/Codex", "não tenho Gemini", "starcode config"), and when the StarCode setup reaches its user config step. Asks which CLIs the user has, analyzes each model they name from the models.dev catalog, proposes a model per crew member by role and cost, and writes the config through the validator after confirmation. Never invents a model ID. Not for the repository setup (Linear, labels), which is setup.
---

# StarCode: config (modelos da tripulação)

Plugin root: `<plugin-root>` in this skill means {{PLUGIN_ROOT}}. Run by the Picard. All output to the user
is PT-BR. Field reference: `<plugin-root>/schemas/config.md`. Models are personal (what **this user** can
run), so they live in one of two files, never in the versioned repo config:

| Escopo | Arquivo | Vale para |
|---|---|---|
| Todos os projetos | `~/.starcode/config.json` (`STARCODE_HOME` overrides the folder) | every repository |
| Só este repositório | `<repo>/.starcode/config.local.json` (fora do Git) | this repository; wins over the global one |

Follow the steps in this order.

## 1. Current state
Run `python "<plugin-root>/scripts/setup_helpers.py" crew-table` and show the table as is (the `Efetivo`
column says whether a value comes from the global or the local config).

## 2. What the user has (one message)
Run `python "<plugin-root>/scripts/setup_helpers.py" clis` and ask, in **one message**:
1. Which of these the user can actually use (a CLI on the PATH is not proof of a subscription), pre-marking
   the ones found: `claude` (Claude), `codex` (ChatGPT), `antigravity` (Gemini), `opencode` (paid or free
   models from many providers: Muse Spark, GLM, Kimi, OpenRouter...).
2. For `opencode` (and any CLI whose models are not in `src/crew.yaml` `families`): which model IDs they want
   to consider, exactly as `opencode models` (or `agy models`) lists them, e.g. `zai/glm-5.3`. For Codex there
   is no confirmed listing command, so ask. **Never invent a model ID.**
3. The scope: **todos os projetos** or **só este repositório** (recommend "só este" when they speak of a
   model for this project, otherwise "todos").

Then stop and wait.

## 3. Analyze each model the user named
Run once with all the IDs the user gave:

    python "<plugin-root>/scripts/model_info.py" --cli <cli> <id> [<id> ...]

It reads the public models.dev catalog (cached for 7 days) and prints, per model: vendor family, cost tier,
price per 1M tokens, context window, tool calling, reasoning, a description and a fixed verdict per role
group (✅ ok, ⚠️ aviso, ⛔ vetado). Show the cards as printed, then **your guidance** in at most 5 lines,
grounded only on the cards:
- ⛔ vetado (no tool calling) is final: never propose that model for any crew member.
- Place each model where its tier fits: `$$$` for the heavy reasoning roles, `$$` for execution, `$` or
  `grátis` for the repetitive ones; a cheaper model in a heavier role is a trade-off the user must accept.
- For the Q, prefer a model whose **family differs from the LaForge's**; same family = degraded verification.
- Say which model you would use for which role and why, in one line each.

Exit 1 (some ID not in the catalog): say so for that ID and ask the user for its tier (`grátis`, `$`, `$$`,
`$$$`); it then goes to step 4 as `<cli>=<id>@<tier>`. Exit 3 (no network and no cache): same, for every ID.

## 4. Suggestion
Run (quote each `--model`, the tier has `$`):

    python "<plugin-root>/scripts/setup_helpers.py" suggest --have <cli1,cli2> [--model '<cli>=<id>[@<tier>]' ...]

Show the table and the notes as printed, then this guide in at most 4 lines:
- Raciocínio pesado (Picard, Spock, McCoy, Worf): o melhor modelo que você tem (`$$$`).
- Execução (Troi, Data, LaForge, Scotty, Kirk): modelo intermediário (`$$`).
- Tarefas repetitivas e rápidas (Uhura, Guinan): o mais barato (`$`, ex.: Haiku ou Gemini Flash).
- Q: outra família de modelo que a do LaForge; sem outra família, a verificação fica degradada.

Ask: aceitar a proposta inteira ou trocar linhas (`<tripulante> = <cli>:<modelo>`). A model not analyzed in
step 3 goes through `model_info.py` before it is accepted; a ⛔ verdict blocks it.

## 5. Optional keys (global scope only, and only if the user asks)
`outputLanguage` (pt-BR | en), `qStrategy` (orca-worker, self-verified),
`fleet.maxBatch` (1–10), `fleet.timeoutMinutes`, `fleet.workers` (list of `<cli>:<model>`). The local file
holds only `crew`.
The local entry takes `cli` and `model` together: the validator refuses an entry with only one of them. The local
file also applies in linked worktrees: a worktree without its own file reads the main worktree's.

## 6. Write
1. Build the final JSON for the chosen scope:
   - **Todos os projetos:** start from the current `~/.starcode/config.json` when it exists and is valid
     (keep every key the user did not change) and replace its `crew` with the `crew` of the accepted
     proposal (only the differences from `src/crew.yaml`; no `crew` key when nothing differs). With no file
     yet, the result is at least `{"schemaVersion": 1}`: the first run creates the file and marks the
     machine as set up, so "manter os padrões" is not a reason to skip writing it.
   - **Só este repositório:** `{"schemaVersion": 1, "crew": {...}}` with only the members that must differ
     **from the global config** in this repository. Nothing differs: remove the local file instead (ask).
2. Show the JSON and ask for confirmation.
3. Write it only through the validator, from a temporary file:
   - global: `python "<plugin-root>/scripts/config/validate_config.py" --kind user --write "<home>/.starcode/config.json" --from <tmp>`
   - local: `python "<plugin-root>/scripts/config/validate_config.py" --kind local --write "<repo>/.starcode/config.local.json" --from <tmp>`
     (the validator also lists the file in `<repo>/.starcode/.gitignore`, so it never reaches Git).
   A validator error: show it, fix the JSON with the user and try again. Never write the file by hand.
4. Run `crew-table` again and show it. Say in one line that the change applies to the next crew member
   started or dispatched; members already running keep their model until they finish.

## Never
- Invent a model ID, a price or a tier, or assume a subscription the user did not confirm.
- Propose a ⛔ vetado model.
- Put `crew` in the versioned repo config (`<repo>/.starcode/config.json`).
- Put a secret, token or API key in any config.
