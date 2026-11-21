**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE. Sem achados que bloqueiem o merge, só um nit.

- **Restore:** passa a ler o `tasks.md` ou o `spec.md` do commit do snapshot (`run_git show`, num diretório temporário). Quando nenhum dos dois existe, recusa com código 2.
- **Capture:** valida o host e o `--out` antes de abrir a aba. O host é lido com `urlsplit`, em minúsculas, com colchetes no IPv6 e com recusa da porta inválida. Pelas sondas, nem userinfo nem fragmento enganam o filtro.
- **Veredito do `screens.md`:** casa pelo último segmento exato.
- **`_png`:** percorre os chunks pelo comprimento declarado e recusa chunk truncado ou `IDAT` vazio.
- **Nit W1:** uma falha de git que não é ausência (código 124 ou 127) aparece como "snapshot sem tasks.md nem spec.md". O efeito é seguro, porque a restauração é recusada, mas a mensagem engana.

## Achados

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | nit | `scripts/snapshot.py:174` | Todo código diferente de 0 no `git show`, inclusive 124 (tempo esgotado) e 127 (git ausente), conta como arquivo ausente. A recusa sai com a mensagem de snapshot sem spec (linha 185). A recusa é segura, mas aponta a causa errada. | `scripts/snapshot.py:174` | aberto |

## Escada determinística
- CI local em 6102416 (evidência do PR): `build --check`, `check_decisions`, `claude plugin validate --strict` e a suíte inteira (1075 testes, 1 pulado), todos verdes.
- Módulos tocados, todos OK: `test_restauracao_e_telas` 9, `test_screens` 11, `test_validate_verification_screens` 11, `test_snapshot` 7 e `test_images` 9.
- Sonda de `url_host`/`host_allowed`:
  - recusados: `localhost@evil.com`, `evil.com#@localhost` e `a.localhost.evil.com`;
  - aceitos: `LOCALHOST:3000` e `[::1]:80`;
  - porta inválida dá host vazio e é recusada.
- `scan_bypasses.py`: 1 candidato, descartado. É o `screens.py:170`, um `noqa: B018` numa expressão que existe para levantar `ValueError` quando a porta é inválida.

## Pesquisa
Nenhuma superfície externa nova: só a biblioteca padrão (`urllib.parse.urlsplit`, `struct` e `tempfile`). Conferi o comportamento do `urlsplit` por sonda local.
