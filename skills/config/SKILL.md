---
name: config
description: StarCode crew model config. Use when the user wants to choose or change which AI model or CLI each StarCode crew member uses, or says they do not have some subscription ("configurar os agentes", "trocar o modelo do LaForge", "qual modelo cada agente usa", "não tenho ChatGPT/Codex", "não tenho Gemini", "starcode config"), and when the StarCode setup reaches its user config step. Asks which CLIs the user has, proposes a model per crew member by role and cost, and writes ~/.starcode/config.json through the validator after confirmation. Never invents a model ID. Not for the repository setup (Linear, labels), which is setup.
---

# StarCode: config (modelos da tripulação)

Plugin root: `<plugin-root>` in this skill means {{PLUGIN_ROOT}}. Run by the Picard. All output to the user
is PT-BR. The user config lives in `~/.starcode/config.json` (`STARCODE_HOME` overrides the folder), is
never versioned and is personal: it says what **this user** can run. Field reference:
`<plugin-root>/schemas/config.md`.

Follow the steps in this order.

## 1. Current state
Run `python "<plugin-root>/scripts/setup_helpers.py" crew-table` and show the table as is.

## 2. What the user has (one message)
Run `python "<plugin-root>/scripts/setup_helpers.py" clis` and ask, in **one message**, which of these the
user can actually use (a CLI on the PATH is not proof of a subscription), pre-marking the ones found:
- `claude` (assinatura Claude / Anthropic)
- `codex` (assinatura ChatGPT / OpenAI)
- `antigravity` (Google / Gemini)
- `opencode` (OpenRouter ou outro provedor; modelos grátis entram aqui)

In the same message, for each CLI the user has and whose models are not in `src/crew.yaml` `families`,
ask which model IDs they want to use. To list models: `agy models`, `opencode models`; for Codex there is
no confirmed listing command, so ask. **Never invent a model ID.** Then stop and wait.

## 3. Suggestion
Run:

    python "<plugin-root>/scripts/setup_helpers.py" suggest --have <cli1,cli2> [--model <cli>=<id> ...]

Show the table and the notes as printed, then this guide in at most 4 lines:
- Raciocínio pesado (Picard, Spock, McCoy, Worf): o melhor modelo que você tem (`$$$`).
- Execução (Troi, Data, LaForge, Scotty, Kirk): modelo intermediário (`$$`).
- Tarefas repetitivas e rápidas (Uhura, Guinan): o mais barato (`$`, ex.: Haiku ou Gemini Flash).
- Q: outra família de modelo que a do LaForge; sem outra família, a verificação fica degradada.

Ask: aceitar a proposta inteira ou trocar linhas (`<tripulante> = <cli>:<modelo>`). A change to a model
not offered by the user in step 2 needs the user to confirm the exact ID.

## 4. Optional keys (only if the user asks)
`outputLanguage` (pt-BR | en), `qStrategy` (opencode-subagent, orca-worker, self-verified),
`fleet.maxBatch` (1–10), `fleet.timeoutMinutes`, `fleet.workers` (list of `<cli>:<model>`).

## 5. Write
1. Build the final JSON: start from the current `~/.starcode/config.json` when it exists and is valid
   (keep every key the user did not change), replace its `crew` with the `crew` of the accepted proposal
   (only the differences from `src/crew.yaml`; no `crew` key when nothing differs). With no file yet,
   the result is at least `{"schemaVersion": 1}`: the first run creates the file and marks the machine as
   set up, so "manter os padrões" is not a reason to skip writing it.
2. Show the JSON and ask for confirmation.
3. Write it only through the validator, from a temporary file:
   `python "<plugin-root>/scripts/config/validate_config.py" --kind user --write "<home>/.starcode/config.json" --from <tmp>`.
   A validator error: show it, fix the JSON with the user and try again. Never write the file by hand.
4. Run `crew-table` again and show it. Say in one line that the change applies to the next crew member
   started or dispatched; members already running keep their model until they finish.

## Never
- Invent a model ID or assume a subscription the user did not confirm.
- Touch the repo config (`<repo>/.starcode/config.json`): models are personal, they live only in the user config.
- Put a secret, token or API key in any config.
