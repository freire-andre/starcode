"""StarCode PreToolUse hook: secret scanner (D12, plan section 8).

Targets:
  - `git commit`: the staged diff (`git diff --cached`; with -a/--all, `git diff HEAD`), added lines
    only, plus staged .env* files.
  - `orca linear comment add/edit | create | save-issue` and `gh pr create/edit`: the command text
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
     re.compile(r"\b[a-z][a-z0-9+.-]{1,20}://[^\s:/@'\"]{1,64}:[^\s@/'\"]{3,128}@[^\s/'\"]+", re.I)),
]
ASSIGNMENT = re.compile(
    r"""(?ix)\b([A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PASSWD|PWD|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|AUTH)[A-Z0-9_]*)
        \s*[:=]\s*["']?([^\s"'#,;]{16,})""")
PLACEHOLDER = re.compile(r"(?i)^(x+|\*+|<.*>|\$\{.*\}|\$[A-Z_]+|changeme|example|placeholder|your[_-].*|dummy.*|test.*|fake.*|redacted.*)$")
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


def scan_text(text: str, allow: Allowlist) -> list[tuple[int, str, str]]:
    """Return (line_number, kind, masked) for each finding in text."""
    findings = []
    for n, line in enumerate(text.splitlines(), 1):
        hit = False
        for kind, rx in PATTERNS:
            for m in rx.finditer(line):
                if allow.match_ok(m.group(0)):
                    continue
                findings.append((n, kind, mask(m.group(0))))
                hit = True
        if hit:
            continue
        for m in ASSIGNMENT.finditer(line):
            value = m.group(2)
            if PLACEHOLDER.match(value) or allow.match_ok(value) or allow.match_ok(m.group(0)):
                continue
            if entropy(value) >= 3.5 and re.search(r"\d", value) and re.search(r"[A-Za-z]", value):
                findings.append((n, f"valor de alta entropia em {m.group(1)}", mask(value)))
    return findings


def _is_binary(data: str) -> bool:
    return "\x00" in data[:8000]


def staged_findings(cwd: str, all_tracked: bool, allow: Allowlist) -> list[str]:
    diff_args = ["diff", "HEAD"] if all_tracked else ["diff", "--cached"]
    names = sc.git([*diff_args, "--name-only", "--diff-filter=ACMR"], cwd)
    if names is None and all_tracked:  # no HEAD yet
        names = sc.git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd)
        diff_args = ["diff", "--cached"]
    out: list[str] = []
    for path in (names or "").splitlines():
        path = path.strip()
        if not path or allow.path_ok(path):
            continue
        name = path.rsplit("/", 1)[-1]
        if name in LOCKFILES:
            continue
        if re.fullmatch(r"\.env(\..+)?", name) and not name.endswith((".example", ".sample", ".template")):
            out.append(f"{path}: arquivo {name} no commit (variáveis de ambiente não vão para o Git)")
            continue
        try:
            res = subprocess.run(["git", *diff_args, "--unified=0", "--no-color", "--", path], cwd=cwd,
                                 capture_output=True, text=True, encoding="utf-8", errors="replace",
                                 timeout=sc.GIT_TIMEOUT)
        except (OSError, subprocess.SubprocessError):
            continue
        diff = res.stdout
        if len(diff) > MAX_DIFF_BYTES:
            out.append(f"{path}: diff grande demais para verificar ({len(diff)} caracteres; limite "
                       f"{MAX_DIFF_BYTES}). Divida o commit ou aprove o arquivo em .starcode/secret-allowlist "
                       "(path:<glob>).")
            continue
        if "Binary files" in diff or _is_binary(diff):
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


def text_findings(label: str, text: str, allow: Allowlist) -> list[str]:
    return [f"{label}, linha {n}: {kind} ({masked})" for n, kind, masked in scan_text(text, allow)]


def evaluate(command: str, cwd: str | None) -> list[str]:
    cwd = cwd or "."
    root = sc.repo_root(cwd)
    allow = Allowlist(root)
    findings: list[str] = []
    for seg in tokenize(command):
        while seg and "=" in seg[0] and seg[0].split("=", 1)[0].isidentifier():
            seg = seg[1:]
        if not seg:
            continue
        prog, args = _base(seg[0]), seg[1:]
        if prog == "git":
            j = 0
            while j < len(args) and args[j].startswith("-"):
                j += 2 if args[j] in ("-C", "-c") else 1
            if j < len(args) and args[j] == "commit":
                rest = args[j + 1:]
                all_tracked = "--all" in rest or any(
                    a.startswith("-") and not a.startswith("--") and "a" in a[1:] for a in rest)
                git_cwd = cwd
                if "-C" in args[:j]:
                    git_cwd = str(Path(cwd) / args[args.index("-C") + 1])
                findings += staged_findings(git_cwd, all_tracked, allow)
                findings += text_findings("mensagem do commit", " ".join(rest), allow)
        elif prog == "orca" and len(args) >= 2 and args[0] == "linear" and (
                args[1] in ("create", "save-issue") or (args[1] == "comment" and len(args) > 2)):
            findings += text_findings("comando orca linear", " ".join(args), allow)
            findings += _body_files(args, cwd, allow)
        elif prog == "gh" and len(args) >= 2 and args[0] == "pr" and args[1] in ("create", "edit", "comment"):
            findings += text_findings("comando gh pr", " ".join(args), allow)
            findings += _body_files(args, cwd, allow)
    return findings


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
