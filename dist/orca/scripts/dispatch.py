"""dispatch.py: what the Picard needs to dispatch workers in sequence (Phase 3, D23).

    python dispatch.py next <slug> [--branch feature/<slug>] [--base <ref>]
        The first ticket of tasks.md whose dependencies are integrated in the branch. Integration is
        read from Git (evidence beats notes): a ticket is integrated when a commit of <base>..<branch>
        cites its Linear ID in a `Refs:` footer, or names it as `integra T<n>`. Exit 0 with the ticket,
        1 when nothing is ready (all integrated, or blocked), 3 when any entry of `**Dispatched:**` is not
        integrated yet (the message cites every open one).
    python dispatch.py overdue <slug> [--minutes N] [--now <ISO-8601>] [--branch ...] [--base ...]
        One line per active (not integrated) entry of `**Dispatched:**` whose time (5th field, UTC) plus N
        minutes has passed: `<Tn> · <ID> · <minutes> min · <dispatch id or ->`. N defaults to
        fleet.timeoutMinutes of the user config (30 when absent); --now is for tests. Exit 0 with some
        overdue, 1 with none, 2 when an entry has no readable time (the message cites it).
    python dispatch.py batch <slug> [--branch feature/<slug>] [--base <ref>] [--assign Tn=cli:model]... [--json]
        The next batch of tickets that can run in parallel: not integrated, not active, dependencies
        integrated, no shared `May change` path with an active or already chosen ticket, nothing
        sensitive or `Runs alone` unless idle, up to fleet.maxBatch minus the active workers. Each
        ticket gets a cli:model (fleet.workers round-robin, else the effective LaForge) and a cost tier.
        Exit 0 with a batch, 1 when empty, 2 on a usage or read error.
    python dispatch.py brief <slug> <ticket> --out <file>
        The worker brief for --spec-file: the ticket's 5 blocks plus the fixed worker rules.
    python dispatch.py start <slug> <ticket> --cli <cli> --model <model> [--root DIR] [--json]
        Starts one worker: brief, `Dispatched` entry, Linear status and label, `worker-start` (OpenCode: a
        worktree first), then the entry again with dispatch id and model, and `worktree set`. Refusal: exit 2.
        `worker-start` failure: entry removed, exit 1. Linear and `worktree set` failures are warnings.
        Exit 3: the worker is running but the second Handoff write failed; the first entry stays, a
        `worker ativo sem registro completo` line is printed and `worktree set` is still tried.
    python dispatch.py settle <slug> <ticket> --branch <ticket branch> [--root DIR]
        Integrates one ticket into feature/<slug> (run in that worktree): gate `ticket` over <entry base>..<branch>,
        `git merge --no-ff`, then entry removed, `Last integrated` and `worker-<T>=ok`. Refusal: exit 2. Red gate or
        merge conflict (merge aborted): exit 1, entry kept.
    python dispatch.py q-brief <slug> --base <ref> --head <sha> --out <file>
        Fills the Q brief (briefs/q-verify.md) with the feature paths and the range; no session history.
    python dispatch.py q-check <slug> [--root DIR]
        Reports (never restores or deletes) what the Q left changed: only `verification.md`, `screens.md` and
        `captures/<name>.running.png` of the feature are allowed. Exit 0 clean, 1 files outside the list, 2 git failed.
    python dispatch.py q-waive <slug> [--root DIR]
        PEQUENA (spec `**Size**: SMALL`, D-a): writes `verification.md` with `**Verification:** waived (PEQUENA)` and
        `Q dispensado: tarefa PEQUENA (D-a).`, exit 0. Any other class: exit 2, nothing written.
    python dispatch.py q-cli --laforge <cli:model> [--laforge <cli:model>]... [<cli:model>...] [--configured <q>]
        The Q CLI: first of Q_CLI_ORDER whose family differs from ALL the given LaForge families and whose
        Orca worker is available. None qualifies: `self-verified` (exit 1).
    python dispatch.py family <cli:model | model | cli> [--compare <other>]
        The model family (crew.yaml `families`, then known prefixes, then the CLI). With --compare:
        `same`, `different` or `unknown`.

Python stdlib only.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE / "gates", HERE / "config"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import gates_common as gc  # noqa: E402
import handoff  # noqa: E402
import impact  # noqa: E402
import lessons  # noqa: E402
import screens  # noqa: E402
import validate_config  # noqa: E402
import starcode_common as sc  # noqa: E402
import tasks_export  # noqa: E402
import validate_tasks as vt  # noqa: E402

PREFIX_FAMILIES = (("claude", "anthropic"), ("gpt", "openai"), ("o1", "openai"), ("o3", "openai"),
                   ("o4", "openai"), ("codex", "openai"), ("gemini", "google"), ("deepseek", "deepseek"))
VENDOR_FAMILIES = {"anthropic": "anthropic", "openai": "openai", "google": "google", "deepseek": "deepseek"}
Q_CLI_ORDER = ("codex", "antigravity", "opencode")
CLI_BINARIES = {"codex": "codex", "antigravity": "agy", "opencode": "opencode"}
CLI_FAMILIES = {"claude": "anthropic", "codex": "openai", "antigravity": "google", "agy": "google"}

WORKER_RULES = """## Regras fixas do worker (StarCode)

- Você é o LaForge, um worker com contexto limpo. Se a skill `laforge` estiver disponível, siga-a.
- Implemente só este ticket e altere só os arquivos de `May change`. Precisa de outro arquivo? Pare e
  diga qual e por quê.
- Nunca escreva `.specs/STATE.md` nem a seção `## Handoff` de nenhum artefato: só o Picard escreve nelas.
- Antes de terminar: `python "{plugin}/scripts/gates/run_gates.py" ticket {slug} {ticket} <base>..HEAD` verde
  (base = commit de partida deste worktree).
- Falhas: identificador estável por erro; na 2ª falha do mesmo erro, use a skill `mccoy`; na 3ª, pare.
- Ticket com tela citada por captura (`captures/<nome>.png`): tire a foto do autor com
  `python "{plugin}/scripts/screens.py" capture` em `captures/<nome>.running.png` e commite-a, dentro do `May change`.
- Relatório final (até 5 linhas): o que mudou, gates executados com resultado, commits, pendências,
  tentativas do disjuntor (`<id>=<n>` ou `none`).
- Nunca desligue a assinatura de commits (commit.gpgsign false, --no-gpg-sign) em código de produto; só repositórios Git temporários de teste podem fazê-lo.
"""


PROOF_RULE = ("O teste deve se chamar exatamente como na linha Proof: o `run_gates.py` procura esse nome na "
              "saída; outro nome deixa a prova vermelha.")


DECISIONS_FILE = gc.DECISIONS_FILE


def effective_may_change(task: vt.Task) -> list[str]:
    return gc.effective_may_change(task.may_change)


def with_decisions(task: vt.Task) -> vt.Task:
    extra = effective_may_change(task)[len(task.may_change):]
    if not extra:
        return task
    done = False
    lines = []
    for ln in task.blocks.get("BOUNDARIES", []):
        if not done and re.match(r"^[-*]?\s*\**May change\**\s*:", ln.strip(), re.IGNORECASE):
            body = ln.rstrip()
            ln = body + "".join(f", `{x}`" if body.endswith("`") else f", {x}" for x in extra)
            done = True
        lines.append(ln)
    return dataclasses.replace(task, blocks={**task.blocks, "BOUNDARIES": lines})


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
    entries = handoff.dispatch_entries(handoff_values(fdir).get("dispatched", "none"))
    open_entries = [e for e in entries if handoff.entry_ticket(e).upper() not in done]
    if open_entries:
        return 3, (f"despacho aberto: {'; '.join(open_entries)} "
                   "(confira com `orca orchestration worker-show` antes de redespachar)")
    for t in tasks:
        if t.tid in done:
            continue
        if all(d in done for d in t.deps):
            return 0, f"{t.tid} {linear_id(t) or '-'} {t.title}"
        return 1, f"nenhum ticket liberado: {t.tid} espera {', '.join(d for d in t.deps if d not in done)}"
    return 1, "todos os tickets integrados"


DEFAULT_MAX_BATCH = 3
DEFAULT_TIMEOUT_MINUTES = 30
TIER_ORDER = ("$$$", "$$", "$", "grátis", "?")


def _entry_pair(entry: str) -> str:
    parts = [x.strip() for x in entry.split("·")]
    return parts[3] if len(parts) > 3 else ""


def _valid_pair(value: str, where: str) -> str:
    errors: list[str] = []
    validate_config._check({"type": "worker"}, value, where, errors)
    if errors:
        raise ValueError("; ".join(errors))
    return value


def _cost_total(costs: list[str]) -> str:
    return " + ".join(f"{costs.count(t)}× {t}" for t in TIER_ORDER if t in costs)


def _sensitive_reason(task: vt.Task, patterns: list[str]) -> str | None:
    pattern = next((pat for p in task.may_change if (pat := gc.is_sensitive(p, patterns))), None)
    if pattern:
        return pattern
    return "Runs alone" if task.runs_alone else None


def batch(slug: str, root: Path, branch: str | None = None, base: str | None = None,
          assign: list[str] | None = None) -> dict:
    """The next parallel batch (R1-R7, R9, R10, R12)."""
    fdir = gc.resolve_feature(slug, root, "spec.md")
    if not (fdir / "tasks.md").is_file():
        raise LookupError(f"tasks.md não encontrado em {fdir}")
    fdir, tasks = load_tasks(slug, root)
    proj = gc.project_root(fdir)
    branch = branch or f"feature/{fdir.name}"
    if base is None:
        cfg, _ = sc.load_repo_config(proj)
        base = (cfg or {}).get("baseBranch", "main")
    overrides: dict[str, str] = {}
    for item in assign or []:
        tid, sep, pair = item.partition("=")
        tid = tid.strip().upper()
        if not sep or not re.fullmatch(r"T\d+", tid):
            raise ValueError(f"--assign espera Tn=cli:modelo, veio {item!r}")
        overrides[tid] = _valid_pair(pair.strip(), f"--assign {tid}")
    user_cfg, _ = sc.load_user_config()
    local_cfg, local_err = sc.load_local_config(proj)
    fleet = (user_cfg or {}).get("fleet") or {}
    max_batch = fleet.get("maxBatch", DEFAULT_MAX_BATCH)
    pool = list(fleet.get("workers") or [])
    crew = sc.load_crew()
    done = integrated(tasks, proj, base, branch)
    by_id = {t.tid: t for t in tasks}
    entries = [e for e in handoff.dispatch_entries(handoff_values(fdir).get("dispatched", "none"))
               if handoff.entry_ticket(e).upper() not in done]
    active_ids = [handoff.entry_ticket(e).upper() for e in entries]
    excluded: list[dict] = []
    candidates: list[vt.Task] = []
    for t in tasks:
        if t.tid in done or t.tid in active_ids:
            continue
        waiting = [d for d in t.deps if d not in done]
        if waiting:
            excluded.append({"ticket": t.tid, "reason": f"espera {', '.join(waiting)}"})
        else:
            candidates.append(t)
    patterns = gc.sensitive_patterns(proj)
    reserved = [(tid, p) for tid in active_ids if tid in by_id for p in effective_may_change(by_id[tid])]
    slots = max_batch - len(entries)
    chosen: list[vt.Task] = []
    solo = False
    for i, t in enumerate(candidates):
        if solo:
            excluded.append({"ticket": t.tid, "reason": f"roda sozinho: {chosen[0].tid}"})
            continue
        paths = effective_may_change(t)
        if not paths:
            excluded.append({"ticket": t.tid, "reason": "sem May change"})
            continue
        why = _sensitive_reason(t, patterns)
        if why:
            if not entries and i == 0:
                chosen.append(t)
                solo = True
            else:
                excluded.append({"ticket": t.tid, "reason": f"roda sozinho: {why}"})
            continue
        clash = next(((tid, p) for p in paths for tid, q in reserved if gc.paths_overlap(p, q)), None)
        if clash:
            excluded.append({"ticket": t.tid, "reason": f"arquivo em comum com {clash[0]}: {clash[1]}"})
            continue
        if len(chosen) >= slots:
            excluded.append({"ticket": t.tid, "reason": f"limite de {max_batch} workers ativos"})
            continue
        chosen.append(t)
        reserved += [(t.tid, p) for p in paths]
    start = 0
    for e in reversed(entries):
        if _entry_pair(e) in pool:
            start = pool.index(_entry_pair(e)) + 1
            break
    lf = sc.effective_crew(crew, user_cfg, None if local_err else local_cfg).get("laforge", {})
    default_pair = f"{lf.get('cli')}:{lf.get('model')}"
    out = []
    for n, t in enumerate(chosen):
        pair = overrides.get(t.tid) or (pool[(start + n) % len(pool)] if pool else default_pair)
        cli, _, model = pair.partition(":")
        out.append({"ticket": t.tid, "linear": linear_id(t), "title": t.title, "cli": cli, "model": model,
                    "cost": sc.cost_tier(model, crew.get("costTiers"))})
    active = [{"ticket": tid, "pair": _entry_pair(e)} for tid, e in zip(active_ids, entries)]
    return {"batch": out, "costTotal": _cost_total([b["cost"] for b in out]), "excluded": excluded,
            "active": active}


def _parse_utc(text: str) -> datetime:
    dt = datetime.fromisoformat(text.strip().replace("Z", "+00:00").replace("z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def overdue(slug: str, root: Path, minutes: int | None = None, now: str | None = None,
            branch: str | None = None, base: str | None = None) -> tuple[int, list[str]]:
    """Active entries of Dispatched whose time + N minutes has passed (R22)."""
    fdir, tasks = load_tasks(slug, root)
    proj = gc.project_root(fdir)
    branch = branch or f"feature/{fdir.name}"
    if base is None:
        cfg, _ = sc.load_repo_config(proj)
        base = (cfg or {}).get("baseBranch", "main")
    if minutes is None:
        user_cfg, _ = sc.load_user_config()
        minutes = ((user_cfg or {}).get("fleet") or {}).get("timeoutMinutes", DEFAULT_TIMEOUT_MINUTES)
    try:
        clock = _parse_utc(now) if now else datetime.now(timezone.utc)
    except ValueError:
        raise ValueError(f"--now não é ISO-8601: {now!r}")
    done = integrated(tasks, proj, base, branch)
    late: list[str] = []
    for e in handoff.dispatch_entries(handoff_values(fdir).get("dispatched", "none")):
        tid = handoff.entry_ticket(e).upper()
        if tid in done:
            continue
        parts = [x.strip() for x in e.split("·")]
        if parts[-1] == "blocked":
            continue
        try:
            started = _parse_utc(parts[4])
        except (IndexError, ValueError):
            raise ValueError(f"entrada de Dispatched sem horário legível: {e}")
        elapsed = int((clock - started).total_seconds() // 60)
        if (clock - started).total_seconds() > minutes * 60:
            extra = parts[5:]
            did = next((x for x in extra if x and x != "blocked" and not x.startswith("model ")), "-")
            late.append(f"{tid} · {parts[1] if len(parts) > 1 else '-'} · {elapsed} min · {did}")
    return (0 if late else 1), late


def format_batch(res: dict) -> str:
    lines = [f"{b['ticket']} {b['linear'] or '-'} {b['title']} · {b['cli']}:{b['model']} · {b['cost']}"
             for b in res["batch"]]
    if res["batch"]:
        lines.append(f"total: {res['costTotal']}")
    lines += [f"{x['ticket']}: {x['reason']}" for x in res["excluded"]]
    return "\n".join(lines)


def spec_brief(slug: str, ticket: str, root: Path) -> str:
    """MEDIUM or SMALL feature (no tasks.md): the briefing comes from spec.md (R23, R24)."""
    fdir = gc.resolve_feature(slug, root, "spec.md")
    lines = gc.read_lines(fdir / "spec.md")
    checks = gc.section(lines, "Checks")
    if not checks or not gc.meaningful(checks):
        raise LookupError("spec sem ## Checks: não há o que entregar ao worker")
    title = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), fdir.name)
    m = re.search(r"^\*\*Linear\*\*:[ \t]*(.*)$", "\n".join(lines), re.M)
    ids = gc.LINEAR_ID_RE.findall(m.group(1)) if m else []
    out = [f"# {title}", "", f"Issue: {ids[0] if ids else 'sem issue'}", "",
           f"Feature: `{fdir.name}` · Ticket {ticket}", ""]
    for name in ("Scope", "Requirements", "Checks"):
        body = gc.section(lines, name) or []
        out += [f"## {name}", *body, ""]
    may = gc.effective_may_change(gc.split_paths(gc.field_value(lines, "May change") or ""))
    out += ["## BOUNDARIES", "May change: " + (", ".join(may) if may else
            "não definido na spec; pare e pergunte antes de alterar arquivos fora do Scope"), ""]
    return "\n".join(out).rstrip() + "\n\n" + PROOF_RULE + "\n\n" + WORKER_RULES.format(
        slug=fdir.name, ticket=ticket, plugin=sc.PLUGIN_ROOT.as_posix())


def require_committed(fdir: Path, names: tuple[str, ...]) -> None:
    """The worker's worktree starts from HEAD: planning that is not committed there does not exist for it."""
    proj = gc.project_root(fdir)
    rel = Path(gc.feature_root_hint(fdir))
    missing = [(rel / n).as_posix() for n in names
               if _git(proj, "cat-file", "-e", f"HEAD:{(rel / n).as_posix()}")[0] != 0]
    if missing:
        raise LookupError("planejamento não commitado em HEAD: " + ", ".join(missing) +
                          ". Faça o commit de `.specs/features/<slug>/` antes de despachar o worker, "
                          "senão o worktree dele nasce sem esses arquivos e o `check_scope` falha")


def checks_context(task: vt.Task, lines: list[str]) -> list[str]:
    """The task's check lines and `Proof:` lines, verbatim from `## Checks`, plus the Run lines they read."""
    body = [ln.strip() for ln in (gc.section(lines, "Checks") or [])]
    ids = {i for ln in task.blocks.get("CONTEXT", []) if re.match(r"^\W*Checks?\W*:", ln.strip(), re.I)
           for i in re.findall(r"\bC\d+\b", ln)}
    if not ids:
        reqs = set(re.findall(r"\bR\d+\b", task.value("Requirements") or ""))
        ids = {c.cid for c in gc.read_checks(lines)[0] if reqs & set(c.reqs)}
    out: list[str] = []
    runs: set[str] = set()
    keep = False
    for ln in body:
        m = gc.CHECK_RE.match(ln)
        if m:
            keep = m.group(1) in ids
            if keep:
                out += ["", ln]
        elif keep and gc.PROOF_RE.match(ln):
            out.append(ln)
            rm = gc.RUN_PROOF_RE.match(gc.PROOF_RE.match(ln).group(1).strip().strip("`").strip())
            if rm:
                runs.add(rm.group(1))
    runlines = [ln for ln in body if (r := gc.RUN_RE.match(ln)) and r.group(1) in runs]
    if not out:
        return []
    return ["", "Checks desta task (linhas exatas de `## Checks`):", *runlines, *out, "", PROOF_RULE]


MAX_LESSONS = 10


def lessons_section(root: Path) -> str:
    """`## Lessons` with up to 10 most recent confirmed lessons; '' when there is none (R25)."""
    try:
        data = lessons._load(root)
    except lessons.StoreError as exc:
        print(f"aviso: lessons.json inválido, briefing sem lições ({exc})", file=sys.stderr)
        return ""
    rows = lessons._recent([x for x in data["lessons"] if x["status"] == "confirmed"])[:MAX_LESSONS]
    if not rows:
        return ""
    body = "\n".join(f"- {x['id']}: {x['text']}" for x in rows)
    return f"\n## Lessons\n\n{body}\n"


def worker_brief(slug: str, ticket: str, root: Path) -> str:
    return _worker_brief(slug, ticket, root) + lessons_section(root)


def _worker_brief(slug: str, ticket: str, root: Path) -> str:
    fdir0 = gc.resolve_feature(slug, root, "spec.md")
    if not (fdir0 / "tasks.md").exists():
        require_committed(fdir0, ("spec.md",))
        return spec_brief(slug, ticket, root)
    require_committed(fdir0, ("spec.md", "tasks.md"))
    fdir, tasks = load_tasks(slug, root)
    want = ticket.upper()
    task = next((t for t in tasks if t.tid == want or linear_id(t) == want), None)
    if task is None:
        raise LookupError(f"ticket {ticket} não existe em {fdir / 'tasks.md'}")
    extra = checks_context(task, gc.read_lines(fdir / "tasks.md"))
    if extra:
        blocks = dict(task.blocks)
        blocks["CONTEXT"] = [*blocks.get("CONTEXT", []), *extra]
        task = dataclasses.replace(task, blocks=blocks)
    body = tasks_export.briefing(with_decisions(task), fdir.name)
    head = f"# Ticket {task.tid}: {task.title}\n\nIssue: {linear_id(task) or 'sem issue'}\n\n"
    return head + body + "\n" + WORKER_RULES.format(slug=fdir.name, ticket=task.tid, plugin=sc.PLUGIN_ROOT.as_posix())


def brief_template(name: str = "q-verify.md") -> Path:
    for cand in (sc.PLUGIN_ROOT / "briefs" / name, sc.PLUGIN_ROOT / "src" / "briefs" / name):
        if cand.is_file():
            return cand
    raise LookupError(f"briefs/{name} não encontrado no plugin")


def regression_block(root: Path, base: str, head: str) -> str:
    """Impact selection for the Q brief (R32); a failure never blocks the brief."""
    try:
        diff = f"{base}..{head}"
        if head == "HEAD" and subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=str(root),
                                             stdin=subprocess.DEVNULL).returncode == 1:
            diff = base  # modo 1: mudanças sem commit, árvore de trabalho contra a base (R14)
        return impact.format_text(impact.select(root, diff=diff))
    except Exception as exc:  # noqa: BLE001 - the brief is generated anyway
        return f"seleção indisponível: {exc}; rode a suíte inteira"


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
    left = [m for m in re.findall(r"\{\{[^}]+\}\}", text) if m != "{{regression}}"]
    if left:
        raise ValueError(f"marcadores não preenchidos no briefing do Q: {', '.join(sorted(set(left)))}")
    text = text.replace("{{regression}}", regression_block(root, base, head))  # depois da checagem: caminhos com {{...}} são dado
    return f"Repositório: {proj.as_posix()}\n\n" + text + lessons_section(root)


def q_check(slug: str, root: Path) -> tuple[int, list[str]]:
    """What the Q left changed outside its allowed files (SC-181); reads `git status`, touches nothing."""
    try:
        res = subprocess.run(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
                             cwd=str(root), capture_output=True, encoding="utf-8", errors="replace",
                             stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        raise ValueError(f"git status falhou em {root}: git não encontrado") from None
    if res.returncode != 0:
        why = _first_line(res.stderr, res.stdout) if (res.stderr or res.stdout).strip() else f"código {res.returncode}"
        raise ValueError(f"git status falhou em {root}: {why}")
    base = f".specs/features/{slug}/"
    allowed = {base + "verification.md", base + "screens.md"}
    capture = re.compile(re.escape(base) + r"captures/[^/]+\.running\.png")
    out = []
    records = res.stdout.split("\0")
    i = 0
    while i < len(records):
        rec = records[i]
        i += 1
        if len(rec) < 4:
            continue
        xy, paths = rec[:2], [rec[3:]]
        if "R" in xy or "C" in xy:  # renomeação/cópia: o caminho antigo vem no registro seguinte
            paths.insert(0, records[i] if i < len(records) else "")
            i += 1
        if all(p in allowed or capture.fullmatch(p) for p in paths):
            continue
        out.append(f"fora da lista: {xy} {' -> '.join(paths)}")
    if not out:
        return 0, ["q-check: só arquivos permitidos alterados"]
    out.append(f"q-check: {len(out)} arquivo(s) fora da lista; desfaça com git restore (rastreados) ou apague (novos)")
    return 1, out


def screens_brief(slug: str, root: Path, url: str, serve: str = "", rnd: int = 1) -> str:
    """Brief of the screen judge: spec, pictures (`screens.py list`), URL, serve command, output, round (R21-R22)."""
    pictures = screens.list_screens(slug, root)
    if not pictures:
        raise ValueError("a spec não cita captura vinculante: não há telas para julgar")
    fdir = gc.resolve_feature(slug, root, "spec.md")
    proj = gc.project_root(fdir)
    rel = Path(gc.feature_root_hint(fdir))
    values = {"spec": rel / "spec.md", "pictures": json.dumps(pictures, ensure_ascii=False, indent=2),
              "url": url, "serve": serve, "output": rel / "screens.md", "round": rnd,
              "screens_py": Path(screens.__file__).resolve()}
    text = brief_template("screens-verify.md").read_text(encoding="utf-8")
    for key, val in values.items():
        text = text.replace("{{" + key + "}}", str(val).replace("\\", "/") if key != "pictures" else str(val))
    left = re.findall(r"\{\{[^}]+\}\}", text)
    if left:
        raise ValueError(f"marcadores não preenchidos no briefing do juiz de telas: {', '.join(sorted(set(left)))}")
    return f"Repositório: {proj.as_posix()}\n\n" + text


def family(spec: str) -> str:
    """Family of `cli:model`, `model` or `cli`; 'unknown' when it cannot be told."""
    cli, _, model = spec.partition(":") if ":" in spec and not spec.lower().startswith("openrouter/")         else ("", "", spec)
    model = model.strip().lower()
    if model.startswith("openrouter/"):
        parts = [p.strip() for p in model.split("/", 2)]
        if len(parts) < 3 or not parts[1] or not parts[2]:
            return "unknown"
        return VENDOR_FAMILIES.get(parts[1]) or _catalog_family(model)
    fams = {k.lower(): v for k, v in (sc.load_crew().get("families") or {}).items()}
    if model in fams:
        return fams[model]
    if model and model not in ("cli-default", "default", "padrão"):
        for prefix, fam in PREFIX_FAMILIES:
            if model.startswith(prefix):
                return fam
        if model in CLI_FAMILIES and not cli:
            return CLI_FAMILIES[model]
        if "/" in model:  # OpenCode `provider/model` (zai/glm-5.3, opencode/muse-spark-1.2...)
            return _catalog_family(model)
    return CLI_FAMILIES.get(cli.strip().lower(), "unknown")


def _catalog_family(model: str) -> str:
    """Vendor family from the cached models.dev catalog (never downloads); 'unknown' when absent."""
    try:
        import model_info  # noqa: PLC0415

        return model_info.cached_family(model) or "unknown"
    except Exception:  # noqa: BLE001 - a broken cache never breaks the dispatch
        return "unknown"


def compare(a: str, b: str) -> str:
    fa, fb = family(a), family(b)
    if "unknown" in (fa, fb):
        return "unknown"
    return "same" if fa == fb else "different"


def _default_caps_dirs() -> list[Path]:
    return [sc.PLUGIN_ROOT.parent, sc.PLUGIN_ROOT / "dist"]


def _orca_worker_status(cli: str, caps_dir: Path | None) -> str | None:
    """The `orca_worker` status of a CLI's capability record; None when no record can be found."""
    for d in ([caps_dir] if caps_dir else _default_caps_dirs()):
        f = d / cli / "capabilities.json"
        if f.is_file():
            try:
                extras = json.loads(f.read_text(encoding="utf-8")).get("extras", {})
            except (OSError, ValueError):
                return "unavailable"
            return (extras.get("orca_worker") or {}).get("status") or "unavailable"
    own = sc.PLUGIN_ROOT / "capabilities.json"
    if not caps_dir and own.is_file():
        try:
            doc = json.loads(own.read_text(encoding="utf-8"))
            if doc.get("cli") == cli:
                return (doc.get("extras", {}).get("orca_worker") or {}).get("status") or "unavailable"
        except (OSError, ValueError):
            pass
    return None


def _orca_worker_ok(cli: str, caps_dir: Path | None, configured: bool = False, which=shutil.which) -> bool:
    """A record decides. Without one (a plugin installed in one CLI only carries its own record), an explicitly
    configured CLI or one whose binary is on PATH counts as available. An explicit --caps-dir is authoritative."""
    status = _orca_worker_status(cli, caps_dir)
    if status is not None:
        return status == "ok"
    if caps_dir:
        return False
    return configured or bool(which(CLI_BINARIES.get(cli, cli)))


def _q_cli_orca_worker(laforge: str | list[str], configured: str | None, caps_dir: Path | None, which) -> str | None:
    """First CLI of (configured, codex, antigravity, opencode) whose family differs from all the LaForge
    families (one spec or a list) and that is available for an Orca worker (R18)."""
    lfs = {family(x) for x in ([laforge] if isinstance(laforge, str) else laforge)}
    seen: list[str] = []
    for spec in ([configured] if configured else []) + list(Q_CLI_ORDER):
        if spec in seen:
            continue
        seen.append(spec)
        cli = spec.partition(":")[0]
        fam = family(spec)
        if (fam != "unknown" and "unknown" not in lfs and fam not in lfs
                and _orca_worker_ok(cli, caps_dir, spec == configured, which)):
            return spec
    return None


def q_cli(laforge: str | list[str], configured: str | None = None, caps_dir: Path | None = None,
          which=shutil.which, strategies: list[str] | None = None, warn=None) -> str | None:
    """Walk the qStrategy list (None = `["orca-worker"]`, the historical order): `orca-worker` picks the first
    CLI of another family available for an Orca worker (R18); `self-verified` stops with None (R19);
    `opencode-subagent` is not implemented yet: `warn` gets a line and the walk goes on. None also when
    no item gives a Q."""
    for item in (strategies if strategies is not None else ["orca-worker"]):
        if item == "self-verified":
            return None
        if item == "opencode-subagent":
            if warn:
                warn("q-cli: estratégia opencode-subagent ainda não implementada; seguindo para a próxima")
            continue
        if item == "orca-worker":
            pick = _q_cli_orca_worker(laforge, configured, caps_dir, which)
            if pick:
                return pick
    return None


def user_q_strategy() -> list[str] | None:
    """`qStrategy` of the valid user config (honours STARCODE_HOME); None when absent, invalid or without the field."""
    cfg, errs = sc.load_user_config()
    if errs or not cfg:
        return None
    return cfg.get("qStrategy")


def default_runner(cmd, **kw):
    """`subprocess.run`, resolving `orca` through PATH (`orca.cmd` on Windows)."""
    if cmd and cmd[0] == "orca":
        cmd = [shutil.which("orca") or "orca", *cmd[1:]]
    return subprocess.run(cmd, **kw)


def _call(runner, cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        res = runner(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace",
                     stdin=subprocess.DEVNULL)
    except OSError:
        return 127, "", f"executável não encontrado: {cmd[0] if cmd else ''}"
    return res.returncode, res.stdout or "", res.stderr or ""


def _first_line(*texts: str) -> str:
    for t in texts:
        for ln in t.splitlines():
            if ln.strip():
                return ln.strip()
    return "sem mensagem"


def _find(data, *names: str):
    """First value of a key in `names` anywhere in a JSON document (breadth first)."""
    queue = [data]
    while queue:
        cur = queue.pop(0)
        if isinstance(cur, dict):
            for n in names:
                if cur.get(n) not in (None, "", {}):
                    return cur[n]
            queue += list(cur.values())
        elif isinstance(cur, list):
            queue += cur
    return None


def _text_of(value) -> str:
    if isinstance(value, dict):
        value = _find(value, "id", "path", "selector", "name")
    return str(value) if value not in (None, "") else ""


def _receipt(out: str) -> dict:
    try:
        data = json.loads(out)
    except ValueError:
        return {"dispatch": "", "model": "", "worktree": ""}
    dispatch = _find(data, "dispatchId", "dispatch_id", "dispatch")
    return {"dispatch": _text_of(dispatch), "model": _text_of(_find(data, "model")),
            "worktree": _text_of(_find(data, "workspace", "worktreeId", "worktree"))}


def medium_ticket(fdir: Path, ticket: str, lines: list[str] | None = None) -> tuple[str, str, str] | None:
    """MEDIUM feature (no tasks.md): the only ticket is `T1`, with the issue of the spec's `**Linear**:`.
    Returns (tid, issue, title), or None when `ticket` is neither `T1` nor that issue."""
    if lines is None:
        lines = gc.read_lines(fdir / "spec.md")
    ids = gc.LINEAR_ID_RE.findall(gc.field_value(lines, "Linear") or "")
    if ticket.upper() not in ("T1", ids[0] if ids else "T1"):
        return None
    title = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), fdir.name)
    return "T1", ids[0] if ids else "", title


def spec_issue(fdir: Path, lines: list[str] | None = None) -> str | None:
    if lines is None:
        lines = gc.read_lines(fdir / "spec.md")
    ids = gc.LINEAR_ID_RE.findall(gc.field_value(lines, "Linear") or "")
    return ids[0] if ids else None


def start(slug: str, ticket: str, cli: str, model: str, root: Path, runner=default_runner,
          emit=print, now: datetime | None = None) -> tuple[int, dict]:
    """Start one worker (R5-R11, R17). Exit 2 refuses before writing or calling Orca."""
    fdir0 = gc.resolve_feature(slug, root, "spec.md")
    medium = not (fdir0 / "tasks.md").exists()

    def refuse(why: str) -> tuple[int, dict]:
        emit(f"start recusado: {why}")
        return 2, {}

    if medium:
        fdir = fdir0
        proj = gc.project_root(fdir)
        spec_lines = gc.read_lines(fdir / "spec.md")
        issue = spec_issue(fdir, spec_lines)
        if not issue:
            return refuse("spec sem **Linear**:")
        found = medium_ticket(fdir, ticket, spec_lines)
        if found is None:
            return refuse(f"ticket {ticket} não é desta feature MÉDIA (use {issue} ou T1)")
        tid, issue, title = found
    else:
        fdir, tasks = load_tasks(slug, root)
        proj = gc.project_root(fdir)
        want = ticket.upper()
        task = next((t for t in tasks if t.tid == want or linear_id(t) == want), None)
        if task is None:
            return refuse(f"ticket {ticket} não existe em tasks.md")
        tid, title = task.tid, task.title
        issue = linear_id(task)
        if not issue:
            return refuse(f"{tid} não tem **Linear**:")
    values = handoff_values(fdir)
    open_ids = [handoff.entry_ticket(e).upper() for e in handoff.dispatch_entries(values.get("dispatched", "none"))]
    if tid in open_ids:
        return refuse(f"{tid} já tem entrada em Dispatched "
                      f"(nova tentativa: handoff.py set {fdir.name} --dispatch-remove {tid})")
    if values.get("integration branch", "").strip() in ("", "not created", "none yet", "none"):
        return refuse("o Handoff não tem **Integration branch:** "
                      "(modo 1: siga a seção 7 do execute.md, sem start)")
    branch = f"feature/{fdir.name}"
    code, sha, _ = _call(runner, ["git", "rev-parse", "--short", branch], proj)
    sha = sha.strip()
    if code != 0 or not sha:
        return refuse(f"ramo {branch} não existe")
    cfg, _ = sc.load_repo_config(proj)
    started = (((cfg or {}).get("linear") or {}).get("states") or {}).get("started") or "started"
    brief = Path(tempfile.mkdtemp(prefix="starcode-")) / f"{fdir.name}-{tid}.md"
    brief.write_text(worker_brief(slug, tid, root), encoding="utf-8", newline="\n")
    emit(f"briefing: {brief}")
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    head = f"{tid} · {issue} · base {sha} · "
    handoff_cmd = [sys.executable, str(HERE / "handoff.py"), "set", fdir.name, "--root", str(root)]

    def record(pair: str, tail: str = "") -> None:
        c, o, e = _call(runner, [*handoff_cmd, "--dispatch-add", f"{head}{pair} · {stamp}{tail}"], proj)
        if c != 0:
            raise ValueError(f"handoff.py falhou: {_first_line(e, o)}")

    def unrecord() -> None:
        _call(runner, [*handoff_cmd, "--dispatch-remove", tid], proj)

    record(f"{cli}:{model}")
    emit(f"Dispatched: {tid} registrado (base {sha})")
    for label, cmd in (
            (f"status {started}", ["orca", "linear", "status", "set", issue, "--to", started]),
            ("label crew:laforge", ["orca", "linear", "label", "add", issue, "--label", "crew:laforge"])):
        c, o, e = _call(runner, cmd, proj)
        emit(f"{label}: {issue}" if c == 0 else f"aviso: {label}: {_first_line(e, o)}")
    worktree = "new-child"
    if cli == "opencode":
        c, o, e = _call(runner, ["orca", "worktree", "create", "--name", tid, "--base-branch", branch,
                                 "--json"], proj)
        created = _receipt(o)["worktree"] if c == 0 else ""
        if not created:
            unrecord()
            emit(f"worker-start falhou: worktree create: {_first_line(e, o)}")
            return 1, {}
        worktree = created
        emit(f"worktree criado: {worktree}")
    c, o, e = _call(runner, ["orca", "orchestration", "worker-start", "--agent", cli, "--model", model,
                             "--worktree", worktree, "--base-branch", branch, "--spec-file", str(brief),
                             "--task-title", f"{tid}: {title}", "--json"], proj)
    if c != 0:
        unrecord()
        emit(f"worker-start falhou: {_first_line(e, o)}")
        return 1, {}
    rec = _receipt(o)
    used = rec["model"] or model
    code = 0
    try:
        record(f"{cli}:{used}", f" · {rec['dispatch']}" if rec["dispatch"] else "")
        emit(f"worker iniciado: {tid} · {cli}:{used} · {rec['dispatch'] or '-'}")
    except ValueError as exc:
        code = 3
        emit(f"worker ativo sem registro completo: {tid} · {rec['dispatch'] or '-'} · "
             f"{rec['worktree'] or '-'}: {_first_line(str(exc))}")
    if rec["worktree"]:
        c, o, e = _call(runner, ["orca", "worktree", "set", "--worktree", rec["worktree"], "--linear-issue",
                                 issue], proj)
        emit(f"worktree {rec['worktree']} ligado a {issue}" if c == 0
             else f"aviso: worktree set: {_first_line(e, o)}")
    else:
        emit("aviso: worktree set: o recibo não traz o workspace")
    return code, {"ticket": tid, "issue": issue, "base": sha, "dispatch": rec["dispatch"],
               "worktree": rec["worktree"], "model": used}


def _entry_base(entry: str) -> str:
    parts = [x.strip() for x in entry.split("·")]
    return parts[2].removeprefix("base").strip() if len(parts) > 2 else ""


def settle(slug: str, ticket: str, branch: str, root: Path, runner=default_runner,
           emit=print) -> int:
    """Integrate one ticket into feature/<slug> (R12-R17). Exit 2 refuses before the gate and the merge."""
    fdir0 = gc.resolve_feature(slug, root, "spec.md")
    target = f"feature/{fdir0.name}"

    def refuse(why: str) -> int:
        emit(f"settle recusado: {why}")
        return 2

    if not (fdir0 / "tasks.md").exists():
        fdir = fdir0
        proj = gc.project_root(fdir)
        found = medium_ticket(fdir, ticket)
        if found is None:
            return refuse(f"ticket {ticket} não é desta feature MÉDIA (use {spec_issue(fdir) or 'o ID do Linear'} ou T1)")
        tid, issue = found[0], found[1] or "-"
    else:
        fdir, tasks = load_tasks(slug, root)
        proj = gc.project_root(fdir)
        want = ticket.upper()
        task = next((t for t in tasks if t.tid == want or linear_id(t) == want), None)
        tid = task.tid if task else want
        issue = (linear_id(task) if task else None) or "-"

    entry = next((e for e in handoff.dispatch_entries(handoff_values(fdir).get("dispatched", "none"))
                  if handoff.entry_ticket(e).upper() == tid), None)
    if entry is None:
        return refuse(f"{tid} não tem entrada em Dispatched")
    base = _entry_base(entry)
    if not base:
        return refuse(f"a entrada de {tid} em Dispatched não traz a base")
    _, current, _ = _call(runner, ["git", "rev-parse", "--abbrev-ref", "HEAD"], proj)
    if current.strip() != target:
        return refuse(f"o ramo atual é {current.strip() or '?'}, não {target}")
    if _call(runner, ["git", "rev-parse", "--verify", "--quiet", f"{branch}^{{commit}}"], proj)[0] != 0:
        return refuse(f"ramo {branch} não existe")
    c, o, e = _call(runner, [sys.executable, str(HERE / "gates" / "run_gates.py"), "ticket", fdir.name, tid,
                             f"{base}..{branch}", "--root", str(root)], proj)
    if c != 0:
        emit(f"gate vermelho: {tid}")
        lines = [ln.strip() for ln in (o + chr(10) + e).splitlines() if "FALHA" in ln or "ERRO" in ln]
        for ln in lines or [_first_line(o, e)]:
            emit(ln)
        return 1
    msg = ["-m", f"merge: integra {tid} ({issue}) em {target}", "-m", f"Refs: {issue}"]
    c, o, e = _call(runner, ["git", "merge", "--no-ff", branch, *msg], proj)
    if c != 0:
        _, files, _ = _call(runner, ["git", "diff", "--name-only", "--diff-filter=U"], proj)
        _call(runner, ["git", "merge", "--abort"], proj)
        names = ", ".join(f for f in files.split() if f) or _first_line(e, o)
        emit(f"conflito no merge de {tid}: {names}")
        return 1
    _, sha, _ = _call(runner, ["git", "rev-parse", "HEAD"], proj)
    sha = sha.strip()
    c, o, e = _call(runner, [sys.executable, str(HERE / "handoff.py"), "set", fdir.name, "--root", str(root),
                             "--dispatch-remove", tid, "--last-integrated", sha, "--attempt", f"worker-{tid}=ok"],
                    proj)
    if c != 0:
        emit(f"aviso: handoff.py falhou depois do merge: {_first_line(e, o)}")
    _, short, _ = _call(runner, ["git", "rev-parse", "--short", "HEAD"], proj)
    emit(f"integrado {tid} em {target}: {short.strip()}")
    return 0


def q_waive(slug: str, root: Path, emit=print) -> int:
    """D-a: the Q is waived for a PEQUENA (Size SMALL); writes verification.md with the marker the `done` gate
    reads. Exit 2 refuses any other class, writing nothing."""
    fdir = gc.resolve_feature(slug, root, "spec.md")
    lines = gc.read_lines(fdir / "spec.md")
    size = gc.size_of(lines)
    if size != "SMALL":
        emit(f"q-waive recusado: só a PEQUENA dispensa o Q (Size: {size or gc.field_value(lines, 'Size') or '?'})")
        return 2
    existing = fdir / "verification.md"
    if existing.exists() and not re.search(
            r"^\*\*Verification:\*\*\s*waived(?: \(PEQUENA\))?\s*$", existing.read_text(encoding="utf-8"), re.M):
        emit("q-waive recusado: verification.md já existe (relatório do Q)")
        return 2
    body = [f"# {fdir.name}: Verification", "", "**Verification:** waived (PEQUENA)", "",
            "Q dispensado: tarefa PEQUENA (D-a)."]
    (fdir / "verification.md").write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")
    emit(f"Q dispensado: verification.md gravado em {fdir.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    sc.utf8_stdio()
    p = argparse.ArgumentParser(prog="dispatch.py", description="Apoio ao despacho sequencial do Picard.")
    sub = p.add_subparsers(dest="cmd", required=True)
    pn = sub.add_parser("next")
    pn.add_argument("slug")
    pn.add_argument("--branch")
    pn.add_argument("--base")
    pn.add_argument("--root", default=".")
    pt = sub.add_parser("batch")
    pt.add_argument("slug")
    pt.add_argument("--branch")
    pt.add_argument("--base")
    pt.add_argument("--assign", action="append", default=[])
    pt.add_argument("--json", action="store_true")
    pt.add_argument("--root", default=".")
    pb = sub.add_parser("brief")
    pb.add_argument("slug")
    pb.add_argument("ticket")
    pb.add_argument("--out", required=True)
    pb.add_argument("--root", default=".")
    pst = sub.add_parser("start")
    pst.add_argument("slug")
    pst.add_argument("ticket")
    pst.add_argument("--cli", required=True)
    pst.add_argument("--model", required=True)
    pst.add_argument("--json", action="store_true")
    pst.add_argument("--root", default=".")
    pse = sub.add_parser("settle")
    pse.add_argument("slug")
    pse.add_argument("ticket")
    pse.add_argument("--branch", required=True)
    pse.add_argument("--root", default=".")
    pw = sub.add_parser("q-waive")
    pw.add_argument("slug")
    pw.add_argument("--root", default=".")
    pq = sub.add_parser("q-brief")
    pq.add_argument("slug")
    pq.add_argument("--base", required=True)
    pq.add_argument("--head", required=True)
    pq.add_argument("--out", required=True)
    pq.add_argument("--root", default=".")
    pk = sub.add_parser("q-check")
    pk.add_argument("slug")
    pk.add_argument("--root", default=".")
    ps = sub.add_parser("screens-brief")
    ps.add_argument("slug")
    ps.add_argument("--url", required=True)
    ps.add_argument("--serve", default="")
    ps.add_argument("--round", type=int, choices=(1, 2), default=1)
    ps.add_argument("--out", required=True)
    ps.add_argument("--root", default=".")
    pf = sub.add_parser("family")
    pf.add_argument("spec")
    pf.add_argument("--compare")
    pc = sub.add_parser("q-cli")
    pc.add_argument("laforge_pos", nargs="*", metavar="laforge")
    pc.add_argument("--laforge", action="append", default=[])
    pc.add_argument("--configured")
    pc.add_argument("--caps-dir")
    po = sub.add_parser("overdue")
    po.add_argument("slug")
    po.add_argument("--minutes", type=int)
    po.add_argument("--now")
    po.add_argument("--branch")
    po.add_argument("--base")
    po.add_argument("--root", default=".")
    a = p.parse_args(argv)
    try:
        if a.cmd == "next":
            code, msg = next_ticket(a.slug, Path(a.root).resolve(), a.branch, a.base)
            print(msg)
            return code
        if a.cmd == "batch":
            res = batch(a.slug, Path(a.root).resolve(), a.branch, a.base, a.assign)
            print(json.dumps(res, ensure_ascii=False) if a.json else format_batch(res))
            return 0 if res["batch"] else 1
        if a.cmd == "overdue":
            code, lines = overdue(a.slug, Path(a.root).resolve(), a.minutes, a.now, a.branch, a.base)
            if lines:
                print("\n".join(lines))
            return code
        if a.cmd == "brief":
            Path(a.out).write_text(worker_brief(a.slug, a.ticket, Path(a.root).resolve()), encoding="utf-8")
            print(f"briefing do ticket gravado em {a.out}")
            return 0
        if a.cmd == "start":
            def emit(line: str) -> None:
                print(line, file=sys.stderr if a.json else sys.stdout)
            code, res = start(a.slug, a.ticket, a.cli, a.model, Path(a.root).resolve(), emit=emit)
            if a.json and code in (0, 3):
                print(json.dumps(res, ensure_ascii=False))
            return code
        if a.cmd == "settle":
            return settle(a.slug, a.ticket, a.branch, Path(a.root).resolve())
        if a.cmd == "q-waive":
            return q_waive(a.slug, Path(a.root).resolve())
        if a.cmd == "q-brief":
            Path(a.out).write_text(q_brief(a.slug, Path(a.root).resolve(), a.base, a.head), encoding="utf-8")
            print(f"briefing do Q gravado em {a.out}")
            return 0
        if a.cmd == "q-check":
            code, lines = q_check(a.slug, Path(a.root).resolve())
            print("\n".join(lines))
            return code
        if a.cmd == "screens-brief":
            text = screens_brief(a.slug, Path(a.root).resolve(), a.url, a.serve, a.round)
            Path(a.out).write_text(text, encoding="utf-8", newline="\n")
            print(f"briefing do juiz de telas gravado em {a.out}")
            return 0
        if a.cmd == "q-cli":
            lfs = [*a.laforge_pos, *a.laforge]
            if not lfs:
                raise ValueError("q-cli precisa de ao menos um --laforge <cli:model>")
            pick = q_cli(lfs, a.configured, Path(a.caps_dir) if a.caps_dir else None,
                         strategies=user_q_strategy(), warn=lambda m: print(m, file=sys.stderr))
            print(pick or "self-verified")
            return 0 if pick else 1
        if a.compare:
            print(compare(a.spec, a.compare))
        else:
            print(family(a.spec))
        return 0
    except FileNotFoundError as exc:
        print(f"dispatch: arquivo não encontrado: {exc.filename or exc}", file=sys.stderr)
        return 2
    except (LookupError, ValueError, screens.ScreenError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
