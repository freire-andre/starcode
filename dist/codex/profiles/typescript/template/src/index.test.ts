import { describe, expect, it } from "vitest";
import { greeting } from "./index";

describe("greeting", () => {
  it("cumprimenta pelo nome", () => {
    expect(greeting("Ana")).toBe("Olá, Ana!");
  });

  it("usa um valor padrão para nome vazio", () => {
    expect(greeting("  ")).toBe("Olá, mundo!");
  });
});
