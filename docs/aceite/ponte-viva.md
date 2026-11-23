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
