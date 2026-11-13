"""validate_tasks.py: deterministic checks of a feature tasks.md before it is shown for approval.

Adapted from tlc-spec-driven `validate_tasks.py` (Felipe Rodrigues, github.com/felipfr, CC-BY-4.0).
Changes for StarCode (ADR-0002, D19, D24): each task carries the 5-block ticket briefing (TASK, CONTEXT,
BOUNDARIES, RULES, DELIVERY) with `May change`; tasks that may run at the same time never share a file;
a task touching a sensitive file is marked `Runs alone`; dependencies come only from `Depends on`
(the tlc diagram cross-check was dropped); requirement coverage is checked against spec.md;
`--published` checks the Linear IDs written back by the Data. Capture rules removed (D25).

What it checks
  ERRO   missing `## Gate Commands`, `## Tasks` or `## Checks`; no task
  ERRO   task without `Depends on`, `Requirements`, `Tests` or `Gate`; Gate not in `## Gate Commands`
  ERRO   unknown dependency, dependency cycle, unknown requirement
  ERRO   missing or empty briefing block; no `May change:` entry
  ERRO   the TASK block quotes a file path that May change does not cover (cite it in CONTEXT instead)
  ERRO   two independent tasks share a path in `May change` (add a dependency or split the file)
  ERRO   a sensitive file in `May change` without `**Runs alone**: yes`
  ERRO   `## Checks` invalid (a check per spec requirement, proofs, Build/Run lines)
  ERRO   --execute: spec.md or tasks.md without the user's approval in their words
  ERRO   --published: a task without `**Linear**: <ID>`
  AVISO  `Tests: none`; RULES without `Refs:`; no `## Handoff`; placeholders left

Usage: python validate_tasks.py [feature|path] [--root DIR] [--execute] [--published] [--strict]
Exit: 0 pass, 1 errors (or warnings with --strict), 2 usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gates_common as gc  # noqa: E402

TASK_RE = re.compile(r"^###\s+(T\d+)\s*:\s*(.*)$", re.IGNORECASE)
BLOCKS = ("TASK", "CONTEXT", "BOUNDARIES", "RULES", "DELIVERY")
CITE_RE = re.compile(r"`([^`\s<>*{}]+)`")
CITE_EXTS = (".py", ".md", ".json", ".ts", ".tsx", ".js", ".mjs", ".toml", ".yaml", ".yml", ".txt", ".sh",
             ".ps1", ".rs", ".css", ".html", ".lock")
YES_RE = re.compile(r"^\W*(yes|sim|true)\b", re.IGNORECASE)


@dataclass
class Task:
    tid: str
    title: str
    lines: list[str] = field(default_factory=list)
    blocks: dict[str, list[str]] = field(default_factory=dict)

    def value(self, name: str) -> str | None:
        head = []
        for ln in self.lines:
            if re.match(r"^####\s+", ln.strip()):
                break
            head.append(ln)
        return gc.field_value(head, name)

    @property
    def deps(self) -> list[str]:
        v = self.value("Depends on") or ""
        return [] if re.match(r"^\W*(none|nenhum|nenhuma|-)\W*$", v, re.I) else sorted(
            set(re.findall(r"\bT\d+\b", v.upper())), key=lambda x: int(x[1:]))

    @property
    def may_change(self) -> list[str]:
        out = []
        for ln in self.blocks.get("BOUNDARIES", []):
            m = re.match(r"^[-*]?\s*\**May change\**\s*:\s*(.*)$", ln.strip(), re.IGNORECASE)
            if m:
                out += gc.split_paths(m.group(1))
        return out

    @property
    def runs_alone(self) -> bool:
        return bool(YES_RE.match(self.value("Runs alone") or ""))


def uncovered_citations(task: Task) -> list[str]:
    """Paths quoted in backticks in the TASK block that the May change does not cover (R20, R21)."""
    entries = [e.replace("\\", "/").strip() for e in task.may_change]
    out: list[str] = []
    for ln in task.blocks.get("TASK", []):
        for cand in CITE_RE.findall(ln):
            path = cand.replace("\\", "/")
            if not path.lower().endswith(CITE_EXTS) or path in out:
                continue
            covered = any(path == e or (e.endswith("/") and path.startswith(e))
                          or ("/" not in path and path == e.rstrip("/").rsplit("/", 1)[-1]) for e in entries)
            if not covered:
                out.append(path)
    return out


def parse_tasks(lines: list[str]) -> list[Task]:
    body = gc.section(lines, "Tasks")
    if body is None:
        return []
    tasks: list[Task] = []
    for ln in body:
        m = TASK_RE.match(ln.strip())
        if m:
            tasks.append(Task(m.group(1).upper(), m.group(2).strip()))
            continue
        if gc.heading_level(ln) == 3:
            tasks.append(Task("?", ln.strip()))  # a level-3 heading that is not a task ends the previous one
            continue
        if tasks:
            tasks[-1].lines.append(ln)
    tasks = [t for t in tasks if t.tid != "?"]
    for t in tasks:
        current = None
        for ln in t.lines:
            m = re.match(r"^####\s+([A-Z]+)\s*$", ln.strip())
            if m:
                current = m.group(1).upper()
                t.blocks[current] = []
            elif current:
                t.blocks[current].append(ln)
    return tasks


def ancestors(tasks: dict[str, Task]) -> tuple[dict[str, set[str]], list[str]]:
    """Transitive dependencies of each task, and the tasks that sit on a cycle."""
    memo: dict[str, set[str]] = {}
    cyclic: list[str] = []

    def visit(tid: str, stack: tuple[str, ...]) -> set[str]:
        if tid in memo:
            return memo[tid]
        if tid in stack:
            cyclic.append(tid)
            return set()
        acc: set[str] = set()
        for d in tasks[tid].deps if tid in tasks else []:
            if d in tasks:
                acc |= {d} | visit(d, stack + (tid,))
        memo[tid] = acc
        return acc

    for tid in tasks:
        visit(tid, ())
    return memo, sorted(set(cyclic))


def gate_names(lines: list[str]) -> set[str]:
    body = gc.section(lines, "Gate Commands") or []
    return {re.sub(r"[*_`]", "", r[0]).strip().lower() for r in gc.table_rows(body) if r and r[0].strip()}


def evaluate(target: str | None, root: Path, execute: bool = False, published: bool = False) -> gc.Result:
    res = gc.Result("validate_tasks")
    try:
        fdir = gc.resolve_feature(target, root, "tasks.md")
    except LookupError as exc:
        res.usage_error = str(exc)
        return res
    path = fdir / "tasks.md"
    res.target = gc.feature_root_hint(path)
    if not path.exists():
        res.usage_error = f"{res.target} não existe"
        return res
    lines = gc.read_lines(path)
    spec_path = fdir / "spec.md"
    spec_lines = gc.read_lines(spec_path) if spec_path.exists() else []
    reqs = gc.requirements(spec_lines)
    errors, warnings = res.errors, res.warnings
    if not spec_lines:
        errors.append("spec.md não existe ao lado de tasks.md: as tasks derivam de uma spec aprovada")

    for name in ("Gate Commands", "Tasks", "Checks"):
        if gc.section(lines, name) is None:
            errors.append(f"falta a seção obrigatória `## {name}`")
    if gc.section(lines, "Handoff") is None:
        warnings.append("sem `## Handoff`: o Picard o cria logo após o Data (fase, ticket, próximo passo)")

    gates = gate_names(lines)
    if gc.section(lines, "Gate Commands") is not None and not gates:
        errors.append("`## Gate Commands` sem tabela (nível | quando usar | comando)")

    ce, cw = gc.validate_checks(lines, reqs)
    errors += ce
    warnings += cw

    tasks = parse_tasks(lines)
    if gc.section(lines, "Tasks") is not None and not tasks:
        errors.append("nenhuma tarefa `### T<n>: <título>` em `## Tasks`")
    by_id: dict[str, Task] = {}
    for t in tasks:
        if t.tid in by_id:
            errors.append(f"{t.tid}: ID de tarefa repetido")
        by_id[t.tid] = t
    patterns = gc.sensitive_patterns(gc.project_root(fdir))

    for t in tasks:
        for name in ("Depends on", "Requirements", "Tests", "Gate"):
            if t.value(name) is None:
                errors.append(f"{t.tid}: falta o campo `**{name}**:`")
        tests = (t.value("Tests") or "").lower()
        if tests.startswith(("none", "nenhum")):
            warnings.append(f"{t.tid}: `Tests: none`; só vale para camada sem teste (configuração, documentação)")
        gate = re.sub(r"[*_`]", "", t.value("Gate") or "").strip().lower()
        if gate and gates and gate not in gates:
            errors.append(f"{t.tid}: Gate '{gate}' não está em `## Gate Commands` ({', '.join(sorted(gates))})")
        for d in t.deps:
            if d not in by_id:
                errors.append(f"{t.tid}: depende de {d}, que não existe")
        treqs = set(gc.REQ_ID_RE.findall(t.value("Requirements") or ""))
        if t.value("Requirements") is not None and not treqs:
            errors.append(f"{t.tid}: `Requirements` não cita nenhum R<n>")
        for r in sorted(treqs):
            if reqs and r not in reqs:
                errors.append(f"{t.tid}: cita {r}, que não existe na spec")
        for b in BLOCKS:
            if b not in t.blocks:
                errors.append(f"{t.tid}: falta o bloco `#### {b}` do briefing")
            elif not gc.meaningful(t.blocks[b]):
                errors.append(f"{t.tid}: o bloco `#### {b}` está vazio")
        if "BOUNDARIES" in t.blocks and not t.may_change:
            errors.append(f"{t.tid}: BOUNDARIES sem `May change: <arquivos ou pastas>`")
        for cited in uncovered_citations(t):
            errors.append(f"{t.tid}: o TASK cita {cited}, fora do May change: acrescente ao May change ou cite em CONTEXT")
        if "RULES" in t.blocks and not any("refs:" in x.lower() for x in t.blocks["RULES"]):
            warnings.append(f"{t.tid}: RULES não lembra o rodapé `Refs: <ID-LINEAR>` do commit")
        hits = sorted({p for p in t.may_change if gc.is_sensitive(p, patterns)})
        if hits and not t.runs_alone:
            errors.append(f"{t.tid}: toca arquivo sensível ({', '.join(hits)}) e não tem `**Runs alone**: yes`")
        if published and not gc.LINEAR_ID_RE.search(t.value("Linear") or ""):
            errors.append(f"{t.tid}: sem `**Linear**: <ID>` (o Data grava o ID depois de criar a issue)")

    anc, cyclic = ancestors(by_id)
    for tid in cyclic:
        errors.append(f"{tid}: está num ciclo de dependências")
    ids = list(by_id)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            ta, tb = by_id[a], by_id[b]
            if ta.runs_alone or tb.runs_alone or a in anc.get(b, set()) or b in anc.get(a, set()):
                continue
            shared = sorted({f"{x}" for x in ta.may_change for y in tb.may_change if gc.paths_overlap(x, y)})
            if shared:
                errors.append(f"{a} e {b} podem rodar ao mesmo tempo e compartilham {', '.join(shared)}: adicione "
                              "`Depends on` entre elas ou separe os arquivos (D19)")

    left = gc.placeholder_lines(lines)
    if left:
        warnings.append(f"{len(left)} linha(s) com marcador de template não preenchido, ex.: {left[0].strip()[:60]}")

    if execute:
        for name, lns in (("spec.md", spec_lines), ("tasks.md", lines)):
            if lns and not gc.approved(lns):
                errors.append(f"{name} sem `**Approved**: <AAAA-MM-DD> - user: \"<palavras do usuário>\"`: a execução "
                              "só começa depois da aprovação; nunca escreva uma aprovação que o usuário não deu")
    return res


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="validate_tasks.py", description="Checa o tasks.md de uma feature.")
    p.add_argument("target", nargs="?")
    p.add_argument("--root", default=".")
    p.add_argument("--execute", action="store_true", help="antes do 1º ticket: exige as duas aprovações")
    p.add_argument("--published", action="store_true", help="exige o ID do Linear em cada tarefa")
    p.add_argument("--strict", action="store_true")
    a = p.parse_args(argv)
    res = evaluate(a.target, Path(a.root).resolve(), a.execute, a.published)
    print(res.report())
    if res.usage_error:
        return 2
    return 1 if res.errors or (a.strict and res.warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
