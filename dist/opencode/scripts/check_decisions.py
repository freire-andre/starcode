"""D30 gate: DECISIONS.md must be updated at or after the last change to skills/, scripts/ or hooks/.

Compares commits, not dates: passes when the last commit touching the watched folders is an ancestor of
(or the same as) the last commit touching DECISIONS.md. Uncommitted changes in the watched folders
fail unless DECISIONS.md is also modified in the working tree.

Usage: python scripts/check_decisions.py [--repo DIR]
Exit: 0 ok, 1 DECISIONS.md out of date, 2 not a git repo / no DECISIONS.md / shallow or unconfirmed-complete clone.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

WATCHED = ("skills", "scripts", "hooks")
DECISIONS = "DECISIONS.md"


def git(repo: Path, *args: str) -> tuple[int, str]:
    res = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8",
                         stdin=subprocess.DEVNULL)
    return res.returncode, res.stdout.rstrip("\r\n")


def check(repo: Path) -> tuple[int, str]:
    code, _ = git(repo, "rev-parse", "--git-dir")
    if code != 0:
        return 2, "check_decisions: não é um repositório Git"
    if not (repo / DECISIONS).exists():
        return 2, f"check_decisions: {DECISIONS} não existe"
    code, shallow = git(repo, "rev-parse", "--is-shallow-repository")
    if code != 0 or shallow not in ("true", "false"):
        return 2, ("check_decisions: não foi possível confirmar que o clone é completo "
                   "(git rev-parse --is-shallow-repository)")
    if shallow == "true":
        return 2, ("check_decisions: repositório raso; o gate D30 precisa do histórico completo "
                   "(use fetch-depth: 0 no actions/checkout ou rode git fetch --unshallow)")
    _, dirty = git(repo, "status", "--porcelain", "--", *WATCHED, DECISIONS)
    dirty_paths = [line[3:] for line in dirty.splitlines()]
    dirty_watched = [p for p in dirty_paths if p.split("/", 1)[0] in WATCHED]
    if dirty_watched and DECISIONS not in dirty_paths:
        return 1, ("check_decisions: FALHOU. Mudanças não commitadas em " + ", ".join(dirty_watched[:5]) +
                   f" sem atualização do {DECISIONS}.")
    _, code_commit = git(repo, "log", "-1", "--format=%H", "--", *WATCHED)
    _, dec_commit = git(repo, "log", "-1", "--format=%H", "--", DECISIONS)
    if not code_commit:
        return 0, "check_decisions: OK (nenhuma mudança em skills/, scripts/ ou hooks/)"
    if not dec_commit:
        if DECISIONS in dirty_paths:
            return 0, f"check_decisions: OK ({DECISIONS} modificado na árvore de trabalho)"
        return 1, f"check_decisions: FALHOU. {DECISIONS} nunca foi commitado."
    if code_commit == dec_commit:
        return 0, f"check_decisions: OK ({DECISIONS} atualizado no mesmo commit {code_commit[:8]})"
    code, _ = git(repo, "merge-base", "--is-ancestor", code_commit, dec_commit)
    if code == 0:
        return 0, f"check_decisions: OK ({DECISIONS} em {dec_commit[:8]}, depois de {code_commit[:8]})"
    if DECISIONS in dirty_paths:
        return 0, f"check_decisions: OK ({DECISIONS} modificado na árvore de trabalho)"
    _, subject = git(repo, "log", "-1", "--format=%h %s", code_commit)
    return 1, (f"check_decisions: FALHOU. skills/, scripts/ ou hooks/ mudaram em {subject} depois da última "
               f"entrada do {DECISIONS}. Registre a decisão (problema → decisão → motivo → por que não é bug).")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Gate D30 do DECISIONS.md.")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    code, message = check(args.repo)
    print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
