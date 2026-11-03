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
"""
from __future__ import annotations

import argparse
import json
import re
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
    user_cfg, errors = sc.load_user_config()
    crew = sc.effective_crew(doc, user_cfg)
    available = set(doc.get("available", crew.keys()))
    rows = ["| Tripulante | Papel | Release | CLI padrão | Modelo padrão | Efetivo (config do usuário) |",
            "|---|---|---|---|---|---|"]
    for key, m in crew.items():
        d = m.get("default", {})
        eff = f"{m['cli']} · {m['model']}" if m["overridden"] else "= padrão"
        rel = m.get("release", "?") + ("" if key in available else " (ainda não instalado)")
        model = "padrão do CLI" if d.get("model") == "cli-default" else d.get("model")
        rows.append(f"| {m.get('emoji', '')} {m['name']} | {m.get('role', '')} | {rel} | {d.get('cli')} | {model} | {eff} |")
    if errors:
        rows.append("\nConfig do usuário INVÁLIDO (não aplicado): " + "; ".join(errors))
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    sc.utf8_stdio()
    parser = argparse.ArgumentParser(description="Ajudantes determinísticos do /starcode:setup.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("map-states")
    sub.add_parser("missing-labels")
    sub.add_parser("crew-table")
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
