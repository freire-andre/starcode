"""validate_verification.py: the completion gate of a feature (plan 4.3, 4.6).

Adapted from tlc-spec-driven `scripts/validate_verification.py` (Felipe Rodrigues, github.com/felipfr,
CC-BY-4.0). Changes: StarCode layout and the shared parser in gates_common, screen rules back in phase 11
(F11-3: `screens.md` of the screen judge, rounds up to 2, pictures at the capture size; the walk is gone),
degraded verification (`**Verification:** degraded | self-verified`, Git mode 1) as a warning that
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
  ERRO  a `Closed` cell with a commit but no coverage (`C<n>` of the feature or an existing `test_<name>`), and a row of
        `## Checks`/`## Findings` whose cell count differs from the header (SC-199; `dispatch.py close-finding`)
  ERRO  `**Verification:** waived` on a spec that is not SMALL; on a SMALL one it replaces the Q tables (AVISO)
  ERRO  spec.md (not SMALL: the minimal PEQUENA spec has no approval, D-a) or tasks.md with no `**Approved**: <date> - user: "<words>"`
  ERRO  a feature has a binding capture cited by a requirement (a "feature with screens") and: no `screens.md`
        with a `Screen`/`Verdict` table, a verdict that is not `match...`, no `**Round**:` or round > 2, no
        `**Verifier**:`, a cited capture with no `<name>.running.png`, a picture whose CSS size differs from the
        capture's, or an unreadable image (ImageError, with the path)
  AVISO `**Pictures**: author's` (the judge judged the author's pictures); with --strict it is an ERRO
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
import images  # noqa: E402

HEAD_RE = re.compile(r"\*\*HEAD\*\*\s*:\s*`?([0-9a-f]{4,40})", re.IGNORECASE)
TREE_RE = re.compile(r"\*\*Tree\*\*\s*:\s*(.+)", re.IGNORECASE)
DEGRADED_RE = re.compile(r"\*\*Verification:?\*\*\s*:?\s*\**\s*(degraded|self-verified)", re.IGNORECASE)
WAIVED_RE = re.compile(r"\*\*Verification:?\*\*\s*:?\s*\**\s*waived(?: \(PEQUENA\))?\s*$", re.IGNORECASE)
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
MODE1_CLOSED = "degradada (modo 1)"
ROUND_RE = re.compile(r"\*\*Round\*\*\s*:\s*(\d+)", re.IGNORECASE)
VERIFIER_RE = re.compile(r"\*\*Verifier\*\*\s*:\s*\S", re.IGNORECASE)
PICTURES_RE = re.compile(r"\*\*Pictures\*\*\s*:\s*\**\s*(running|author)", re.IGNORECASE)
NOT_BINDING_RE = re.compile(r"(non|not|não)[- ](binding|vinculante)", re.IGNORECASE)


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


# --- tables with line numbers, closing of findings (SC-199) -------------------------------------------

COVER_ID_RE = re.compile(r"\bC\d+\b")
COVER_TEST_RE = re.compile(r"\btest_\w+")
SEP_ROW_RE = re.compile(r"^\|?[\s:|-]+\|?$")
CLOSED_DOT = "·"


def numbered_lines(text: str) -> list[tuple[int, str]]:
    """(1-based line number, rstripped text) of every line outside fenced code blocks."""
    out, in_fence = [], False
    for i, ln in enumerate(text.splitlines(), 1):
        if ln.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((i, ln.rstrip()))
    return out


def section_pairs(pairs: list[tuple[int, str]], name: str) -> list[tuple[int, str]] | None:
    """Like gc.section, over numbered lines."""
    pat = re.compile(r"^##\s+" + re.escape(name) + r"\s*\*?\s*$", re.IGNORECASE)
    start = next((i + 1 for i, (_, ln) in enumerate(pairs) if pat.match(ln.strip())), None)
    if start is None:
        return None
    body = []
    for item in pairs[start:]:
        lvl = gc.heading_level(item[1])
        if lvl and lvl <= 2:
            break
        body.append(item)
    return body


def cell_spans(line: str) -> list[tuple[int, int]]:
    """Character span of every cell of a table row, between its `|` (an escaped `&#124;` is not one)."""
    text = line.rstrip()
    pipes = [i for i, ch in enumerate(text) if ch == "|"]
    if not pipes:
        return []
    lead = text[:pipes[0]].strip() == ""
    starts = [pipes[0] + 1] if lead else [0]
    bounds = pipes[1:] if lead else pipes[:]
    spans, begin = [], starts[0]
    for b in bounds:
        spans.append((begin, b))
        begin = b + 1
    if begin < len(text) or not bounds:
        spans.append((begin, len(text)))
    return spans


class Table:
    def __init__(self, header: list[str], size: int):
        self.header, self.size = header, size
        self.rows: list[tuple[int, list[str], list[tuple[int, int]]]] = []  # (line, cells, spans)
        self.bad: list[tuple[int, int]] = []  # (line, cells)


def numbered_tables(body: list[tuple[int, str]]) -> list[Table]:
    out: list[Table] = []
    buf: list[tuple[int, str]] = []
    for item in body + [(0, "")]:
        if item[1].strip().startswith("|"):
            buf.append(item)
            continue
        rows = [(n, ln) for n, ln in buf if not (SEP_ROW_RE.match(ln.strip()) and "-" in ln)]
        buf = []
        if len(rows) < 2:
            continue
        hspans = cell_spans(rows[0][1])
        t = Table([rows[0][1][a:b].strip().lower() for a, b in hspans], len(hspans))
        for n, ln in rows[1:]:
            spans = cell_spans(ln)
            if len(spans) != t.size:
                t.bad.append((n, len(spans)))
            else:
                t.rows.append((n, [ln[a:b].strip() for a, b in spans], spans))
        out.append(t)
    return out


def feature_check_ids(fdir: Path) -> list[str]:
    src = fdir / "tasks.md" if (fdir / "tasks.md").exists() else fdir / "spec.md"
    checks, _, _ = gc.read_checks(gc.read_lines(src))
    return [c.cid for c in checks]


def defines_test(root: Path, name: str) -> bool:
    """True when some file under tests/ at HEAD defines `def <name>(`."""
    code, _ = _git(root, "grep", "-q", "-E", "-e", rf"^[[:space:]]*def {re.escape(name)}[[:space:]]*\(",
                   "HEAD", "--", "tests")
    return code == 0


def valid_cover(root: Path, fdir: Path, token: str) -> bool:
    if re.fullmatch(r"C\d+", token):
        return token in feature_check_ids(fdir)
    if re.fullmatch(r"test_\w+", token):
        return defines_test(root, token)
    return False


def cover_tokens(closed: str) -> list[str]:
    part = closed.split(CLOSED_DOT, 1)[1] if CLOSED_DOT in closed else closed
    return COVER_ID_RE.findall(part) + COVER_TEST_RE.findall(part)


def findings_table(vtext: str) -> tuple[list[tuple[int, str]], list[Table]]:
    """(numbered lines, tables of `## Findings`); raises ValueError when verification.md has no findings table."""
    pairs = numbered_lines(vtext)
    body = section_pairs(pairs, "Findings")
    if body is None:
        raise ValueError("verification.md sem `## Findings`")
    return pairs, [t for t in numbered_tables(body) if _col(t.header, "closed") is not None]


def close_finding(fdir: Path, root: Path, n: int, commits: list[str], covers: list[str]) -> str:
    """Writes `<sha7> · <cover>` in the `Closed` cell of finding n. ValueError (exit 2) names the problem;
    nothing is written then. Only the bytes of that cell change."""
    vpath = fdir / "verification.md"
    if not vpath.exists():
        raise ValueError("falta verification.md")
    raw = vpath.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"verification.md não é UTF-8: {exc}")
    _, tables = findings_table(text)
    if not tables:
        raise ValueError("`## Findings` sem tabela com a coluna `Closed`")
    for t in tables:
        if t.bad:
            line, m = t.bad[0]
            raise ValueError(f"verification.md:{line}: {m} células, o cabeçalho tem {t.size} (escape pipe como &#124;)")
    rows = [(t, r) for t in tables for r in t.rows]
    if n < 1 or n > len(rows):
        raise ValueError(f"achado {n} fora da faixa: a tabela tem {len(rows)} achado(s)")
    shorts = []
    for sha in commits:
        code, out = (1, "") if sha.startswith("-") or not sha else _git(root, "rev-parse", "--verify", "-q", f"{sha}^{{commit}}")
        if code != 0 or not out:
            raise ValueError(f"o commit {sha or '(vazio)'} não existe neste repositório")
        shorts.append(out[:7])
    for cov in covers:
        if not valid_cover(root, fdir, cov):
            raise ValueError(f"cobertura '{cov}' inválida: use um C<n> dos checks da feature ou um test_<nome> "
                             "definido como `def test_<nome>` em tests/ no HEAD")
    t, (line, _cells, spans) = rows[n - 1]
    ci = _col(t.header, "closed")
    a, b = spans[ci]
    lines = text.splitlines(keepends=True)
    old = lines[line - 1]
    body = old.rstrip("\r\n")
    eol = old[len(body):]
    new_cell = f" {', '.join(shorts)} {CLOSED_DOT} {', '.join(covers)} "
    lines[line - 1] = body[:a] + new_cell + body[b:] + eol
    vpath.write_bytes("".join(lines).encode("utf-8"))
    return f"achado {n} fechado: {', '.join(shorts)} {CLOSED_DOT} {', '.join(covers)}"


def _binding_captures(fdir: Path, res: gc.Result) -> list[Path]:
    """Captures with a binding `## Sources` line cited in backticks by a `**R<n>**` requirement (R5)."""
    try:
        caps = images.list_captures(fdir)
    except images.ImageError as exc:
        res.errors.append(str(exc))
        return []
    if not caps:
        return []
    lines = gc.read_lines(fdir / "spec.md")
    sources = gc.section(lines, "Sources") or []
    reqs = [ln for ln in (gc.section(lines, "Requirements") or []) if gc.REQ_LINE_RE.match(ln.strip())]
    found = []
    for cap in caps:
        name = re.escape(cap.name)
        ref = re.compile(rf"captures/{name}(?![\w@-])")
        line = next((x for x in sources if ref.search(x)), None)
        if line is None or NOT_BINDING_RE.search(line):
            continue
        cited = re.compile(rf"`(?:[^`]*/)?captures/{name}`")
        if any(cited.search(r) for r in reqs):
            found.append(cap)
    return found


def _check_screens(fdir: Path, strict: bool, res: gc.Result) -> None:
    """Screen judge rules (F11-3): screens.md, verdicts, round, verifier, pictures at the capture size."""
    caps = _binding_captures(fdir, res)
    if not caps:
        return
    spath = fdir / "screens.md"
    slines = gc.read_lines(spath) if spath.exists() else []
    body = "\n".join(slines)
    rows: list[tuple[str, str]] = []
    for header, trows in _tables(slines):
        si, vi = _col(header, "screen"), _col(header, "verdict")
        if si is None or vi is None:
            continue
        rows += [(_cell(r, si).strip("` "), _cell(r, vi)) for r in trows]
    if not rows:
        res.errors.append("a feature tem tela mas falta `screens.md` (juiz de telas)")
    for screen, verdict in rows:
        if not verdict.strip("*` ").lower().startswith("match"):
            res.errors.append(f"screens.md: a tela `{screen}` está '{verdict[:40]}', não `match`")
    for cap in caps:
        run_name = images.running_path(cap).name
        if not any(run_name in screen or cap.name in screen for screen, _ in rows):
            res.errors.append(f"screens.md sem veredito para `{cap.name}`")
    if spath.exists():
        m = ROUND_RE.search(body)
        if not m:
            res.errors.append("screens.md sem `**Round**:`")
        elif int(m.group(1)) > 2:
            res.errors.append("não há rodada 3: o que ainda difere vai para o usuário")
        if not VERIFIER_RE.search(body):
            res.errors.append("screens.md sem `**Verifier**:`")
        pm = PICTURES_RE.search(body)
        if pm and pm.group(1).lower() == "author":
            msg = "verificação degradada: o juiz julgou as fotos do autor"
            (res.errors if strict else res.warnings).append(msg)
    for cap in caps:
        run = images.running_path(cap)
        if not run.exists():
            res.errors.append(f"a captura `{cap.name}` não tem `{run.name}`")
            continue
        try:
            css = images.css_size(cap)
            pic = images.image_size(run)
        except images.ImageError as exc:
            res.errors.append(str(exc))
            continue
        if not images.same_css(pic, css):
            res.errors.append(f"`{run.name}` tem {pic[0]}x{pic[1]} e a captura tem {css[0]}x{css[1]}: "
                              "tire a foto no tamanho da captura")


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

    small = gc.size_of(gc.read_lines(spec)) == "SMALL"
    for art in [spec] + ([tasks] if tasks.exists() else []):
        if art == spec and small:
            continue  # D-a: the minimal PEQUENA spec carries no approval line
        err = gc.approval_error(gc.read_lines(art), fdir, art.name, art == tasks,
                                f"{art.name} sem `**Approved**: <AAAA-MM-DD> - user: \"<palavras do usuário>\"`")
        if err:
            res.errors.append(err)

    vpath, ppath = fdir / "verification.md", fdir / "proofs.md"
    vlines = gc.read_lines(vpath) if vpath.exists() else []
    degraded = any(DEGRADED_RE.search(ln) for ln in vlines)
    waived = any(WAIVED_RE.search(ln) for ln in vlines) and not degraded

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
    if waived and not small:
        res.errors.append("`**Verification:** waived` só vale para a PEQUENA")
    elif waived:
        res.warnings.append("Q dispensado (PEQUENA)")
        _check_screens(fdir, strict, res)
        return res
    vpairs = numbered_lines(vpath.read_text(encoding="utf-8", errors="replace"))
    judged: dict[str, str] = {}
    vchecks = section_pairs(vpairs, "Checks")
    for table in numbered_tables(vchecks or []):
        for line, m in table.bad:
            res.errors.append(f"verification.md:{line}: {m} células, o cabeçalho tem {table.size} "
                              "(escape pipe como &#124;)")
        ci, ti = _col(table.header, "check"), _col(table.header, "test")
        if ci is None or ti is None:
            continue
        for _, r, _ in table.rows:
            judged[_cell(r, ci).strip("*` ")] = _cell(r, ti)
    if not judged:
        res.errors.append("verification.md sem tabela em `## Checks` (| Check | Test | Holds |)")
    else:
        for cid in ids:
            if cid not in judged:
                res.errors.append(f"verification.md: {cid} sem linha em `## Checks`")
            elif not judged[cid] or judged[cid] in ("-", "—"):
                res.errors.append(f"verification.md: {cid} sem o teste que o Q conferiu")
    findings = section_pairs(vpairs, "Findings")
    if findings is None:
        res.errors.append("verification.md sem `## Findings` (use `None.` quando não houver achados)")
    else:
        for table in numbered_tables(findings):
            for line, m in table.bad:
                res.errors.append(f"verification.md:{line}: {m} células, o cabeçalho tem {table.size} "
                                  "(escape pipe como &#124;)")
            fi, cl = _col(table.header, "finding"), _col(table.header, "closed")
            if cl is None:
                res.errors.append("`## Findings` sem a coluna `Closed`")
                continue
            for _, r, _ in table.rows:
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
                elif not any(valid_cover(proj, fdir, t) for t in cover_tokens(closed)):
                    res.errors.append(f"achado '{name}': `Closed` sem cobertura (C<n> ou test_<nome>): "
                                      "use dispatch.py close-finding")

    _check_screens(fdir, strict, res)

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
