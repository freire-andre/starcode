**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE. Sem achados que bloqueiem o merge, só um nit.

- **`orca_cli.run`:** concentra a resolução do executável, o env, o tempo limite e a leitura do JSON, e nunca levanta exceção.
  - O env sai sem `NODE_*`, `ELECTRON_RUN_AS_NODE`, `ORCA_NODE_OPTIONS` e `ORCA_CLI_COMMAND`.
  - O campo `kind` separa a falha de execução do código devolvido pelo `orca`.
- **`screens.py` e banner:** decidem a mensagem pelo `kind` e mantêm os textos anteriores.
- **`dispatch.default_runner`:** só acrescenta o env quando o comando é `orca`.
- **`model_info`:** confere a forma antes de gravar o cache e memoriza por origem, inclusive o `None`. O `download` atualiza o valor memorizado.
- **Nit W1:** o `_run` do banner ignora `cmd[0]`.

## Achados

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | nit | `hooks/scripts/banner.py:36` | O `_run(cmd, ...)` repassa só `cmd[1:]` ao `orca_cli.run` e descarta `cmd[0]` sem conferir se ele é `orca`. Os dois chamadores (linhas 63 e 70) passam `orca`, mas a assinatura promete um comando genérico. | `hooks/scripts/banner.py:36` | aberto |

## Escada determinística
- CI local em 0f8c670 (evidência do PR): `build --check`, `check_decisions`, `claude plugin validate --strict` e a suíte inteira (1083 testes, 1 pulado), todos verdes.
- Módulos tocados, todos OK: `test_catalogo_e_orca` 8, `test_model_info` 27, `test_banner` 24, `test_screens` 11, `test_screens_flow` 4 e `test_dispatch_start` 17.
- `scan_bypasses.py`: 3 candidatos, descartados. São os `noqa: E402` nos imports do `orca_cli` (em `banner.py:29`, `dispatch.py:80` e `screens.py:26`), que seguem o padrão dos imports vizinhos.

## Pesquisa
Nenhuma superfície externa nova: só a biblioteca padrão. O comportamento do CLI da Orca segue o registrado em `DECISIONS.md` (F10-14) e em `.specs/stack/orca.md`. Por regra deste review, não houve sonda real.
