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
    python dispatch.py q-brief <slug> --base <ref> --head <sha> --out <file>
        Fills the Q brief (briefs/q-verify.md) with the feature paths and the range; no session history.
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
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE / "gates", HERE / "config"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import gates_common as gc  # noqa: E402
import handoff  # noqa: E402
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
- Relatório final (até 5 linhas): o que mudou, gates executados com resultado, commits, pendências,
  tentativas do disjuntor (`<id>=<n>` ou `none`).
"""


PROOF_RULE = ("O teste deve se chamar exatamente como na linha Proof: o `run_gates.py` procura esse nome na "
              "saída; outro nome deixa a prova vermelha.")


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
    reserved = [(tid, p) for tid in active_ids if tid in by_id for p in by_id[tid].may_change]
    slots = max_batch - len(entries)
    chosen: list[vt.Task] = []
    solo = False
    for i, t in enumerate(candidates):
        if solo:
            excluded.append({"ticket": t.tid, "reason": f"roda sozinho: {chosen[0].tid}"})
            continue
        paths = t.may_change
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
    lf = sc.effective_crew(crew, user_cfg).get("laforge", {})
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
    """MEDIUM feature (no tasks.md): the briefing comes from spec.md (R23, R24)."""
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
    may = gc.split_paths(gc.field_value(lines, "May change") or "")
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
    body = tasks_export.briefing(task, fdir.name)
    head = f"# Ticket {task.tid}: {task.title}\n\nIssue: {linear_id(task) or 'sem issue'}\n\n"
    return head + body + "\n" + WORKER_RULES.format(slug=fdir.name, ticket=task.tid, plugin=sc.PLUGIN_ROOT.as_posix())


def brief_template(name: str = "q-verify.md") -> Path:
    for cand in (sc.PLUGIN_ROOT / "briefs" / name, sc.PLUGIN_ROOT / "src" / "briefs" / name):
        if cand.is_file():
            return cand
    raise LookupError(f"briefs/{name} não encontrado no plugin")


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
    return f"Repositório: {proj.as_posix()}\n\n" + text + lessons_section(root)


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
        return VENDOR_FAMILIES.get(parts[1], "unknown")
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


def q_cli(laforge: str | list[str], configured: str | None = None, caps_dir: Path | None = None,
          which=shutil.which) -> str | None:
    """First CLI of (configured, codex, antigravity, opencode) whose family differs from all the LaForge
    families (one spec or a list) and that is available for an Orca worker (R18); None means self-verified (R19), only when no CLI of
    another family is configured or available."""
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
    pq = sub.add_parser("q-brief")
    pq.add_argument("slug")
    pq.add_argument("--base", required=True)
    pq.add_argument("--head", required=True)
    pq.add_argument("--out", required=True)
    pq.add_argument("--root", default=".")
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
        if a.cmd == "q-brief":
            Path(a.out).write_text(q_brief(a.slug, Path(a.root).resolve(), a.base, a.head), encoding="utf-8")
            print(f"briefing do Q gravado em {a.out}")
            return 0
        if a.cmd == "screens-brief":
            text = screens_brief(a.slug, Path(a.root).resolve(), a.url, a.serve, a.round)
            Path(a.out).write_text(text, encoding="utf-8", newline="\n")
            print(f"briefing do juiz de telas gravado em {a.out}")
            return 0
        if a.cmd == "q-cli":
            lfs = [*a.laforge_pos, *a.laforge]
            if not lfs:
                raise ValueError("q-cli precisa de ao menos um --laforge <cli:model>")
            pick = q_cli(lfs, a.configured, Path(a.caps_dir) if a.caps_dir else None)
            print(pick or "self-verified")
            return 0 if pick else 1
        if a.compare:
            print(compare(a.spec, a.compare))
        else:
            print(family(a.spec))
        return 0
    except (LookupError, ValueError, screens.ScreenError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
