import { describe, expect, it } from "vitest";
import { normalizeName } from "./greeting";

describe("normalizeName", () => {
  it("remove espaços nas pontas", () => {
    expect(normalizeName("  Ana ")).toBe("Ana");
  });

  it("mantém o nome vazio como vazio", () => {
    expect(normalizeName("   ")).toBe("");
  });
});
