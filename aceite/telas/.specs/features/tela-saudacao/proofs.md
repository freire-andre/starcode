# tela-saudacao proofs

**HEAD**: 7d16638
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 6 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / ✓ src/ui.test.ts > tela de saudação > traz os textos do mockup` | pass |
| C2 | `run unit / ✓ src/ui.test.ts > tela de saudação > mostra a saudação com o nome` | pass |
| C3 | `run unit / ✓ src/ui.test.ts > tela de saudação > mostra a saudação ao mundo com o campo vazio` | pass |
| Build | `npx biome check .` | pass |
| Build | `npx tsc --noEmit` | pass |
| Build | `cd src-tauri && cargo fmt --check && cargo clippy --all-targets -- -D warnings` | pass |

## Output

`Run unit` - exit 0

```
 ✓ src/dev-mocks.test.ts > handleCommand > responde greet como o comando Rust 2ms
 ✓ src/dev-mocks.test.ts > handleCommand > responde greet vazio com o mundo 0ms
 ✓ src/dev-mocks.test.ts > handleCommand > ignora comando desconhecido 0ms
 ✓ src/ui.test.ts > tela de saudação > traz os textos do mockup 2ms
 ✓ src/ui.test.ts > tela de saudação > não altera a caixa do texto do botão 1ms
 ✓ src/ui.test.ts > tela de saudação > mostra a saudação com o nome 0ms
 ✓ src/ui.test.ts > tela de saudação > mostra a saudação ao mundo com o campo vazio 0ms

 Test Files  3 passed (3)
      Tests  9 passed (9)
   Start at  08:25:15
   Duration  248ms (tests 47%, transform 25%, import 21%, worker 6%)

npm notice run starcode-telas@0.1.0 npx
npm notice run vitest run --reporter=verbose
```
