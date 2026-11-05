"""validate_verification.py: the completion gate of a feature (plan 4.3, 4.6).

Adapted from tlc-spec-driven `scripts/validate_verification.py` (Felipe Rodrigues, github.com/felipfr,
CC-BY-4.0). Changes: StarCode layout and the shared parser in gates_common, screen/walk/round rules removed
(D25), degraded verification (`**Verification:** degraded | self-verified`, Git mode 1) as a warning that
`--strict` turns into an error, findings closed by a real commit, PT-BR messages, a Result for run_gates.

A feature is done when proofs.md shows every proof green at HEAD on a clean tree, the verifier (Q) judged
every check in verification.md, and each finding is closed by a commit. It reads the artifacts and Git,
never the target code.

  ERRO  no proofs.md or no verification.md
  ERRO  proofs.md written at another commit than HEAD (later commits that touch only .specs/ are fine), or
        on a dirty tree (Git mode 1 only with degraded)
  ERRO  a check of `## Checks` with no `pass` row in proofs.md; `**Build**:` commands and no passing Build row
  ERRO  verification.md with no `## Checks` table, or a check with no row or no test in it
  ERRO  verification.md with no `## Findings`, or a finding whose `Closed` cell names no commit of this repo
        (Git mode 1: `degradada (modo 1)` instead of a commit, only with degraded verification)
  ERRO  spec.md or tasks.md with no `**Approved**: <date> - user: "<words>"`
  AVISO verificação degradada (`degraded`, `self-verified` or Git mode 1); with --strict it is an ERRO

Usage: python validate_verification.py [feature] [--root DIR] [--strict]
Exit 0 ok, 1 the feature is not done, 2 usage error.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gates_common as gc  # noqa: E402

HEAD_RE = re.compile(r"\*\*HEAD\*\*\s*:\s*`?([0-9a-f]{4,40})", re.IGNORECASE)
TREE_RE = re.compile(r"\*\*Tree\*\*\s*:\s*(.+)", re.IGNORECASE)
DEGRADED_RE = re.compile(r"\*\*Verification:?\*\*\s*:?\s*\**\s*(degraded|self-verified)", re.IGNORECASE)
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
MODE1_CLOSED = "degradada (modo 1)"


def _git(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return p.returncode, p.stdout.strip()


def _is_commit(root: Path, sha: str) -> bool:
    code, _ = _git(root, "cat-file", "-e", f"{sha}^{{commit}}")
    return code == 0


def _only_specs_since(root: Path, sha: str) -> bool:
    """True when every commit after `sha` touches only .specs/ (proofs.md and verification.md being
    committed after the run): the proofs still describe the code at HEAD."""
    code, out = _git(root, "diff", "--name-only", f"{sha}..HEAD")
    if code != 0:
        return False
    return all(p.replace("\\", "/").startswith(".specs/") for p in out.splitlines() if p.strip())


def _tables(lines: list[str]) -> list[tuple[list[str], list[list[str]]]]:
    """Every markdown table in lines: (lowercased header, data rows)."""
    out, buf = [], []
    for ln in lines + [""]:
        s = ln.strip()
        if s.startswith("|"):
            buf.append(s)
            continue
        if buf:
            rows = [[c.strip() for c in r.strip("|").split("|")] for r in buf
                    if not (re.match(r"^\|?[\s:|-]+\|?$", r) and "-" in r)]
            if len(rows) >= 2:
                out.append(([c.lower() for c in rows[0]], rows[1:]))
            buf = []
    return out


def _col(header: list[str], *names: str) -> int | None:
    for i, cell in enumerate(header):
        if any(n in cell for n in names):
            return i
    return None


def _cell(row: list[str], i: int | None) -> str:
    return row[i].strip() if i is not None and i < len(row) else ""


def evaluate(feature: str | None, root: Path, strict: bool = False) -> gc.Result:
    res = gc.Result("validate_verification")
    try:
        fdir = gc.resolve_feature(feature, root, "spec.md")
    except LookupError as e:
        res.usage_error = str(e)
        return res
    res.target = gc.feature_root_hint(fdir)
    proj = gc.project_root(fdir)
    spec, tasks = fdir / "spec.md", fdir / "tasks.md"
    checks_src = tasks if tasks.exists() else spec
    checks_lines = gc.read_lines(checks_src)
    checks, _, build = gc.read_checks(checks_lines)
    build = [] if len(build) == 1 and build[0].lower().startswith("none") else build
    ids = [c.cid for c in checks]

    for art in [spec] + ([tasks] if tasks.exists() else []):
        if not gc.approved(gc.read_lines(art)):
            res.errors.append(f"{art.name} sem `**Approved**: <AAAA-MM-DD> - user: \"<palavras do usuário>\"`")

    vpath, ppath = fdir / "verification.md", fdir / "proofs.md"
    vlines = gc.read_lines(vpath) if vpath.exists() else []
    degraded = any(DEGRADED_RE.search(ln) for ln in vlines)

    # proofs.md: written at HEAD, clean tree, every check and the Build passing.
    if not ppath.exists():
        res.errors.append("falta proofs.md: rode `run_gates.py proofs <feature>` (check_proofs.py)")
    else:
        plines = gc.read_lines(ppath)
        body = "\n".join(plines)
        m = HEAD_RE.search(body)
        code, head = _git(proj, "rev-parse", "HEAD")
        if not m:
            res.errors.append("proofs.md sem `**HEAD**`: rode check_proofs.py de novo")
        elif code == 0 and not head.startswith(m.group(1)) and not _only_specs_since(proj, m.group(1)):
            res.errors.append(f"proofs.md foi gravado em {m.group(1)} e o HEAD é {head[:7]}: rode check_proofs.py de novo")
        tree = TREE_RE.search(body)
        tree_val = tree.group(1).strip().lower() if tree else ""
        mode1 = tree_val.startswith("dirty (modo 1)")
        if tree_val.startswith("dirty"):
            if mode1 and degraded:
                res.warnings.append("proofs.md rodou em árvore suja (modo 1): vale só como verificação degradada")
            else:
                res.errors.append("proofs.md rodou com mudanças não commitadas: commite e rode check_proofs.py de novo"
                                  + ("" if not mode1 else " (no modo 1, marque `**Verification:** degraded`)"))
        seen: dict[str, bool] = {}
        for header, rows in _tables(plines):
            ci, ri = _col(header, "check"), _col(header, "result")
            if ci is None or ri is None:
                continue
            for r in rows:
                cid, result = _cell(r, ci), _cell(r, ri).lower()
                ok = result.startswith("pass")
                seen[cid] = seen.get(cid, True) and ok
                if not ok:
                    res.errors.append(f"proofs.md: {cid} está '{_cell(r, ri)[:40]}'")
        for cid in ids:
            if cid not in seen:
                res.errors.append(f"proofs.md sem linha para {cid}: rode check_proofs.py de novo")
        if build and "Build" not in seen:
            res.errors.append("`**Build**:` tem comandos e proofs.md não tem linha Build: rode check_proofs.py de novo")

    # verification.md: the Q's judgement of every check, and every finding closed.
    if not vpath.exists():
        res.errors.append("falta verification.md: o Q (verificador independente) ainda não rodou")
        return res
    vchecks = gc.section(vlines, "Checks")
    judged: dict[str, str] = {}
    for header, rows in _tables(vchecks or []):
        ci, ti = _col(header, "check"), _col(header, "test")
        if ci is None or ti is None:
            continue
        for r in rows:
            judged[_cell(r, ci).strip("*` ")] = _cell(r, ti)
    if not judged:
        res.errors.append("verification.md sem tabela em `## Checks` (| Check | Test | Holds |)")
    else:
        for cid in ids:
            if cid not in judged:
                res.errors.append(f"verification.md: {cid} sem linha em `## Checks`")
            elif not judged[cid] or judged[cid] in ("-", "—"):
                res.errors.append(f"verification.md: {cid} sem o teste que o Q conferiu")
    findings = gc.section(vlines, "Findings")
    if findings is None:
        res.errors.append("verification.md sem `## Findings` (use `None.` quando não houver achados)")
    else:
        for header, rows in _tables(findings):
            fi, cl = _col(header, "finding"), _col(header, "closed")
            if cl is None:
                res.errors.append("`## Findings` sem a coluna `Closed`")
                continue
            for r in rows:
                name, closed = _cell(r, fi)[:50] or "achado", _cell(r, cl)
                if MODE1_CLOSED in closed.lower():
                    if not degraded:
                        res.errors.append(f"achado '{name}': `{MODE1_CLOSED}` só vale com `**Verification:** degraded`")
                    continue
                shas = SHA_RE.findall(closed)
                if not shas:
                    res.errors.append(f"achado '{name}' sem commit em `Closed`: corrija e cite o commit (ciclo 4.6)")
                elif not any(_is_commit(proj, s) for s in shas):
                    res.errors.append(f"achado '{name}': `Closed` cita {shas[0]}, que não é commit deste repo")

    if degraded or any("modo 1" in w for w in res.warnings):
        msg = "verificação degradada: Q no mesmo modelo/família, self-verified ou modo 1"
        (res.errors if strict else res.warnings).append(msg)
    return res


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="validate_verification.py", description="Gate de conclusão da feature.")
    p.add_argument("feature", nargs="?")
    p.add_argument("--root", default=".")
    p.add_argument("--strict", action="store_true", help="verificação degradada vira erro")
    a = p.parse_args(argv)
    res = evaluate(a.feature, Path(a.root).resolve(), a.strict)
    print(res.report())
    if res.usage_error:
        return 2
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
