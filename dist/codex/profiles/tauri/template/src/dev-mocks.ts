export function greet(args: unknown): string {
  const raw = (args as { name?: unknown } | undefined)?.name;
  const who = (typeof raw === "string" ? raw : "").trim();
  return who === "" ? "Olá, mundo!" : `Olá, ${who}!`;
}

export function handleCommand(cmd: string, args: unknown): unknown {
  if (cmd === "greet") return greet(args);
  return undefined;
}

export async function installDevMocks(): Promise<void> {
  const { mockIPC } = await import("@tauri-apps/api/mocks");
  mockIPC(handleCommand);
}
