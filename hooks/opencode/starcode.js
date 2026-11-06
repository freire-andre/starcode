// StarCode guard plugin for OpenCode (V2 plugin API).
// No package import (only the node: builtin): an unresolved import makes OpenCode skip the plugin silently.
// install_local replaces the STARCODE_ROOT placeholder with the absolute plugin path.
import { spawnSync } from "node:child_process"

const STARCODE_ROOT = "{{STARCODE_ROOT}}"
const GUARDS = ["git_guard.py", "secret_scan.py"]

function warn(message) {
  process.stderr.write(`StarCode hook: ${message}\n`)
}

// Returns the deny reason, or null to let the command through (also when the guard itself fails).
function runGuard(script, command) {
  const payload = JSON.stringify({ tool_input: { command }, cwd: process.cwd() })
  const res = spawnSync("python", [`${STARCODE_ROOT}/hooks/scripts/${script}`], {
    input: payload, encoding: "utf8", timeout: 30000, windowsHide: true,
  })
  if (res.error) { warn(`${script} did not run (${res.error.message}); command allowed`); return null }
  if (res.status !== 0) { warn(`${script} exited with code ${res.status}; command allowed`); return null }
  const out = (res.stdout || "").trim()
  if (!out) return null
  let parsed
  try { parsed = JSON.parse(out) } catch { warn(`${script} returned invalid JSON; command allowed`); return null }
  const hso = parsed && parsed.hookSpecificOutput
  if (hso && hso.permissionDecision === "deny") return String(hso.permissionDecisionReason || "blocked by StarCode")
  return null
}

export default {
  id: "starcode",
  async setup(ctx) {
    await ctx.tool.hook("execute.before", (event) => {
      const command = event && event.input && event.input.command
      if (typeof command !== "string") return
      for (const script of GUARDS) {
        const reason = runGuard(script, command)
        if (reason !== null) throw new Error(reason)
      }
    })
  },
}
