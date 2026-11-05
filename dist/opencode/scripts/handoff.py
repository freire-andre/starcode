"""handoff.py: write the feature `## Handoff` without the agent editing the file by hand (F2-10).

The Handoff lives in the most advanced artifact of the feature (tasks.md > spec.md > context.md, F2-3).
`set` updates only the fields passed, moves the section to the most advanced artifact when needed and
prints one line. The agent never pastes the Handoff or its diff in the chat.

    python handoff.py set <slug> --phase spec --next "Spock apresenta a spec" [--root .]
    python handoff.py set <slug> --settle "limite de 10 MB"     # appends "<date>: <text>" to Settled
    python handoff.py set <slug> --dispatched "T1 · PROJ-7 · base abc1234" --integration-branch feature/x
    python handoff.py set <slug> --report "T1: 3 arquivos, gates verdes, 2 commits"  # appends to Reports
    python handoff.py set <slug> --attempt worker-T1=fail       # counts per error id; 3rd fail opens the breaker
    python handoff.py set <slug> --attempt worker-T1=ok         # a success resets that id
    python handoff.py show <slug>                               # one line per field

Exit codes: 0 written / shown, 1 feature or artifact not found, 2 usage error. Python stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ARTIFACTS = ("tasks.md", "spec.md", "context.md")  # most advanced first
FIELDS = (  # (option, marker, default)
    ("phase", "Phase", "discovery"),
    ("size", "Size", "none yet"),
    ("git_mode", "Git mode", "none yet"),
    ("next", "Next", "none yet"),
    ("linear", "Linear", "none yet"),
    ("integration_branch", "Integration branch", "not created"),
    ("last_integrated", "Last integrated", "none"),
    ("dispatched", "Dispatched", "none"),
    ("settled", "Settled", "none"),
    ("attempts", "Attempts", "none"),
    ("reports", "Reports", "none"),
    ("breaker", "Breaker", "closed"),
)
BREAKER_LIMIT = 3  # D27: the 3rd failure of the same error id opens the breaker
ATTEMPT_RE = re.compile(r"^([\w.:/-]+)=(fail|ok)$")
PHASES = ("discovery", "spec", "spec-approved", "tasks", "tasks-approved", "published", "execute",
          "review", "done")
FIELD_RE = re.compile(r"^\*\*([^*]+?):\*\*\s*(.*)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def section_bounds(lines: list[str]) -> tuple[int, int] | None:
    """(start, end) of the `## Handoff` section outside code fences; end is exclusive."""
    fenced, start = False, None
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if start is None and line.strip() == "## Handoff":
            start = i
        elif start is not None and re.match(r"^#{1,2}\s", line):
            return start, i
    return (start, len(lines)) if start is not None else None


def read_fields(lines: list[str], bounds: tuple[int, int]) -> dict[str, str]:
    values = {}
    for line in lines[bounds[0] + 1:bounds[1]]:
        m = FIELD_RE.match(line.strip())
        if m:
            values[m.group(1).strip().lower()] = m.group(2).strip()
    return values


def strip_section(lines: list[str], bounds: tuple[int, int]) -> list[str]:
    out = lines[:bounds[0]] + lines[bounds[1]:]
    while out and not out[-1].strip():
        out.pop()
    return out


def render(values: dict[str, str]) -> list[str]:
    body = ["## Handoff", ""]
    for _, marker, default in FIELDS:
        body.append(f"**{marker}:** {values.get(marker.lower()) or default}")
    return body


def feature_dir(slug: str, root: Path) -> Path:
    p = Path(slug)
    if p.is_dir():
        return p
    return root / ".specs" / "features" / slug


def parse_attempts(value: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in (value or "").split(","):
        name, _, n = item.strip().partition("=")
        if name and n.strip().isdigit():
            out[name.strip()] = int(n)
    return out


def apply_attempt(values: dict[str, str], attempt: str) -> None:
    """Count a failure (or reset on success) for a stable error id; open the breaker on the 3rd failure."""
    m = ATTEMPT_RE.match(attempt.strip())
    if not m:
        raise ValueError(f"tentativa inválida {attempt!r}: use <id-do-erro>=fail ou <id-do-erro>=ok")
    eid, outcome = m.group(1), m.group(2)
    counts = parse_attempts(values.get("attempts", ""))
    if outcome == "ok":
        counts.pop(eid, None)
    else:
        counts[eid] = counts.get(eid, 0) + 1
        if counts[eid] >= BREAKER_LIMIT:
            values["breaker"] = f"open ({eid}, attempts {counts[eid]}/{BREAKER_LIMIT})"
    values["attempts"] = ", ".join(f"{k}={v}" for k, v in counts.items()) or "none"


def append_item(values: dict[str, str], key: str, text: str, today: str | None) -> None:
    stamp = f"{today or dt.date.today().isoformat()}: {text}"
    old = values.get(key, "")
    values[key] = stamp if old in ("", "none") else f"{old}; {stamp}"


def set_handoff(slug: str, root: Path, updates: dict[str, str], settle: str | None = None,
                today: str | None = None, report: str | None = None,
                attempt: str | None = None) -> tuple[Path, dict[str, str]]:
    fdir = feature_dir(slug, root)
    present = [fdir / a for a in ARTIFACTS if (fdir / a).is_file()]
    if not present:
        raise LookupError(f"nenhum artefato (tasks.md, spec.md, context.md) em {fdir}")
    target = present[0]
    values: dict[str, str] = {}
    texts = {}
    for art in reversed(present):  # oldest first, so the most advanced artifact wins on conflicts
        lines = art.read_text(encoding="utf-8").splitlines()
        bounds = section_bounds(lines)
        if bounds:
            values.update(read_fields(lines, bounds))
            texts[art] = strip_section(lines, bounds)
        elif art == target:
            texts[art] = lines
    for option, marker, _ in FIELDS:
        if updates.get(option) is not None:
            values[marker.lower()] = updates[option]
    if settle:
        append_item(values, "settled", settle, today)
    if report:
        append_item(values, "reports", report, today)
    if attempt:
        apply_attempt(values, attempt)
    for art, lines in texts.items():
        if art == target:
            lines = lines + [""] + render(values)
        art.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    return target, values


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="handoff.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("set")
    ps.add_argument("feature")
    ps.add_argument("--root", default=".")
    for option, marker, _ in FIELDS:
        if option in ("attempts", "reports"):
            continue  # written through --attempt and --report
        ps.add_argument("--" + option.replace("_", "-"), dest=option, help=f"**{marker}:**")
    ps.add_argument("--settle", help="acrescenta '<data>: <texto>' ao Settled")
    ps.add_argument("--report", help="acrescenta '<data>: <relatório do worker>' ao Reports")
    ps.add_argument("--attempt", help="<id-do-erro>=fail|ok: conta a tentativa; a 3ª falha abre o disjuntor")
    pv = sub.add_parser("show")
    pv.add_argument("feature")
    pv.add_argument("--root", default=".")
    try:
        args = p.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    root = Path(args.root)
    if args.cmd == "show":
        fdir = feature_dir(args.feature, root)
        for art in ARTIFACTS:
            f = fdir / art
            if f.is_file():
                lines = f.read_text(encoding="utf-8").splitlines()
                b = section_bounds(lines)
                if b:
                    print(f"Handoff em {f}:")
                    print("\n".join(lines[b[0] + 1:b[1]]).strip())
                    return 0
        print(f"ERRO: sem ## Handoff em {fdir}", file=sys.stderr)
        return 1
    if args.phase and args.phase not in PHASES:
        print(f"ERRO: fase inválida {args.phase!r}; use uma de: {', '.join(PHASES)}", file=sys.stderr)
        return 2
    updates = {option: getattr(args, option, None) for option, _, _ in FIELDS}
    try:
        target, values = set_handoff(args.feature, root, updates, args.settle, report=args.report,
                                     attempt=args.attempt)
    except ValueError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    except LookupError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    if values.get("breaker", "closed").startswith("open"):
        print(f"DISJUNTOR ABERTO: {values['breaker']} (D27): pare e ofereça as duas saídas")
    print(f"Handoff gravado em {target.name}: {values.get('phase', 'discovery')} · próximo: "
          f"{values.get('next', 'none yet')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
