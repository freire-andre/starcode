"""Fake secrets are assembled at runtime so this file never contains a literal token
(it would trip the StarCode hook itself and GitHub push protection)."""
import json
import subprocess
import sys
import unittest

from helpers import FIXTURES, ROOT, TempRepoCase, run_git

import secret_scan as ss

HOOK = ROOT / "hooks" / "scripts" / "secret_scan.py"

FAKE = {
    "github": "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
    "aws": "AK" + "IA" + "Q3EGRZ7XW2PL5N4M",
    "anthropic": "sk-" + "ant-" + "api03-" + "Zx9Yw8Vu7Ts6Rq5Po4Nm3Lk2Ji1Hg0FeDcBa",
    "openai": "sk-" + "proj-" + "Zx9Yw8Vu7Ts6Rq5Po4Nm3Lk2Ji1Hg0FeDcBa99",
    "linear": "lin" + "_api_" + "Zx9Yw8Vu7Ts6Rq5Po4Nm3Lk2Ji1Hg0FeDcBa",
    "pem": "-----BEGIN " + "RSA PRIVATE KEY-----",
    "dsn": "postgres" + "ql://app:" + "S3cr3tPassw0rd" + "@db.internal:5432/app",
    "assignment": "API_" + "KEY=" + "q8Zr2Lm9Xv4Tn7Wp1Ks6Yd3",
}

LOOKALIKES = [
    "token = os.environ['GITHUB_TOKEN']",
    "API_KEY=${API_KEY}",
    "PASSWORD=changeme",
    "SECRET_KEY=your-secret-key-here",
    "url = 'postgresql://localhost:5432/app'",
    "see https://user@example.com/docs",
    "sk-short",
    "AKIA is the AWS access key prefix",
    "hash: 3f786850e387550fdab836ed7e6dc881de23001b",
    "def test_token_parser(): assert parse('abc')",
    "ACCESS_TOKEN_TTL=3600",
]


class ScanTextTests(unittest.TestCase):
    def setUp(self):
        self.allow = ss.Allowlist(None)

    def test_each_fake_secret_is_found(self):
        for kind, value in FAKE.items():
            with self.subTest(kind=kind):
                self.assertTrue(ss.scan_text(f"value: {value}", self.allow), kind)

    def test_lookalikes_pass(self):
        for text in LOOKALIKES:
            with self.subTest(text=text):
                self.assertEqual(ss.scan_text(text, self.allow), [], text)

    def test_secret_is_masked(self):
        findings = ss.scan_text(FAKE["github"], self.allow)
        self.assertNotIn(FAKE["github"], findings[0][2])

    def test_anthropic_key_reported_once(self):
        self.assertEqual(len(ss.scan_text(FAKE["anthropic"], self.allow)), 1)


class CommitTests(TempRepoCase):
    def stage(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        run_git(self.repo, "add", name)

    def test_staged_secret_blocks_commit(self):
        self.stage("app/config.py", f"TOKEN = '{FAKE['github']}'\n")
        findings = ss.evaluate("git commit -m 'add config'", str(self.repo))
        self.assertEqual(len(findings), 1)
        self.assertIn("app/config.py:1", findings[0])
        self.assertIn("token do GitHub", findings[0])

    def test_secret_after_2mb_of_staged_diff_is_found(self):  # Q: segredo depois de 2 MB
        secret = "gh" + "p_" + "".join(chr(65 + i % 26) + str(i % 10) for i in range(20))
        self.stage("big.txt", ("x" * 99 + "\n") * 20_100 + f"TOKEN = '{secret}'\n")
        self.assertGreater((self.repo / "big.txt").stat().st_size, 2_000_000)
        findings = ss.evaluate("git commit -m safe", str(self.repo))
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("token do GitHub", findings[0])

    def test_diff_over_hard_limit_denies_instead_of_skipping(self):
        self.stage("big.txt", ("x" * 99 + "\n") * 2_000)
        old = ss.MAX_DIFF_BYTES
        ss.MAX_DIFF_BYTES = 10_000
        try:
            findings = ss.evaluate("git commit -m safe", str(self.repo))
        finally:
            ss.MAX_DIFF_BYTES = old
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("grande demais para verificar", findings[0])
        self.assertIn("big.txt", findings[0])

    def test_clean_commit_passes(self):
        self.stage("app/main.py", "print('hello')\nAPI_KEY = os.environ['API_KEY']\n")
        self.assertEqual(ss.evaluate("git commit -m 'feat: hello'", str(self.repo)), [])

    def test_env_file_blocks(self):
        self.stage(".env", "DEBUG=1\n")
        self.assertIn(".env", ss.evaluate("git commit -m x", str(self.repo))[0])

    def test_env_example_passes(self):
        self.stage(".env.example", "API_KEY=\n")
        self.assertEqual(ss.evaluate("git commit -m x", str(self.repo)), [])

    def test_lockfile_ignored(self):
        self.stage("package-lock.json", f'{{"integrity": "{FAKE["aws"]}"}}\n')
        self.assertEqual(ss.evaluate("git commit -m x", str(self.repo)), [])

    def test_commit_all_scans_unstaged_tracked_changes(self):
        (self.repo / "README.md").write_text(f"key {FAKE['aws']}\n", encoding="utf-8")
        self.assertEqual(ss.evaluate("git commit -m x", str(self.repo)), [])
        self.assertTrue(ss.evaluate("git commit -am x", str(self.repo)))

    def test_removed_lines_are_not_scanned(self):
        self.stage("old.txt", f"{FAKE['aws']}\n")
        run_git(self.repo, "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "legacy")
        (self.repo / "old.txt").write_text("clean\n", encoding="utf-8")
        run_git(self.repo, "add", "old.txt")
        self.assertEqual(ss.evaluate("git commit -m 'remove key'", str(self.repo)), [])

    def test_allowlist_path_and_hash(self):
        self.stage("tests/fixtures/keys.txt", f"{FAKE['aws']}\n")
        self.stage("docs/example.md", f"{FAKE['github']}\n")
        allow = self.repo / ".starcode" / "secret-allowlist"
        allow.parent.mkdir(parents=True)
        allow.write_text(f"path:tests/fixtures/*\nsha256:{ss.sha(FAKE['github'])}\n", encoding="utf-8")
        self.assertEqual(ss.evaluate("git commit -m x", str(self.repo)), [])

    def test_secret_in_commit_message(self):
        self.assertTrue(ss.evaluate(f"git commit -m 'oops {FAKE['linear']}'", str(self.repo)))


class AddAntesDoCommitTests(TempRepoCase):
    def write(self, name, text, base=None):
        path = (base or self.repo) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit_all(self, *names):
        run_git(self.repo, "add", *names)
        run_git(self.repo, "commit", "-q", "-m", "base")

    def segredo(self):
        return f"TOKEN = '{FAKE['github']}'\n"

    def achado(self, caminho):
        return f"{caminho}:1: token do GitHub ({ss.mask(FAKE['github'])})"

    def test_add_antes_do_commit_escaneia_novo_e_modificado(self):
        self.write("README.md", self.segredo())
        self.write("app/novo.py", self.segredo())
        for cmd in ("git add -A && git commit -m x", "git add . ; git commit -m x",
                    "git add --all || git commit -m x", "git add . | git commit -m x",
                    "git add .\ngit commit -m x"):
            with self.subTest(cmd=cmd):
                findings = ss.evaluate(cmd, str(self.repo))
                self.assertEqual(findings, [self.achado("README.md"), self.achado("app/novo.py")])
        semhead = self.tmp / "semhead"
        semhead.mkdir()
        run_git(semhead, "init", "-q", "-b", "main")
        self.write("README.md", self.segredo(), semhead)
        self.write("app/novo.py", self.segredo(), semhead)
        findings = ss.evaluate("git add -A && git commit -m x", str(semhead))
        self.assertEqual(findings, [self.achado("README.md"), self.achado("app/novo.py")])

    def test_add_antes_do_commit_sem_segredo_passa(self):
        self.write("README.md", "hello mudado\n")
        self.write("app/novo.py", "print('ok')\n")
        self.assertEqual(ss.evaluate("git add -A && git commit -m x", str(self.repo)), [])

    def test_add_update_ignora_nao_rastreados(self):
        self.write("novo.py", self.segredo())
        self.assertEqual(ss.evaluate("git add -u && git commit -m x", str(self.repo)), [])
        self.assertEqual(ss.evaluate("git add --update && git commit -m x", str(self.repo)), [])
        self.write("README.md", self.segredo())
        findings = ss.evaluate("git add -u && git commit -m x", str(self.repo))
        self.assertEqual(findings, [self.achado("README.md")])

    def test_add_so_escaneia_caminhos_passados(self):
        self.write("a.py", "a = 1\n")
        self.write("b.py", "b = 1\n")
        self.commit_all("a.py", "b.py")
        self.write("a.py", "a = 2\n")
        self.write("b.py", self.segredo())
        self.write("c.py", self.segredo())
        self.assertEqual(ss.evaluate("git add a.py && git commit -m x", str(self.repo)), [])
        findings = ss.evaluate("git add a.py c.py && git commit -m x", str(self.repo))
        self.assertEqual(findings, [self.achado("c.py")])

    def test_add_arquivo_novo_env_e_allowlist(self):
        self.write(".env", "DEBUG=1\n")
        self.assertEqual(ss.evaluate("git add -A && git commit -m x", str(self.repo)),
                         [".env: arquivo .env no commit (variáveis de ambiente não vão para o Git)"])
        (self.repo / ".env").unlink()
        self.write("docs/chave.txt", self.segredo())
        self.write("package-lock.json", f'{{"i": "{FAKE["aws"]}"}}\n')
        self.assertEqual(len(ss.evaluate("git add -A && git commit -m x", str(self.repo))), 1)
        self.write(".starcode/secret-allowlist", "path:docs/*\n")
        self.assertEqual(ss.evaluate("git add docs && git commit -m x", str(self.repo)), [])

    def test_add_com_dash_c(self):
        sub = self.tmp / "pai" / "sub"
        sub.mkdir(parents=True)
        run_git(sub, "init", "-q", "-b", "main")
        self.write("novo.py", self.segredo(), sub)
        findings = ss.evaluate("git -C sub add -A; git -C sub commit -m x", str(self.tmp / "pai"))
        self.assertEqual(findings, [self.achado("novo.py")])

    def test_add_arquivo_novo_grande_nega(self):
        self.write("grande.txt", ("x" * 99 + "\n") * 2_000)
        tamanho = len((self.repo / "grande.txt").read_text(encoding="utf-8"))
        old = ss.MAX_DIFF_BYTES
        ss.MAX_DIFF_BYTES = 10_000
        try:
            findings = ss.evaluate("git add -A && git commit -m x", str(self.repo))
        finally:
            ss.MAX_DIFF_BYTES = old
        self.assertEqual(findings, [
            f"grande.txt: arquivo grande demais para verificar ({tamanho} caracteres; limite 10000). "
            "Divida o commit ou aprove o arquivo em .starcode/secret-allowlist (path:<glob>)."])

    def test_secret_scan_nega_commit_pelo_powershell(self):
        self.write("app/novo.py", self.segredo())
        outs = {}
        for tool in ("Bash", "PowerShell"):
            payload = {"tool_name": tool, "tool_input": {"command": "git add -A; git commit -m x"},
                       "cwd": str(self.repo)}
            res = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True,
                                 text=True, encoding="utf-8")
            self.assertEqual(res.returncode, 0)
            outs[tool] = json.loads(res.stdout)["hookSpecificOutput"]
        self.assertEqual(outs["PowerShell"]["permissionDecision"], "deny")
        self.assertEqual(outs["PowerShell"]["permissionDecisionReason"], outs["Bash"]["permissionDecisionReason"])
        self.assertIn("app/novo.py:1:", outs["PowerShell"]["permissionDecisionReason"])

    def test_decisions_guardas_add_commit_powershell(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = text.split("### SC-178:", 1)[1].split("\n### ", 1)[0]
        for campo in ("**Problema**", "**Decisão**", "**Motivo**", "**Por que não é bug**"):
            self.assertIn(campo, entry)
        for nome in ("git add", "PowerShell", "Bash|PowerShell"):
            self.assertIn(nome, entry)


class TextTargetsTests(TempRepoCase):
    def test_orca_linear_comment(self):
        cmd = f"orca linear comment add SC-8 --body 'deploy key {FAKE['anthropic']}'"
        self.assertTrue(ss.evaluate(cmd, str(self.repo)))

    def test_orca_linear_body_file(self):
        (self.repo / "body.md").write_text(f"conn {FAKE['dsn']}\n", encoding="utf-8")
        self.assertTrue(ss.evaluate("orca linear create --team SC --title t --body-file body.md", str(self.repo)))

    def test_gh_pr_body(self):
        self.assertTrue(ss.evaluate(f"gh pr create --title t --body '{FAKE['openai']}'", str(self.repo)))

    def test_normal_flow_commands_pass(self):
        for cmd in ("orca linear comment add SC-8 --body 'Gates verdes; commit abc1234'",
                    "orca linear status set SC-8 --state 'In Progress'",
                    "gh pr create --title 'feat: x' --body 'Refs: SC-8'",
                    "git status", "ls -la"):
            with self.subTest(cmd=cmd):
                self.assertEqual(ss.evaluate(cmd, str(self.repo)), [])


class HookProtocolTests(TempRepoCase):
    def test_deny_json_exit_0_and_no_secret_echo(self):
        payload = {"tool_input": {"command": f"gh pr create --body '{FAKE['github']}'"}, "cwd": str(self.repo)}
        res = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True,
                             text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertNotIn(FAKE["github"], res.stdout)

    def test_secret_commit_denied_codex_and_antigravity_payloads(self):
        path = self.repo / "app" / "config.py"
        path.parent.mkdir()
        path.write_text(f"TOKEN = '{FAKE['github']}'\n", encoding="utf-8")
        run_git(self.repo, "add", "app/config.py")
        cwd = str(self.repo)
        cases = [
            ("codex", [], {"tool_input": {"command": "git commit -m 'add config'"}, "cwd": cwd}),
            ("antigravity", ["--agy"],
             {"toolCall": {"args": {"CommandLine": "git commit -m 'add config'", "Cwd": cwd}}}),
        ]
        for name, args, payload in cases:
            with self.subTest(cli=name):
                res = subprocess.run([sys.executable, str(HOOK), *args], input=json.dumps(payload),
                                     capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(res.returncode, 0)
                out = json.loads(res.stdout)
                decision = out["decision"] if args else out["hookSpecificOutput"]["permissionDecision"]
                self.assertEqual(decision, "deny")
                self.assertNotIn(FAKE["github"], res.stdout)

    def test_agy_real_commit_payload_denies_staged_secret(self):
        # Payload real do agy 1.5.2 (sem Cwd/cwd; o repositório vem em workspacePaths) e o hook
        # rodando fora do repositório, na pasta do plugin, como na sessão real (SC-57).
        payload = json.loads((FIXTURES / "agy-pretooluse-commit.json").read_text(encoding="utf-8"))
        payload["workspacePaths"] = [str(self.repo).replace("\\", "/")]
        path = self.repo / "app" / "config.py"
        path.parent.mkdir()
        path.write_text(f"TOKEN = '{FAKE['github']}'\n", encoding="utf-8")
        run_git(self.repo, "add", "app/config.py")
        outside = self.tmp / "plugin"
        outside.mkdir()
        res = subprocess.run([sys.executable, str(HOOK), "--agy"], input=json.dumps(payload), cwd=outside,
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(json.loads(res.stdout or "{}").get("decision"), "deny", res.stderr)
        self.assertNotIn(FAKE["github"], res.stdout)

    def test_hash_helper(self):
        res = subprocess.run([sys.executable, str(HOOK), "--hash", "abc"], capture_output=True, text=True)
        self.assertEqual(res.stdout.strip(), "sha256:" + ss.sha("abc"))


if __name__ == "__main__":
    unittest.main()
