"""StarCode PreToolUse hook: blocks dangerous Git commands and enforces the session's Git mode (D11, D12).

Always blocked (any repo): push --force/-f/--force-with-lease/+refspec/--mirror, remote branch
deletion (push --delete / :branch), reset --hard, branch -D (or --delete --force), clean -f
(without --dry-run), checkout/restore of the whole tree (". :/ *").

When StarCode is active in the worktree (a Git mode was recorded or .starcode/config.json exists):
  mode 1: no commit, merge, push or PR       mode 2: no push or PR
  modes 3/4: push and PR allowed (the skill still confirms right before)
  any mode: merge into the base branch, push to the base branch and `gh pr merge` need the user's
  separate authorization, recorded with `git_mode.py authorize-merge <branch>`.

Output: PreToolUse JSON deny on stdout, exit 0 (never exit 2; see DECISIONS F0-5).
`--agy`: Antigravity format ({"decision": "deny"}), input in toolCall.args.CommandLine; repo dir from
toolCall.args.Cwd, payload cwd or the first workspacePaths entry (Phase 5, SC-57).
Known limit: commands built at runtime (variables, eval, aliases, scripts) are not seen.
"""
from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import starcode_common as sc  # noqa: E402

SEPARATORS = {"&&", "||", ";", "|", "&", "|&", ";;", "(", ")"}
WRAPPERS = {"sudo", "command", "env", "time", "nohup", "exec", "xargs"}
SHELLS = {"bash", "sh", "zsh", "dash", "pwsh", "powershell", "cmd"}
WHOLE_TREE = {".", "./", ":/", ":(top)", "*", "./*"}
HINT = "Se o usuário pediu isso de forma explícita, peça que ele mesmo rode o comando no terminal."


def _base(token: str) -> str:
    name = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name[:-4] if name.endswith(".exe") else name


def tokenize(command: str) -> list[list[str]]:
    """Split a shell command line into simple commands (token lists)."""
    segments: list[list[str]] = []
    for line in command.splitlines() or [command]:
        lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        try:
            tokens = list(lexer)
        except ValueError:  # unbalanced quotes: fall back to a plain split
            tokens = line.replace("&&", " && ").replace(";", " ; ").replace("|", " | ").split()
        current: list[str] = []
        for tok in tokens:
            if tok in SEPARATORS or (tok and set(tok) <= set("&|;()")):
                if current:
                    segments.append(current)
                current = []
            else:
                current.append(tok)
        if current:
            segments.append(current)
    return segments


def _short_flags(args: list[str]) -> set[str]:
    flags: set[str] = set()
    for a in args:
        if a.startswith("-") and not a.startswith("--") and len(a) > 1:
            flags.update(a[1:])
    return flags


def _positionals(args: list[str], takes_value: set[str] = frozenset()) -> list[str]:
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        if a == "--":
            continue
        if a.startswith("-"):
            if a in takes_value:
                skip = True
            continue
        out.append(a)
    return out


class Guard:
    def __init__(self, cwd: str | None):
        self.cwd = cwd or os.getcwd()

    # --- context ---------------------------------------------------------------------------
    def _ctx(self, cwd: str) -> dict:
        root = sc.repo_root(cwd)
        mode = sc.git_mode(cwd) if root else None
        active = root is not None and (mode is not None or sc.repo_config_path(root).exists())
        return {"root": root, "mode": mode, "active": active,
                "bases": sc.base_branches(root) if active else set()}

    # --- entry -----------------------------------------------------------------------------
    def evaluate(self, command: str, depth: int = 0) -> str | None:
        cwd = self.cwd
        for seg in tokenize(command):
            i = 0
            while i < len(seg) and ("=" in seg[i] and not seg[i].startswith("-")
                                    and seg[i].split("=", 1)[0].isidentifier()):
                i += 1  # leading VAR=value assignments
            while i < len(seg) and _base(seg[i]) in WRAPPERS:
                i += 1
            if i >= len(seg):
                continue
            prog, args = _base(seg[i]), seg[i + 1:]
            if prog == "cd" and args:
                target = Path(args[0]).expanduser()
                cwd = str(target if target.is_absolute() else Path(cwd) / target)
                continue
            if prog in SHELLS and depth < 3:
                for flag in ("-c", "-Command", "-command", "/c", "/C"):
                    if flag in args and args.index(flag) + 1 < len(args):
                        inner = " ".join(args[args.index(flag) + 1:])
                        reason = Guard(cwd).evaluate(inner, depth + 1)
                        if reason:
                            return reason
                continue
            if prog == "git":
                reason = self._git(args, cwd)
            elif prog == "gh":
                reason = self._gh(args, cwd)
            else:
                reason = None
            if reason:
                return reason
        return None

    # --- git -------------------------------------------------------------------------------
    def _git(self, args: list[str], cwd: str) -> str | None:
        i = 0
        while i < len(args) and args[i].startswith("-"):
            opt = args[i]
            if opt == "-C" and i + 1 < len(args):
                target = Path(args[i + 1]).expanduser()
                cwd = str(target if target.is_absolute() else Path(cwd) / target)
                i += 2
                continue
            if opt in ("-c", "--git-dir", "--work-tree", "--namespace") and i + 1 < len(args):
                i += 2
                continue
            i += 1
        if i >= len(args):
            return None
        sub, rest = args[i], args[i + 1:]
        handler = getattr(self, f"_git_{sub.replace('-', '_')}", None)
        return handler(rest, cwd) if handler else None

    def _git_push(self, args: list[str], cwd: str) -> str | None:
        shorts = _short_flags(args)
        longs = {a.split("=", 1)[0] for a in args if a.startswith("--")}
        pos = _positionals(args, {"-o", "--push-option", "--repo", "--receive-pack", "--exec"})
        refspecs = pos[1:]
        if "f" in shorts or longs & {"--force", "--force-with-lease", "--force-if-includes", "--mirror"} \
                or any(r.startswith("+") for r in refspecs):
            return ("StarCode bloqueou `git push` forçado (--force, -f, --force-with-lease, +refspec ou "
                    "--mirror). Reescrever o histórico remoto é proibido no fluxo. " + HINT)
        if "d" in shorts or "--delete" in longs or "--prune" in longs or any(r.startswith(":") for r in refspecs):
            return ("StarCode bloqueou a exclusão de branch remota (push --delete, --prune ou :branch). "
                    "Exclusão de branch pede aprovação do usuário. " + HINT)
        ctx = self._ctx(cwd)
        if not ctx["active"]:
            return None
        mode = ctx["mode"]
        if mode is not None and mode < 3:
            return (f"StarCode bloqueou `git push`: o modo Git deste worktree é {mode} "
                    f"({sc.MODES[mode]}). Push só nos modos 3 e 4. Para trocar o modo, rode "
                    "/starcode:engajar e escolha outro.")
        targets = set()
        for r in refspecs:
            dst = r.split(":", 1)[-1]
            targets.add(dst.removeprefix("refs/heads/"))
        if not refspecs:
            branch = sc.current_branch(cwd)
            if branch:
                targets.add(branch)
        for base in sorted(targets & ctx["bases"]):
            if not sc.merge_authorized(cwd, base):
                return (f"StarCode bloqueou o push direto no ramo base `{base}`. Entregas vão por PR; "
                        "push no ramo base pede autorização separada do usuário, registrada com "
                        f"`git_mode.py authorize-merge {base}`.")
        return None

    def _git_reset(self, args: list[str], cwd: str) -> str | None:
        if "--hard" in args:
            return ("StarCode bloqueou `git reset --hard`: descarta trabalho sem volta. Use `git stash` "
                    "ou um commit, ou peça ao usuário. " + HINT)
        return None

    def _git_branch(self, args: list[str], cwd: str) -> str | None:
        shorts = {a for a in args if a.startswith("-") and not a.startswith("--")}
        flags = _short_flags(args)
        longs = set(a for a in args if a.startswith("--"))
        if "-D" in shorts or "D" in flags or (("d" in flags or "--delete" in longs) and
                                              ("f" in flags or "--force" in longs)):
            return ("StarCode bloqueou `git branch -D` (exclusão forçada de branch). Exclusão de branch "
                    "pede aprovação do usuário. " + HINT)
        return None

    def _git_clean(self, args: list[str], cwd: str) -> str | None:
        flags = _short_flags(args)
        if "n" in flags or "--dry-run" in args:
            return None
        if "f" in flags or "--force" in args:
            return ("StarCode bloqueou `git clean -f`: apaga arquivos não versionados sem volta. "
                    "Rode `git clean -n` para listar e peça ao usuário. " + HINT)
        return None

    def _git_checkout(self, args: list[str], cwd: str) -> str | None:
        paths = args[args.index("--") + 1:] if "--" in args else [a for a in args if not a.startswith("-")]
        if any(p in WHOLE_TREE for p in paths):
            return ("StarCode bloqueou `git checkout -- .`: descarta todas as mudanças locais. "
                    "Use `git stash` ou peça ao usuário. " + HINT)
        return None

    def _git_restore(self, args: list[str], cwd: str) -> str | None:
        if ("--staged" in args or "-S" in args) and not ("--worktree" in args or "-W" in args):
            return None
        paths = [a for a in args if not a.startswith("-")]
        if any(p in WHOLE_TREE for p in paths):
            return ("StarCode bloqueou `git restore .`: descarta todas as mudanças locais. "
                    "Use `git stash` ou peça ao usuário. " + HINT)
        return None

    def _git_commit(self, args: list[str], cwd: str) -> str | None:
        ctx = self._ctx(cwd)
        if ctx["active"] and ctx["mode"] == 1:
            return ("StarCode bloqueou `git commit`: o modo Git deste worktree é 1 (somente código "
                    "local). Para commitar, rode /starcode:engajar e escolha o modo 2, 3 ou 4.")
        return None

    def _git_merge(self, args: list[str], cwd: str) -> str | None:
        if any(a in ("--abort", "--quit", "--continue") for a in args):
            return None
        ctx = self._ctx(cwd)
        if not ctx["active"]:
            return None
        if ctx["mode"] == 1:
            return ("StarCode bloqueou `git merge`: o modo Git deste worktree é 1 (somente código "
                    "local, sem commits).")
        branch = sc.current_branch(cwd)
        if branch in ctx["bases"] and not sc.merge_authorized(cwd, branch):
            return (f"StarCode bloqueou o merge no ramo base `{branch}`. Merge no ramo base pede "
                    "autorização separada do usuário, registrada com "
                    f"`git_mode.py authorize-merge {branch}`. Merge de ticket no ramo de integração "
                    "da feature não precisa disso.")
        return None

    # --- gh --------------------------------------------------------------------------------
    def _gh(self, args: list[str], cwd: str) -> str | None:
        if len(args) < 2 or args[0] != "pr":
            return None
        ctx = self._ctx(cwd)
        if not ctx["active"]:
            return None
        action = args[1]
        if action == "create" and ctx["mode"] is not None and ctx["mode"] < 3:
            return (f"StarCode bloqueou `gh pr create`: o modo Git deste worktree é {ctx['mode']}. "
                    "PR só nos modos 3 e 4.")
        if action == "merge" and not any(sc.merge_authorized(cwd, b) for b in ctx["bases"]):
            return ("StarCode bloqueou `gh pr merge`: merge no ramo base pede autorização separada do "
                    "usuário, registrada com `git_mode.py authorize-merge <ramo base>`.")
        return None


def deny_json(reason: str, agy: bool) -> str:
    if agy:
        return json.dumps({"decision": "deny", "reason": reason}, ensure_ascii=False)
    return json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False)


def extract(payload: dict, agy: bool) -> tuple[str | None, str | None]:
    if agy:
        args = (payload.get("toolCall") or {}).get("args") or {}
        command = args.get("CommandLine") if isinstance(args, dict) else None
        cwd = (args.get("Cwd") if isinstance(args, dict) else None) or payload.get("cwd")
        if not cwd:
            # agy 1.5.2 não manda Cwd: o repositório vem em workspacePaths e o processo do hook roda
            # na pasta do plugin (SC-57; tests/fixtures/agy-pretooluse-commit.json).
            paths = payload.get("workspacePaths")
            if isinstance(paths, list):
                cwd = next((p for p in paths if isinstance(p, str) and p), None)
    else:
        tool_input = payload.get("tool_input") or {}
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        cwd = payload.get("cwd")
    return (command if isinstance(command, str) else None), cwd


def warn(detail: str) -> None:
    """Fail-open: avisa em stderr (uma linha) e deixa o comando passar."""
    line = " ".join(str(detail).split())[:300]
    sys.stderr.write(f"StarCode hook: git_guard não avaliou o comando ({line}); o comando segue sem "
                     "verificação.\n")


def main() -> int:
    sc.utf8_stdio()
    agy = "--agy" in sys.argv[1:]
    try:
        payload = json.load(sys.stdin)
        command, cwd = extract(payload if isinstance(payload, dict) else {}, agy)
        if not command:
            return 0
        reason = Guard(cwd).evaluate(command)
    except Exception as exc:  # noqa: BLE001
        warn(f"{type(exc).__name__}: {exc}")
        return 0
    if reason:
        sys.stdout.write(deny_json(reason, agy))
    return 0


if __name__ == "__main__":
    sys.exit(main())
