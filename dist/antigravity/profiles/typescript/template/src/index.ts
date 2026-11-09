export function greeting(name: string): string {
  const who = name.trim() || "mundo";
  return `Olá, ${who}!`;
}
