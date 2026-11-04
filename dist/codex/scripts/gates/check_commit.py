r"""check_commit.py: Conventional Commits with the StarCode `Refs: <LINEAR-ID>` footer (D24).

Adapted from tlc-spec-driven `check_commit.py` (Felipe Rodrigues, github.com/felipfr, CC-BY-4.0).
Changes for StarCode: the footer `Refs: <ID>` is required (one or more Linear IDs, comma-separated);
`--expect-ref` pins the ticket's ID; PT-BR messages; the reminder after the last task points to the
StarCode verification flow (check_proofs + Q, Phase 3).

Reads the message from a file path (as git passes it to `commit-msg`), `--message`, or stdin.

What it checks
  ERRO   header not `type(scope)!: description`; type not allowed
  ERRO   description empty, starting uppercase or ending with a period
  ERRO   `!` without a `BREAKING CHANGE:` footer
  ERRO   no `Refs: <ID>` footer (unless --refs-optional); --expect-ref ID not in Refs
  AVISO  header longer than 72 characters

Usage:
  python check_commit.py --message "feat(export): gerar csv" --expect-ref SC-12
  python check_commit.py .git/COMMIT_EDITMSG
Exit: 0 pass, 1 violation, 2 usage error.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gates_common as gc  # noqa: E402

TYPES = ["feat", "fix", "refactor", "docs", "test", "style", "perf", "build", "ci", "chore", "revert"]
HEADER_RE = re.compile(r"^(?P<type>\w+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?: (?P<desc>.+)$")
REFS_RE = re.compile(r"^Refs:\s*(.+)$", re.MULTILINE)


def check(message: str, refs_optional: bool = False, expect_ref: str | None = None) -> gc.Result:
    res = gc.Result("check_commit", "mensagem de commit")
    lines = [ln for ln in message.splitlines() if not ln.lstrip().startswith("#")]
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        res.errors.append("mensagem de commit vazia")
        return res
    header = lines[0].rstrip()
    if len(header) > 72:
        res.warnings.append(f"cabeçalho com {len(header)} caracteres (>72)")
    m = HEADER_RE.match(header)
    if not m:
        res.errors.append(f"cabeçalho fora do formato 'tipo(escopo): descrição': {header!r}")
    else:
        if m.group("type") not in TYPES:
            res.errors.append(f"tipo '{m.group('type')}' não é um de: {', '.join(TYPES)}")
        desc = m.group("desc").strip()
        if not desc:
            res.errors.append("descrição vazia")
        else:
            if desc[:1].isupper():
                res.errors.append(f"a descrição deve começar com minúscula: '{desc[:30]}'")
            if desc.endswith("."):
                res.errors.append("a descrição não deve terminar com ponto")
    body = "\n".join(lines[1:])
    if m and m.group("bang") and not re.search(r"^BREAKING CHANGE:", body, re.MULTILINE):
        res.errors.append("marca '!' sem o rodapé 'BREAKING CHANGE:'")
    refs = [i for r in REFS_RE.findall(body) for i in gc.LINEAR_ID_RE.findall(r)]
    if not refs and not refs_optional:
        res.errors.append("falta o rodapé `Refs: <ID-LINEAR>` (ex.: `Refs: SC-12`), separado do corpo por linha "
                          "em branco")
    if expect_ref and expect_ref not in refs:
        res.errors.append(f"o rodapé Refs não cita {expect_ref}, o ticket deste worktree")
    return res


def read_message(a: argparse.Namespace) -> str:
    if a.message is not None:
        return a.message
    if a.msgfile:
        if os.path.isfile(a.msgfile):
            return Path(a.msgfile).read_text(encoding="utf-8")
        return a.msgfile
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def owed_verification(root: Path) -> list[str]:
    base = root / ".specs" / "features"
    out = []
    for d in sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []:
        if (d / "verification.md").exists():
            continue
        for name in ("tasks.md", "spec.md"):
            f = d / name
            if f.exists() and gc.section(gc.read_lines(f), "Checks") is not None:
                out.append(d.name)
                break
    return out


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="check_commit.py", description="Valida a mensagem de commit.")
    p.add_argument("msgfile", nargs="?")
    p.add_argument("--message")
    p.add_argument("--expect-ref", help="ID do Linear que o rodapé Refs precisa citar")
    p.add_argument("--refs-optional", action="store_true", help="não exige o rodapé Refs")
    p.add_argument("--root", default=".")
    a = p.parse_args(argv)
    msg = read_message(a)
    if not msg.strip():
        print("check_commit: nenhuma mensagem (passe um arquivo, --message ou stdin)", file=sys.stderr)
        return 2
    res = check(msg, a.refs_optional, a.expect_ref)
    print(res.report())
    if res.errors:
        return 1
    for name in owed_verification(Path(a.root).resolve()):
        print(f"Lembrete: depois do último ticket de `{name}`, a feature ainda não terminou: check_proofs, Q e "
              "validate_verification no ramo de integração.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
