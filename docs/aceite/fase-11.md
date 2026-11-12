# Aceite da Fase 11 (SC-141): telas com mockup vinculante

**Resultado**: aprovado

Conduzido pelo Picard com o usuário em 2026-11-11 e 2026-11-12; registrado pelo LaForge (T9). App de teste em `F:\Projetos\starcode-telas`, issues no time PROJ. Evidências copiadas para `docs/aceite/fase-11/`. Achados que pedem código ficam em `## Pendências`.

## App

**Resultado**: aprovado

App Tauri novo em `F:\Projetos\starcode-telas`, criado pelo Scotty com `scaffold.py new --profile tauri --pin-tested` (Tauri 2.12.5, @tauri-apps/api 2.12.4, Vite 8.3.8). Os 8 gates do perfil passaram, incluindo `npm run tauri build -- --debug --no-bundle`. Git local sem remoto, modo Git 2, ramo `feature/tela-saudacao`. Linear (time PROJ): PROJ-34 (Done).

## Mockup

**Resultado**: aprovado

Arquivo: `docs/aceite/fase-11/mockup-saudacao.png` (800x600 @1x, 17029 bytes). Gerado a partir de HTML e capturado com `screens.py capture` no tamanho da janela do app. Aprovado pelo usuário junto com a spec ("sim para os dois", 2026-11-11).

## Rodada 1

**Resultado**: aprovado

Foto: `docs/aceite/fase-11/rodada1-saudacao.running.png` (800x600 @1x, 17426 bytes); relatório: `docs/aceite/fase-11/screens-rodada1.md`. Fotos tiradas pelo juiz no navegador da Orca com o frontend no Vite (`npm run dev`, `mockIPC`), `**Pictures**: running`.

Divergência plantada: `text-transform: uppercase` no botão. O HTML manteve "Saudar", então os testes passavam e só a tela mostrava a diferença (diferença em relação ao texto do R37, "um rótulo trocado": o rótulo trocou na tela, não no HTML, para que os testes não pegassem antes do juiz).

Juiz de telas (codex · gpt-6-luna): `diverges`, 1 linha `differs` de 9 (botão desenha "SAUDAR" em vez de "Saudar", copy). Q (codex · gpt-6-luna): FAIL com 2 achados (o mesmo `text-transform` e o teste do C1 com `toContain`). `validate_verification` reprovou com exit 1 (R7 e achados abertos). Correção pós-Q por um LaForge: cf05251 (remove a caixa alta) e 712c30c (C1 com igualdade exata; dois mutantes derrubam o teste).

## Rodada 2

**Resultado**: aprovado

Foto: `docs/aceite/fase-11/rodada2-saudacao.running.png` (800x600 @1x, 17203 bytes); relatório: `docs/aceite/fase-11/screens-rodada2.md`. O juiz reabriu só a linha do botão: `same`. A tela ficou `matches` (nenhuma linha difere), `**Pictures**: running`. A divergência de copy da rodada 1 está fechada.

## Gate

**Resultado**: aprovado

Rodada 1: `validate_verification` exit 1, com 3 erros: dois achados sem commit em `Closed` e `screens.md` 'diverges', não `match`. Rodada 2, em a9f0d26 (`docs(specs): telas rodada 2 (tela-saudacao)`):

```
[validate_verification] .specs/features/tela-saudacao
  ok
VEREDITO: VERDE (etapa done, 1 gate(s))
  OK   validate_verification  0 erro(s), 0 aviso(s)
```

Saída do gate com exit 0 (R35 a R38 atendidos). Ocorrências: o 1º LaForge morreu com o reinício da sessão (`terminal_missing`) e foi redespachado no mesmo worktree aproveitando o diff; o `worker-start --worktree new-child` criou o worktree no repo do terminal chamador (StarCode), então o worktree do app foi criado antes com `orca worktree create --repo`.

## Pendências

- Template tauri sem `.gitattributes`: `core.autocrlf=true` deixa os arquivos em CRLF e o `biome check` reprova (contornado no app com `core.autocrlf false` local).
- SC-143: `cd src-tauri` duplo na linha Build do `scaffold.py checks`.
- SC-142: a Ponte mostra missão de outro worktree.
- SC-144: Playwright como segundo motor.
