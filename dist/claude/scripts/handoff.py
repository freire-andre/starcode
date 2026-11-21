"""handoff.py: write the feature `## Handoff` without the agent editing the file by hand (F2-10).

The Handoff lives in the most advanced artifact of the feature (tasks.md > spec.md > context.md, F2-3).
`set` updates only the fields passed, moves the section to the most advanced artifact when needed and
prints one line. The agent never pastes the Handoff or its diff in the chat.

    python handoff.py set <slug> --phase spec --next "Spock apresenta a spec" [--root .]
    python handoff.py set <slug> --settle "limite de 10 MB"     # appends "<date>: <text>" to Settled
    python handoff.py set <slug> --dispatched "T1 · PROJ-7 · base abc1234" --integration-branch feature/x
    python handoff.py set <slug> --dispatch-add "T2 · PROJ-8 · base abc1234 · claude:claude-sonnet-5-5 · 2026-11-07T16:40:00Z"
        # one entry per open ticket, separated by "; "; an entry of the same <Tn> is replaced in place
    python handoff.py set <slug> --dispatch-remove T2           # drops only T2; no entries left -> none
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

sys.path.insert(0, str(Path(__file__).resolve().parent))

import starcode_common as sc  # noqa: E402

ARTIFACTS = ("tasks.md", "spec.md", "context.md")  # most advanced first
FIELDS = (  # (option, marker, default)
    ("phase", "Phase", "discovery"),
    ("size", "Size", "none yet"),
    ("git_mode", "Git mode", "none yet"),
    ("plugin", "Plugin", "none yet"),
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
          "review", "pr-review", "done")
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


ISO_DATE_START = re.compile(r"^\d{4}-\d{2}-\d{2}")


def starts_with_iso_date(text: str) -> bool:
    """True when the text opens with a real calendar date (AAAA-MM-DD), not just that shape."""
    if not ISO_DATE_START.match(text):
        return False
    try:
        dt.date.fromisoformat(text[:10])
    except ValueError:
        return False
    return True


def append_item(values: dict[str, str], key: str, text: str, today: str | None,
                keep_leading_date: bool = False) -> None:
    if keep_leading_date and starts_with_iso_date(text):
        stamp = text
    else:
        stamp = f"{today or dt.date.today().isoformat()}: {text}"
    old = values.get(key, "")
    values[key] = stamp if old in ("", "none") else f"{old}; {stamp}"


SEP = "; "


def dispatch_entries(value: str) -> list[str]:
    return [e.strip() for e in (value or "").split(";") if e.strip() and e.strip() != "none"]


def entry_ticket(entry: str) -> str:
    m = re.match(r"\s*(\S+)", entry)
    return m.group(1) if m else ""


LINEAR_ID_RE = re.compile(r"(?<![A-Za-z0-9-])[A-Z][A-Z0-9]*-\d+(?:\.\.[A-Z][A-Z0-9]*-\d+)?(?![A-Za-z0-9])")
_ENTRY_KEYS = ("base", "dispatch", "model")


def parse_dispatch_entry(entry: str) -> dict:
    """Reads one entry of `**Dispatched:**` (R1 of SC-207), the only reader of its fields.

    `start` format: `<Tn> · <issues> · base <sha> · <cli>:<model> · <UTC> [· <dispatch id>] [· blocked]`.
    Old format: `<Tn> · <issues> · base <sha> · dispatch <id> · model <m>`.
    Returns ticket, issues (list), issues_text (the field as written), base, model, at, dispatch and blocked; a missing field is None."""
    parts = [p.strip() for p in (entry or "").split("·")]
    out: dict = {"ticket": parts[0] if parts and parts[0] else None, "issues": [], "issues_text": None, "base": None, "model": None,
                 "at": None, "dispatch": None, "blocked": len(parts) > 1 and parts[-1] == "blocked"}
    if len(parts) > 1:
        out["issues_text"] = parts[1] or None
        out["issues"] = list(dict.fromkeys(LINEAR_ID_RE.findall(parts[1])))
    for part in parts[2:]:
        for key in _ENTRY_KEYS:
            if part.startswith(key + " ") and out[key] is None:
                out[key] = part[len(key) + 1:].strip() or None
    keyed = lambda p: any(p.startswith(k + " ") for k in _ENTRY_KEYS)  # noqa: E731
    if len(parts) > 3 and parts[3] and parts[3] != "blocked" and not keyed(parts[3]):
        if out["model"] is None:
            out["model"] = parts[3]
        if len(parts) > 4 and parts[4] and parts[4] != "blocked" and not keyed(parts[4]):
            out["at"] = parts[4]
            if out["dispatch"] is None:
                out["dispatch"] = next((p for p in parts[5:] if p and p != "blocked" and not keyed(p)), None)
    return out


def dispatch_add(values: dict[str, str], entry: str) -> None:
    """Add an entry to Dispatched, replacing in place the one with the same <Tn>."""
    entry = entry.strip()
    ticket = entry_ticket(entry)
    if not ticket:
        raise ValueError("--dispatch-add precisa de uma entrada que comece com <Tn>")
    entries = dispatch_entries(values.get("dispatched", ""))
    for i, e in enumerate(entries):
        if entry_ticket(e) == ticket:
            entries[i] = entry
            break
    else:
        entries.append(entry)
    values["dispatched"] = SEP.join(entries)


def dispatch_remove(values: dict[str, str], ticket: str) -> bool:
    """Drop the entry of one ticket; returns False when there was none. No entries left -> none."""
    entries = dispatch_entries(values.get("dispatched", ""))
    kept = [e for e in entries if entry_ticket(e) != ticket.strip()]
    values["dispatched"] = SEP.join(kept) or "none"
    return len(kept) != len(entries)


def set_handoff(slug: str, root: Path, updates: dict[str, str], settle: str | None = None,
                today: str | None = None, report: str | None = None,
                attempt: str | None = None, dispatch_add_entry: str | None = None,
                dispatch_remove_ticket: str | None = None) -> tuple[Path, dict[str, str]]:
    fdir = feature_dir(slug, root)
    with sc.locked(fdir / ".handoff", timeout=5.0):  # lê, muda e grava sob a trava da feature (SC-208)
        return _set_handoff_locked(fdir, updates, settle, today, report, attempt, dispatch_add_entry,
                                   dispatch_remove_ticket)


def _set_handoff_locked(fdir: Path, updates: dict[str, str], settle: str | None, today: str | None,
                        report: str | None, attempt: str | None, dispatch_add_entry: str | None,
                        dispatch_remove_ticket: str | None) -> tuple[Path, dict[str, str]]:
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
    was_open = re.match(r"open\s*\(\s*([^,)\s]+)", values.get("breaker", ""))
    for option, marker, _ in FIELDS:
        if updates.get(option) is not None:
            values[marker.lower()] = updates[option]
    if was_open and values.get("breaker", "").startswith("closed"):
        # Closing after the user's choice gives that error id a fresh count (D27).
        counts = parse_attempts(values.get("attempts", ""))
        counts.pop(was_open.group(1), None)
        values["attempts"] = ", ".join(f"{k}={v}" for k, v in counts.items()) or "none"
    if settle:
        append_item(values, "settled", settle, today)
    if report:
        append_item(values, "reports", report, today, keep_leading_date=True)
    if attempt:
        apply_attempt(values, attempt)
    if dispatch_add_entry:
        dispatch_add(values, dispatch_add_entry)
    if dispatch_remove_ticket:
        if not dispatch_remove(values, dispatch_remove_ticket):
            print(f"sem entrada de {dispatch_remove_ticket.strip()} em Dispatched")
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
    ps.add_argument("--dispatch-add", dest="dispatch_add",
                    help="acrescenta (ou substitui a do mesmo <Tn>) uma entrada em Dispatched")
    ps.add_argument("--dispatch-remove", dest="dispatch_remove", metavar="Tn",
                    help="tira de Dispatched só a entrada desse ticket")
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
                                     attempt=args.attempt, dispatch_add_entry=args.dispatch_add,
                                     dispatch_remove_ticket=args.dispatch_remove)
    except TimeoutError:
        print(f"handoff ocupado: {feature_dir(args.feature, root)}", file=sys.stderr)
        return 2
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
