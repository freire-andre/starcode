"""dispatch.py: what the Picard needs to dispatch workers in sequence (Phase 3, D23).

    python dispatch.py next <slug> [--branch feature/<slug>] [--base <ref>]
        The first ticket of tasks.md whose dependencies are integrated in the branch. Integration is
        read from Git (evidence beats notes): a ticket is integrated when a commit of <base>..<branch>
        cites its Linear ID in a `Refs:` footer, or names it as `integra T<n>`. Exit 0 with the ticket,
        1 when nothing is ready (all integrated, or blocked), 3 when the Handoff has an open dispatch.
    python dispatch.py brief <slug> <ticket> --out <file>
        The worker brief for --spec-file: the ticket's 5 blocks plus the fixed worker rules.
    python dispatch.py q-brief <slug> --base <ref> --head <sha> --out <file>
        Fills the Q brief (briefs/q-verify.md) with the feature paths and the range; no session history.
    python dispatch.py family <cli:model | model | cli> [--compare <other>]
        The model family (crew.yaml `families`, then known prefixes, then the CLI). With --compare:
        `same`, `different` or `unknown`.

Python stdlib only.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE / "gates"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import gates_common as gc  # noqa: E402
import handoff  # noqa: E402
import starcode_common as sc  # noqa: E402
import tasks_export  # noqa: E402
import validate_tasks as vt  # noqa: E402

PREFIX_FAMILIES = (("claude", "anthropic"), ("gpt", "openai"), ("o1", "openai"), ("o3", "openai"),
                   ("o4", "openai"), ("codex", "openai"), ("gemini", "google"))
CLI_FAMILIES = {"claude": "anthropic", "codex": "openai", "antigravity": "google", "agy": "google"}

WORKER_RULES = """## Regras fixas do worker (StarCode)

- Você é o LaForge, um worker com contexto limpo. Se a skill `laforge` estiver disponível, siga-a.
- Implemente só este ticket e altere só os arquivos de `May change`. Precisa de outro arquivo? Pare e
  diga qual e por quê.
- Nunca escreva `.specs/STATE.md` nem a seção `## Handoff` de nenhum artefato: só o Picard escreve nelas.
- Antes de terminar: `run_gates.py ticket {slug} {ticket} <base>..HEAD` verde (base = commit de partida
  deste worktree).
- Falhas: identificador estável por erro; na 2ª falha do mesmo erro, use a skill `mccoy`; na 3ª, pare.
- Relatório final (até 5 linhas): o que mudou, gates executados com resultado, commits, pendências,
  tentativas do disjuntor (`<id>=<n>` ou `none`).
"""


def _git(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, encoding="utf-8", errors="replace",
                       stdin=subprocess.DEVNULL)
    return p.returncode, p.stdout


def load_tasks(slug: str, root: Path) -> tuple[Path, list[vt.Task]]:
    fdir = gc.resolve_feature(slug, root, "tasks.md")
    return fdir, vt.parse_tasks(gc.read_lines(fdir / "tasks.md"))


def linear_id(task: vt.Task) -> str | None:
    ids = gc.LINEAR_ID_RE.findall(task.value("Linear") or "")
    return ids[0] if ids else None


def integrated(tasks: list[vt.Task], root: Path, base: str, branch: str) -> set[str]:
    code, log = _git(root, "log", "--format=%B%x1e", f"{base}..{branch}")
    if code != 0:
        return set()
    text = log
    refs = {i for line in re.findall(r"^Refs:\s*(.+)$", text, re.M) for i in gc.LINEAR_ID_RE.findall(line)}
    named = {m.upper() for m in re.findall(r"\bintegra\s+(T\d+)\b", text, re.I)}
    return {t.tid for t in tasks if (linear_id(t) and linear_id(t) in refs) or t.tid in named}


def handoff_values(fdir: Path) -> dict[str, str]:
    for art in handoff.ARTIFACTS:
        f = fdir / art
        if f.is_file():
            lines = f.read_text(encoding="utf-8").splitlines()
            b = handoff.section_bounds(lines)
            if b:
                return handoff.read_fields(lines, b)
    return {}


def next_ticket(slug: str, root: Path, branch: str | None = None,
                base: str | None = None) -> tuple[int, str]:
    fdir, tasks = load_tasks(slug, root)
    proj = gc.project_root(fdir)
    branch = branch or f"feature/{fdir.name}"
    if base is None:
        cfg, _ = sc.load_repo_config(proj)
        base = (cfg or {}).get("baseBranch", "main")
    done = integrated(tasks, proj, base, branch)
    dispatched = handoff_values(fdir).get("dispatched", "none")
    m = re.match(r"\s*(T\d+)\b", dispatched or "")
    if m and m.group(1).upper() not in done:
        return 3, f"despacho aberto: {dispatched} (confira com `orca orchestration worker-show` antes de redespachar)"
    for t in tasks:
        if t.tid in done:
            continue
        if all(d in done for d in t.deps):
            return 0, f"{t.tid} {linear_id(t) or '-'} {t.title}"
        return 1, f"nenhum ticket liberado: {t.tid} espera {', '.join(d for d in t.deps if d not in done)}"
    return 1, "todos os tickets integrados"


def worker_brief(slug: str, ticket: str, root: Path) -> str:
    fdir, tasks = load_tasks(slug, root)
    want = ticket.upper()
    task = next((t for t in tasks if t.tid == want or linear_id(t) == want), None)
    if task is None:
        raise LookupError(f"ticket {ticket} não existe em {fdir / 'tasks.md'}")
    body = tasks_export.briefing(task, fdir.name)
    head = f"# Ticket {task.tid}: {task.title}\n\nIssue: {linear_id(task) or 'sem issue'}\n\n"
    return head + body + "\n" + WORKER_RULES.format(slug=fdir.name, ticket=task.tid)


def brief_template() -> Path:
    for cand in (sc.PLUGIN_ROOT / "briefs" / "q-verify.md", sc.PLUGIN_ROOT / "src" / "briefs" / "q-verify.md"):
        if cand.is_file():
            return cand
    raise LookupError("briefs/q-verify.md não encontrado no plugin")


def q_brief(slug: str, root: Path, base: str, head: str) -> str:
    fdir = gc.resolve_feature(slug, root, "spec.md")
    proj = gc.project_root(fdir)
    rel = Path(gc.feature_root_hint(fdir))
    tasks = rel / ("tasks.md" if (fdir / "tasks.md").exists() else "spec.md")
    values = {"spec": rel / "spec.md", "tasks": tasks, "proofs": rel / "proofs.md",
              "range": f"{base}..{head}", "output": rel / "verification.md"}
    text = brief_template().read_text(encoding="utf-8")
    for key, val in values.items():
        text = text.replace("{{" + key + "}}", str(val).replace("\\", "/"))
    left = re.findall(r"\{\{[^}]+\}\}", text)
    if left:
        raise ValueError(f"marcadores não preenchidos no briefing do Q: {', '.join(sorted(set(left)))}")
    return f"Repositório: {proj.as_posix()}\n\n" + text


def family(spec: str) -> str:
    """Family of `cli:model`, `model` or `cli`; 'unknown' when it cannot be told."""
    cli, _, model = spec.partition(":") if ":" in spec else ("", "", spec)
    model = model.strip().lower()
    fams = {k.lower(): v for k, v in (sc.load_crew().get("families") or {}).items()}
    if model in fams:
        return fams[model]
    if model and model not in ("cli-default", "default", "padrão"):
        for prefix, fam in PREFIX_FAMILIES:
            if model.startswith(prefix):
                return fam
        if model in CLI_FAMILIES and not cli:
            return CLI_FAMILIES[model]
    return CLI_FAMILIES.get(cli.strip().lower(), "unknown")


def compare(a: str, b: str) -> str:
    fa, fb = family(a), family(b)
    if "unknown" in (fa, fb):
        return "unknown"
    return "same" if fa == fb else "different"


def main(argv: list[str] | None = None) -> int:
    sc.utf8_stdio()
    p = argparse.ArgumentParser(prog="dispatch.py", description="Apoio ao despacho sequencial do Picard.")
    sub = p.add_subparsers(dest="cmd", required=True)
    pn = sub.add_parser("next")
    pn.add_argument("slug")
    pn.add_argument("--branch")
    pn.add_argument("--base")
    pn.add_argument("--root", default=".")
    pb = sub.add_parser("brief")
    pb.add_argument("slug")
    pb.add_argument("ticket")
    pb.add_argument("--out", required=True)
    pb.add_argument("--root", default=".")
    pq = sub.add_parser("q-brief")
    pq.add_argument("slug")
    pq.add_argument("--base", required=True)
    pq.add_argument("--head", required=True)
    pq.add_argument("--out", required=True)
    pq.add_argument("--root", default=".")
    pf = sub.add_parser("family")
    pf.add_argument("spec")
    pf.add_argument("--compare")
    a = p.parse_args(argv)
    try:
        if a.cmd == "next":
            code, msg = next_ticket(a.slug, Path(a.root).resolve(), a.branch, a.base)
            print(msg)
            return code
        if a.cmd == "brief":
            Path(a.out).write_text(worker_brief(a.slug, a.ticket, Path(a.root).resolve()), encoding="utf-8")
            print(f"briefing do ticket gravado em {a.out}")
            return 0
        if a.cmd == "q-brief":
            Path(a.out).write_text(q_brief(a.slug, Path(a.root).resolve(), a.base, a.head), encoding="utf-8")
            print(f"briefing do Q gravado em {a.out}")
            return 0
        if a.compare:
            print(compare(a.spec, a.compare))
        else:
            print(family(a.spec))
        return 0
    except (LookupError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
