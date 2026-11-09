#!/usr/bin/env python3
"""Diagnóstico do harness de um repo (R26-R28, R35). Só stdlib.

  diagnostico.py run [--root <repo>] [--date YYYY-MM-DD]

Roda `npx --yes harness-score@<versão fixada> --json <repo>` (pontuação de maturidade) e o Track A
do harness-eval (`scripts/harness/`, quebrados determinísticos) e escreve
`<repo>/docs/diagnostico/<data>.md`. Tracks B/C (juízes LLM, custam tokens) não rodam aqui.

Saída: 0 ok (inclusive harness-score ausente/falho: o relatório diz `não executado - <motivo>`);
2 Track A falhou (`track A falhou: <motivo>`).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

HARNESS_SCORE_VERSION = "1.8.4"  # lida do registro npm em 2026-11-09
NPX_TIMEOUT_S = 120
HARNESS_DIR = Path(__file__).resolve().parent / "harness"


def _npx_timeout() -> float:
    raw = os.environ.get("STARCODE_DIAGNOSTICO_NPX_TIMEOUT")
    try:
        return float(raw) if raw else float(NPX_TIMEOUT_S)
    except ValueError:
        return float(NPX_TIMEOUT_S)


def run_harness_score(repo: Path) -> tuple[dict | None, str]:
    """Devolve (json, "") ou (None, motivo)."""
    npx = shutil.which("npx")
    if not npx:
        return None, "npx não encontrado"
    timeout = _npx_timeout()
    cmd = [npx, "--yes", f"harness-score@{HARNESS_SCORE_VERSION}", "--json", str(repo)]
    try:
        res = subprocess.run(cmd, capture_output=True, stdin=subprocess.DEVNULL,
                             timeout=timeout, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return None, f"timeout após {timeout:g}s"
    except OSError as exc:
        return None, f"npx não executou ({exc})"
    if res.returncode != 0:
        return None, f"npx saiu com código {res.returncode}"
    try:
        data = json.loads(res.stdout)
        level = data["level"]
        int(level["index"])
        str(level["name"])
        data["score"]["earned"], data["score"]["max"]
        list(data["dimensions"])
    except (ValueError, KeyError, TypeError):
        return None, "JSON inválido na saída do harness-score"
    return data, ""


def run_track_a(repo: Path, run_id: str) -> tuple[list[dict] | None, str]:
    for script in ("inventory_extract.py", "track_a_correctness.py"):
        cmd = [sys.executable, "-I", str(HARNESS_DIR / script), "--root", str(repo), "--run-id", run_id]
        res = subprocess.run(cmd, capture_output=True, stdin=subprocess.DEVNULL,
                             encoding="utf-8", errors="replace")
        if res.returncode != 0:
            detail = (res.stderr or res.stdout).strip().splitlines()
            return None, f"{script} saiu com código {res.returncode}" + (f": {detail[-1]}" if detail else "")
    out = repo / ".harness-eval" / "runs" / run_id / "04-correctness.json"
    try:
        findings = json.loads(out.read_text(encoding="utf-8"))
        if not isinstance(findings, list):
            raise ValueError("não é lista")
    except (OSError, ValueError) as exc:
        return None, f"04-correctness.json ilegível ({exc})"
    return findings, ""


def render(date: str, score: dict | None, reason: str, findings: list[dict] | None, track_a_reason: str) -> str:
    lines = [f"# Diagnóstico do harness — {date}", ""]
    if score is None:
        lines += [f"**Level**: não executado - {reason}", ""]
    else:
        lvl, sc = score["level"], score["score"]
        lines += [f"**Level**: L{int(lvl['index'])} · {lvl['name']}",
                  f"**Score**: {sc['earned']}/{sc['max']}", "",
                  "| Dimensão | % |", "|---|---|"]
        for d in score["dimensions"]:
            if d.get("applicable", True):
                lines.append(f"| {d.get('title') or d.get('id')} | {d.get('percent')}% |")
        gaps = lvl.get("nextLevelGaps") or []
        lines.append("")
        if gaps:
            lines.append(f"Próximo degrau: To reach L{int(lvl['index']) + 1}: {'; '.join(gaps)}")
        else:
            lines.append("Próximo degrau: nenhum (nível máximo ou sem lacunas listadas)")
        lines.append("")
    if findings is None:
        lines += [f"**Track A**: falhou - {track_a_reason}", ""]
    else:
        broken = [f for f in findings if f.get("severity") == "BROKEN"]
        groups = Counter(str(f.get("source", "?")) for f in broken)
        lines += [f"**Track A**: {len(broken)} quebrados"]
        if groups:
            lines.append("")
            lines += [f"- `{src}`: {n}" for src, n in sorted(groups.items(), key=lambda kv: (-kv[1], kv[0]))[:5]]
        lines.append("")
    lines += ["**Tracks B/C**: não executados (sem aprovação de custo)", ""]
    return "\n".join(lines)


def gitignore_has_harness_eval(repo: Path) -> bool:
    try:
        text = (repo / ".gitignore").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(ln.strip() in (".harness-eval/", ".harness-eval", "/.harness-eval/", "/.harness-eval")
               for ln in text.splitlines())


def cmd_run(args: argparse.Namespace) -> int:
    repo = Path(args.root).resolve()
    date = args.date or _dt.date.today().isoformat()
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            raise ValueError(date)
        _dt.date.fromisoformat(date)
    except ValueError:
        print("data inválida: use YYYY-MM-DD", file=sys.stderr)
        return 2
    if not repo.is_dir():
        print(f"repo não encontrado: {repo}", file=sys.stderr)
        return 2
    if not gitignore_has_harness_eval(repo):
        print(f"aviso: .harness-eval/ não está no .gitignore de {repo}")
    score, reason = run_harness_score(repo)
    findings, ta_reason = run_track_a(repo, f"{date}-diag")
    out = repo / "docs" / "diagnostico" / f"{date}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(date, score, reason, findings, ta_reason), encoding="utf-8", newline="\n")
    print(f"diagnóstico escrito em {out}")
    if findings is None:
        print(f"track A falhou: {ta_reason}", file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="roda harness-score + Track A e escreve o relatório")
    run.add_argument("--root", default=".")
    run.add_argument("--date", default=None)
    run.set_defaults(func=cmd_run)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
