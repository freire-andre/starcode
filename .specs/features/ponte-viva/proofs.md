# ponte-viva proofs

**HEAD**: 394920a
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 25 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / ponte viva identifica os 12 integrantes` | pass |
| C2 | `run unit / ponte viva limita a seis integrantes` | pass |
| C3 | `run unit / ponte viva mantém presença sem rodízio` | pass |
| C4 | `run unit / ponte viva anima sem alterar estado` | pass |
| C5 | `run unit / ponte viva representa trabalho` | pass |
| C6 | `run unit / ponte viva representa ociosidade` | pass |
| C7 | `run unit / ponte viva distingue estados` | pass |
| C8 | `run unit / ponte viva não inventa atividade` | pass |
| C9 | `run unit / ponte viva lista os 12 integrantes` | pass |
| C10 | `run unit / ponte viva permite selecionar integrante` | pass |
| C11 | `run unit / ponte viva atualiza por evento` | pass |
| C12 | `run unit / ponte viva reconcilia automaticamente` | pass |
| C13 | `run unit / ponte viva informa dados desatualizados` | pass |
| C14 | `run unit / ponte viva descarta resposta obsoleta` | pass |
| C15 | `run unit / ponte viva mantém rótulos legíveis` | pass |
| C16 | `run unit / ponte viva expõe lista acessível` | pass |
| C17 | `run unit / ponte viva respeita movimento reduzido` | pass |
| C18 | `run unit / ponte viva preserva transição em atualização repetida` | pass |
| C19 | `run unit / ponte viva prioriza presença estável` | pass |
| C20 | `run unit / ponte viva mantém integrante já presente` | pass |
| C21 | `run unit / ponte viva vincula sessão ao worktree` | pass |
| C22 | `run unit / ponte viva não infere troca sem vínculo` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `python scripts/check_decisions.py` | pass |
| Build | `claude plugin validate dist/claude --strict` | pass |

## Output

`Run unit` - exit 0

```
[starcode-ponte] snapshot falhou: boom
[starcode-ponte] snapshot falhou: boom
[starcode-ponte] snapshot falhou: boom
[starcode-ponte] snapshot falhou: boom
✔ ponte viva descarta resposta obsoleta (466.9876ms)
✔ ponte viva preserva transição em atualização repetida (10.386ms)
ℹ tests 117
ℹ suites 0
ℹ pass 117
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 4192.4436
5 test file(s) passed (node).
```
