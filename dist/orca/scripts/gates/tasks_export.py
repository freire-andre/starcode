"""tasks_export.py: turn an approved tasks.md into the Linear publication plan, and record the IDs back.

  plan    writes one body file per task (the 5-block briefing, plan 5.1) and prints the plan: issue titles,
          body files, `blocks` relations and labels. The Data shows it for confirmation before any write.
  record  writes `**Linear**: <ID>` under each task heading after the issues exist (T1=SC-20 T2=SC-21).

The Data runs the `orca linear` commands itself (plan 5.0); this script never touches the network.

Usage:
  python tasks_export.py plan <feature> [--root DIR] [--out DIR] [--json]
  python tasks_export.py record <feature> T1=SC-20 T2=SC-21 [--root DIR]
Exit: 0 ok, 1 tasks.md invalid for publication, 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gates_common as gc  # noqa: E402
import validate_tasks as vt  # noqa: E402


def briefing(task: vt.Task, feature: str) -> str:
    out = [f"Feature: `{feature}` · Tarefa {task.tid}", ""]
    for name in ("Requirements", "Depends on", "Tests", "Gate", "Runs alone"):
        v = task.value(name)
        if v:
            out.append(f"**{name}**: {v}")
    out.append("")
    for b in vt.BLOCKS:
        out.append(f"#### {b}")
        out += [ln for ln in task.blocks.get(b, [])]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def plan(feature: str | None, root: Path, out_dir: Path | None) -> tuple[dict, int]:
    fdir = gc.resolve_feature(feature, root, "tasks.md")
    res = vt.evaluate(str(fdir), root)
    lines = gc.read_lines(fdir / "tasks.md")
    tasks = vt.parse_tasks(lines)
    out = out_dir or Path(tempfile.mkdtemp(prefix=f"starcode-{fdir.name}-"))
    out.mkdir(parents=True, exist_ok=True)
    issues = []
    for t in tasks:
        body = out / f"{t.tid}.md"
        body.write_text(briefing(t, fdir.name), encoding="utf-8", newline="\n")
        lid = gc.LINEAR_ID_RE.search(t.value("Linear") or "")
        issues.append({"task": t.tid, "title": f"{t.tid}: {t.title}", "bodyFile": str(body),
                       "dependsOn": t.deps, "linear": lid.group(0) if lid else None, "labels": ["crew:data"]})
    relations = [{"blocker": d, "blocked": t.tid} for t in tasks for d in t.deps]
    data = {"feature": fdir.name, "spec": str(fdir / "spec.md"), "issues": issues, "relations": relations,
            "gate": {"ok": res.ok, "errors": res.errors}}
    return data, (0 if res.ok else 1)


def render_md(data: dict) -> str:
    lines = [f"Plano de publicação no Linear: feature `{data['feature']}`", ""]
    if not data["gate"]["ok"]:
        lines.append("ATENÇÃO: validate_tasks está vermelho; corrija antes de publicar:")
        lines += [f"  - {e}" for e in data["gate"]["errors"]]
        lines.append("")
    lines.append("Issues (uma por tarefa, label crew:data, descrição = briefing de 5 blocos):")
    for i in data["issues"]:
        done = f" (já existe: {i['linear']})" if i["linear"] else ""
        lines.append(f"  - {i['title']}{done}\n    corpo: {i['bodyFile']}")
    lines.append("")
    lines.append("Relações `blocks`:" if data["relations"] else "Relações `blocks`: nenhuma")
    for r in data["relations"]:
        lines.append(f"  - {r['blocker']} bloqueia {r['blocked']}")
    return "\n".join(lines)


def record(feature: str | None, root: Path, pairs: list[str]) -> tuple[str, int]:
    fdir = gc.resolve_feature(feature, root, "tasks.md")
    path = fdir / "tasks.md"
    mapping = {}
    for p in pairs:
        m = re.fullmatch(r"(T\d+)=([A-Z][A-Z0-9]*-\d+)", p.strip(), re.IGNORECASE)
        if not m:
            return f"par inválido {p!r} (use T1=SC-20)", 2
        mapping[m.group(1).upper()] = m.group(2).upper()
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    out, current, seen, in_fence = [], None, set(), False
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            in_fence = not in_fence
        m = None if in_fence else vt.TASK_RE.match(ln.strip())
        if m:
            current = m.group(1).upper()
            out.append(ln)
            if current in mapping:
                # replace an existing **Linear** line in the task head, else insert right after the heading
                j = i + 1
                head_end = j
                while head_end < len(lines) and not lines[head_end].strip().startswith(("####", "### ")):
                    head_end += 1
                existing = [k for k in range(j, head_end) if re.match(r"^\**\s*Linear\s*\**\s*:", lines[k].strip(), re.I)]
                if existing:
                    for k in existing:
                        lines[k] = f"**Linear**: {mapping[current]}"
                else:
                    out.append(f"**Linear**: {mapping[current]}")
                seen.add(current)
            i += 1
            continue
        out.append(ln)
        i += 1
    missing = sorted(set(mapping) - seen)
    if missing:
        return "tarefas não encontradas em tasks.md: " + ", ".join(missing), 1
    path.write_text("\n".join(out), encoding="utf-8", newline="\n")
    return "gravado: " + ", ".join(f"{k}={v}" for k, v in mapping.items()), 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="tasks_export.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("plan")
    pp.add_argument("feature", nargs="?")
    pp.add_argument("--root", default=".")
    pp.add_argument("--out")
    pp.add_argument("--json", action="store_true")
    pr = sub.add_parser("record")
    pr.add_argument("feature")
    pr.add_argument("pairs", nargs="+")
    pr.add_argument("--root", default=".")
    a = p.parse_args(argv)
    root = Path(a.root).resolve()
    try:
        if a.cmd == "plan":
            data, code = plan(a.feature, root, Path(a.out) if a.out else None)
            print(json.dumps(data, indent=2, ensure_ascii=False) if a.json else render_md(data))
            return code
        msg, code = record(a.feature, root, a.pairs)
        print(msg)
        return code
    except LookupError as exc:
        print(f"tasks_export: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
