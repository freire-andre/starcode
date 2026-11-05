"""run_gates.py: one command that runs the gates of a stage and prints the VERDICT first.

Stages
  spec      before showing the spec           validate_spec
  tasks     before showing the tasks          validate_spec --approved, validate_tasks
  publish   after the Linear writes           validate_tasks --published
  execute   before the first ticket           validate_spec --approved, validate_tasks --execute
            (MEDIUM, no tasks.md: validate_spec --approved, which also checks `## Checks`)
  commit    before each commit                check_commit (--message, --expect-ref)
  ticket    before integrating a ticket       check_scope + check_commit on every commit of the range
            (the expected Refs is the ticket's `**Linear**:` ID)
  proofs    after the last ticket             check_proofs (writes proofs.md)
  done      after the Q and the post-Q cycle  validate_verification (--strict: degraded is red)

Output: the verdict line, one line per gate, then the full report. Exit 0 green, 1 red, 2 usage error.

Usage:
  python run_gates.py spec <feature> [--root DIR]
  python run_gates.py commit --message "feat(x): y" --expect-ref SC-12
  python run_gates.py ticket <feature> <T<n>|ID> <base>..<head>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import subprocess  # noqa: E402

import check_commit  # noqa: E402
import check_proofs  # noqa: E402
import check_scope  # noqa: E402
import gates_common as gc  # noqa: E402
import validate_verification  # noqa: E402
import validate_spec  # noqa: E402
import validate_tasks  # noqa: E402

STAGES = ("spec", "tasks", "publish", "execute", "commit", "ticket", "proofs", "done")


def ticket_commits(feature: str | None, ticket: str, rng: str, root: Path) -> list[gc.Result]:
    """check_commit on every commit message of the range, expecting the ticket's Linear ID in Refs."""
    try:
        fdir = gc.resolve_feature(feature, root, "tasks.md")
    except LookupError:
        return []
    task = check_scope.find_task(fdir, ticket)
    linear = gc.LINEAR_ID_RE.findall(task.value("Linear") or "") if task else []
    p = subprocess.run(["git", "log", "--format=%H%x00%B%x1e", rng], cwd=gc.project_root(fdir),
                       capture_output=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    if p.returncode != 0:
        return []
    res = gc.Result("check_commit", target=rng)
    for chunk in [c for c in p.stdout.split("\x1e") if c.strip()]:
        sha, _, msg = chunk.strip().partition("\x00")
        r = check_commit.check(msg.strip(), False, linear[0] if linear else None)
        res.errors += [f"{sha[:7]}: {e}" for e in r.errors]
        res.warnings += [f"{sha[:7]}: {w}" for w in r.warnings]
    return [res]


def run_stage(stage: str, feature: str | None, root: Path, message: str | None = None,
              expect_ref: str | None = None, refs_optional: bool = False, ticket: str | None = None,
              rng: str | None = None, strict: bool = False) -> list[gc.Result]:
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
    if stage == "ticket":
        if not ticket or not rng:
            return [gc.Result("check_scope", usage_error="passe <feature> <ticket> <base>..<head>")]
        scope = check_scope.evaluate(feature, ticket, rng, root)
        return [scope] + ([] if scope.usage_error else ticket_commits(feature, ticket, rng, root))
    if stage == "proofs":
        return [check_proofs.evaluate(feature, root)]
    if stage == "done":
        return [validate_verification.evaluate(feature, root, strict)]
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
    p.add_argument("ticket", nargs="?", help="etapa ticket: T<n> ou o ID do Linear")
    p.add_argument("range", nargs="?", help="etapa ticket: <base>..<head>")
    p.add_argument("--root", default=".")
    p.add_argument("--strict", action="store_true", help="etapa done: verificação degradada vira vermelho")
    p.add_argument("--message")
    p.add_argument("--expect-ref")
    p.add_argument("--refs-optional", action="store_true")
    a = p.parse_args(argv)
    results = run_stage(a.stage, a.feature, Path(a.root).resolve(), a.message, a.expect_ref, a.refs_optional,
                        a.ticket, a.range, a.strict)
    text, code = render(a.stage, results)
    print(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
