"""Deterministic helpers for /starcode:setup. Python stdlib only.

  python setup_helpers.py map-states < states.json
      Input: output of `orca linear team states --team KEY --json`. Proposes the mapping by category
      (unstarted, started, review, completed, blocked) and lists ambiguities the user must resolve.
  python setup_helpers.py missing-labels < labels.json
      Input: output of `orca linear team labels --team KEY --json`. Prints the crew:* labels missing.
  python setup_helpers.py crew-table
      Prints the crew with default cli/model (crew.yaml) and the effective value after the user config.
  python setup_helpers.py repo-config --workspace ID --team KEY --base-branch B --states-json FILE
                          [--stack a,b] [--sensitive p1,p2]
      Prints a repo config (schemaVersion 1) for review; write it with validate_config.py --write.
  python setup_helpers.py clis
      Which StarCode CLIs are on PATH (claude, codex, agy, opencode): one line each.
  python setup_helpers.py suggest --have claude,codex [--model opencode=<id>[@$$] ...] [--json]
      Proposes a model per crew member from only the CLIs the user has, keeping the cost tier of each
      default (heavy reasoning $$$, execution $$, repetitive $). Q goes to another family when there is
      one; otherwise it stays degraded (self-verified). Prints a table, notes and the user config with
      only the differences from crew.yaml; write it with validate_config.py --kind user --write.
      A --model tier comes from @<tier>, else crew.yaml costTiers, else the cached models.dev catalog.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import starcode_common as sc  # noqa: E402

REVIEW = re.compile(r"review|revis|\bqa\b|valida|homolog|test(?:ing)?\b", re.I)
BLOCKED = re.compile(r"block|bloque|imped|on hold|parad|waiting|aguard", re.I)


def _states(doc: dict) -> list[dict]:
    result = doc.get("result", doc)
    states = result.get("states", []) if isinstance(result, dict) else []
    return [s for s in states if isinstance(s, dict) and "name" in s and "type" in s]


def map_states(doc: dict) -> dict:
    states = sorted(_states(doc), key=lambda s: s.get("position", 0))
    by_type: dict[str, list[str]] = {}
    for s in states:
        by_type.setdefault(s["type"], []).append(s["name"])
    started = by_type.get("started", [])
    review = [n for n in started if REVIEW.search(n)]
    blocked = [s["name"] for s in states if BLOCKED.search(s["name"]) and s["type"] not in ("completed", "canceled")]
    plain_started = [n for n in started if n not in review and n not in blocked]
    candidates = {
        "unstarted": by_type.get("unstarted", []) or by_type.get("backlog", []),
        "started": plain_started,
        "review": review,
        "completed": by_type.get("completed", []),
        "blocked": blocked,
    }
    mapping: dict[str, str | None] = {}
    ambiguous: dict[str, list[str]] = {}
    missing: list[str] = []
    for key, names in candidates.items():
        if len(names) == 1:
            mapping[key] = names[0]
        elif not names:
            mapping[key] = None
            if key not in ("review", "blocked"):
                missing.append(key)
        else:
            mapping[key] = None
            ambiguous[key] = names
    return {"mapping": mapping, "ambiguous": ambiguous, "missing": missing,
            "team": (doc.get("result", doc) or {}).get("team", {})}


def missing_labels(doc: dict, crew_keys: list[str]) -> list[str]:
    result = doc.get("result", doc)
    names = {l.get("name", "").lower() for l in (result.get("labels", []) if isinstance(result, dict) else [])}
    return [f"crew:{k}" for k in crew_keys if f"crew:{k}" not in names]


def crew_table() -> str:
    doc = sc.load_crew()
    root = sc.repo_root(None)
    user_cfg, errors = sc.load_user_config()
    local_cfg, local_errors = sc.load_local_config(root)
    crew = sc.effective_crew(doc, None if errors else user_cfg, None if local_errors else local_cfg)
    available = set(doc.get("available", crew.keys()))
    rows = ["| Tripulante | Papel | Release | CLI padrão | Modelo padrão | Efetivo |",
            "|---|---|---|---|---|---|"]
    for key, m in crew.items():
        d = m.get("default", {})
        where = {"user": "config do usuário", "local": "config local do repositório"}.get(m["source"], "")
        eff = f"{m['cli']} · {m['model']} ({where})" if m["overridden"] else "= padrão"
        rel = m.get("release", "?") + ("" if key in available else " (ainda não instalado)")
        model = "padrão do CLI" if d.get("model") == "cli-default" else d.get("model")
        rows.append(f"| {m.get('emoji', '')} {m['name']} | {m.get('role', '')} | {rel} | {d.get('cli')} | {model} | {eff} |")
    if errors:
        rows.append("\nConfig do usuário INVÁLIDO (não aplicado): " + "; ".join(errors))
    if local_errors:
        rows.append("\nConfig local do repositório INVÁLIDO (não aplicado): " + "; ".join(local_errors))
    return "\n".join(rows)


# --- model suggestion (/starcode:config) -----------------------------------------------------

CLIS = ("claude", "codex", "antigravity", "opencode")
CLI_BINARIES = {"claude": "claude", "codex": "codex", "antigravity": "agy", "opencode": "opencode"}
CLI_FAMILIES = {"claude": "anthropic", "codex": "openai", "antigravity": "google"}
Q_ORDER = ("codex", "antigravity", "opencode")  # same order as dispatch.q_cli
TIER_RANK = {"grátis": 0, "$": 1, "$$": 2, "$$$": 3}


def clis_found(which=shutil.which) -> dict[str, bool]:
    return {cli: bool(which(CLI_BINARIES[cli])) for cli in CLIS}


def parse_model_arg(item: str) -> tuple[str, str, str | None] | None:
    """`<cli>=<id>[@<tier>]` -> (cli, id, tier or None); None when malformed."""
    cli, sep, rest = item.partition("=")
    model, _, tier = rest.rpartition("@") if "@" in rest else (rest, "", "")
    tier = {"gratis": "grátis"}.get(tier.strip(), tier.strip()) or None
    if not sep or cli not in CLIS or not model.strip() or (tier is not None and tier not in TIER_RANK):
        return None
    return cli, model.strip(), tier


def model_tier(model: str, tiers: dict, declared: str | None = None) -> str:
    """Tier of a model: given by the user, else crew.yaml costTiers, else the cached models.dev catalog,
    else 'grátis' for :free, else '?'."""
    if declared:
        return declared
    if model in tiers:
        return tiers[model]
    try:
        import model_info  # noqa: PLC0415

        cached = model_info.cached_tier(model)
    except Exception:  # noqa: BLE001
        cached = None
    return cached or sc.cost_tier(model, tiers)


def _candidates(doc: dict, have: list[str], extra: dict[str, list]) -> list[tuple[str, str, str]]:
    """(cli, model, tier) the user can run: crew.yaml models of the CLI family plus the --model ones.
    A CLI with no known model offers its own default (tier '?')."""
    tiers = doc.get("costTiers", {})
    out: list[tuple[str, str, str]] = []
    for cli in have:
        known = [m for m, fam in doc.get("families", {}).items() if fam == CLI_FAMILIES.get(cli)]
        given = [(m, None) if isinstance(m, str) else tuple(m) for m in extra.get(cli, [])]
        given_ids = {m for m, _ in given}
        models = [(m, None) for m in known if m not in given_ids] + given
        if not models:
            out.append((cli, "cli-default", "?"))
        out += [(cli, m, model_tier(m, tiers, t)) for m, t in models]
    return out


def _pick(cands: list[tuple[str, str, str]], want: str) -> tuple[str, str, str] | None:
    """Same tier first, else the nearest known tier (a tie goes to the stronger one), else an unknown one."""
    known = [c for c in cands if c[2] in TIER_RANK]
    if known and want in TIER_RANK:
        target = TIER_RANK[want]
        return min(known, key=lambda c: (abs(TIER_RANK[c[2]] - target), -TIER_RANK[c[2]]))
    if known:
        return known[0]
    return cands[0] if cands else None


def _family(cli: str, model: str, doc: dict) -> str:
    """Same rule the dispatch uses to pick the Q (crew.yaml families, openrouter/<vendor>/..., prefixes)."""
    import dispatch  # noqa: PLC0415  (heavy import, only for suggest)

    return dispatch.family(f"{cli}:{model}")


def suggest(doc: dict, have: list[str], extra: dict[str, list[str]] | None = None) -> dict:
    """Model per crew member using only the CLIs in `have`. A member whose default CLI is available keeps
    its default; the others get the candidate nearest to the cost tier of their default model. Q gets
    another family than the LaForge (like dispatch.q_cli); with none, it stays degraded (self-verified)."""
    extra = extra or {}
    have = [c for c in CLIS if c in have]
    if not have:
        return {"rows": [], "config": {"schemaVersion": 1}, "notes": ["nenhum CLI informado: nada a sugerir"]}
    tiers = doc.get("costTiers", {})
    crew = doc.get("crew", {})
    cands = _candidates(doc, have, extra)
    chosen: dict[str, tuple[str, str]] = {}
    overrides: dict[str, dict] = {}
    notes: list[str] = [f"--model {cli}=... ignorado: {cli} não está entre os CLIs informados"
                        for cli in extra if cli not in have]
    for key, m in crew.items():
        if key == "q":
            continue
        d = m.get("default", {})
        want = model_tier(d.get("model", ""), tiers)
        if d.get("cli") in have:
            chosen[key] = (d["cli"], d["model"])
            continue
        pick = _pick(cands, want)
        chosen[key] = (pick[0], pick[1])
        overrides[key] = {"cli": pick[0], "model": pick[1]}
        if pick[2] != want:
            notes.append(f"{m['name']}: pedia a faixa {want}; o mais próximo disponível é {pick[2]} ({pick[1]})")
    if "q" in crew:
        qd = crew["q"].get("default", {})
        lf_fam = _family(*chosen.get("laforge", ("claude", "")), doc)
        q_pick = None
        if qd.get("cli") in have and _family(qd["cli"], qd.get("model", ""), doc) not in (lf_fam, "unknown"):
            q_pick = (qd["cli"], qd.get("model"), "")  # the default already verifies in another family
        for cli in Q_ORDER if q_pick is None else ():
            if cli not in have:
                continue
            q_cands = [c for c in cands if c[0] == cli and _family(c[0], c[1], doc) not in (lf_fam, "unknown")]
            if not q_cands and CLI_FAMILIES.get(cli, lf_fam) != lf_fam:
                q_cands = [(cli, "cli-default", "?")]
            if q_cands:
                q_pick = _pick(q_cands, "$$")
                break
        if q_pick is None:
            chosen["q"] = ("—", "self-verified (degradado)")
            notes.append("Q sem CLI de outra família: a verificação fica degradada (self-verified). Codex, "
                         "Antigravity ou um modelo de outra família no OpenCode resolvem.")
        else:
            chosen["q"] = (q_pick[0], q_pick[1])
            if (q_pick[0], q_pick[1]) != (qd.get("cli"), qd.get("model")):
                overrides["q"] = {"cli": q_pick[0], "model": q_pick[1]}
    given_tier = {(c, m): t for c, m, t in cands}
    rows = []
    for key, m in crew.items():
        cli, model = chosen[key]
        rows.append({"member": key, "name": m["name"], "emoji": m.get("emoji", ""), "role": m.get("role", ""),
                     "cli": cli, "model": model,
                     "tier": "—" if cli == "—" else model_tier(model or "", tiers, given_tier.get((cli, model))),
                     "changed": key in overrides})
    cfg: dict = {"schemaVersion": 1}
    if overrides:
        cfg["crew"] = overrides
    return {"rows": rows, "config": cfg, "notes": notes}


def render_suggestion(res: dict) -> str:
    out = ["| Tripulante | Papel | CLI | Modelo | Faixa | |", "|---|---|---|---|---|---|"]
    for r in res["rows"]:
        model = "padrão do CLI" if r["model"] == "cli-default" else r["model"]
        out.append(f"| {r['emoji']} {r['name']} | {r['role']} | {r['cli']} | {model} | {r['tier']} | "
                   f"{'alterado' if r['changed'] else '= padrão'} |")
    if res["notes"]:
        out.append("")
        out += [f"- {n}" for n in res["notes"]]
    out += ["", "Config proposto:", json.dumps(res["config"], ensure_ascii=False, indent=2)]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    sc.utf8_stdio()
    parser = argparse.ArgumentParser(description="Ajudantes determinísticos do /starcode:setup.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("map-states")
    sub.add_parser("missing-labels")
    sub.add_parser("crew-table")
    sub.add_parser("clis")
    sg = sub.add_parser("suggest")
    sg.add_argument("--have", required=True, help="CLIs que o usuário tem, separados por vírgula")
    sg.add_argument("--model", action="append", default=[], help="<cli>=<modelo> confirmado pelo usuário")
    sg.add_argument("--json", action="store_true")
    rc = sub.add_parser("repo-config")
    rc.add_argument("--workspace", required=True)
    rc.add_argument("--team", required=True)
    rc.add_argument("--base-branch", required=True)
    rc.add_argument("--states-json", required=True, type=Path,
                    help='JSON {"unstarted":..,"started":..,"review":..,"completed":..,"blocked":..}')
    rc.add_argument("--stack", default="")
    rc.add_argument("--sensitive", default="")
    args = parser.parse_args(argv)

    if args.cmd in ("map-states", "missing-labels"):
        try:
            doc = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            print(f"ERRO: JSON inválido na entrada ({exc.msg})")
            return 2
        if args.cmd == "map-states":
            print(json.dumps(map_states(doc), ensure_ascii=False, indent=2))
        else:
            crew_keys = list(sc.load_crew().get("crew", {}).keys())
            missing = missing_labels(doc, crew_keys)
            print(json.dumps({"missing": missing}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "crew-table":
        print(crew_table())
        return 0
    if args.cmd == "clis":
        for cli, ok in clis_found().items():
            print(f"{cli} ({CLI_BINARIES[cli]}): {'encontrado' if ok else 'não encontrado'}")
        return 0
    if args.cmd == "suggest":
        have = [c.strip() for c in args.have.split(",") if c.strip()]
        bad = [c for c in have if c not in CLIS]
        extra: dict[str, list] = {}
        for item in args.model:
            parsed = parse_model_arg(item)
            if parsed is None:
                bad.append(item)
                continue
            extra.setdefault(parsed[0], []).append((parsed[1], parsed[2]))
        if bad:
            print(f"ERRO: valor inválido: {', '.join(bad)} (CLIs: {', '.join(CLIS)}; "
                  "--model <cli>=<modelo>[@grátis|$|$$|$$$])")
            return 2
        res = suggest(sc.load_crew(), have, extra)
        print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else render_suggestion(res))
        return 0
    states = json.loads(args.states_json.read_text(encoding="utf-8"))
    cfg: dict = {
        "schemaVersion": 1,
        "linear": {
            "workspace": args.workspace,
            "team": args.team,
            "states": {k: states.get(k) for k in ("unstarted", "started", "review", "completed", "blocked")}
                      | {"verifiedAt": date.today().isoformat()},
        },
        "baseBranch": args.base_branch,
    }
    if args.stack:
        cfg["stack"] = [s.strip() for s in args.stack.split(",") if s.strip()]
    if args.sensitive:
        cfg["sensitiveFiles"] = [s.strip() for s in args.sensitive.split(",") if s.strip()]
    print(json.dumps(cfg, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
