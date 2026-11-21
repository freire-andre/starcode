**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE.

- **`parse_dispatch_entry`:** lê o formato do `start` (posicional) e o antigo (campos com chave) sem confundir os dois. Campo com chave nunca vira modelo nem horário, e o `blocked` no fim é reconhecido.
- **`overdue` e `settle`:** trocaram o corte próprio pelo leitor comum e mantêm a saída de antes; o `overdue` usa `issues_text`, e não as issues normalizadas.
- **Painel:**
  - o casamento de token considera letras e números Unicode;
  - o `issue.url` exige o prefixo `https://linear.app/`, com a barra;
  - o nome do worktree separa `/` e `\`.
- **CI:** o passo segue a sintaxe documentada de `::warning title=` e de `$GITHUB_STEP_SUMMARY`.

Um nit: a regex de ID do Linear agora existe em dois lugares. Ficaram fora do review os arquivos mecânicos (`dist/`).

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | nit | `scripts/handoff.py:158` | `LINEAR_ID_RE` repete a `LINEAR_TOKEN_RE`, que continua em uso em `linear_ids` (`scripts/ponte.py:222`). Se uma das duas mudar, o painel passa a ler as issues do `Dispatched` diferente do campo Linear. Sugestão: o `ponte.py` importar `handoff.LINEAR_ID_RE`. | `scripts/ponte.py:35` | open |

## Escada determinística
- **CI na `aff73e5`** (evidência do PR): verdes o `python tools/build.py --check`, o `check_decisions`, o `claude plugin validate dist/claude --strict`, o `orca plugin validate src/orca --json` e a suíte inteira (1053 testes, 1 pulado).
- **Módulos tocados no head `6d639a6`:** todos OK.
  - `test_ponte_manutencao`: 7 testes;
  - `test_ponte`: 21;
  - `test_handoff`: 13;
  - `test_dispatch`: 56;
  - `test_orca_manifest`: 2;
  - `test_ci_workflow`: 15.
- **`orca plugin test src/orca`** no worktree do drive da Orca, em `6d639a6`: 74 ok, 0 falhas.
- **`scan_bypasses.py`:** 7 candidatos, e nenhum vira achado. São 6 `noqa: E731` (o lambda de `handoff.py` e as cópias em `dist/`) e 1 `as any` numa fixture de teste do painel.

## Pesquisa
- Context7 `/websites/github_en_actions`, sobre os comandos de workflow: `::warning title={title}::{message}` e `echo ... >> $GITHUB_STEP_SUMMARY`. Fonte: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands
