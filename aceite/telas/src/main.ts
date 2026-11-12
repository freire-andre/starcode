/// <reference types="vite/client" />
import { invoke } from "@tauri-apps/api/core";
import { normalizeName } from "./greeting";
import "./style.css";

async function boot(): Promise<void> {
  if (import.meta.env.DEV && !("__TAURI_INTERNALS__" in window)) {
    const { installDevMocks } = await import("./dev-mocks");
    await installDevMocks();
  }

  const form = document.querySelector<HTMLFormElement>("#greet-form");
  const input = document.querySelector<HTMLInputElement>("#greet-input");
  const message = document.querySelector<HTMLParagraphElement>("#greet-msg");

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!input || !message) return;
    message.textContent = await invoke<string>("greet", { name: normalizeName(input.value) });
  });
}

void boot();
