#!/usr/bin/env python3
# Origem: adaptado de tlc-spec-driven/scripts/lessons.py (tlc-spec-driven 4.1.0, Felipe Rodrigues,
# licença CC-BY-4.0). Mudanças: formato lessons.json do StarCode (schemaVersion 1, ids L<n>),
# sinal novo `review_finding`, limite de 300 caracteres, `penalize` leva confirmed direto a
# quarantined, `list --limit/--json`, mensagens em português e UTF-8 explícito.
"""Lições por repo (R22, R23). Só stdlib.

O LLM decide qual lição registrar; este script cuida do mecânico: ids, recorrência por
feature distinta, promoção candidate -> confirmed, quarentena, poda e a renderização.

  lessons.py [--root <repo>] init
  lessons.py [--root <repo>] add --feature <slug> --signal <s> --source <ref> --text "<frase>" [--scope <s>]
  lessons.py [--root <repo>] penalize --id L<n>
  lessons.py [--root <repo>] list [--status confirmed|candidate|quarantined|all] [--limit N] [--json]
  lessons.py [--root <repo>] prune
  lessons.py [--root <repo>] status

Estado: `.specs/lessons.json` (só o script escreve). Visão: `.specs/LESSONS.md` (refeita a cada escrita).
Saída: 0 ok, 2 entrada inválida ou `lessons.json` inválido (sem sobrescrever).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
import unicodedata
from pathlib import Path

SIGNALS = ("weak_test", "spec_precision_gap", "ac_gap", "spec_deviation", "gate_fail", "review_finding")
STATUSES = ("confirmed", "candidate", "quarantined")
MAX_TEXT = 300
PROMOTE_THRESHOLD = 2
WINDOW_DAYS = 45  # candidata que não recorreu nesse prazo é podada


class StoreError(Exception):
    pass


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _age_days(stamp: str) -> int:
    try:
        d = _dt.datetime.strptime(str(stamp)[:10], "%Y-%m-%d").replace(tzinfo=_dt.timezone.utc)
    except ValueError:
        return 0
    return (_dt.datetime.now(_dt.timezone.utc) - d).days


def _store_path(root: Path) -> Path:
    return root / ".specs" / "lessons.json"


def _render_path(root: Path) -> Path:
    return root / ".specs" / "LESSONS.md"


def _empty() -> dict:
    return {"schemaVersion": 1, "promote_threshold": PROMOTE_THRESHOLD, "lessons": []}


def _load(root: Path) -> dict:
    path = _store_path(root)
    if not path.exists():
        return _empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:  # UnicodeDecodeError é ValueError
        raise StoreError(f"não leu o JSON ({exc})")
    if not isinstance(data, dict) or not isinstance(data.get("lessons"), list):
        raise StoreError("falta a lista `lessons`")
    thr = data.setdefault("promote_threshold", PROMOTE_THRESHOLD)
    if not isinstance(thr, int) or isinstance(thr, bool) or thr < 1:
        raise StoreError("`promote_threshold` não é um inteiro positivo")
    data.setdefault("schemaVersion", 1)
    for i, les in enumerate(data["lessons"]):
        if not isinstance(les, dict):
            raise StoreError(f"lições[{i}] não é um objeto")
        for k in ("id", "text", "signal", "status"):
            if not isinstance(les.get(k), str):
                raise StoreError(f"lições[{i}] sem `{k}` válido")
        if les["status"] not in STATUSES:
            raise StoreError(f"{les['id']}: status `{les['status']}` desconhecido")
        for k in ("features", "sources"):
            if not isinstance(les.setdefault(k, []), list):
                raise StoreError(f"{les['id']}: `{k}` não é lista")
        les.setdefault("scope", "")
        les.setdefault("created", "")
        les.setdefault("updated", les["created"])
    return data


def _save(root: Path, data: dict) -> None:
    (root / ".specs").mkdir(parents=True, exist_ok=True)
    _store_path(root).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _render(root, data)


def _norm(text: str) -> str:
    """Chave de dedupe: sem acento, caixa e pontuação; espaços colapsados."""
    t = unicodedata.normalize("NFD", text.casefold())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = "".join(c if (c.isalnum() or c.isspace()) else " " for c in t)
    return re.sub(r"\s+", " ", t).strip()


def _num(les: dict) -> int:
    m = re.fullmatch(r"L(\d+)", les["id"])
    return int(m.group(1)) if m else 0


def _recent(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda x: (x.get("updated", ""), _num(x)), reverse=True)


def _prune(data: dict) -> list[str]:
    kept, dropped = [], []
    for les in data["lessons"]:
        if (les["status"] == "candidate" and len(les["features"]) < data["promote_threshold"]
                and _age_days(les.get("updated") or les.get("created", "")) > WINDOW_DAYS):
            dropped.append(les["id"])
        else:
            kept.append(les)
    data["lessons"] = kept
    return dropped


def _render(root: Path, data: dict) -> None:
    lines = ["# LESSONS - mantido por scripts/lessons.py", "",
             "> Gerado. Não edite à mão: o próximo `lessons.py` sobrescreve. O estado fica em `.specs/lessons.json`.",
             f"> promote_threshold={data['promote_threshold']} features distintas", ""]
    titles = {
        "confirmed": ("Confirmed", "Vistas em features distintas. Entram nos briefs."),
        "candidate": ("Candidates", "Vistas uma vez. Em observação, não entram nos briefs."),
        "quarantined": ("Quarantined", "Confirmadas que falharam ao serem aplicadas. Ignorar."),
    }
    for status in STATUSES:
        title, note = titles[status]
        lines += [f"## {title}", "", note, ""]
        items = [x for x in data["lessons"] if x["status"] == status]
        if not items:
            lines += ["_nenhuma_", ""]
            continue
        for les in sorted(items, key=_num):
            scope = f" · scope: `{les['scope']}`" if les.get("scope") else ""
            lines += [f"### {les['id']} - {les['text']}",
                      f"- signal: `{les['signal']}` · features: {len(les['features'])}{scope}",
                      f"- features: {', '.join(les['features']) or '-'}",
                      f"- sources: {', '.join(les['sources']) or '-'}",
                      f"- updated: {les.get('updated') or '-'}", ""]
    _render_path(root).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _invalid(field: str, reason: str) -> int:
    print(f"{field} inválido: {reason}", file=sys.stderr)
    return 2


def cmd_init(root: Path, args) -> int:
    data = _load(root)
    _save(root, data)
    print(f"store criado em {_store_path(root)}")
    return 0


def cmd_add(root: Path, args) -> int:
    signal = args.signal
    source = (args.source or "").strip()
    text = (args.text or "").strip()
    feature = (args.feature or "").strip()
    scope = (args.scope or "").strip()
    if signal not in SIGNALS:
        return _invalid("signal", f"`{signal}` fora da lista ({', '.join(SIGNALS)})")
    if not feature:
        return _invalid("feature", "vazio")
    if not source:
        return _invalid("source", "vazio; cite arquivo:linha, id do critério ou da checagem")
    if not text:
        return _invalid("text", "vazio")
    if len(text) > MAX_TEXT:
        return _invalid("text", f"{len(text)} caracteres, o limite é {MAX_TEXT}")

    data = _load(root)
    _prune(data)
    now = _now()
    key = _norm(text)
    found = next((x for x in data["lessons"] if _norm(x["text"]) == key), None)
    if found:
        if feature not in found["features"]:
            found["features"].append(feature)
        if source not in found["sources"]:
            found["sources"].append(source)
        found["updated"] = now
        promoted = (found["status"] == "candidate"
                    and len(found["features"]) >= data["promote_threshold"])
        if promoted:
            found["status"] = "confirmed"
        _save(root, data)
        print(f"atualizada {found['id']} (features={len(found['features'])}, status={found['status']})"
              + (" - promovida a confirmed" if promoted else ""))
        return 0
    lid = f"L{max([_num(x) for x in data['lessons']], default=0) + 1}"
    status = "confirmed" if data["promote_threshold"] <= 1 else "candidate"
    data["lessons"].append({"id": lid, "text": text, "signal": signal, "status": status,
                            "features": [feature], "sources": [source], "scope": scope,
                            "created": now, "updated": now})
    _save(root, data)
    print(f"adicionada {lid} (status={status})")
    return 0


def cmd_penalize(root: Path, args) -> int:
    data = _load(root)
    target = next((x for x in data["lessons"] if x["id"].lower() == args.id.lower()), None)
    if target is None:
        return _invalid("id", f"nenhuma lição {args.id}")
    if target["status"] != "confirmed":
        return _invalid("id", f"{target['id']} está `{target['status']}`; só confirmed vai para quarantined")
    target["status"] = "quarantined"
    target["updated"] = _now()
    _save(root, data)
    print(f"{target['id']} em quarantined")
    return 0


def cmd_list(root: Path, args) -> int:
    data = _load(root)
    rows = [x for x in data["lessons"] if args.status == "all" or x["status"] == args.status]
    rows = _recent(rows)
    if args.limit is not None:
        rows = rows[:max(args.limit, 0)]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    if not rows:
        print(f"(nenhuma lição {args.status})")
        return 0
    for les in rows:
        sc = f" [scope:{les['scope']}]" if les.get("scope") else ""
        print(f"{les['id']} ({les['status']}, x{len(les['features'])}){sc}: {les['text']}")
    return 0


def cmd_prune(root: Path, args) -> int:
    data = _load(root)
    dropped = _prune(data)
    _save(root, data)
    print(f"podadas {len(dropped)}: {', '.join(dropped) if dropped else '-'}")
    return 0


def cmd_status(root: Path, args) -> int:
    data = _load(root)
    counts = {s: sum(1 for x in data["lessons"] if x["status"] == s) for s in STATUSES}
    print(f"lessons: {len(data['lessons'])} total | " + " ".join(f"{s}={n}" for s, n in counts.items()))
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="lessons.py", description="Lições por repo (.specs/lessons.json).")
    p.add_argument("--root", default=".", help="pasta que contém .specs/ (padrão: atual)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(fn=cmd_init)
    sp = sub.add_parser("add")
    sp.add_argument("--feature", required=True)
    sp.add_argument("--signal", required=True)  # validado em cmd_add: sai com 2 e `signal inválido`
    sp.add_argument("--source", required=True)
    sp.add_argument("--text", required=True)
    sp.add_argument("--scope", default="")
    sp.set_defaults(fn=cmd_add)
    sp = sub.add_parser("penalize")
    sp.add_argument("--id", required=True)
    sp.set_defaults(fn=cmd_penalize)
    sp = sub.add_parser("list")
    sp.add_argument("--status", default="confirmed", choices=[*STATUSES, "all"])
    sp.add_argument("--limit", type=int, default=None)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_list)
    sub.add_parser("prune").set_defaults(fn=cmd_prune)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    for sp in sub.choices.values():
        sp.add_argument("--root", default=argparse.SUPPRESS, help="o mesmo que --root antes do subcomando")
    args = p.parse_args(argv)
    try:
        return args.fn(Path(args.root).resolve(), args)
    except StoreError as exc:
        print(f"lessons.json inválido: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
