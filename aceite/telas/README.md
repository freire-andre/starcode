# starcode-telas

App de aceite da verificação de telas (Fase 11)

## Gates

```sh
npx biome check .
cd src-tauri && cargo fmt --check
cd src-tauri && cargo clippy --all-targets -- -D warnings
npx tsc --noEmit
npx vitest run
cd src-tauri && cargo test
npm run tauri build -- --debug --no-bundle
```

## Rodar

```sh
npm install
npm run tauri dev
```
