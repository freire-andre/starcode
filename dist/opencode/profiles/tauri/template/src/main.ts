import { invoke } from "@tauri-apps/api/core";
import { normalizeName } from "./greeting";

const form = document.querySelector<HTMLFormElement>("#greet-form");
const input = document.querySelector<HTMLInputElement>("#greet-input");
const message = document.querySelector<HTMLParagraphElement>("#greet-msg");

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!input || !message) return;
  message.textContent = await invoke<string>("greet", { name: normalizeName(input.value) });
});
