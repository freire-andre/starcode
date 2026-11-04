"""validate_spec.py: deterministic checks of a feature spec.md before it is shown for approval.

Adapted from tlc-spec-driven `validate_spec.py` (Felipe Rodrigues, github.com/felipfr, CC-BY-4.0).
Changes for StarCode (ADR-0002): the spec template of plan section 4.5 replaces the tlc sections;
requirement IDs are R<n>; `**Size**:` selects the brief (MEDIUM) or full (LARGE/COMPLEX) template;
the brief spec carries `## Checks` (D24); a decision map with closed statuses; capture rules removed (D25).

What it checks
  ERRO   `**Size**:` missing or SMALL (a SMALL task has no spec)
  ERRO   a required section is missing or empty; a `*` section N/A without a reason
  ERRO   no requirement, a duplicated R<n>, a requirement without SHALL (EARS)
  ERRO   `## Open Questions` not empty
  ERRO   a decision row whose status is not approved/adjusted/rejected (full template)
  ERRO   a binding source without `## Differences from the Source`
  ERRO   MEDIUM: `## Checks` invalid (a check per requirement, proofs, Build/Run lines)
  ERRO   LARGE/COMPLEX: `## Checks` in spec.md (they live only in tasks.md, D24)
  ERRO   --approved: no `**Approved**: <date> - user: "<their words>"`
  AVISO  requirement with SHALL but no EARS lead keyword; placeholders left; MEDIUM without Edge Cases

Usage: python validate_spec.py [feature|path] [--root DIR] [--approved] [--strict]
Exit: 0 pass, 1 errors (or warnings with --strict), 2 usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gates_common as gc  # noqa: E402

FULL = ["Context", "Scope", "Non-Goals", "Requirements", "Data & Contracts", "States", "Edge Cases",
        "Decisions", "Open Questions"]
BRIEF = ["Context", "Scope", "Non-Goals", "Requirements", "Open Questions", "Checks"]
OPTIONAL_NA = {"Data & Contracts", "States", "Differences from the Source"}
DECISION_STATUS = {"approved", "adjusted", "rejected", "aprovado", "aprovada", "ajustado", "ajustada",
                   "rejeitado", "rejeitada"}
MODAL_RE = re.compile(r"\b(SHALL|DEVE|DEVERÁ)\b", re.IGNORECASE)
LEAD_RE = re.compile(r"^\s*(WHEN|WHILE|WHERE|IF|QUANDO|ENQUANTO|ONDE|SE|THE|O|A|OS|AS)\b", re.IGNORECASE)
BINDING_RE = re.compile(r"(?<![-\w])(binding|vinculante)\b", re.IGNORECASE)
NOT_BINDING_RE = re.compile(r"\b(non|not|não)[- ](binding|vinculante)\b", re.IGNORECASE)


def evaluate(target: str | None, root: Path, require_approval: bool = False) -> gc.Result:
    res = gc.Result("validate_spec")
    try:
        fdir = gc.resolve_feature(target, root, "spec.md")
    except LookupError as exc:
        res.usage_error = str(exc)
        return res
    path = fdir / "spec.md"
    res.target = gc.feature_root_hint(path)
    if not path.exists():
        res.usage_error = f"{res.target} não existe"
        return res
    lines = gc.read_lines(path)
    errors, warnings = res.errors, res.warnings

    size = gc.size_of(lines)
    if size is None:
        errors.append("falta a linha `**Size**: MEDIUM | LARGE | COMPLEX` (classe do dimensionamento por risco)")
        size = "LARGE"
    elif size == "SMALL":
        errors.append("`**Size**: SMALL` não tem spec: a tarefa PEQUENA vai direto ao LaForge com checks inline")
        return res
    brief = size == "MEDIUM"

    for name in (BRIEF if brief else FULL):
        body = gc.section(lines, name)
        if body is None:
            errors.append(f"falta a seção obrigatória `## {name}`")
            continue
        if name in ("Open Questions", "Checks", "Decisions"):
            continue  # validated below
        na, reason = gc.is_na(body)
        if na:
            if name not in OPTIONAL_NA:
                errors.append(f"`## {name}` não pode ser N/A")
            elif not reason:
                errors.append(f"`## {name}` está N/A sem justificativa (`N/A - <motivo>`)")
        elif not gc.meaningful(body):
            errors.append(f"`## {name}` está vazia")
    if brief and gc.section(lines, "Edge Cases") is None:
        warnings.append("spec breve sem `## Edge Cases`: confira conexão, concorrência, timeout e entrada inválida")

    # Requirements (EARS).
    body = gc.section(lines, "Requirements") or []
    seen: dict[str, int] = {}
    reqs: dict[str, str] = {}
    for ln in body:
        s = ln.strip()
        m = gc.REQ_LINE_RE.match(s)
        if not m:
            if re.match(r"^([-*]|\d+\.)\s+\S", s):
                warnings.append(f"item de requisito sem ID R<n>: {s[:70]}")
            continue
        rid, text = m.group(1), m.group(2).strip()
        seen[rid] = seen.get(rid, 0) + 1
        reqs.setdefault(rid, text)
        if not MODAL_RE.search(text):
            errors.append(f"{rid}: sem SHALL (critério não testável no formato EARS): {text[:70]}")
        elif not LEAD_RE.match(text):
            warnings.append(f"{rid}: tem SHALL, mas não começa por WHEN/WHILE/WHERE/IF/THE: {text[:60]}")
    for rid, n in seen.items():
        if n > 1:
            errors.append(f"{rid}: ID de requisito repetido ({n} vezes)")
    if gc.section(lines, "Requirements") is not None and not reqs:
        errors.append("`## Requirements` sem nenhum requisito `R<n> - <critério EARS>`")

    # Open Questions must be empty before approval.
    oq = gc.section(lines, "Open Questions")
    if oq is not None:
        items = [x for x in gc.meaningful(oq) if not gc.NONE_RE.match(x)]
        if items:
            errors.append(f"`## Open Questions` tem {len(items)} item(ns): pergunte ao usuário e mova cada resposta "
                          "para a seção certa antes de apresentar a spec")

    # Decision map.
    dec = gc.section(lines, "Decisions")
    if dec is not None:
        rows = [r for r in gc.table_rows(dec) if any(c for c in r)]
        na, reason = gc.is_na(dec)
        none_line = any(re.match(r"^(none|nenhuma)\b\s*[-–—:]\s*\S", x, re.I) for x in gc.meaningful(dec))
        if not rows and not (none_line or (na and reason)):
            if not brief:
                errors.append("`## Decisions` sem decisões: registre o decision map (item | opções | status) ou "
                              "`None - <por que não houve alternativas>`")
        for r in rows:
            status = re.sub(r"[*_`]", "", r[-1]).strip().lower().split(" ")[0] if r else ""
            if status not in DECISION_STATUS:
                errors.append(f"decisão '{r[0][:40]}': status '{r[-1][:20]}' (use approved, adjusted ou rejected, "
                              "com a resposta do usuário)")

    # Binding source → Differences from the Source.
    sources = gc.section(lines, "Sources") or []
    if any(BINDING_RE.search(x) and not NOT_BINDING_RE.search(x) for x in sources):
        diff = gc.section(lines, "Differences from the Source")
        if diff is None or not gc.meaningful(diff):
            errors.append("há fonte vinculante em `## Sources`, mas falta `## Differences from the Source` "
                          "(liste cada diferença aprovada, ou `None - o produto segue a fonte`)")

    # Checks.
    if brief:
        if gc.section(lines, "Checks") is not None:
            ce, cw = gc.validate_checks(lines, reqs)
            errors += ce
            warnings += cw
    elif gc.section(lines, "Checks") is not None:
        errors.append("`## Checks` na spec de uma feature LARGE/COMPLEX: os checks ficam só em tasks.md (D24)")

    # Placeholders (inline code excluded).
    left = gc.placeholder_lines(lines)
    if left:
        warnings.append(f"{len(left)} linha(s) com marcador de template não preenchido, ex.: {left[0].strip()[:60]}")

    if require_approval and not gc.approved(lines):
        errors.append("falta `**Approved**: <AAAA-MM-DD> - user: \"<palavras do usuário>\"`: apresente a spec e "
                      "pare; nunca escreva uma aprovação que o usuário não deu")
    return res


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="validate_spec.py", description="Checa a spec.md de uma feature.")
    p.add_argument("target", nargs="?")
    p.add_argument("--root", default=".")
    p.add_argument("--approved", action="store_true", help="exige a aprovação do usuário registrada")
    p.add_argument("--strict", action="store_true", help="avisos contam como erros")
    a = p.parse_args(argv)
    res = evaluate(a.target, Path(a.root).resolve(), a.approved)
    print(res.report())
    if res.usage_error:
        return 2
    return 1 if res.errors or (a.strict and res.warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
