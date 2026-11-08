// StarCode guard plugin for OpenCode (V2 plugin API).
// No package import (only the node: builtin): an unresolved import makes OpenCode skip the plugin silently.
// install_local replaces the STARCODE_ROOT placeholder with the absolute plugin path.
import { spawnSync } from "node:child_process"

const STARCODE_ROOT = "{{STARCODE_ROOT}}"
const GUARDS = ["git_guard.py", "secret_scan.py"]

function warn(message) {
  process.stderr.write(`StarCode hook: ${message}\n`)
}

// SC-86: OpenCode moves process.cwd() away from the project; the project folder is ctx.location.directory.
let projectDir = null

function pickDir(workdir) {
  if (typeof workdir === "string" && workdir) return workdir
  if (projectDir) return projectDir
  return process.cwd()
}

// Returns the deny reason, or null to let the command through (also when the guard itself fails).
function runGuard(script, command, workdir) {
  const cwd = pickDir(workdir)
  const payload = JSON.stringify({ tool_input: { command }, cwd })
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

const CREW_ORDER = "Comece sua próxima resposta ao usuário com este cabeçalho, sem mudar nada:\n"

function sessionOf(event) {
  const e = event || {}
  return e.sessionID || e.sessionId || (e.session && e.session.id) || (e.input && (e.input.sessionID || e.input.sessionId)) || null
}

// F7-16: sends the normalized event to crew_hook.py and returns the header it prints, or null. Never throws.
function runCrew(payload) {
  try {
    const cwd = pickDir(payload.cwd)
    const res = spawnSync("python", [`${STARCODE_ROOT}/hooks/scripts/crew_hook.py`, "--cli", "opencode"], {
      input: JSON.stringify({ ...payload, cwd }), encoding: "utf8", timeout: 10000, windowsHide: true,
    })
    if (res.error || res.status !== 0) return null
    const out = (res.stdout || "").trim()
    if (!out) return null
    const parsed = JSON.parse(out)
    return parsed && typeof parsed.header === "string" && parsed.header ? parsed.header : null
  } catch { return null }
}

function crewEvent(ctx, event, name, extra) {
  try {
    const sid = sessionOf(event)
    if (!sid) return
    const header = runCrew({ event: name, session_id: sid, cwd: event && event.input && event.input.workdir, ...extra })
    if (header && ctx.session && typeof ctx.session.synthetic === "function") {
      const sent = ctx.session.synthetic({ sessionID: sid, text: CREW_ORDER + header, resume: false })
      if (sent && typeof sent.catch === "function") sent.catch(() => {})
    }
  } catch { /* a crew hook never blocks the tool nor the turn */ }
}

function register(call) {
  try {
    const p = call()
    if (p && typeof p.catch === "function") p.catch(() => {})
  } catch { /* hook registration is best effort */ }
}

export default {
  id: "starcode",
  async setup(ctx) {
    try {
      const dir = ctx && ctx.location && ctx.location.directory
      if (typeof dir === "string" && dir) projectDir = dir
    } catch { /* fall back to process.cwd() */ }
    await ctx.tool.hook("execute.before", (event) => {
      if (event && event.tool === "skill" && event.input && typeof event.input.id === "string") {
        crewEvent(ctx, event, "skill", { skill: event.input.id })
      }
      const command = event && event.input && event.input.command
      if (typeof command !== "string") return
      for (const script of GUARDS) {
        const reason = runGuard(script, command, event.input.workdir)
        if (reason !== null) throw new Error(reason)
      }
    })
    register(() => ctx.tool.hook("execute.after", (event) => { try { crewEvent(ctx, event, "pulse", {}) } catch { /* ignore */ } }))
    register(() => ctx.session.hook("prompt", (event) => { try { crewEvent(ctx, event, "prompt", {}) } catch { /* ignore */ } }))
    register(() => ctx.session.hook("experimental.idle", (event) => { try { crewEvent(ctx, event, "idle", {}) } catch { /* ignore */ } }))
  },
}
