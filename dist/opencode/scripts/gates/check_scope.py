"""check_scope.py: did a ticket change only its own files, and leave the Picard's records alone? (D19, D28)

Runs before the Picard integrates a ticket branch into the feature integration branch. It reads the
ticket's `**May change**:` in tasks.md and the files changed in a commit range.

  ERRO  a changed file outside the ticket's `May change` (an entry ending in `/` covers the folder;
        glob patterns are allowed)
  ERRO  `.specs/STATE.md` changed (only the Picard writes it)
  ERRO  the `## Handoff` section of context.md, spec.md or tasks.md of any feature changed
  ERRO  no commit in the range (the worker did not commit)

  MEDIUM (no tasks.md): the allowed list is the spec's `**May change**:` line; without it, a warning.

Usage: python check_scope.py <feature> <ticket> <base>..<head> [--root DIR]
Exit 0 ok, 1 out of scope, 2 usage error.
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gates_common as gc  # noqa: E402
import validate_tasks as vt  # noqa: E402

ARTIFACTS = ("context.md", "spec.md", "tasks.md")


def _git(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, encoding="utf-8", errors="replace",
                       stdin=subprocess.DEVNULL)
    return p.returncode, p.stdout


def allowed(path: str, patterns: list[str]) -> bool:
    p = gc.norm_path(path)
    for pat in patterns:
        pat = gc.norm_path(pat)
        if pat.endswith("/"):
            if p.startswith(pat):
                return True
        elif p == pat or fnmatch.fnmatch(p, pat):
            return True
    return False


def handoff_text(text: str) -> str:
    lines = text.splitlines()
    body = gc.section(lines, "Handoff")
    return "\n".join(body).strip() if body is not None else ""


def find_task(fdir: Path, ticket: str) -> vt.Task | None:
    tasks = vt.parse_tasks(gc.read_lines(fdir / "tasks.md"))
    want = ticket.upper()
    for t in tasks:
        linear = (t.value("Linear") or "").upper()
        if t.tid == want or (linear and want in gc.LINEAR_ID_RE.findall(linear)):
            return t
    return None


def spec_may_change(fdir: Path) -> list[str]:
    """MEDIUM feature (no tasks.md): the paths of the spec's `**May change**:` line (empty line = absent)."""
    return gc.split_paths(gc.field_value(gc.read_lines(fdir / "spec.md"), "May change") or "")


def spec_linear(fdir: Path) -> list[str]:
    return gc.LINEAR_ID_RE.findall((gc.field_value(gc.read_lines(fdir / "spec.md"), "Linear") or "").upper())


def changed_files(root: Path, rng: str) -> tuple[list[str] | None, list[str]]:
    code, names = _git(root, "diff", "--name-only", rng)
    if code != 0:
        return None, []
    code, commits = _git(root, "rev-list", rng)
    return [n.strip() for n in names.splitlines() if n.strip()], [c for c in commits.split() if c]


def evaluate(feature: str | None, ticket: str, rng: str, root: Path) -> gc.Result:
    res = gc.Result("check_scope")
    try:
        try:
            fdir = gc.resolve_feature(feature, root, "tasks.md")
        except LookupError:
            fdir = gc.resolve_feature(feature, root, "spec.md")
    except LookupError as e:
        res.usage_error = str(e)
        return res
    if ".." not in rng:
        res.usage_error = f"intervalo inválido {rng!r}: use <base>..<head>"
        return res
    medium = not (fdir / "tasks.md").exists()
    res.target = f"{gc.feature_root_hint(fdir)} {ticket} {rng}"
    patterns: list[str] | None
    if medium:
        if not (fdir / "spec.md").exists():
            res.usage_error = f"feature sem tasks.md nem spec.md em {gc.feature_root_hint(fdir)}"
            return res
        ids = spec_linear(fdir)
        if ticket.upper() != "T1" and ticket.upper() not in ids:
            res.usage_error = (f"ticket {ticket} não é desta feature MÉDIA "
                               f"(use {ids[0] if ids else 'o ID do Linear'} ou T1)")
            return res
        tid = ticket
        patterns = spec_may_change(fdir) or None
        if patterns is None:
            res.warnings.append("spec sem **May change**: escopo não conferido")
    else:
        task = find_task(fdir, ticket)
        if task is None:
            res.usage_error = f"ticket {ticket} não existe em tasks.md"
            return res
        tid = task.tid
        patterns = task.may_change
    proj = gc.project_root(fdir)
    files, commits = changed_files(proj, rng)
    if files is None:
        res.usage_error = f"git não leu o intervalo {rng}"
        return res
    if not commits:
        res.errors.append(f"nenhum commit em {rng}: o worker não commitou o ticket")
    base, head = rng.split("..", 1)
    for f in files:
        n = gc.norm_path(f)
        if n == ".specs/STATE.md":
            res.errors.append("`.specs/STATE.md` alterado: só o Picard escreve nele (D28)")
            continue
        if re.match(r"^\.specs/features/[^/]+/(" + "|".join(re.escape(a) for a in ARTIFACTS) + r")$", n):
            _, old = _git(proj, "show", f"{base}:{n}")
            _, new = _git(proj, "show", f"{head}:{n}")
            if handoff_text(old) != handoff_text(new):
                res.errors.append(f"`## Handoff` alterado em {n}: só o Picard escreve nele (D28)")
                continue
        if patterns is not None and not allowed(n, patterns):
            res.errors.append(f"{n}: fora do `May change` de {tid} ({', '.join(patterns) or 'vazio'})")
    return res


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="check_scope.py", description="Confere o escopo de arquivos de um ticket.")
    p.add_argument("feature")
    p.add_argument("ticket", help="T<n> ou o ID do Linear do ticket")
    p.add_argument("range", help="<base>..<head>")
    p.add_argument("--root", default=".")
    a = p.parse_args(argv)
    res = evaluate(a.feature, a.ticket, a.range, Path(a.root).resolve())
    print(res.report())
    if res.usage_error:
        return 2
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
