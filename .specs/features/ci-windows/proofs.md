# ci-windows proofs

**HEAD**: 0bf4f5e
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 2 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `python -m unittest discover -s tests -p "test_helpers_tmp.py"` | pass |
| Build | `python tools/build.py --check` | pass |

## Output

`python -m unittest discover -s tests -p "test_helpers_tmp.py"` - exit 0

```
.
----------------------------------------------------------------------
Ran 1 test in 0.433s

OK
```
