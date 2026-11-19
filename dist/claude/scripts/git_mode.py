"""Git mode of the current worktree (D11), read by the git_guard hook.

State lives in <git-dir>/starcode/session.json (per worktree, never committed). The Picard asks the
mode at every session and records the answer here; the hook enforces the last recorded mode.

Usage:
  python git_mode.py get                      -> prints the mode or "unset"
  python git_mode.py set N                    -> N in 1..4
  python git_mode.py authorize-merge BRANCH [--minutes M]
        Records the user's separate authorization to merge into / push to BRANCH (default 10 min).
        Call it only right after the user explicitly authorized that merge.
  python git_mode.py revoke-merge
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import starcode_common as sc  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    sc.utf8_stdio()
    parser = argparse.ArgumentParser(description="Modo Git do worktree atual (StarCode).")
    parser.add_argument("--cwd", default=".", help="diretório dentro do repositório")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("get")
    p_set = sub.add_parser("set")
    p_set.add_argument("mode", type=int, choices=sorted(sc.MODES))
    p_auth = sub.add_parser("authorize-merge")
    p_auth.add_argument("branch")
    p_auth.add_argument("--minutes", type=int, default=10, choices=range(1, 61), metavar="1-60")
    sub.add_parser("revoke-merge")
    args = parser.parse_args(argv)

    if sc.git_dir(args.cwd) is None:
        print("ERRO: não é um repositório Git.")
        return 2
    try:
        return _run(args)
    except TimeoutError as exc:
        print(f"trava ocupada: {exc} (tente de novo)", file=sys.stderr)
        return 2


def _run(args: argparse.Namespace) -> int:
    if args.cmd == "get":
        data = sc.read_session(args.cwd)
        mode = sc.git_mode(args.cwd)
        if mode is None:
            print("unset")
        else:
            print(f"{mode} ({sc.MODES[mode]}; definido em {data.get('setAt', '?')})")
        return 0
    if args.cmd == "set":
        def mutate(data: dict) -> None:
            data.update({"gitMode": args.mode, "setAt": sc.now_iso()})
            data.pop("mergeAuthorization", None)

        path = sc.update_session(args.cwd, mutate)
        print(f"OK: modo Git {args.mode} ({sc.MODES[args.mode]}) gravado em {path}")
        return 0
    if args.cmd == "authorize-merge":
        expires = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=args.minutes)

        def mutate(data: dict) -> None:
            data["mergeAuthorization"] = {"branch": args.branch, "expiresAt": expires.isoformat()}

        sc.update_session(args.cwd, mutate)
        print(f"OK: merge/push em {args.branch} autorizado até {expires.isoformat()}")
        return 0
    sc.update_session(args.cwd, lambda data: data.pop("mergeAuthorization", None))
    print("OK: autorização de merge revogada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
