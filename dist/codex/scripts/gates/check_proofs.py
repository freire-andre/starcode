"""check_proofs.py: run every proof named in `## Checks`, as the project runs it, and write proofs.md.

Adapted from tlc-spec-driven `scripts/check_proofs.py` (Felipe Rodrigues, github.com/felipfr, CC-BY-4.0).
Changes: StarCode layout (`tasks.md ## Checks`, or `spec.md ## Checks` for a MEDIUM feature), the shared
parser in gates_common, screen and walk proofs removed (D25), `**Tree**: dirty (modo 1)` for Git mode 1
(D11), PT-BR messages, a Result object for run_gates.

A proof is the project's own command:
  **Run unit**: `python -m unittest discover -s tests -v 2>&1`   one command, run once
  Proof: run unit | test_x ... ok                                 the line the run must print
  Proof: `pytest tests/test_x.py`                                 run alone, judged by its exit code

A `run` proof passes only when every word after `|` appears, in that order, on one line of the run's
output, so a filter that selects nothing reads "nenhum teste rodou" instead of a green exit code.
Commands run one at a time, each once, from the project root. On Windows they run in Git for Windows'
bash, because proofs are written for a POSIX shell.

Usage: python check_proofs.py <feature> [--root DIR]
Writes .specs/features/<feature>/proofs.md. Exit 0 every proof passed on a clean tree, 1 otherwise,
2 usage error.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gates_common as gc  # noqa: E402

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
TAIL = 15
DIRTY_MARK = "dirty (modo 1)"
PROOF_TIMEOUT = 1800  # segundos por comando de prova (R4)
TIMEOUT_CODE = -1000
TIMEOUT_RESULT = "fail - tempo limite (1800 s)"


def checks_path(fdir: Path) -> Path:
    tasks = fdir / "tasks.md"
    return tasks if tasks.exists() else fdir / "spec.md"


def find_bash() -> str | None:
    """Git for Windows' bash.exe, or None. The `bash` on PATH may be WSL's launcher, so the one beside git
    comes first."""
    try:
        p = subprocess.run(["git", "--exec-path"], capture_output=True, encoding="utf-8", errors="replace",
                           stdin=subprocess.DEVNULL)
        if p.returncode == 0:
            bash = Path(p.stdout.strip()).parent.parent.parent / "bin" / "bash.exe"
            if bash.is_file():
                return str(bash)
    except OSError:
        pass
    bash = shutil.which("bash")
    if bash and "\\system32\\" not in bash.lower() and "windowsapps" not in bash.lower():
        return bash
    return None


def shell_of() -> tuple[str | None, str]:
    if os.name != "nt":
        return None, "/bin/sh"
    bash = find_bash()
    return (bash, bash) if bash else (None, "cmd.exe (Git Bash não encontrado)")


def _kill_tree(p: subprocess.Popen) -> None:
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True,
                           stdin=subprocess.DEVNULL, timeout=30)
        else:
            os.killpg(p.pid, 9)
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        p.kill()
    except OSError:
        pass


def run(root: Path, cmd: str, bash: str | None) -> tuple[int, str]:
    argv = [bash, "-c", cmd] if bash else cmd
    extra = {} if os.name == "nt" else {"start_new_session": True}
    p = subprocess.Popen(argv, shell=bash is None, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         stdin=subprocess.DEVNULL, **extra)
    try:
        out, err = p.communicate(timeout=PROOF_TIMEOUT)
    except subprocess.TimeoutExpired:
        _kill_tree(p)
        try:
            p.communicate(timeout=5)
        except (subprocess.SubprocessError, OSError):
            pass
        return TIMEOUT_CODE, ""
    text = (out or b"").decode("utf-8", errors="replace") + (err or b"").decode("utf-8", errors="replace")
    return p.returncode, ANSI_RE.sub("", text)


DOC_HEAD = re.compile(r"^\s*\w+ \([\w.]*\.[\w.]*\)\s*$")  # `test_x (m.C.test_x)`: unittest verboso com docstring


def _word_rx(w: str) -> str:
    return ((r"(?<!\w)" if re.match(r"\w", w[0]) else "") + re.escape(w)
            + (r"(?!\w)" if re.match(r"\w", w[-1]) else ""))


def sees(output: str, expected: str) -> bool:
    """Every word of `expected` on one line of `output`, in order, anything between them.
    A word that starts/ends with a word character has no word character glued on that side (R2);
    a `name (a.b.c)` line is also tried joined to the next one (R3)."""
    words = expected.split()
    if not words:
        return False
    rx = re.compile(".*?".join(_word_rx(w) for w in words))
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if rx.search(line):
            return True
        if i + 1 < len(lines) and DOC_HEAD.match(line) and rx.search(line.rstrip() + " " + lines[i + 1]):
            return True
    return False


def git(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return p.returncode, p.stdout


def dirty_paths(root: Path) -> list[str]:
    """Uncommitted paths outside .specs/: the proofs ran on the working tree, not on HEAD."""
    code, out = git(root, "status", "--porcelain", "--untracked-files=all")
    if code != 0:
        return []
    paths = [ln[3:].strip().strip('"') for ln in out.splitlines() if len(ln) > 3]
    return [p for p in paths if p and not p.replace("\\", "/").startswith(".specs/")]


def git_head(root: Path) -> str:
    code, out = git(root, "rev-parse", "--short", "HEAD")
    return out.strip() if code == 0 else "unknown"


def _tail(output: str) -> list[str]:
    return [ln.replace("```", "'''") for ln in output.strip().splitlines()[-TAIL:]] or ["(sem saída)"]


def _cell(text: str, width: int = 110) -> str:
    return text.replace("|", "/").replace("`", "")[:width]


def evaluate(feature: str | None, root: Path, write: bool = True) -> gc.Result:
    res = gc.Result("check_proofs")
    try:
        fdir = gc.resolve_feature(feature, root, "spec.md")
    except LookupError as e:
        res.usage_error = str(e)
        return res
    src = checks_path(fdir)
    res.target = gc.feature_root_hint(src)
    if not src.exists():
        res.usage_error = f"sem tasks.md nem spec.md em {fdir}"
        return res
    lines = gc.read_lines(src)
    if gc.section(lines, "Checks") is None:
        res.usage_error = f"{src.name} não tem `## Checks`"
        return res
    checks, runs, build = gc.read_checks(lines)
    if len(build) == 1 and build[0].lower().startswith("none"):
        build = []
    proj = gc.project_root(fdir)
    bash, shell_label = shell_of()

    used_runs: list[str] = []
    lone: list[str] = []
    for c in checks:
        for proof in c.proofs:
            m = gc.RUN_PROOF_RE.match(proof)
            if m:
                if m.group(1) in runs and m.group(1) not in used_runs:
                    used_runs.append(m.group(1))
            elif proof and proof not in lone:
                lone.append(proof)
    for name in runs:  # a declared Run no Proof cites still runs once and is recorded
        if name not in used_runs:
            used_runs.append(name)
    results: dict[str, tuple[int, str]] = {}
    for name in used_runs:
        results.setdefault(runs[name], run(proj, runs[name], bash))
    for proof in lone:
        results.setdefault(proof, run(proj, proof, bash))

    rows: list[tuple[str, str, str]] = []
    for c in checks:
        for proof in c.proofs or [""]:
            m = gc.RUN_PROOF_RE.match(proof) if proof else None
            result = "pass"
            if not proof:
                result, proof = "fail - sem prova", "(nenhuma)"
            elif m:
                name = m.group(1)
                if name not in runs:
                    result = f"fail - não há linha `Run {name}:`"
                else:
                    code, output = results[runs[name]]
                    if code == TIMEOUT_CODE:
                        result = TIMEOUT_RESULT
                    elif not sees(output, (m.group(2) or "").strip().strip("`")):
                        result = "fail" if code else "fail - nenhum teste rodou (linha esperada ausente)"
            elif results[proof][0] == TIMEOUT_CODE:
                result = TIMEOUT_RESULT
            elif results[proof][0]:
                result = f"fail - exit {results[proof][0]}"
            rows.append((c.cid, proof, result))
    for name in used_runs:
        code, _ = results[runs[name]]
        if code:
            rows.append((f"Run {name}", runs[name], TIMEOUT_RESULT if code == TIMEOUT_CODE else f"fail - exit {code}"))
    for cmd in build:
        code, output = run(proj, cmd, bash)
        out_lines = output.strip().splitlines()
        err = next((ln for ln in out_lines if "error" in ln.lower() or "erro" in ln.lower()),
                   out_lines[-1] if out_lines else "")
        rows.append(("Build", cmd, "pass" if code == 0 else TIMEOUT_RESULT if code == TIMEOUT_CODE
                     else f"fail - {_cell(err.strip(), 100)}"))
    failed = [r for r in rows if r[2] != "pass"]

    dirty = dirty_paths(proj)
    tree = "clean" if not dirty else f"{DIRTY_MARK} - " + ", ".join(dirty[:5])
    out = [f"# {fdir.name} proofs", "",
           f"**HEAD**: {git_head(proj)}",
           f"**Tree**: {tree}",
           f"**Shell**: {shell_label}",
           f"**Result**: {len(rows) - len(failed)} pass, {len(failed)} fail", "",
           "| Check | Proof | Result |", "| --- | --- | --- |"]
    out += [f"| {c} | `{_cell(p)}` | {r} |" for c, p, r in rows]
    if results:
        out += ["", "## Output", ""]
        for name in used_runs:
            code, output = results[runs[name]]
            out += [f"`Run {name}` - exit {code}", "", "```", *_tail(output), "```", ""]
        for proof in lone:
            code, output = results[proof]
            out += [f"`{_cell(proof)}` - exit {code}", "", "```", *_tail(output), "```", ""]
    if write:
        (fdir / "proofs.md").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8", newline="\n")

    for c, p, r in failed:
        res.errors.append(f"{c}: {r} ({p[:80]})")
    if dirty:
        res.errors.append(f"árvore com mudanças não commitadas ({', '.join(dirty[:5])}): `**Tree**: {DIRTY_MARK}`; "
                          "as provas não valem para o HEAD")
    if not rows:
        res.errors.append("nenhuma prova para rodar em `## Checks`")
    return res


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="check_proofs.py", description="Roda as provas de `## Checks` e grava proofs.md.")
    p.add_argument("feature", nargs="?")
    p.add_argument("--root", default=".")
    a = p.parse_args(argv)
    res = evaluate(a.feature, Path(a.root).resolve())
    print(res.report())
    if res.usage_error:
        return 2
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
