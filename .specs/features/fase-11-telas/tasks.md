# Fase 11 — Verificação de telas (v1.5): Tasks

**Approved**: 2026-11-11 - user: "sim"

**Spec**: `.specs/features/fase-11-telas/spec.md`
**Status**: Approved
**Integration branch**: `feature/fase-11-telas`

## Gate Commands

| Level | When | Command |
|---|---|---|
| quick | task with unit tests only, no generator change | `python -m unittest discover -s tests -v` |
| full | task that changes `scripts/`, `src/`, `skills/`, `profiles/`, `tools/` or `tests/` (F3-1: `dist/` regenerated in the same commit) | `python tools/build.py && python tools/build.py --check && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |
| build | records task, or after the last code task | `python tools/build.py && python tools/build.py --check && claude plugin validate dist/claude --strict && python scripts/check_decisions.py && python -m unittest discover -s tests -v` |

## Tasks

### T1: Leitura de imagens e capturas (images.py)
**Linear**: SC-133
**Depends on**: none
**Requirements**: R11, R12
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/gates/images.py` (só stdlib), usado pelos gates e pelo `screens.py`:
- `image_size(path) -> (largura, altura)` para PNG (IHDR), JPEG (marcadores SOF0–SOF15, exceto DHT/DAC) e WebP (`VP8 `, `VP8L`, `VP8X`). Arquivo ausente, formato não suportado ou cabeçalho ilegível → `ImageError` com o caminho e o motivo em PT-BR (R12).
- `capture_scale(nome) -> 1|2|3` pelo sufixo `@2x`/`@3x` antes da extensão (sem sufixo, 1); `css_size(path)` = tamanho em pixels dividido pela escala.
- `running_path(capture) -> Path`: `captures/<nome sem @Nx>.running.png` na mesma pasta.
- `same_css(running_px, capture_css) -> bool`: verdadeiro quando `running_px / k == capture_css` para algum k em 1, 2, 3 (divisão exata) (R11).
- `list_captures(fdir) -> list[Path]`: imagens `.png/.jpg/.jpeg/.webp` (extensão sem diferenciar maiúsculas) em `<fdir>/captures/`, exceto `*.running.png`; duas capturas com o mesmo `running_path` → `ImageError` "duas capturas para `<nome>.running.png`".
- Entrada F11-1 em `DECISIONS.md` (leitura de imagem só com stdlib, regra de escala pelo nome e de tamanho em CSS).
- Testes em `tests/test_images.py` (imagens sintéticas geradas no teste com `struct`/`zlib`, sem arquivo binário no repo), com os nomes: `test_image_size_png`, `test_image_size_jpeg`, `test_image_size_webp_variantes`, `test_image_size_ilegivel`, `test_capture_scale_e_css`, `test_same_css_1x_2x_3x`, `test_list_captures_ignora_running_e_duplicadas`.

#### CONTEXT
Spec: `.specs/features/fase-11-telas/spec.md` (R11, R12; Data & Contracts; Edge Cases). Checks: C11, C12.
Referência do método (CC-BY-4.0, adaptar, não copiar às cegas): `_image_size` e `_same_layout` em `scripts/validate_verification.py` do tlc, dentro de `docs/reference/tlc-spec-driven.zip`. Cabeçalho do arquivo com a atribuição, como em `scripts/gates/check_proofs.py`. Módulos dos gates importam irmãos com `sys.path.insert(0, ...)` (veja `scripts/gates/validate_verification.py`).

#### BOUNDARIES
May change: `scripts/gates/images.py`, `tests/test_images.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/gates/validate_spec.py`, `scripts/gates/validate_verification.py`, `scripts/screens.py`, `scripts/dispatch.py`, `skills/`, `profiles/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-11-telas`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T2: Regras de captura na spec (validate_spec)
**Linear**: SC-134
**Depends on**: T1
**Requirements**: R1, R2, R3, R4
**Tests**: unit
**Gate**: full

#### TASK
Em `scripts/gates/validate_spec.py`, usando `images.list_captures`:
- R1: `captures/` com captura e spec sem `## Sources` → ERRO "captures/ tem o design mas falta `## Sources`: uma linha por captura, `![<nome>](captures/<arquivo>) - binding - <o que desenha>`".
- R2: captura sem linha em `## Sources`, ou linha `non-binding` sem `user: "<palavras>"` → ERRO citando o arquivo. Linha sem `non-binding` = vinculante.
- R3: captura vinculante não citada entre crases (`captures/<arquivo>` ou o caminho completo) numa linha de requisito `**R<n>**` → ERRO "nenhum requisito cita a captura `<arquivo>`".
- R4: captura sem `![...](captures/<arquivo>)` na spec → ERRO citando o arquivo.
- Feature sem `captures/`: comportamento atual inalterado. Atualize a docstring (remova "capture rules removed (D25)" e liste as regras novas).
- Entrada F11-2 em `DECISIONS.md`.
- Testes em `tests/test_validate_spec_captures.py`: `test_captura_sem_sources`, `test_captura_sem_linha_ou_non_binding_sem_citacao`, `test_captura_vinculante_sem_requisito`, `test_captura_sem_imagem_na_spec`, `test_spec_com_captura_completa_passa`, `test_spec_sem_captures_inalterada`.

#### CONTEXT
Spec: `.specs/features/fase-11-telas/spec.md` (R1–R4; Data & Contracts). Checks: C1–C4.
Já existe: `## Sources` vinculante exige `## Differences from the Source` (`BINDING_RE`/`NOT_BINDING_RE` em `validate_spec.py`). Referência: `_check_captures` em `scripts/validate_spec.py` do tlc (`docs/reference/tlc-spec-driven.zip`). Fixtures de spec existentes: `tests/test_gates.py`.

#### BOUNDARIES
May change: `scripts/gates/validate_spec.py`, `tests/test_validate_spec_captures.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/gates/images.py`, `scripts/gates/validate_verification.py`, `scripts/screens.py`, `skills/`, `profiles/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-11-telas`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T3: Telas no gate final (validate_verification)
**Linear**: SC-135
**Depends on**: T2
**Requirements**: R5, R6, R7, R8, R9, R10, R11, R12, R13
**Tests**: unit
**Gate**: full

#### TASK
Em `scripts/gates/validate_verification.py`, usando `images.py`:
- R5: a feature "tem telas" quando a spec tem captura vinculante citada por um requisito (mesma leitura do T2: linha de `## Sources` sem `non-binding` e citação numa linha `**R<n>**`). Sem telas, nada muda.
- R6: sem `screens.md` com tabela de colunas `Screen` e `Verdict` → ERRO "a feature tem tela mas falta `screens.md` (juiz de telas)".
- R7: linha de veredito que não começa com `match` → ERRO com a tela e o veredito.
- R8: sem `**Round**:` → ERRO "screens.md sem `**Round**:`"; rodada > 2 → ERRO "não há rodada 3: o que ainda difere vai para o usuário".
- R9: sem `**Verifier**:` → ERRO.
- R10: captura citada sem `running_path` existente → ERRO "a captura `<arquivo>` não tem `<nome>.running.png`".
- R11: `same_css` falso → ERRO "`<foto>` tem <L>x<A> e a captura tem <L>x<A>: tire a foto no tamanho da captura" (tamanhos em CSS da captura).
- R12: `ImageError` vira ERRO com o caminho, sem stack trace.
- R13: `**Pictures**: author's` → AVISO "verificação degradada: o juiz julgou as fotos do autor"; com `--strict`, ERRO.
- Atualize a docstring (remova "screen/walk/round rules removed (D25)").
- Entrada F11-3 em `DECISIONS.md`.
- Testes em `tests/test_validate_verification_screens.py`, montando a feature completa (spec/tasks aprovadas, `proofs.md` no HEAD de um repo Git temporário, `verification.md`) como em `tests/test_validate_verification.py`: `test_feature_sem_telas_inalterada`, `test_telas_sem_screens_md`, `test_tela_diverges_reprova`, `test_screens_sem_round_ou_round_3`, `test_screens_sem_verifier`, `test_captura_sem_running`, `test_running_em_outro_tamanho`, `test_running_2x_de_captura_1x_passa`, `test_imagem_ilegivel_vira_erro`, `test_fotos_do_autor_degradada_e_strict`.

#### CONTEXT
Spec: `.specs/features/fase-11-telas/spec.md` (R5–R13; `screens.md` em Data & Contracts; States). Checks: C5–C13.
Referência: `_screen_evidence`, `_picture_sizes`, `_screens_verdicts` em `scripts/validate_verification.py` do tlc (`docs/reference/tlc-spec-driven.zip`). O gate atual já tem `_tables`, `_col`, `DEGRADED_RE` e o padrão de AVISO/`--strict`.

#### BOUNDARIES
May change: `scripts/gates/validate_verification.py`, `tests/test_validate_verification_screens.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/gates/images.py`, `scripts/gates/validate_spec.py`, `scripts/screens.py`, `tests/test_validate_verification.py`, `skills/`, `profiles/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-11-telas`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T4: Captura pela Orca (screens.py)
**Linear**: SC-136
**Depends on**: T3
**Requirements**: R14, R15, R16, R17, R18, R19, R20
**Tests**: unit
**Gate**: full

#### TASK
Criar `scripts/screens.py` (stdlib + CLI `orca`), reusando `scripts/gates/images.py`:
- `capture --url <http(s)> --width L --height A --out <png>`: `orca tab create --url <url> --json` (pega `result.browserPageId`), `orca exec --page <id> --command "set viewport L A" --json`, `orca screenshot --page <id> --json` (pega `result.path`), copia para `--out` (cria a pasta), confere que o PNG tem LxA, `orca tab close --page <id>` sempre (try/finally), imprime `{"out", "width", "height"}`, exit 0 (R14).
- URL fora de http(s) → exit 2 "use uma URL http(s): a Orca não desenha páginas data:" (R15).
- Falha de qualquer chamada, `orca` fora do PATH, JSON com `ok: false` ou PNG em outro tamanho → exit 1 com uma linha com o passo e o motivo (ex.: "screenshot: page did not draw"), aba fechada se aberta (R16).
- Erro com "did not draw a frame": `orca tab switch --page <id>` e uma segunda tentativa; falhando, exit 1 "a página não desenhou: deixe o navegador da Orca visível e tente de novo" (R17).
- `size <imagem>` → `<L>x<A> @<escala>x css <Lc>x<Ac>`, exit 0; ilegível → exit 1 (R18).
- `list <slug> [--root DIR]` → JSON das capturas vinculantes citadas na spec: `capture`, `running`, `exists`, `px`, `scale`, `css`, `requirements` (caminhos relativos à raiz, com `/`); sem capturas `[]`, exit 0 (R19).
- Chamadas ao `orca` por `subprocess.run([...])` sem shell, `stdin=DEVNULL`, tempo limite 60 s; o executável vem de `shutil.which("orca")`. Saída UTF-8 (`sys.stdout.reconfigure`).
- Entrada F11-4 em `DECISIONS.md`.
- Testes em `tests/test_screens.py` com um `orca` falso no PATH (script Python + `.cmd` no Windows, como em `tests/test_install_local.py`), que registra os argumentos e devolve JSON fixo (R20): `test_capture_chama_orca_na_ordem`, `test_capture_url_data_recusada`, `test_capture_falha_fecha_aba`, `test_capture_tamanho_errado_falha`, `test_capture_sem_frame_tenta_de_novo`, `test_size_imprime_css`, `test_list_capturas_da_spec`.

#### CONTEXT
Spec: `.specs/features/fase-11-telas/spec.md` (R14–R20; Data & Contracts). Checks: C14–C20.
Fatos testados no Orca 1.4.256 (2026-11-11): `tab create --json` devolve `result.browserPageId`; `exec --command "set viewport 800 600"` devolve `{width, height, deviceScaleFactor: 1}`; `screenshot --page <id> --json` devolve `result.path` num temporário que expira; com URL `data:` o screenshot falha com "Screenshot timed out — the browser page did not draw a frame."; com `http://127.0.0.1` o PNG sai em 800x600. Binário falso de exemplo: `tests/test_install_local.py`, `tests/helpers.py`.

#### BOUNDARIES
May change: `scripts/screens.py`, `tests/test_screens.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/gates/`, `scripts/dispatch.py`, `skills/`, `profiles/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-11-telas`. Testes citados por check não têm docstring. Nos testes, nunca chame o `orca` real.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T5: Brief do juiz de telas (screens-verify.md e screens-brief)
**Linear**: SC-137
**Depends on**: T4
**Requirements**: R21, R22, R23, R24, R25, R26, R27
**Tests**: unit
**Gate**: full

#### TASK
- `src/briefs/screens-verify.md` (inglês nas instruções, saída em PT-BR, autocontido, funciona num CLI sem StarCode), com placeholders preenchidos pelo dispatch: spec, lista de capturas (saída do `screens.py list`), URL do app, comando que serve o app, caminho do `screens.md`, rodada e o caminho do `screens.py`. Seções:
  - "What you receive": só isso; não recebe checks, `tasks.md`, diff, `proofs.md` nem Handoff (R21).
  - "Take the pictures yourself": sobe o app com o comando (se dado), espera a URL responder até 60 s, `screens.py capture` no tamanho em CSS de cada captura, chegando ao estado pelo gesto do requisito que a cita, salvando sobre `captures/<nome>.running.png` (R23).
  - "Judge each picture": inventário primeiro, `same`/`differs` pelas categorias `controls`, `arrangement`, `copy`, `drawing`, `render`; espaçamento, tom e peso são nota; uma linha `differs` → `diverges` (R24).
  - "Report": formato de `screens.md` de Data & Contracts, com `**Verifier**: pending` (o Picard preenche), `**Round**`, `**Pictures**` (R25).
  - "When capture fails": julga a foto do autor, `**Pictures**: author's`, motivo em `## Limits` (R26).
  - "Round 2": só as fotos com `differs`, só essas linhas, `**Round**: 2`, nada novo no inventário, sem rodada 3 (R27).
  - Regra UTF-8 sem BOM ao escrever arquivos (como em `src/briefs/q-verify.md`), nunca commitar, escreve só `screens.md` e os `.running.png`.
- `scripts/dispatch.py`: subcomando `screens-brief <slug> --url <URL> [--serve "<cmd>"] [--round 1|2] --out <arquivo>` que preenche o brief; spec sem captura vinculante → exit 2 "a spec não cita captura vinculante: não há telas para julgar" (R22). Reuse a leitura de capturas do `screens.py list` (importe a função, sem duplicar).
- Entrada F11-5 em `DECISIONS.md`.
- Testes em `tests/test_dispatch_screens.py`: `test_screens_brief_preenche_campos`, `test_screens_brief_sem_captura_sai_2`, `test_screens_brief_nao_leva_checks_nem_diff`, `test_screens_brief_regras_de_julgamento`, `test_screens_brief_rodada_2`.

#### CONTEXT
Spec: `.specs/features/fase-11-telas/spec.md` (R21–R27). Checks: C21–C27.
Modelo: `src/briefs/q-verify.md` e `dispatch.py q-brief` (`q_brief`, `brief_template`). Método do juiz: `references/verify-screens.md` do tlc (`docs/reference/tlc-spec-driven.zip`, CC-BY-4.0: atribuição no topo do brief). `tools/build.py` já copia `src/briefs/` para `dist/<cli>/briefs/`.

#### BOUNDARIES
May change: `src/briefs/screens-verify.md`, `scripts/dispatch.py`, `tests/test_dispatch_screens.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/gates/`, `scripts/screens.py`, `src/briefs/q-verify.md`, `skills/`, `profiles/`, `tests/test_dispatch.py`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-11-telas`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T6: Telas no fluxo da tripulação (Picard, Q, Spock, LaForge)
**Linear**: SC-138
**Depends on**: T5
**Requirements**: R28, R29, R30
**Tests**: unit
**Gate**: full

#### TASK
- `skills/engajar/references/execute.md`, seção 4 e 5: quando `screens.py list <slug>` não é vazio, depois de despachar o Q, o Picard gera `dispatch.py screens-brief` (URL e comando do perfil `screens` do `.starcode/stack.json`, ou perguntados) e despacha o juiz de telas como worker da Orca no worktree de integração, no mesmo CLI/família escolhido pelo `q-cli`, nunca na família do LaForge; preenche `**Verifier**:` como faz no Q; as linhas `differs` entram na única correção pós-Q junto com os achados do Q; depois, rodada 2 com `--round 2`; o que ainda difere vai ao usuário (R28).
- `skills/q/SKILL.md`: uma linha apontando o juiz de telas (brief `screens-verify.md`) como worker separado, que o Q não faz.
- `skills/spock/SKILL.md`: troque o aviso "Screens: mockups are not verified automatically in v1.0 (D25)" pelas regras: captura vinculante em `captures/`, linha em `## Sources` com imagem, um requisito por tela com o gesto e o caminho da captura, rótulos copiados caractere por caractere. `skills/spock/references/spec-template.md`: exemplo de `## Sources` com captura e de requisito que cita tela (R29).
- `skills/laforge/SKILL.md` e as regras do brief do worker (`WORKER_RULES` em `scripts/dispatch.py`, usado por `dispatch.py brief`): ticket com tela citada por captura → foto do autor com `screens.py capture` em `captures/<nome>.running.png`, commitada, dentro do `May change` (R30).
- Entrada F11-6 em `DECISIONS.md`.
- Testes em `tests/test_screens_flow.py`: `test_execute_despacha_juiz_de_telas`, `test_q_aponta_juiz_separado`, `test_spock_regras_de_captura_sem_d25`, `test_laforge_foto_do_autor`.

#### CONTEXT
Spec: `.specs/features/fase-11-telas/spec.md` (R28–R30). Checks: C28–C30.
Testes de skill existentes como modelo: `tests/test_q_skill.py`, `tests/test_worker_skills.py`, `tests/test_skills_exec.py`. Skills usam `<plugin-root>` e são geradas para os 4 CLIs pelo `tools/build.py`.

#### BOUNDARIES
May change: `skills/engajar/references/execute.md`, `skills/q/SKILL.md`, `skills/spock/SKILL.md`, `skills/spock/references/spec-template.md`, `skills/laforge/SKILL.md`, `scripts/dispatch.py`, `tests/test_screens_flow.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/gates/`, `scripts/screens.py`, `profiles/`, `src/briefs/screens-verify.md`, `src/briefs/q-verify.md`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-11-telas`. Testes citados por check não têm docstring. Em `scripts/dispatch.py` mude só `WORKER_RULES`.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T7: Perfil Tauri com telas no navegador (mockIPC)
**Linear**: SC-139
**Depends on**: T6
**Requirements**: R31, R32
**Tests**: unit
**Gate**: full

#### TASK
- `profiles/tauri/profile.yaml`: chave `screens` com `serve: "npm run dev"` e `url: "http://localhost:5173"` (a porta do `vite.config.ts` do template). Se o carregador de perfis (`scripts/scaffold.py`) ou `tests/test_profiles.py` recusar chave nova, ajuste-os para aceitar `screens` (mapa com `serve` e `url`).
- `profiles/tauri/template/src/main.ts`: antes de ligar o formulário, quando `import.meta.env.DEV` é verdadeiro e `window.__TAURI_INTERNALS__` não existe, `await import("@tauri-apps/api/mocks")` e `mockIPC` respondendo `greet` como o comando Rust do template. Import dinâmico só nesse ramo: o build de produção não leva o módulo de mocks (R31). Se precisar, um `src/dev-mocks.ts` com a função e teste vitest.
- Gates do template continuam verdes (`npx vitest run`, `npx tsc --noEmit`, `npx biome check .`) e a série dos perfis existente também (R32).
- Entrada F11-7 em `DECISIONS.md`.
- Testes em `tests/test_profile_screens.py`: `test_perfil_tauri_tem_screens`, `test_template_tauri_mockipc_so_em_dev`.

#### CONTEXT
Spec: `.specs/features/fase-11-telas/spec.md` (R31, R32). Checks: C31, C32.
Context7 (`/tauri-apps/tauri-docs`, v2, consultado em 2026-11-11): `mockIPC((cmd, args) => ...)` de `@tauri-apps/api/mocks` simula `window.__TAURI_INTERNALS__.invoke` num navegador comum. Perfil e template atuais: `profiles/tauri/`; testes do perfil: `tests/test_profile_ts_tauri.py`, `tests/test_profiles.py`.

#### BOUNDARIES
May change: `profiles/tauri/profile.yaml`, `profiles/tauri/template/src/main.ts`, `profiles/tauri/template/src/dev-mocks.ts`, `profiles/tauri/template/src/dev-mocks.test.ts`, `scripts/scaffold.py`, `tests/test_profiles.py`, `tests/test_profile_screens.py`, `DECISIONS.md`, `dist/`
Do not touch: `scripts/gates/`, `scripts/screens.py`, `scripts/dispatch.py`, `skills/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-11-telas`. Testes citados por check não têm docstring. Não mude versões de dependência do template.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T8: Build nos 4 CLIs e registros da fase
**Linear**: SC-140
**Depends on**: T7
**Requirements**: R33, R34
**Tests**: unit
**Gate**: build
**Runs alone**: yes

#### TASK
- Confirme que `python tools/build.py` leva `scripts/screens.py`, `scripts/gates/images.py`, `briefs/screens-verify.md` e as skills alteradas para `dist/claude`, `dist/codex`, `dist/antigravity`, `dist/opencode`; se algo faltar, ajuste `tools/build.py` (R33).
- `DECISIONS.md`: nota na D25 "superada pela Fase 11 (F11-1..F11-n)" e uma entrada de fechamento da fase (F11-8).
- `docs/adr/ADR-0002-formato-dos-gates.md`: a linha "Regras de captura (`captures/`, `screens.md`) | removidas | D25" passa a dizer que voltaram na Fase 11, com o que mudou em relação ao tlc (sem provas `browser`/`walk`, sem `**Walked:**`, escala pelo nome, juiz como worker).
- `CHANGELOG.md`: `## [1.5.0] - não lançada` com a verificação de telas.
- `docs/compatibilidade.md`: linha da verificação de telas (navegador da Orca, independente do CLI; sem navegador = degradada).
- `CREDITS.md`: tlc-spec-driven (Felipe Rodrigues, CC-BY-4.0) para as regras de captura e o juiz de telas (R34).
- Testes: `tests/test_release_docs_f11.py` (`test_release_docs_f11`) e, em `tests/test_build.py`, `test_build_leva_telas_aos_4_clis`.

#### CONTEXT
Spec: `.specs/features/fase-11-telas/spec.md` (R33, R34). Checks: C33, C34.
Modelos: `tests/test_release_docs_f10.py`, `tests/test_credits_f9.py`, seção 1.4.0 do `CHANGELOG.md`, formato das entradas verificado por `scripts/check_decisions.py`.

#### BOUNDARIES
May change: `tools/build.py`, `DECISIONS.md`, `docs/adr/ADR-0002-formato-dos-gates.md`, `CHANGELOG.md`, `docs/compatibilidade.md`, `CREDITS.md`, `tests/test_release_docs_f11.py`, `tests/test_build.py`, `dist/`
Do not touch: `scripts/`, `skills/`, `profiles/`, `src/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-11-telas`. Testes citados por check não têm docstring.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

### T9: Aceite real com app Tauri e mockup vinculante
**Linear**: SC-141
**Depends on**: T8
**Requirements**: R35, R36, R37, R38
**Tests**: unit
**Gate**: build

#### TASK
O Picard conduz o aceite com o usuário (aprovações do mockup e da spec da feature de teste, workers e Linear no time PROJ). Este ticket registra o resultado:
- `docs/aceite/fase-11.md` com as seções `## App`, `## Mockup`, `## Rodada 1`, `## Rodada 2`, `## Gate`, cada uma com `**Resultado**: aprovado` ou `reprovado`, e um `**Resultado**:` geral no topo. O documento traz:
  - o caminho `F:\Projetos\starcode-telas` e as issues PROJ;
  - o tamanho do mockup e das fotos;
  - os vereditos das duas rodadas (a rodada 1 com a divergência plantada em `copy`);
  - a saída do `validate_verification` (R35–R38).
- Cópias de evidência em `docs/aceite/fase-11/`: o mockup, as fotos das duas rodadas e o `screens.md` de cada rodada.
- Teste `tests/test_acceptance_doc_f11.py` (`test_fase11_acceptance_sections`).

#### CONTEXT
Spec: `.specs/features/fase-11-telas/spec.md` (R35–R38, Success). Checks: C35–C38.
Modelos: `docs/aceite/fase-10.md` e `tests/test_acceptance_doc_f10.py`. O `release.py` recusa aceite com `**Resultado**` diferente de `aprovado`.

#### BOUNDARIES
May change: `docs/aceite/fase-11.md`, `docs/aceite/fase-11/`, `tests/test_acceptance_doc_f11.py`
Do not touch: `scripts/`, `skills/`, `profiles/`, `src/`, `tools/`, `dist/`

#### RULES
Leia AGENTS.md. TDD; gates verdes antes do commit. Modo Git: 3 (sem push: o Picard cuida).
Commit: Conventional Commits + "Refs: <ID-LINEAR>"; descrição começando em minúscula. Nunca segredos. Não faça deploy, push nem merge.
Nunca escreva `.specs/STATE.md` nem a seção `## Handoff`. Trabalhe só na pasta atual do worktree; nunca faça commit em `feature/fase-11-telas`. Testes citados por check não têm docstring. Achados que pedem código viram pendência, não correção aqui.

#### DELIVERY
Commits na branch do worktree. Relatório final (até 5 linhas): o que mudou, gates executados com
resultado, commits, pendências, tentativas do disjuntor.

## Checks

**Build**: `python tools/build.py --check`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v`

**C1** - `captures/` com captura e spec sem `## Sources` dá ERRO pedindo a linha de Sources (R1)
Proof: run unit | test_captura_sem_sources ... ok

**C2** - Captura sem linha em Sources, ou `non-binding` sem `user: "..."`, dá ERRO com o arquivo (R2)
Proof: run unit | test_captura_sem_linha_ou_non_binding_sem_citacao ... ok

**C3** - Captura vinculante não citada por um requisito `**R<n>**` dá ERRO "nenhum requisito cita a captura" (R3)
Proof: run unit | test_captura_vinculante_sem_requisito ... ok

**C4** - Captura sem `![...](captures/<arquivo>)` na spec dá ERRO; spec completa passa e spec sem `captures/` fica inalterada (R4)
Proof: run unit | test_captura_sem_imagem_na_spec ... ok

**C5** - Feature sem captura vinculante passa no gate final como antes (R5)
Proof: run unit | test_feature_sem_telas_inalterada ... ok

**C6** - Feature com telas e sem `screens.md` dá ERRO "falta `screens.md`" (R6)
Proof: run unit | test_telas_sem_screens_md ... ok

**C7** - Tela com veredito `diverges` reprova o gate citando a tela (R7)
Proof: run unit | test_tela_diverges_reprova ... ok

**C8** - `screens.md` sem `**Round**:` ou com rodada 3 dá ERRO (R8)
Proof: run unit | test_screens_sem_round_ou_round_3 ... ok

**C9** - `screens.md` sem `**Verifier**:` dá ERRO (R9)
Proof: run unit | test_screens_sem_verifier ... ok

**C10** - Captura citada sem `<nome>.running.png` ao lado dá ERRO (R10)
Proof: run unit | test_captura_sem_running ... ok

**C11** - Foto em outro tamanho em CSS dá ERRO com os dois tamanhos; foto 2x de captura 1x passa (R11)
Proof: run unit | test_running_em_outro_tamanho ... ok

**C12** - Imagem ilegível ou fora de PNG/JPEG/WebP vira ERRO com o caminho, sem stack trace (R12)
Proof: run unit | test_imagem_ilegivel_vira_erro ... ok

**C13** - `**Pictures**: author's` dá AVISO de degradada e ERRO com `--strict` (R13)
Proof: run unit | test_fotos_do_autor_degradada_e_strict ... ok

**C14** - `screens.py capture` chama `tab create`, `set viewport`, `screenshot`, copia o PNG e fecha a aba, nessa ordem (R14)
Proof: run unit | test_capture_chama_orca_na_ordem ... ok

**C15** - URL `data:` sai com 2 e a mensagem de URL http(s) (R15)
Proof: run unit | test_capture_url_data_recusada ... ok

**C16** - Falha numa chamada à Orca sai com 1 e fecha a aba aberta (R16)
Proof: run unit | test_capture_falha_fecha_aba ... ok

**C17** - "did not draw a frame" ativa a aba e tenta de novo uma vez (R17)
Proof: run unit | test_capture_sem_frame_tenta_de_novo ... ok

**C18** - `screens.py size` imprime pixels, escala e tamanho em CSS (R18)
Proof: run unit | test_size_imprime_css ... ok

**C19** - `screens.py list` imprime as capturas vinculantes citadas com px, escala, css e requisitos (R19)
Proof: run unit | test_list_capturas_da_spec ... ok

**C20** - Os testes do `screens.py` rodam com um `orca` falso que registra as chamadas, sem o real (R20)
Proof: run unit | test_capture_tamanho_errado_falha ... ok

**C21** - O brief do juiz leva spec, capturas, URL, comando, saída e rodada, e não leva checks, tasks, diff, proofs nem Handoff (R21)
Proof: run unit | test_screens_brief_nao_leva_checks_nem_diff ... ok

**C22** - `dispatch.py screens-brief` preenche o brief; spec sem captura vinculante sai com 2 (R22)
Proof: run unit | test_screens_brief_sem_captura_sai_2 ... ok

**C23** - O brief manda o juiz tirar a própria foto no tamanho em CSS da captura pelo gesto do requisito (R23)
Proof: run unit | test_screens_brief_preenche_campos ... ok

**C24** - O brief traz inventário primeiro, as cinco categorias e a regra "uma linha differs = diverges" (R24)
Proof: run unit | test_screens_brief_regras_de_julgamento ... ok

**C25** - O formato de `screens.md` do brief traz Verifier, Round, Pictures, a tabela de veredito e o inventário (R25)
Proof: run unit | test_screens_brief_regras_de_julgamento ... ok

**C26** - Sem captura possível, o brief manda julgar a foto do autor com `**Pictures**: author's` (R26)
Proof: run unit | test_screens_brief_regras_de_julgamento ... ok

**C27** - A rodada 2 retira só as fotos com `differs`, reabre só essas linhas e não tem rodada 3 (R27)
Proof: run unit | test_screens_brief_rodada_2 ... ok

**C28** - O execute.md despacha o juiz de telas na família do Q depois do Q e junta as divergências à correção pós-Q (R28)
Proof: run unit | test_execute_despacha_juiz_de_telas ... ok

**C29** - A skill do Spock tem as regras de captura e não tem mais o aviso da D25 (R29)
Proof: run unit | test_spock_regras_de_captura_sem_d25 ... ok

**C30** - A skill do LaForge e o brief do ticket mandam tirar e commitar a foto do autor (R30)
Proof: run unit | test_laforge_foto_do_autor ... ok

**C31** - O perfil tauri tem `screens` (serve e url) e o template instala `mockIPC` só em dev e fora do Tauri (R31)
Proof: run unit | test_template_tauri_mockipc_so_em_dev ... ok

**C32** - O perfil tauri segue válido com a chave `screens` (R32)
Proof: run unit | test_perfil_tauri_tem_screens ... ok

**C33** - O build leva `screens.py`, `images.py`, o brief do juiz e as skills para os 4 CLIs (R33)
Proof: run unit | test_build_leva_telas_aos_4_clis ... ok

**C34** - DECISIONS (D25 superada), ADR-0002, CHANGELOG 1.5.0, compatibilidade e CREDITS registram a fase (R34)
Proof: run unit | test_release_docs_f11 ... ok

**C35** - O aceite registra o app Tauri novo, as issues PROJ e o mockup gerado e aprovado (R35)
Proof: run unit | test_fase11_acceptance_sections ... ok

**C36** - O aceite registra `screens.md` todo em `matches` com fotos `running` e o gate saindo com 0 (R36)
Proof: run unit | test_fase11_acceptance_sections ... ok

**C37** - O aceite registra a divergência plantada em `copy` na rodada 1 e fechada na rodada 2 (R37)
Proof: run unit | test_fase11_acceptance_sections ... ok

**C38** - `docs/aceite/fase-11.md` tem as seções e `**Resultado**: aprovado` só com R36 e R37 atendidos (R38)
Proof: run unit | test_fase11_acceptance_sections ... ok

## Handoff

**Phase:** published
**Size:** GRANDE
**Git mode:** 3
**Next:** ramo de integração e primeiro ticket (T1/SC-133)
**Linear:** SC-18 (mãe); SC-133..SC-141
**Integration branch:** feature/fase-11-telas
**Last integrated:** none
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
