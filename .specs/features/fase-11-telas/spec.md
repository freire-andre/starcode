# Fase 11 — Verificação de telas (v1.5): Spec

**Approved**: 2026-11-11 - user: "sim"

**Size**: LARGE
**Risk triggers**: none
**Status**: Approved

## Context

Desde a D25 o StarCode não verifica telas. A adaptação dos gates (ADR-0002) removeu as regras de captura do tlc: `captures/`, `screens.md`, rodadas do juiz. Uma feature com tela passa no gate final sem que ninguém compare a tela rodando com o mockup aprovado. A Fase 11 traz essas regras de volta, escritas para o StarCode. Uma spec pode citar um mockup vinculante. Um juiz de telas independente tira as próprias fotos no navegador da Orca, no tamanho do mockup, e escreve `screens.md`. O `validate_verification` só aceita a feature com todas as telas em `matches`.

Sucesso: uma feature Tauri real com mockup vinculante tem as telas capturadas no tamanho do mockup e julgadas, e o `screens.md` é aceito pelo `validate_verification`.

Discovery: `.specs/features/fase-11-telas/context.md`. Issue: SC-18.

## Scope

- `scripts/gates/validate_spec.py`: regras de captura na spec (R1–R4).
- `scripts/gates/validate_verification.py`: regras de tela no gate final (R5–R13).
- `scripts/gates/gates_common.py` (ou módulo novo `scripts/gates/images.py`): leitura do tamanho de PNG, JPEG e WebP só com a stdlib, e a escala `@2x`/`@3x` pelo nome do arquivo.
- `scripts/screens.py` (novo, stdlib): `capture`, `size` e `list` pelo CLI da Orca (R14–R20).
- `briefs/screens-verify.md` (novo) e `scripts/dispatch.py screens-brief` (R21–R22).
- Skills e referências:
  - `skills/q/` ganha a referência do juiz de telas;
  - `skills/engajar/references/execute.md`: despacho do juiz, ciclo pós-Q e rodada 2;
  - `skills/spock/SKILL.md` e `skills/spock/references/spec-template.md`: regras de captura, sem o aviso da D25;
  - `skills/laforge/`: foto do autor (R23–R29).
- `profiles/tauri/`: `screens` no `profile.yaml` e `mockIPC` no template (R30–R31).
- `tools/build.py` nos 4 CLIs; testes `unittest` com binário `orca` falso e imagens sintéticas.
- Registros:
  - `DECISIONS.md`: F11-n e nota na D25;
  - `docs/adr/ADR-0002-formato-dos-gates.md`: as regras de captura voltam;
  - `CHANGELOG.md`: `## [1.5.0] - não lançada`;
  - `docs/compatibilidade.md`;
  - `dist/` regenerado;
  - `CREDITS.md`: atribuição do tlc.
- Aceite real (R35–R38) em `docs/aceite/fase-11.md`.

## Non-Goals

- Capturar a janela nativa do Tauri (`orca computer` no Windows não redimensiona janela).
- Mockup em HTML, Figma ou link: só imagem PNG, JPEG ou WebP em `captures/`.
- Comparação automática por pixel: quem julga é o worker de telas, pelo inventário.
- As provas `browser` e `walk` do tlc e a linha `**Walked:**` obrigatória: o gesto que leva à tela está no critério da spec.
- Emulador móvel, animação e vídeo.
- Snapshot e raio de impacto (Fase 12).

## Requirements

### Captura na spec (`validate_spec.py`)

- **R1** - IF a pasta da feature tem `captures/` com imagem (`.png`, `.jpg`, `.jpeg`, `.webp`, exceto `*.running.png`) e a spec não tem `## Sources` THEN the system SHALL dar ERRO "captures/ tem o design mas falta `## Sources`: uma linha por captura, `![<nome>](captures/<arquivo>) - binding - <o que desenha>`".
- **R2** - IF uma captura de `captures/` não tem linha em `## Sources`, ou tem `non-binding` sem `user: "<palavras>"` THEN the system SHALL dar ERRO citando o arquivo.
- **R3** - IF uma captura vinculante não é citada entre crases (`captures/<arquivo>` ou o caminho completo) em nenhuma linha de requisito `**R<n>**` THEN the system SHALL dar ERRO "nenhum requisito cita a captura `<arquivo>`".
- **R4** - IF uma captura não aparece como imagem `![...](captures/<arquivo>)` na spec THEN the system SHALL dar ERRO citando o arquivo.

### Telas no gate final (`validate_verification.py`)

- **R5** - WHEN a spec tem ao menos uma captura vinculante citada por um requisito THEN the system SHALL tratar a feature como "com telas" e aplicar R6–R13. Sem captura vinculante, o resultado do gate não muda (testes atuais seguem verdes).
- **R6** - IF a feature tem telas e não há `screens.md` com uma tabela de colunas `Screen` e `Verdict` THEN the system SHALL dar ERRO "a feature tem tela mas falta `screens.md` (juiz de telas)".
- **R7** - IF uma linha da tabela de veredito não começa com `match` THEN the system SHALL dar ERRO com o nome da tela e o veredito lido.
- **R8** - IF `screens.md` não tem `**Round**:` ou o número passa de 2 THEN the system SHALL dar ERRO ("sem rodada" ou "não há rodada 3: o que ainda difere vai para o usuário").
- **R9** - IF `screens.md` não tem `**Verifier**:` THEN the system SHALL dar ERRO.
- **R10** - IF uma captura citada não tem `<nome>.running.png` ao lado (mesma pasta) THEN the system SHALL dar ERRO "a captura `<arquivo>` não tem `<nome>.running.png`".
- **R11** - IF o tamanho em CSS da foto não é o da captura THEN the system SHALL dar ERRO "`<foto>` tem <L>x<A> e a captura tem <L>x<A>: tire a foto no tamanho da captura". O tamanho em CSS da captura é o tamanho em pixels dividido pela escala do nome (`@2x`, `@3x`; sem sufixo, 1). A foto passa quando o tamanho em pixels dividido por 1, 2 ou 3 for igual a esse tamanho.
- **R12** - IF uma imagem citada não existe, não é PNG, JPEG ou WebP ou tem cabeçalho ilegível THEN the system SHALL dar ERRO com o caminho, sem stack trace.
- **R13** - WHEN `screens.md` tem `**Pictures**: author's` THEN the system SHALL dar AVISO de verificação degradada ("o juiz julgou as fotos do autor"), que vira ERRO com `--strict`.

### Captura pela Orca (`screens.py`)

- **R14** - WHEN `python scripts/screens.py capture --url <http(s)://...> --width <L> --height <A> --out <arquivo.png>` roda THEN the system SHALL executar `orca tab create --url`, `orca exec --page <id> --command "set viewport <L> <A>"` e `orca screenshot --page <id> --json`, copiar o PNG para `--out` (o temporário da Orca expira), fechar a aba (`orca tab close --page <id>`), imprimir `{"out": ..., "width": L, "height": A}` e sair com 0.
- **R15** - IF a URL não começa com `http://` ou `https://` THEN the system SHALL sair com 2 e a mensagem "use uma URL http(s): a Orca não desenha páginas data:".
- **R16** - IF qualquer chamada à Orca falha, o `orca` não está no PATH ou o PNG salvo não tem `<L>x<A>` THEN the system SHALL sair com 1 e uma linha com o passo e o motivo, fechando a aba se ela foi aberta.
- **R17** - IF o screenshot volta "did not draw a frame" THEN the system SHALL ativar a aba (`orca tab switch --page <id>`), tentar uma segunda vez e, falhando, sair com 1 e a mensagem "a página não desenhou: deixe o navegador da Orca visível e tente de novo".
- **R18** - WHEN `screens.py size <imagem>` roda THEN the system SHALL imprimir `<L>x<A> @<escala>x css <Lc>x<Ac>` e sair com 0. Com imagem ilegível, sai com 1.
- **R19** - WHEN `screens.py list <slug> [--root DIR]` roda THEN the system SHALL imprimir um JSON com uma entrada por captura vinculante citada na spec: `capture`, `running`, `exists`, `px`, `scale`, `css` e os requisitos `R<n>` que a citam. Sem capturas, imprime `[]` e sai com 0.
- **R20** - The system SHALL usar só a stdlib do Python e o CLI `orca`. Nos testes, um `orca` falso no PATH registra as chamadas e devolve JSON gravado.

### Juiz de telas (worker)

- **R21** - The system SHALL ter um brief autocontido `briefs/screens-verify.md` para o juiz de telas. Ele recebe: o caminho da spec, a lista do `screens.py list`, a URL do app e o comando que o serve, o caminho de `screens.md` e a rodada. Ele não recebe os checks, o `tasks.md`, o diff, o `proofs.md` nem o Handoff.
- **R22** - WHEN `python scripts/dispatch.py screens-brief <slug> --url <URL> [--serve "<comando>"] [--round 1|2] --out <arquivo>` roda THEN the system SHALL gravar o brief preenchido. IF a spec não cita captura vinculante THEN sai com 2 e "a spec não cita captura vinculante: não há telas para julgar".
- **R23** - WHEN o juiz roda a rodada 1 THEN the system SHALL tirar a própria foto de cada captura com `screens.py capture`, no tamanho em CSS da captura, chegando ao estado pelo gesto do requisito que a cita, e salvar sobre `captures/<nome>.running.png`.
- **R24** - WHEN o juiz julga uma foto THEN the system SHALL escrever primeiro o inventário da captura: uma linha por região, controle, rótulo, frase, marca de estado, linha e arranjo. Depois marca cada linha `same` ou `differs` pelas categorias `controls`, `arrangement`, `copy`, `drawing` e `render`, e diz o que a foto desenha no lugar. Espaçamento, tom e peso exatos são nota numa linha `same`. Uma linha `differs` torna a tela `diverges`; sem nenhuma, `matches`.
- **R25** - The system SHALL gravar `screens.md` com: título, `**Verifier**: <cli> · requested <modelo> · effective <modelo>`, `**Round**: <n>`, `**Pictures**: running | author's`, a tabela `| Screen | Compared with | Verdict | Finding |` e um inventário por foto.
- **R26** - IF a captura falha (navegador indisponível, servidor fora do ar, página que não desenha) THEN the system SHALL julgar a foto do autor e gravar `**Pictures**: author's` com o motivo em `## Limits`.
- **R27** - WHEN há rodada 2 THEN the system SHALL retirar só as fotos com linha `differs` e reabrir só essas linhas. As linhas `same` ficam como estavam e nada novo entra no inventário. O arquivo passa a `**Round**: 2`, e o que ainda difere vai para o usuário.
- **R28** - WHEN a feature tem telas e o Q foi despachado THEN the Picard SHALL despachar o juiz de telas como worker da Orca no worktree de integração, no CLI e na família de modelo escolhidos para o Q (`dispatch.py q-cli`), nunca na família do LaForge. As linhas `differs` entram na única rodada de correção pós-Q junto com os achados do Q. Depois da correção vem a rodada 2.

### Regras de autoria

- **R29** - The system SHALL descrever na skill do Spock e no template da spec as capturas vinculantes em `captures/` (com linha em `## Sources` e imagem), um requisito por tela com o gesto que leva a ela e o caminho da captura, e rótulos copiados caractere por caractere. O aviso "mockups não são verificados (D25)" sai da skill.
- **R30** - WHEN um ticket do LaForge implementa uma tela citada por captura THEN the system SHALL exigir no brief e na skill que o worker tire a foto do autor com `screens.py capture` e a commite como `captures/<nome>.running.png`, dentro do `May change` do ticket.
- **R31** - The system SHALL acrescentar ao perfil `tauri` a chave `screens` com `serve: "npm run dev"` e `url: "http://localhost:5173"`. O template SHALL instalar `mockIPC` de `@tauri-apps/api/mocks` (resposta ao comando `greet`) só quando `import.meta.env.DEV` é verdadeiro e `window.__TAURI_INTERNALS__` não existe. Assim o frontend roda no navegador da Orca sem o binário do Tauri. O build de produção não importa o módulo de mocks.
- **R32** - The system SHALL manter verdes os gates do template Tauri (`npx vitest run`, `npx tsc --noEmit`, `npx biome check .`) e a série de testes dos perfis existente.

### Build e registros

- **R33** - WHEN `python tools/build.py` roda THEN the system SHALL levar `screens.py`, `briefs/screens-verify.md` e as referências novas para os 4 CLIs. O `build.py --check` falha se `dist/` divergir da fonte.
- **R34** - The system SHALL registrar as decisões F11-n em `DECISIONS.md` (com nota na D25, "superada pela Fase 11"), a volta das regras de captura em `docs/adr/ADR-0002-formato-dos-gates.md`, `## [1.5.0] - não lançada` no `CHANGELOG.md`, a linha da verificação de telas em `docs/compatibilidade.md` e a atribuição CC-BY-4.0 do tlc no cabeçalho de cada arquivo adaptado e em `CREDITS.md`.

### Aceite

- **R35** - WHEN o aceite roda THEN the system SHALL criar com o Scotty (`scaffold.py`, perfil `tauri`) um app novo em `F:\Projetos\starcode-telas`, com Linear no time PROJ, e gerar um mockup a partir de HTML, capturado em PNG 1x com `screens.py capture`. O usuário aprova o mockup junto com a spec da feature de teste.
- **R36** - WHEN a feature de teste roda pelo fluxo (LaForge, Q e juiz de telas como workers) THEN the system SHALL produzir `screens.md` com todas as telas em `matches` e `**Pictures**: running`, e `validate_verification` SHALL sair com 0.
- **R37** - The system SHALL plantar na rodada 1 uma divergência conhecida (um rótulo trocado em relação ao mockup). O juiz SHALL marcar a tela `diverges` com a linha de `copy`. A correção pós-Q SHALL fechar a divergência na rodada 2.
- **R38** - The system SHALL registrar o aceite em `docs/aceite/fase-11.md` com o caminho do app, as issues PROJ, os tamanhos do mockup e das fotos, os vereditos das duas rodadas e a saída do gate, e escrever `**Resultado**: aprovado` só quando R36 e R37 forem atendidos.

## Data & Contracts

- Captura: `.specs/features/<slug>/captures/<nome>[@2x|@3x].<png|jpg|jpeg|webp>`. Foto: `captures/<nome>.running.png`, na mesma pasta, sem o sufixo de escala, por exemplo `card-form@2x.png` → `card-form.running.png`.
- Linha de Sources: `- ![<nome>](captures/<arquivo>) - binding - <o que desenha>` ou `- ![<nome>](captures/<arquivo>) - non-binding - user: "<palavras>"`.
- Requisito que cita tela, por exemplo: `**R3** - WHEN o usuário abre o app THEN the system SHALL mostrar a tela de captures/home.png` (o caminho entre crases no texto real).
- `screens.md`:

```markdown
# <Feature> screens

**Verifier**: <cli> · requested <modelo> · effective <modelo>
**Round**: 1
**Pictures**: running

| Screen | Compared with | Verdict | Finding |
| --- | --- | --- | --- |
| `captures/home.running.png` | `captures/home.png` | diverges | 1 linha difere (copy) |

### `captures/home.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| botão principal `Saudar` | differs | `Enviar` |

## Limits
```

- `screens.py list` (JSON): `[{"capture": ".specs/.../home.png", "running": ".specs/.../home.running.png", "exists": true, "px": [800, 600], "scale": 1, "css": [800, 600], "requirements": ["R3"]}]`.
- Perfil: `screens: {serve: "npm run dev", url: "http://localhost:5173"}`.

## States

- Feature sem captura: gates como hoje.
- Feature com telas, juiz não rodou: ERRO R6.
- Rodada 1 com `diverges`: ERRO R7. Correção pós-Q e rodada 2.
- Rodada 2 ainda `diverges`: ERRO R7. Vai para o usuário, sem rodada 3.
- Fotos do autor: AVISO de degradada (ERRO com `--strict`).

## Edge Cases

- Captura `@2x` de 1600x1200: tamanho em CSS 800x600. Foto de 800x600, 1600x1200 ou 2400x1800 passa.
- Captura com extensão em maiúsculas (`HOME.PNG`): reconhecida.
- `*.running.png` dentro de `captures/` nunca conta como captura (R1).
- WebP sem o chunk `VP8X`/`VP8 `/`VP8L` reconhecível: ERRO R12.
- Duas capturas com o mesmo nome e extensões diferentes (`home.png`, `home.jpg`): ERRO "duas capturas para `home.running.png`".
- Servidor de desenvolvimento ainda subindo: o juiz espera a URL responder (até 60 s) antes de capturar e, depois disso, cai em R26.
- Aba de captura deixada aberta por uma falha: R16 a fecha.

## Decisions

| Item | Options | Status |
|---|---|---|
| Captura de tela Tauri | frontend (Vite) no navegador da Orca com viewport do mockup e `mockIPC` (tamanho exato, testado) · janela nativa via `orca computer` (sem controle de tamanho no Windows) | approved - user: "Frontend no navegador (Recommended)" |
| Quem julga as telas | worker próprio na família do Q (contexto limpo) · dentro do worker do Q (mais barato, mesmo agente) | approved - user: "Worker próprio (Recommended)" |
| Mockup do aceite | gerado por nós (HTML → PNG 1x, aprovado pelo usuário) · fornecido pelo usuário | approved - user: "Nós geramos (Recommended)" |
| Projeto do aceite | app Tauri novo pelo Scotty, Linear no time PROJ · `starcode-sandbox` | approved - user: "Novo no sandbox (Recommended)" |

## Open Questions
None.

## Sources

- `docs/reference/tlc-spec-driven.zip` → `references/verify-screens.md` e `scripts/validate_verification.py`, `scripts/validate_spec.py` (tlc-spec-driven 4.1.0, CC-BY-4.0) - non-binding - user: "Reintroduzir as regras de captura do tlc" (fonte de método, adaptada ao StarCode).
