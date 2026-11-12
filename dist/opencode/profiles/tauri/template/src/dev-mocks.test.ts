import { describe, expect, it } from "vitest";
import { handleCommand } from "./dev-mocks";

describe("handleCommand", () => {
  it("responde greet como o comando Rust", () => {
    expect(handleCommand("greet", { name: " Ana " })).toBe("Olá, Ana!");
  });

  it("responde greet vazio com o mundo", () => {
    expect(handleCommand("greet", { name: "  " })).toBe("Olá, mundo!");
  });

  it("ignora comando desconhecido", () => {
    expect(handleCommand("outro", {})).toBeUndefined();
  });
});
