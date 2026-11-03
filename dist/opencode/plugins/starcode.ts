// StarCode Phase 0 probe (OpenCode V2 plugin API).
// No import of "@opencode/plugin": an unresolved import makes OpenCode skip the plugin silently.
// The default export is the same object Plugin.define() would receive.
const MARKER = "STARCODE_BLOCK_TEST"

export default {
  id: "starcode.hello",
  async setup(ctx: any) {
    await ctx.tool.hook("execute.before", (event: any) => {
      const input = event.input as { command?: string }
      if (typeof input?.command === "string" && input.command.includes(MARKER)) {
        throw new Error("STARCODE-HOOK-BLOCKED: command blocked by StarCode probe hook")
      }
    })
  },
}
