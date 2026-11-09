#!/usr/bin/env python3
# Origem: adaptado de the-judge/scripts/post_review.py (the-judge 1.4.0, Felipe Rodrigues,
# licença CC-BY-4.0). Mudanças: formato review.json do StarCode, recusa por gate e por rodada
# já publicada, fallback COMMENT no próprio PR, códigos de saída 0/2/3, só stdlib.
"""Publica o review do Worf no PR (R14-R16). Só stdlib.

  post_review.py <review.json> --pr <N> --review-md <review.md>

Saídas: 0 publicado; 2 `gh` falhou (review.md intacto); 3 recusado (gate falhou ou rodada já publicada).
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
INLINE = ("blocker", "should-fix", "nit")
EMOJI = {"blocker": "🔴", "should-fix": "🟠", "nit": "🟡", "pre-existing": "🟣"}


def gh(*args: str) -> str:
    exe = shutil.which("gh")
    if not exe:
        raise RuntimeError("gh indisponível: não encontrado no PATH")
    try:
        res = subprocess.run([exe, *args], capture_output=True, text=True, encoding="utf-8",
                             stdin=subprocess.DEVNULL)
    except OSError as e:
        raise RuntimeError(f"gh indisponível: {e}")
    if res.returncode != 0:
        raise RuntimeError((res.stderr or res.stdout).strip() or f"exit {res.returncode}")
    return res.stdout.strip()


def is_inline(f: dict) -> bool:
    return (f.get("severity") in INLINE and f.get("hardening") is not True
            and bool(f.get("path")) and isinstance(f.get("line"), int))


def build_payload(data: dict, event: str, intended: str | None) -> dict:
    findings = [f for f in data.get("findings", [])
                if isinstance(f, dict) and f.get("state") != "rejected"]
    comments, only_body = [], []
    for f in findings:
        emoji = EMOJI.get(f.get("severity"), "")
        if is_inline(f):
            text = f.get("body", "")
            lead = "" if emoji and str(text).lstrip().startswith(emoji) else f"{emoji} "
            comments.append({"path": f["path"], "line": f["line"], "side": "RIGHT",
                             "body": f"{lead}**{f.get('severity')}** ({f.get('id', '?')}): {text}"})
        else:
            where = f"{f.get('path')}:{f.get('line')}" if f.get("path") else "geral"
            tag = "hardening" if f.get("hardening") is True else f.get("severity")
            only_body.append(f"- {emoji} {tag} ({f.get('id', '?')}, {where}): {f.get('body', '')}")
    body = str(data.get("summary", ""))
    if only_body:
        body += "\n\n" + "\n".join(only_body)
    if intended:
        body += f"\n\nVeredito pretendido: {intended} (o GitHub não aceita {intended} no próprio PR)"
    return {"body": body, "event": event, "comments": comments}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="post_review.py")
    ap.add_argument("review_json")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--review-md", required=True)
    args = ap.parse_args(argv[1:])

    gate = subprocess.run([sys.executable, "-I", str(HERE / "review_gate.py"), args.review_json],
                          capture_output=True, text=True, encoding="utf-8")
    if gate.returncode != 0:
        print("recusado: review_gate falhou")
        if gate.stdout.strip():
            print(gate.stdout.strip())
        return 3
    data = json.loads(Path(args.review_json).read_text(encoding="utf-8"))
    rnd = data.get("round", 1)
    md_path = Path(args.review_md)
    md = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    m = re.search(r"^\*\*Round\*\*:\s*(\d+)", md, re.M)
    md_round = int(m.group(1)) if m else rnd
    if re.search(r"^\*\*Posted\*\*:", md, re.M) and md_round == rnd:
        print(f"recusado: rodada {rnd} já publicada")
        return 3

    try:
        author = json.loads(gh("pr", "view", args.pr, "--json", "author")).get("author", {}).get("login")
        me = gh("api", "user", "--jq", ".login")
        verdict = data["verdict"]
        own = bool(author) and author == me
        payload = build_payload(data, "COMMENT" if own else verdict, verdict if own else None)
        fd, tmp = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False)
            out = gh("api", f"repos/{{owner}}/{{repo}}/pulls/{args.pr}/reviews", "--method", "POST",
                     "--input", tmp)
        finally:
            os.unlink(tmp)
        url = json.loads(out).get("html_url", "")
    except (RuntimeError, ValueError) as e:
        print(f"gh falhou: {e}")
        return 2

    with open(md_path, "a", encoding="utf-8", newline="") as fh:
        if md and not md.endswith("\n"):
            fh.write("\n")
        fh.write(f"**Posted**: {datetime.date.today().isoformat()} - {url}\n")
    print(url)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
