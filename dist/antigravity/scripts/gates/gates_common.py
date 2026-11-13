"""Shared parsing for the StarCode gates (ADR-0002, D24).

Adapted from tlc-spec-driven `lean_config.py` and the parsing helpers of its gate scripts
(Felipe Rodrigues, github.com/felipfr, CC-BY-4.0). Changes: StarCode layout and markers, requirement IDs
R<n>, capture/screen rules removed (D25), PT-BR messages, one parser for every gate.

Every reader works on lines with fenced code blocks removed, so examples inside ``` never count.
Python stdlib only.
"""
from __future__ import annotations

import fnmatch
import json
import os
import posixpath
import re
from dataclasses import dataclass, field
from pathlib import Path

# --- markers read by the gates (English, D16) ------------------------------------------------
APPROVED_RE = re.compile(
    r"^\**\s*Approved\s*\**\s*:\s*\**\s*\d{4}-\d{2}-\d{2}\b.*\buser\s*:\s*[\"“][^\"”]*\S[^\"”]*[\"”]",
    re.IGNORECASE)
SIZE_RE = re.compile(r"^\**\s*Size\s*\**\s*:\s*\**\s*([A-Za-zÉÁ]+)", re.IGNORECASE)
REQ_ID_RE = re.compile(r"\bR\d+\b")
REQ_LINE_RE = re.compile(r"^(?:[-*]\s+|\d+\.\s+)?\**\s*(R\d+)\s*\**\s*[-–—:.)]\s*(.+)$")
CHECK_RE = re.compile(r"^\**\s*(C\d+)\s*\**\s*[-–—:]\s*(.+)$")
PROOF_RE = re.compile(r"^\**\s*Proof\s*\**\s*:\s*(.+)$", re.IGNORECASE)
BUILD_RE = re.compile(r"^\**\s*Build\s*\**\s*:\s*(.+)$", re.IGNORECASE)
RUN_RE = re.compile(r"^\**\s*Run\s+([\w-]+)\s*\**\s*:\s*(.+)$", re.IGNORECASE)
RUN_PROOF_RE = re.compile(r"^run\s+([\w-]+)\s*(?:\|\s*(.*))?$", re.IGNORECASE)
LINEAR_ID_RE = re.compile(r"\b[A-Z][A-Z0-9]*-\d+\b")
PLACEHOLDER_RE = re.compile(r"<[^<>\n]{2,}>|\[(?:TODO|TBD|preencher)[^\]]*\]", re.IGNORECASE)
NA_RE = re.compile(r"^\s*(?:N/?A|n[ãa]o se aplica)\b\s*[-–—:]?\s*(.*)$", re.IGNORECASE)
NONE_RE = re.compile(r"^\s*[-*]?\s*(?:none|nenhuma?|vazia)\b\.?\s*$", re.IGNORECASE)

SIZES = {"MEDIUM": "MEDIUM", "MEDIA": "MEDIUM", "MÉDIA": "MEDIUM", "LARGE": "LARGE", "GRANDE": "LARGE",
         "COMPLEX": "COMPLEX", "COMPLEXA": "COMPLEX", "SMALL": "SMALL", "PEQUENA": "SMALL"}

# Plan 4.4: a ticket touching one of these runs alone (adjustable via .starcode/config.json sensitiveFiles).
DEFAULT_SENSITIVE = (
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "poetry.lock", "uv.lock", "Pipfile.lock",
    "Cargo.lock", "composer.lock", "Gemfile.lock", "go.sum", "*.lock",
    "migrations/", "pyproject.toml", "package.json", "Cargo.toml", "tsconfig.json",
    ".github/workflows/", ".gitlab-ci.yml", "azure-pipelines.yml", ".circleci/",
)


@dataclass
class Result:
    gate: str
    target: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    usage_error: str = ""

    @property
    def ok(self) -> bool:
        return not self.errors and not self.usage_error

    def report(self) -> str:
        out = [f"[{self.gate}] {self.target}".rstrip()]
        if self.usage_error:
            out.append(f"  USO   {self.usage_error}")
        out += [f"  ERRO  {e}" for e in self.errors]
        out += [f"  AVISO {w}" for w in self.warnings]
        if self.ok and not self.warnings:
            out.append("  ok")
        return "\n".join(out)

    def summary(self) -> str:
        if self.usage_error:
            return "não rodou: " + self.usage_error
        return f"{len(self.errors)} erro(s), {len(self.warnings)} aviso(s)"


# --- file and feature resolution -------------------------------------------------------------

def read_lines(path: Path) -> list[str]:
    """Lines of a markdown file with fenced code blocks removed (rstripped)."""
    out, in_fence = [], False
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(ln.rstrip())
    return out


def resolve_feature(target: str | None, root: Path, needs: str) -> Path:
    """Return the feature directory. `target`: a feature slug, a feature dir, or a file inside it.
    Without target: the single feature under <root>/.specs/features that has `needs`."""
    if target:
        p = Path(target)
        if p.is_file():
            return p.resolve().parent
        if p.is_dir() and (p / needs).exists():
            return p.resolve()
        cand = root / ".specs" / "features" / target
        if cand.is_dir():
            return cand.resolve()
        raise LookupError(f"feature {target!r} não encontrada em {root / '.specs' / 'features'}")
    base = root / ".specs" / "features"
    found = sorted(d for d in base.iterdir() if (d / needs).exists()) if base.is_dir() else []
    if len(found) == 1:
        return found[0].resolve()
    if not found:
        raise LookupError(f"nenhuma feature com {needs} em {base}; passe o nome da feature")
    raise LookupError("mais de uma feature; passe uma: " + ", ".join(d.name for d in found))


def project_root(feature_dir: Path) -> Path:
    """The folder that holds .specs/ above the feature dir (falls back to the feature's grandparent)."""
    cur = feature_dir.resolve()
    for parent in [cur, *cur.parents]:
        if parent.name == ".specs":
            return parent.parent
    return cur.parent


# --- sections --------------------------------------------------------------------------------

def heading_level(line: str) -> int:
    m = re.match(r"^(#{1,6})\s+\S", line.strip())
    return len(m.group(1)) if m else 0


def section(lines: list[str], name: str, level: int = 2) -> list[str] | None:
    """Body of the `## name` heading (case-insensitive, trailing '*' allowed) up to the next heading of the
    same or higher level. None when the heading is absent."""
    pat = re.compile(r"^#{" + str(level) + r"}\s+" + re.escape(name) + r"\s*\*?\s*$", re.IGNORECASE)
    start = None
    for i, ln in enumerate(lines):
        if pat.match(ln.strip()):
            start = i + 1
            break
    if start is None:
        return None
    body = []
    for ln in lines[start:]:
        lvl = heading_level(ln)
        if lvl and lvl <= level:
            break
        body.append(ln)
    return body


def meaningful(body: list[str]) -> list[str]:
    """Non-empty lines that are not HTML comments."""
    text = re.sub(r"<!--.*?-->", "", "\n".join(body), flags=re.S)
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def is_na(body: list[str]) -> tuple[bool, str]:
    """(True, reason) when the section is `N/A - <reason>`."""
    lines = meaningful(body)
    if not lines:
        return False, ""
    m = NA_RE.match(lines[0].lstrip("-* "))
    if not m:
        return False, ""
    reason = (m.group(1) + " " + " ".join(lines[1:])).strip()
    return True, reason


def table_rows(body: list[str]) -> list[list[str]]:
    """Data rows of the first markdown table in body (header and separator dropped)."""
    rows = [ln.strip() for ln in body if ln.strip().startswith("|")]
    data = [r for r in rows if not re.match(r"^\|?[\s:|-]+\|?$", r)]
    return [[c.strip() for c in r.strip().strip("|").split("|")] for r in data[1:]]


def field_value(lines: list[str], name: str) -> str | None:
    pat = re.compile(r"^\**\s*" + re.escape(name) + r"\s*\**\s*:\s*\**\s*(.*)$", re.IGNORECASE)
    for ln in lines:
        m = pat.match(ln.strip())
        if m:
            return m.group(1).strip()
    return None


def approved(lines: list[str]) -> bool:
    return any(APPROVED_RE.match(ln.strip()) for ln in lines)


def size_of(lines: list[str]) -> str | None:
    for ln in lines:
        m = SIZE_RE.match(ln.strip())
        if m:
            return SIZES.get(m.group(1).upper())
    return None


# --- requirements and checks -----------------------------------------------------------------

def requirements(lines: list[str]) -> dict[str, str]:
    """{R<n>: text} from `## Requirements` (one requirement per line/item)."""
    body = section(lines, "Requirements") or []
    out: dict[str, str] = {}
    for ln in body:
        m = REQ_LINE_RE.match(ln.strip())
        if m:
            out.setdefault(m.group(1), m.group(2).strip())
    return out


@dataclass
class Check:
    cid: str
    claim: str
    proofs: list[str]
    reqs: list[str]


def read_checks(lines: list[str]) -> tuple[list[Check], dict[str, str], list[str]]:
    """(checks, runs {name: command}, build commands) from a file's `## Checks` section."""
    body = section(lines, "Checks") or []
    checks: list[Check] = []
    runs: dict[str, str] = {}
    build: list[str] = []
    for ln in [x.strip() for x in lines]:
        m = BUILD_RE.match(ln)
        if m:
            build += [c.strip().strip("`").strip() for c in m.group(1).split(";") if c.strip()]
        r = RUN_RE.match(ln)
        if r:
            runs[r.group(1)] = r.group(2).strip().strip("`").strip()
    current = None
    for ln in [x.strip() for x in body]:
        m = CHECK_RE.match(ln)
        if m:
            current = Check(m.group(1), m.group(2).strip(), [], sorted(set(REQ_ID_RE.findall(m.group(2)))))
            checks.append(current)
        elif current is not None:
            p = PROOF_RE.match(ln)
            if p:
                current.proofs.append(p.group(1).strip().strip("`").strip())
    return checks, runs, build


def validate_checks(lines: list[str], reqs: dict[str, str]) -> tuple[list[str], list[str]]:
    """Errors/warnings for `## Checks`: a check per requirement, a proof per check, Build and Run lines."""
    errors, warnings = [], []
    if section(lines, "Checks") is None:
        return ["falta a seção obrigatória `## Checks`"], warnings
    checks, runs, build = read_checks(lines)
    if not checks:
        errors.append("`## Checks` sem nenhum check: um `**C<n>** - <afirmação observável> (R<n>)` por critério, "
                      "cada um seguido de `Proof: <comando de teste que seleciona o teste>`")
    seen, covered, read = set(), set(), set()
    for c in checks:
        if c.cid in seen:
            errors.append(f"{c.cid}: ID de check repetido")
        seen.add(c.cid)
        if not c.reqs:
            errors.append(f"{c.cid}: não cita nenhum requisito (R<n>) entre parênteses")
        for r in c.reqs:
            if reqs and r not in reqs:
                errors.append(f"{c.cid}: cita {r}, que não existe em `## Requirements` da spec")
            covered.add(r)
        if not c.proofs:
            errors.append(f"{c.cid}: sem linha `Proof:`; diga o comando de teste cujo filtro seleciona o teste")
        for text in c.proofs:
            rm = RUN_PROOF_RE.match(text)
            if not rm:
                continue
            name, expected = rm.group(1), (rm.group(2) or "").strip().strip("`").strip()
            read.add(name)
            if name not in runs:
                errors.append(f"{c.cid}: a prova lê `run {name}`, mas não há linha `**Run {name}**: <comando>`")
            if not expected:
                errors.append(f"{c.cid}: `run {name}` sem a linha esperada depois de `|` (a linha que o teste "
                              "imprime quando passa, com a marca de sucesso)")
    for r in sorted(reqs, key=lambda x: int(x[1:])):
        if r not in covered:
            errors.append(f"{r}: nenhum check cobre este requisito; cada critério precisa de um check com prova")
    for name in runs:
        if name not in read:
            warnings.append(f"`Run {name}` não é lido por nenhuma prova; aponte um check para ele ou remova")
    if not build:
        errors.append("falta a linha `**Build**:` (build, checagem de tipos e lint do repo, separados por `;`, "
                      "ou `**Build**: none - <motivo>`)")
    return errors, warnings


# --- repo config -----------------------------------------------------------------------------

def sensitive_patterns(root: Path) -> list[str]:
    pats = list(DEFAULT_SENSITIVE)
    cfg = root / ".starcode" / "config.json"
    try:
        extra = json.loads(cfg.read_text(encoding="utf-8")).get("sensitiveFiles") or []
        pats += [p for p in extra if isinstance(p, str) and p.strip()]
    except (OSError, ValueError, AttributeError):
        pass
    return pats


def norm_path(p: str) -> str:
    p = p.strip().strip("`'\"").replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


def is_sensitive(path: str, patterns: list[str]) -> str | None:
    p = norm_path(path)
    parts = p.rstrip("/").split("/")
    for pat in patterns:
        if pat.endswith("/"):
            seq = pat.rstrip("/").split("/")
            for i in range(len(parts) - len(seq) + 1):
                if parts[i:i + len(seq)] == seq:
                    return pat
        elif fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(parts[-1], pat):
            return pat
    return None


def _prefix(p: str) -> str:
    """Literal directory prefix before any glob character."""
    m = re.search(r"[*?\[]", p)
    if not m:
        return p
    head = p[:m.start()]
    return head[: head.rfind("/") + 1] if "/" in head else ""


def paths_overlap(a: str, b: str) -> bool:
    a, b = norm_path(a), norm_path(b)
    if a == b:
        return True
    if any(ch in a + b for ch in "*?["):
        if fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a):
            return True
        pa, pb = _prefix(a), _prefix(b)
        if pa == "" or pb == "":
            return True
        return pa.startswith(pb) or pb.startswith(pa)
    da, db = a.rstrip("/") + "/", b.rstrip("/") + "/"
    return da.startswith(db) or db.startswith(da)


def split_paths(value: str) -> list[str]:
    """Paths from a `May change:` value: backticked items, or comma-separated."""
    ticks = re.findall(r"`([^`]+)`", value)
    items = ticks if ticks else [x for x in re.split(r"[,;]", value)]
    return [norm_path(x) for x in items if norm_path(x) and norm_path(x).lower() not in ("none", "nenhum")]


ALLOWED_TOKENS = ("<ID-LINEAR>",)  # filled by the worker from the issue linked to its worktree


def placeholder_lines(lines: list[str]) -> list[str]:
    """Lines that still hold a template marker (inline code and allowed tokens excluded)."""
    out = []
    for ln in lines:
        s = re.sub(r"`[^`]*`", "", ln)
        for tok in ALLOWED_TOKENS:
            s = s.replace(tok, "")
        if PLACEHOLDER_RE.search(s):
            out.append(ln)
    return out


def feature_root_hint(feature_dir: Path) -> str:
    try:
        return os.path.relpath(feature_dir, project_root(feature_dir)).replace("\\", "/")
    except ValueError:
        return str(feature_dir)


# One path-coverage rule shared by check_scope and the tasks gate (R1, R3).
def normalize(path: str) -> str:
    return posixpath.normpath(path.strip().strip("`'\"").replace("\\", "/"))


def covers(path: str, entry: str) -> bool:
    p = normalize(path)
    if p == ".." or p.startswith("../") or p.startswith("/"):
        return False
    e = entry.strip().strip("`'\"").replace("\\", "/")
    while e.startswith("./"):
        e = e[2:]
    if e.endswith("/"):
        return p.startswith(e)
    return p == e or fnmatch.fnmatch(p, e)
