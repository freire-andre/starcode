import json
import subprocess
import sys
import unittest

from helpers import ROOT, TempRepoCase, run_git

import starcode_common as sc
from git_guard import Guard, tokenize

HOOK = ROOT / "hooks" / "scripts" / "git_guard.py"

ALWAYS_BLOCKED = [
    "git push --force origin feature",
    "git push -f",
    "git push -uf origin feature",
    "git push --force-with-lease",
    "git push --force-with-lease=main:abc123 origin main",
    "git push origin +feature",
    "git push --mirror backup",
    "git push origin --delete feature",
    "git push -d origin feature",
    "git push origin :feature",
    "git push --prune origin",
    "git reset --hard",
    "git reset --hard HEAD~3",
    "git branch -D old",
    "git branch --delete --force old",
    "git branch -df old",
    "git clean -fd",
    "git clean -xdf",
    "git clean --force",
    "git checkout -- .",
    "git checkout .",
    "git restore .",
    "git restore --worktree --staged .",
    "git status && git reset --hard",
    "cd sub; git push -f",
    "git -C . reset --hard",
    "git -c core.pager=cat push --force",
    'bash -c "git push --force"',
    "FOO=1 git push -f",
    "sudo git clean -fdx",
]

ALWAYS_ALLOWED = [
    "git status",
    "git log --oneline --grep=force",
    "git diff HEAD~1",
    "git push origin feature",
    "git push -u origin feature",
    "git commit -m 'reset --hard explained'",
    "git branch -d merged-branch",
    "git branch -a",
    "git clean -n",
    "git clean -nd",
    "git checkout -- src/app.py",
    "git checkout -b feature/new",
    "git checkout main",
    "git reset --soft HEAD~1",
    "git reset HEAD file.txt",
    "git restore --staged .",
    "git restore src/app.py",
    "git stash",
    "git merge --abort",
    'echo "git push --force"',
    "grep -r 'reset --hard' docs/",
    "python -c \"print('git clean -fd')\"",
    "orca linear issue --current --json",
]


class TokenizeTests(unittest.TestCase):
    def test_splits_compound_commands(self):
        self.assertEqual(tokenize("git status && git push -f; echo ok | cat"),
                         [["git", "status"], ["git", "push", "-f"], ["echo", "ok"], ["cat"]])

    def test_quotes_stay_in_one_token(self):
        self.assertEqual(tokenize('echo "git push --force"'), [["echo", "git push --force"]])


class NoModeTests(TempRepoCase):
    def test_always_blocked(self):
        for cmd in ALWAYS_BLOCKED:
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(Guard(str(self.repo)).evaluate(cmd), cmd)

    def test_no_false_positive_without_starcode(self):
        for cmd in ALWAYS_ALLOWED:
            with self.subTest(cmd=cmd):
                self.assertIsNone(Guard(str(self.repo)).evaluate(cmd), cmd)

    def test_inactive_repo_allows_push_to_main(self):
        self.assertIsNone(Guard(str(self.repo)).evaluate("git push origin main"))


class ModeTests(TempRepoCase):
    def guard(self, cmd):
        return Guard(str(self.repo)).evaluate(cmd)

    def test_mode_1(self):
        self.set_mode(1)
        for cmd in ("git commit -m x", "git commit -am x", "git merge feature", "git push origin feature",
                    "gh pr create --fill"):
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(self.guard(cmd))
        for cmd in ("git add .", "git status", "git diff", "git stash"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.guard(cmd))

    def test_mode_2(self):
        self.set_mode(2)
        self.assertIsNone(self.guard("git commit -m x"))
        self.assertIn("modo Git deste worktree é 2", self.guard("git push origin feature"))
        self.assertIsNotNone(self.guard("gh pr create"))

    def test_mode_3_push_feature_ok_base_blocked(self):
        self.set_mode(3)
        run_git(self.repo, "checkout", "-q", "-b", "feature/x")
        self.assertIsNone(self.guard("git push -u origin feature/x"))
        self.assertIsNone(self.guard("git push"))
        self.assertIsNone(self.guard("gh pr create --fill"))
        self.assertIn("ramo base `main`", self.guard("git push origin HEAD:main"))
        self.assertIn("ramo base `main`", self.guard("git push origin main"))

    def test_mode_3_push_on_main_without_refspec_blocked(self):
        self.set_mode(3)
        self.assertIsNotNone(self.guard("git push"))

    def test_merge_into_base_needs_authorization(self):
        self.set_mode(4)
        reason = self.guard("git merge feature/x")
        self.assertIn("merge no ramo base `main`", reason)
        self.assertIsNotNone(self.guard("gh pr merge 12"))
        data = sc.read_session(self.repo)
        data["mergeAuthorization"] = {"branch": "main", "expiresAt": "2999-01-01T00:00:00+00:00"}
        sc.write_session(self.repo, data)
        self.assertIsNone(self.guard("git merge feature/x"))
        self.assertIsNone(self.guard("gh pr merge 12"))
        self.assertIsNone(self.guard("git push origin main"))

    def test_expired_authorization_blocks(self):
        self.set_mode(4)
        data = sc.read_session(self.repo)
        data["mergeAuthorization"] = {"branch": "main", "expiresAt": "2000-01-01T00:00:00+00:00"}
        sc.write_session(self.repo, data)
        self.assertIsNotNone(self.guard("git merge feature/x"))

    def test_merge_into_feature_branch_is_free(self):
        self.set_mode(2)
        run_git(self.repo, "checkout", "-q", "-b", "feature/slug")
        self.assertIsNone(self.guard("git merge ticket-1"))

    def test_base_branch_from_repo_config(self):
        self.write_repo_config(base="develop")
        self.set_mode(3)
        self.assertIsNotNone(self.guard("git push origin develop"))
        self.assertIsNone(self.guard("git push origin main"))

    def test_config_without_mode_still_protects_base(self):
        self.write_repo_config()
        self.assertIsNone(self.guard("git commit -m x"))
        self.assertIsNotNone(self.guard("git push origin main"))
        self.assertIsNone(self.guard("git push origin feature"))

    def test_mode_is_per_worktree(self):
        self.set_mode(1)
        wt = self.tmp / "wt"
        run_git(self.repo, "worktree", "add", "-q", "-b", "ticket", str(wt))
        self.assertIsNone(Guard(str(wt)).evaluate("git commit -m x"))
        self.assertIsNotNone(self.guard("git commit -m x"))


class HookProtocolTests(TempRepoCase):
    def run_hook(self, payload, *args):
        return subprocess.run([sys.executable, str(HOOK), *args], input=payload, capture_output=True,
                              text=True, encoding="utf-8")

    def test_deny_is_json_with_exit_0(self):
        res = self.run_hook(json.dumps({"tool_input": {"command": "git push -f"}, "cwd": str(self.repo)}))
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("StarCode bloqueou", out["permissionDecisionReason"])

    def test_allow_prints_nothing(self):
        res = self.run_hook(json.dumps({"tool_input": {"command": "git status"}, "cwd": str(self.repo)}))
        self.assertEqual((res.returncode, res.stdout), (0, ""))

    def test_malformed_payload_is_ignored(self):
        res = self.run_hook("not json")
        self.assertEqual((res.returncode, res.stdout), (0, ""))

    def test_antigravity_format(self):
        payload = {"toolCall": {"args": {"CommandLine": "git reset --hard"}}, "cwd": str(self.repo)}
        res = self.run_hook(json.dumps(payload), "--agy")
        self.assertEqual(json.loads(res.stdout)["decision"], "deny")

    # --- payloads por CLI (Codex no formato do Claude; Antigravity com toolCall.args) -------
    def payloads(self, command):
        cwd = str(self.repo)
        return [
            ("codex", [], {"tool_input": {"command": command}, "cwd": cwd}),
            ("antigravity", ["--agy"], {"toolCall": {"args": {"CommandLine": command, "Cwd": cwd}}}),
        ]

    def run_script(self, script, payload, *args):
        return subprocess.run([sys.executable, str(ROOT / "hooks" / "scripts" / script), *args],
                              input=payload if isinstance(payload, str) else json.dumps(payload),
                              capture_output=True, text=True, encoding="utf-8")

    def assert_denied(self, res, agy):
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        decision = out["decision"] if agy else out["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")

    def test_force_push_denied_codex_and_antigravity_payloads(self):
        for name, args, payload in self.payloads("git push --force origin main"):
            with self.subTest(cli=name):
                self.assert_denied(self.run_script("git_guard.py", payload, *args), bool(args))

    def test_normal_flow_commands_pass_all_payloads(self):
        self.write_repo_config()
        self.set_mode(2)
        run_git(self.repo, "checkout", "-q", "-b", "feature/slug")
        commands = [
            "git status",
            "git add .",
            'git commit -m "feat: x"',
            "git switch -c feature/x",
            "git merge --no-ff feature/x",
            "orca linear issue SC-1 --json",
            "python scripts/gates/run_gates.py ticket x",
            "python -m unittest discover -s tests -v",
        ]
        for command in commands:
            for name, args, payload in self.payloads(command):
                for script in ("git_guard.py", "secret_scan.py"):
                    with self.subTest(cli=name, script=script, command=command):
                        res = self.run_script(script, payload, *args)
                        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))

    def test_invalid_payload_fails_open_with_warning(self):
        for script in ("git_guard.py", "secret_scan.py"):
            for args in ([], ["--agy"]):
                with self.subTest(script=script, args=args):
                    res = self.run_script(script, "not json", *args)
                    self.assertEqual((res.returncode, res.stdout), (0, ""))
                    self.assertTrue(res.stderr.startswith("StarCode hook:"), res.stderr)

    def test_evaluation_error_fails_open_with_warning(self):
        import git_guard

        class Boom:
            def __init__(self, cwd):
                pass

            def evaluate(self, command):
                raise RuntimeError("boom")

        old_guard, old_stdin = git_guard.Guard, sys.stdin
        old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
        import io
        git_guard.Guard = Boom
        sys.stdin = io.StringIO(json.dumps({"tool_input": {"command": "git status"}}))
        sys.argv, sys.stderr, sys.stdout = ["git_guard.py"], io.StringIO(), io.StringIO()
        try:
            code = git_guard.main()
            err, out = sys.stderr.getvalue(), sys.stdout.getvalue()
        finally:
            git_guard.Guard, sys.stdin = old_guard, old_stdin
            sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
        self.assertEqual((code, out), (0, ""))
        self.assertTrue(err.startswith("StarCode hook:"), err)

    def test_payload_without_command_passes_silently(self):
        for script in ("git_guard.py", "secret_scan.py"):
            for payload, args in (({"tool_input": {}}, []), ({"toolCall": {"args": {}}}, ["--agy"])):
                with self.subTest(script=script, args=args):
                    res = self.run_script(script, payload, *args)
                    self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))


if __name__ == "__main__":
    unittest.main()
