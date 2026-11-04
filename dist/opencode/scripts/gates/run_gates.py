"""run_gates.py: one command that runs the gates of a stage and prints the VERDICT first.

Stages
  spec      before showing the spec           validate_spec
  tasks     before showing the tasks          validate_spec --approved, validate_tasks
  publish   after the Linear writes           validate_tasks --published
  execute   before the first ticket           validate_spec --approved, validate_tasks --execute
            (MEDIUM, no tasks.md: validate_spec --approved, which also checks `## Checks`)
  commit    before each commit                check_commit (--message, --expect-ref)

Output: the verdict line, one line per gate, then the full report. Exit 0 green, 1 red, 2 usage error.

Usage:
  python run_gates.py spec <feature> [--root DIR]
  python run_gates.py commit --message "feat(x): y" --expect-ref SC-12
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_commit  # noqa: E402
import gates_common as gc  # noqa: E402
import validate_spec  # noqa: E402
import validate_tasks  # noqa: E402

STAGES = ("spec", "tasks", "publish", "execute", "commit")


def run_stage(stage: str, feature: str | None, root: Path, message: str | None = None,
              expect_ref: str | None = None, refs_optional: bool = False) -> list[gc.Result]:
    if stage == "spec":
        return [validate_spec.evaluate(feature, root)]
    if stage == "tasks":
        return [validate_spec.evaluate(feature, root, require_approval=True),
                validate_tasks.evaluate(feature, root)]
    if stage == "publish":
        return [validate_tasks.evaluate(feature, root, published=True)]
    if stage == "execute":
        results = [validate_spec.evaluate(feature, root, require_approval=True)]
        try:
            fdir = gc.resolve_feature(feature, root, "spec.md")
            has_tasks = (fdir / "tasks.md").exists()
        except LookupError:
            has_tasks = False
        if has_tasks:
            results.append(validate_tasks.evaluate(feature, root, execute=True))
        return results
    if stage == "commit":
        if not message:
            r = gc.Result("check_commit", usage_error="passe --message")
            return [r]
        return [check_commit.check(message, refs_optional, expect_ref)]
    raise ValueError(stage)


def render(stage: str, results: list[gc.Result]) -> tuple[str, int]:
    usage = any(r.usage_error for r in results)
    failed = [r for r in results if not r.ok]
    if usage:
        verdict, code = "VEREDITO: NÃO RODOU (erro de uso)", 2
    elif failed:
        verdict, code = f"VEREDITO: VERMELHO ({len(failed)} de {len(results)} gate(s) falhou): corrija antes de seguir", 1
    else:
        verdict, code = f"VEREDITO: VERDE (etapa {stage}, {len(results)} gate(s))", 0
    width = max(len(r.gate) for r in results)
    lines = [verdict]
    for r in results:
        mark = "OK  " if r.ok else "FALHA"
        lines.append(f"  {mark} {r.gate.ljust(width)}  {r.summary()}")
    lines.append("")
    lines.append("--- relatório completo ---")
    lines += [r.report() for r in results]
    return "\n".join(lines), code


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="run_gates.py", description="Roda os gates de uma etapa (veredito primeiro).")
    p.add_argument("stage", choices=STAGES)
    p.add_argument("feature", nargs="?")
    p.add_argument("--root", default=".")
    p.add_argument("--message")
    p.add_argument("--expect-ref")
    p.add_argument("--refs-optional", action="store_true")
    a = p.parse_args(argv)
    results = run_stage(a.stage, a.feature, Path(a.root).resolve(), a.message, a.expect_ref, a.refs_optional)
    text, code = render(a.stage, results)
    print(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
