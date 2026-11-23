# Aceite da ponte viva (SC-221)

Executado em 2026-11-22 pelo LaForge no worktree `shad` (mesmo drive da instalação da Orca). Resultado geral: **parcial**. Os gates automáticos passaram; a validação visual na Orca com captura e troca real de estado não foi feita (ver `## Limitações`).

## Gates executados

- `python tools/build.py` e `python tools/build.py --check`: OK, `dist/` em dia (commit `6faacf7`).
- `orca plugin test src/orca`: 104 testes, 104 passaram. Cobre C1 (`ponte viva identifica os 12 integrantes`), C2 (`ponte viva limita a seis integrantes`), C11 (`ponte viva atualiza por evento`), C12 (`ponte viva reconcilia automaticamente`), C15 (`ponte viva mantém rótulos legíveis`), C16 (`ponte viva expõe lista acessível`) e C17 (`ponte viva respeita movimento reduzido`).
- `python scripts/check_decisions.py`: OK.
- `claude plugin validate dist/claude --strict`: passou.
- `orca plugin check dist/orca`: manifesto válido, `needsApproval: true`, painéis `ponte` e `ponte-cena` renderizam no stand-in (sem erros).
- `python -m unittest discover -s tests`: 1107 testes, 1 falha, 1 ignorado. Falha: `test_impact.TestImpact.test_impact_no_repo_starcode` (`run-all` em vez de `selected`, motivo `grafo incompleto: src/orca/src/scene.test.ts: chaves ou parênteses desbalanceados`). Vem do analisador de `scripts/impact.py` diante do `scene.test.ts` de T3/T4; não é do `dist/` e a correção está fora do `May change` deste ticket.

## Limitações

- **Captura e troca real de estado não executadas.** O plugin instalado `local.starcode-ponte` 1.9.0 vem de `F:\Projetos\StarCode\dist\orca` (contentHash `98f39fb5…fd0b4`), diferente deste `dist` (contentHash `ba652e80…35770`). `orca plugin shot` só aceita plugin-key instalada, não diretório. Carregar este `dist` (`orca plugin dev load`) sobrescreve a chave instalada e exige aprovar as capabilities `workspace:read`, `agent:read`, `workspace:write` e `agent:launch` com fingerprint; isso não foi feito sem autorização do usuário.
- Não há preview isolado com outro id na CLI (`orca plugin dev load/watch` usam a chave do manifesto; `plugin check` não alcança o app). Um id distinto exigiria uma cópia do `dist` com manifesto alterado, fora do que o build gera.
- Pendente para fechar o aceite: o usuário aprova e carrega este `dist` (ou o reinstala a partir do worktree) e então rodam-se `orca plugin shot local.starcode-ponte --panel ponte-cena --width 240` e `--width 360` antes e depois de uma troca real de estado de agente, salvando em `docs/aceite/ponte-viva/`.

## Reexecução do aceite (SC-224, T8)

Executado em 2026-11-23 sobre `HEAD` 6510245 (T7 integrada). Resultado geral: **parcial**. Gates automáticos verdes; captura nova e troca real na Orca **não** feitas.

### Gates executados (todos verdes)

- `python tools/build.py` regenerou `dist/` sem diferença (`git status` limpo) e `python tools/build.py --check`: OK. `orca plugin inspect dist/orca`: contentHash `b2b3cece…a4ffe`, 27 arquivos.
- `orca plugin test src/orca`: 114 testes, 114 passaram, 0 falhas. Cobre C1, C2, C4, C11, C12, C15, C16, C17, C21 e C22 pelos nomes exatos das linhas Proof.
- `python -m unittest discover -s tests`: 1116 testes, OK (1 ignorado). A falha de `test_impact_no_repo_starcode` do aceite anterior foi corrigida em SC-221 (correção).
- `python scripts/check_decisions.py`: OK. `claude plugin validate dist/claude --strict`: passou.

### Evidências reais e sintéticas

- **Reais (Orca, build antigo)**: `docs/aceite/ponte-viva/orca-240.png`, `orca-360.png` e as `-revisada` são capturas de `orca plugin shot` do plugin instalado a partir de `F:\Projetos\StarCode\dist\orca` (contentHash `98f39fb5…fd0b4`), anteriores a T5 a T7. Comprovam legibilidade e identidade daquele build, não deste `dist`.
- **Sintéticas**: as renderizações de `orca plugin test` e `orca plugin check` (stand-in, sem o app) provam C15, C16, C17 por asserção, não por captura.
- **Não comprovado**: capturas de 240 e 360 px do `dist` atual; troca real de presença (R4) e vínculo real de sessão e worktree (R21, R22) com agentes da Orca; verificação manual de teclado e de leitor de tela (R16). A comparação com `referencias/ponte-conceito.png` e `tripulacao-conceito.png` não foi refeita.
- **Limitação da prova de acessibilidade (SC-216, achado 3)**: `scene.test.ts` exercita os ouvintes (teclado, `aria-pressed`, `role="status"`) em elementos simulados; isso prova a lógica, não a navegação real por Tab e Esc nem o anúncio por leitor de tela. Nenhuma dessas duas provas foi feita em ambiente real e nenhum resultado foi inventado: dependem do usuário carregar o `dist` na Orca e rodar o roteiro de teclado e leitor de tela abaixo.

### Por que não foi feito

`local.starcode-ponte` está `pending` (`needsReconsent: true`) e vem de outro caminho e hash. Para capturar este `dist` é preciso `orca plugin dev load` ou reinstalar, o que substitui a chave instalada e exige aprovar `workspace:read`, `agent:read`, `workspace:write` e `agent:launch` (trusted-worker). O brief não traz essa autorização, então nada foi carregado, instalado ou aprovado.

### Para fechar

O usuário autoriza carregar o `dist` e aprovar as quatro capacidades; então: `orca plugin shot local.starcode-ponte --panel ponte-cena --width 240` e `--width 360` antes e depois de uma troca real de estado de agente, salvos em `docs/aceite/ponte-viva/`, e um roteiro de teclado e leitor de tela (Tab, Esc, `aria-pressed`, anúncio de `role="status"`).
