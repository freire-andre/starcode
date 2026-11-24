# teste-git-linux proofs

**HEAD**: 4ab0195
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 2 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `python -m unittest discover -s tests -p "test_falhas_start_settle.py" -k test_run_git_argumentos_invalidos` | pass |
| Build | `python tools/build.py --check` | pass |

## Output

`python -m unittest discover -s tests -p "test_falhas_start_settle.py" -k test_run_git_argumentos_invalidos` - exit 0

```
.
----------------------------------------------------------------------
Ran 1 test in 0.676s

OK
```
