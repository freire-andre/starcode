"""StarCode PreToolUse hook: secret scanner (D12, plan section 8).

Targets:
  - `git commit`: the staged diff (`git diff --cached`; with -a/--all, `git diff HEAD`), added lines
    only, plus staged .env* files.
  - `orca linear comment add/edit | create | save-issue`, `gh pr create/edit/comment/review` and
    `gh issue create/comment/edit`: the command text
    and any --body-file / --description-file / -F file it points to.
Detection: provider token patterns (AWS, GitHub, Linear, OpenAI, Anthropic, Slack, Google), PEM
private keys, connection strings with a password, and high-entropy values in KEY=... assignments.
Allowlist: .starcode/secret-allowlist, one entry per line:
    path:<glob>        ignore files matching the glob (repo-relative, forward slashes)
    sha256:<hex>       ignore one approved false positive (hash of the matched text)
Binary files and lockfiles are ignored. The matched secret is never echoed back (masked).
Known limits: obfuscated or split secrets are not detected; this is not a CI scanner replacement.

Output: PreToolUse JSON deny, exit 0 (DECISIONS F0-5). `--agy`: Antigravity format.
`python secret_scan.py --hash TEXT` prints the sha256 entry for the allowlist.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))
sys.path.insert(0, str(HERE))

import starcode_common as sc  # noqa: E402
from git_guard import _base, extract, tokenize  # noqa: E402

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("chave privada PEM", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("token do GitHub", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b")),
    ("chave da API do Linear", re.compile(r"\blin_(?:api|oauth)_[A-Za-z0-9]{32,}\b")),
    ("chave da Anthropic", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{32,}\b")),
    ("chave da OpenAI", re.compile(r"\bsk-(?!ant-)(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{32,}\b")),
    ("token do Slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("chave do Google", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("string de conexão com senha",
     re.compile(r"\b[a-z][a-z0-9+.-]{1,20}://[^\s:/@'\"]{1,64}:([^\s@/'\"]{3,128})@([^\s/'\"]+)", re.I)),
]
ASSIGNMENT = re.compile(
    r"""(?ix)\b([A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PASSWD|PWD|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|(?<![A-Z0-9])O?AUTH(?![A-Z0-9]))[A-Z0-9_]*)
        \s*[:=]\s*["']?([^\s"'#,;]{16,})""")
PLACEHOLDER = re.compile(r"(?i)^(x+|\*+|<.*>|\$\{.*\}|\$[A-Z_]+|changeme|example|placeholder|your[_-].*|dummy.*|test.*|fake.*|redacted.*)$")
CONN_PLACEHOLDER = re.compile(r"^(?:\$\{.*\}|\$[A-Za-z_]\w*|<.*>)$")
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
URL_VALUE = re.compile(r"(?i)^https?://")
URL_CREDENTIALS = re.compile(r"(?i)^https?://[^/\s@]*@")
LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "uv.lock",
             "Cargo.lock", "Pipfile.lock", "composer.lock", "Gemfile.lock", "bun.lockb", "go.sum"}
BODY_FILE_FLAGS = {"--body-file", "--description-file", "-F", "--file"}
MAX_DIFF_BYTES = 64_000_000  # staged diff per file: above this the hook denies (never skips silently)


def entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = {c: s.count(c) for c in set(s)}
    return -sum(n / len(s) * math.log2(n / len(s)) for n in counts.values())


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def mask(text: str) -> str:
    return text[:4] + "…" + f"({len(text)} caracteres)" if len(text) > 8 else "…"


class Allowlist:
    def __init__(self, root: Path | None):
        self.paths: list[str] = []
        self.hashes: set[str] = set()
        if root is None:
            return
        f = root / ".starcode" / "secret-allowlist"
        if not f.exists():
            return
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("path:"):
                self.paths.append(line[5:].strip())
            elif line.startswith("sha256:"):
                self.hashes.add(line[7:].strip().lower())

    def path_ok(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, g) for g in self.paths)

    def match_ok(self, matched: str) -> bool:
        return sha(matched) in self.hashes


def _benign_connection(m: re.Match) -> bool:
    """R3: senha placeholder (`${...}`, `$NOME`, `<...>`) ou host local não é segredo."""
    if CONN_PLACEHOLDER.match(m.group(1)):
        return True
    host = m.group(2).lower()
    host = host[1:host.index("]")] if host.startswith("[") and "]" in host else host.split(":")[0]
    return host in LOCAL_HOSTS or m.group(2).lower().startswith("::1")


def scan_text(text: str, allow: Allowlist) -> list[tuple[int, str, str]]:
    """Return (line_number, kind, masked) for each finding in text."""
    findings = []
    for n, line in enumerate(text.splitlines(), 1):
        hit = False
        for kind, rx in PATTERNS:
            for m in rx.finditer(line):
                if allow.match_ok(m.group(0)):
                    continue
                if rx.groups and _benign_connection(m):
                    continue
                findings.append((n, kind, mask(m.group(0))))
                hit = True
        if hit:
            continue
        for m in ASSIGNMENT.finditer(line):
            value = m.group(2)
            if URL_VALUE.match(value) and not URL_CREDENTIALS.match(value):
                continue  # R5: URL sem usuário:senha@
            if PLACEHOLDER.match(value) or allow.match_ok(value) or allow.match_ok(m.group(0)):
                continue
            if entropy(value) >= 3.5 and re.search(r"\d", value) and re.search(r"[A-Za-z]", value):
                findings.append((n, f"valor de alta entropia em {m.group(1)}", mask(value)))
    return findings


BINARY_DIFF = re.compile(r"^Binary files .* differ$", re.M)  # R5: só o cabeçalho do git, não a frase em texto


def _skipped(path: str, reason: str) -> None:
    sys.stderr.write(f"StarCode hook: secret_scan pulou {path} ({reason})\n")


def _is_binary(data: str) -> bool:
    return "\x00" in data  # R5: o diff inteiro, não só os primeiros 8000 caracteres


def _env_finding(path: str, name: str) -> str | None:
    if re.fullmatch(r"\.env(\..+)?", name) and not name.endswith((".example", ".sample", ".template")):
        return f"{path}: arquivo {name} no commit (variáveis de ambiente não vão para o Git)"
    return None


def staged_findings(cwd: str, all_tracked: bool, allow: Allowlist, pathspecs: list[str] | None = None,
                    list_cwd: str | None = None) -> list[str]:
    diff_args = ["diff", "HEAD"] if all_tracked else ["diff", "--cached"]
    spec = ["--", *pathspecs] if pathspecs else []
    where = list_cwd or cwd
    top = sc.repo_root(cwd) or cwd  # W3: os nomes vêm relativos à raiz; o diff por arquivo roda nela
    quote = ["-c", "core.quotepath=off"]  # W2: nome não ASCII sem aspas
    names = sc.git([*quote, *diff_args, "--name-only", "--diff-filter=ACMR", *spec], where)
    if names is None and all_tracked:  # no HEAD yet
        names = sc.git([*quote, "diff", "--cached", "--name-only", "--diff-filter=ACMR", *spec], where)
        diff_args = ["diff", "--cached"]
    out: list[str] = []
    for path in (names or "").splitlines():
        path = path.strip()
        if not path or allow.path_ok(path):
            continue
        name = path.rsplit("/", 1)[-1]
        if name in LOCKFILES:
            continue
        env = _env_finding(path, name)
        if env:
            out.append(env)
            continue
        try:
            res = subprocess.run(["git", *diff_args, "--unified=0", "--no-color", "--", path], cwd=top,
                                 capture_output=True, text=True, encoding="utf-8", errors="replace",
                                 timeout=sc.GIT_TIMEOUT)
        except (OSError, subprocess.SubprocessError) as exc:
            _skipped(path, type(exc).__name__)
            continue
        if res.returncode != 0:
            _skipped(path, f"git diff saiu com {res.returncode}")
            continue
        diff = res.stdout
        if len(diff) > MAX_DIFF_BYTES:
            out.append(f"{path}: diff grande demais para verificar ({len(diff)} caracteres; limite "
                       f"{MAX_DIFF_BYTES}). Divida o commit ou aprove o arquivo em .starcode/secret-allowlist "
                       "(path:<glob>).")
            continue
        if BINARY_DIFF.search(diff) or _is_binary(diff):
            continue
        new_line = 0
        for raw in diff.splitlines():
            m = re.match(r"^@@ -\S+ \+(\d+)", raw)
            if m:
                new_line = int(m.group(1))
                continue
            if raw.startswith("+") and not raw.startswith("+++"):
                for _, kind, masked in scan_text(raw[1:], allow):
                    out.append(f"{path}:{new_line}: {kind} ({masked})")
                new_line += 1
    return out


def untracked_findings(root: Path, pathspecs: list[str], allow: Allowlist, force: bool = False,
                       list_cwd: str | None = None) -> list[str]:
    """Arquivos novos (não rastreados, não ignorados; com `add -f`, também os ignorados) dentro dos pathspecs:
    o conteúdo inteiro é linha nova."""
    listing = sc.git(["-c", "core.quotepath=off", "ls-files", "--others", *([] if force else ["--exclude-standard"]),
                      "--full-name", *(["--", *pathspecs] if pathspecs else [])], list_cwd or str(root))
    out: list[str] = []
    for path in (listing or "").splitlines():
        path = path.strip()
        if not path or allow.path_ok(path):
            continue
        name = path.rsplit("/", 1)[-1]
        if name in LOCKFILES:
            continue
        env = _env_finding(path, name)
        if env:
            out.append(env)
            continue
        try:
            text = (root / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _is_binary(text):
            continue
        if len(text) > MAX_DIFF_BYTES:
            out.append(f"{path}: arquivo grande demais para verificar ({len(text)} caracteres; limite "
                       f"{MAX_DIFF_BYTES}). Divida o commit ou aprove o arquivo em .starcode/secret-allowlist "
                       "(path:<glob>).")
            continue
        for n, kind, masked in scan_text(text, allow):
            out.append(f"{path}:{n}: {kind} ({masked})")
    return out


def _git_call(args: list[str], cwd: str) -> tuple[str, list[str], str] | None:
    """(subcomando, argumentos dele, diretório do git) de um `git ...`, ou None sem subcomando."""
    j, git_cwd = 0, cwd
    while j < len(args) and args[j].startswith("-"):
        if args[j] == "-C" and j + 1 < len(args):
            git_cwd = str(Path(git_cwd) / args[j + 1])
        j += 2 if args[j] in ("-C", "-c") else 1
    if j >= len(args):
        return None
    return args[j], args[j + 1:], git_cwd


def parse_add(rest: list[str], git_cwd: str) -> dict:
    mode, paths, only_paths, force, from_file = "paths", [], False, False, False
    for a in rest:
        short = a.startswith("-") and not a.startswith("--")
        if only_paths:
            paths.append(a)
        elif a == "--":
            only_paths = True
        elif a in ("--all", "--update", "--force") or short:
            letters = a[1:] if short else ""  # W1: cada letra do grupo curto conta (`-Af`, `-fu`...)
            if a == "--all" or "A" in letters:
                mode = "all"
            if a == "--update" or "u" in letters:
                mode = "update"
            if a == "--force" or "f" in letters:
                force = True
        elif a == "--pathspec-from-file" or a.startswith("--pathspec-from-file="):
            from_file = True
        elif not a.startswith("-"):
            paths.append(a)
    if from_file:  # a lista de caminhos vem de um arquivo: trata como o repositório inteiro (mais rígido)
        paths = []
        if mode == "paths":
            mode = "all"
    return {"cwd": git_cwd, "mode": mode, "paths": paths, "force": force}


def add_findings(add: dict, allow_for: dict[str, Allowlist]) -> list[str]:
    """O que um `git add` anterior ao commit vai incluir e ainda não está no índice."""
    root = sc.repo_root(add["cwd"])
    if root is None:
        return []
    root = Path(root).resolve()
    allow = allow_for.setdefault(str(root), Allowlist(root))
    base = Path(add["cwd"]).resolve()
    pathspecs: list[str] = []
    for p in add["paths"]:
        if p.startswith(":"):  # pathspec mágico (`:/`, `:(top)`...): o git resolve a partir do cwd do comando
            pathspecs.append(p)
            continue
        try:
            rel = (base / p).resolve().relative_to(root).as_posix()
            pathspecs.append(":(top)" + ("" if rel == "." else rel))
        except ValueError:
            continue
    if add["paths"] and not pathspecs:
        return []
    if not add["paths"] and add["mode"] == "paths":
        return []
    # W3: sem caminho (`-A`, `--all`, `-u`) o add cobre o repositório inteiro, qualquer que seja o cwd
    where = add["cwd"] if pathspecs else str(root)
    out = staged_findings(str(root), True, allow, pathspecs or None, where)
    if add["mode"] != "update":
        out += untracked_findings(root, pathspecs, allow, add.get("force", False), where)
    return out


def text_findings(label: str, text: str, allow: Allowlist) -> list[str]:
    return [f"{label}, linha {n}: {kind} ({masked})" for n, kind, masked in scan_text(text, allow)]


def evaluate(command: str, cwd: str | None) -> list[str]:
    cwd = cwd or "."
    root = sc.repo_root(cwd)
    allow = Allowlist(root)
    allow_for: dict[str, Allowlist] = {}
    findings: list[str] = []
    adds: list[dict] = []
    publishes = False
    for seg in tokenize(command):
        while seg and "=" in seg[0] and seg[0].split("=", 1)[0].isidentifier():
            seg = seg[1:]
        if not seg:
            continue
        prog, args = _base(seg[0]), seg[1:]
        if prog == "git":
            call = _git_call(args, cwd)
            if call is None:
                continue
            sub, rest, git_cwd = call
            if sub in ("add", "stage"):  # `git stage` é sinônimo de `git add`
                adds.append(parse_add(rest, git_cwd))
            elif sub == "commit":
                all_tracked = "--all" in rest or any(
                    a.startswith("-") and not a.startswith("--") and "a" in a[1:] for a in rest)
                findings += staged_findings(git_cwd, all_tracked, allow)
                for add in adds:
                    findings += add_findings(add, allow_for)
                publishes = True
        elif prog == "orca" and len(args) >= 2 and args[0] == "linear" and (
                args[1] in ("create", "save-issue") or (args[1] == "comment" and len(args) > 2)):
            publishes = True
            findings += _body_files(args, cwd, allow)
        elif prog == "gh" and len(args) >= 2 and (
                (args[0] == "pr" and args[1] in ("create", "edit", "comment", "review"))
                or (args[0] == "issue" and args[1] in ("create", "comment", "edit"))):
            publishes = True
            findings += _body_files(args, cwd, allow)
    if publishes:  # R1: o texto inteiro do comando, inclusive o corpo de heredoc
        findings += text_findings("texto do comando", command, allow)
    return list(dict.fromkeys(findings))


def _body_files(args: list[str], cwd: str, allow: Allowlist) -> list[str]:
    out = []
    for i, a in enumerate(args):
        flag, _, inline = a.partition("=")
        if flag in BODY_FILE_FLAGS:
            value = inline or (args[i + 1] if i + 1 < len(args) else "")
            if not value or value == "-":
                continue
            p = Path(value)
            p = p if p.is_absolute() else Path(cwd) / p
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if len(text) > MAX_DIFF_BYTES:
                out.append(f"arquivo {value}: grande demais para verificar ({len(text)} caracteres)")
                continue
            out += text_findings(f"arquivo {value}", text, allow)
    return out


def main() -> int:
    sc.utf8_stdio()
    argv = sys.argv[1:]
    if argv[:1] == ["--hash"] and len(argv) == 2:
        print(f"sha256:{sha(argv[1])}")
        return 0
    agy = "--agy" in argv
    try:
        from git_guard import deny_json  # noqa: PLC0415

        payload = json.load(sys.stdin)
        command, cwd = extract(payload if isinstance(payload, dict) else {}, agy)
        if not command:
            return 0
        findings = evaluate(command, cwd)
    except Exception as exc:  # noqa: BLE001
        line = " ".join(f"{type(exc).__name__}: {exc}".split())[:300]
        sys.stderr.write(f"StarCode hook: secret_scan não avaliou o comando ({line}); o comando segue "
                         "sem verificação.\n")
        return 0
    if findings:
        shown = "\n".join(f"- {f}" for f in findings[:10])
        more = f"\n(+{len(findings) - 10} achados)" if len(findings) > 10 else ""
        reason = ("StarCode bloqueou o comando: possível segredo encontrado.\n" + shown + more +
                  "\nRemova o segredo (use variável de ambiente ou cofre). Se for falso positivo, o "
                  "usuário pode aprovar em .starcode/secret-allowlist (path:<glob> ou sha256:<hash>; "
                  "hash com `secret_scan.py --hash <texto>`).")
        sys.stdout.write(deny_json(reason, agy))
    return 0


if __name__ == "__main__":
    sys.exit(main())
