/// <reference types="vite/client" />

import { beforeAll, describe, expect, it, vi } from "vitest";
import html from "../index.html?raw";

type Listener = (event: { preventDefault(): void }) => unknown;

const form = {
  listener: undefined as Listener | undefined,
  addEventListener(_type: string, fn: Listener) {
    form.listener = fn;
  },
};
const input = { value: "" };
const message = { textContent: "A saudação aparece aqui." };

async function saudar(nome: string): Promise<string> {
  input.value = nome;
  await form.listener?.({ preventDefault() {} });
  return message.textContent;
}

describe("tela de saudação", () => {
  beforeAll(async () => {
    const elements: Record<string, unknown> = {
      "#greet-form": form,
      "#greet-input": input,
      "#greet-msg": message,
    };
    vi.stubGlobal("window", {});
    vi.stubGlobal("document", { querySelector: (sel: string) => elements[sel] ?? null });
    await import("./main");
    await vi.waitFor(() => expect(form.listener).toBeDefined());
  });

  it("traz os textos do mockup", () => {
    const textoDe = (seletor: RegExp): string | undefined => {
      const m = html.match(seletor);
      return m?.[1]?.replace(/\s+/g, " ").trim();
    };
    expect({
      titulo: textoDe(/<h1>([\s\S]*?)<\/h1>/),
      instrucao: textoDe(/<p class="lead">([\s\S]*?)<\/p>/),
      rotulo: textoDe(/<label for="greet-input">([\s\S]*?)<\/label>/),
      placeholder: textoDe(/<input[^>]*\splaceholder="([^"]*)"/),
      botao: textoDe(/<button type="submit">([\s\S]*?)<\/button>/),
      mensagem: textoDe(/<p id="greet-msg" class="message">([\s\S]*?)<\/p>/),
      rodape: textoDe(/<footer class="footer">([\s\S]*?)<\/footer>/),
      barraSuperior: textoDe(
        /<header class="topbar">[\s\S]*?<span class="brand">([\s\S]*?)<\/span>/,
      ),
    }).toStrictEqual({
      titulo: "Saudação da Frota",
      instrucao: "Identifique-se para receber as boas-vindas.",
      rotulo: "Seu nome",
      placeholder: "Ex.: Jean-Luc",
      botao: "Saudar",
      mensagem: "A saudação aparece aqui.",
      rodape: "StarCode · aceite da Fase 11",
      barraSuperior: "Ponte de Comando",
    });
  });

  it("não altera a caixa do texto do botão", async () => {
    // sem @types/node no projeto: o módulo é resolvido em tempo de execução
    const fs = (await import(/* @vite-ignore */ ["node", "fs"].join(":"))) as {
      readFileSync(path: string, enc: string): string;
    };
    const css = fs.readFileSync("src/style.css", "utf-8");
    expect(css).toContain(".topbar");
    expect(css).not.toMatch(/text-transform\s*:/);
  });

  it("mostra a saudação com o nome", async () => {
    expect(await saudar("Ana")).toBe("Olá, Ana!");
  });

  it("mostra a saudação ao mundo com o campo vazio", async () => {
    expect(await saudar("")).toBe("Olá, mundo!");
  });
});
