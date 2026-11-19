import json
import subprocess
import sys
import unittest

from helpers import FIXTURES, ROOT, TempRepoCase, run_git

import starcode_common as sc
from git_guard import Guard, extract, tokenize

HINT_TEXT = ("Se o usuário pediu isso de forma explícita, peça que ele mesmo rode o comando no "
             "terminal.")
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


HEREDOC_TOKENS = [
    ("cat <<EOF > a.md\ngit reset --hard\nEOF\ngit status",
     [["cat", "<<", "EOF", ">", "a.md"], ["git", "reset", "--hard"], ["EOF"], ["git", "status"]]),
    ("bash <<-EOF\n\tgit status\n\tEOF",
     [["bash", "<<", "-EOF"], ["git", "status"], ["EOF"]]),
    ("git commit -m \"$(cat <<'EOF'\nmsg\nEOF\n)\"",
     [["git", "commit", "-m", '"$(cat', "<<'EOF'"], ["msg"], ["EOF"], [')"']]),
    ('cat <<"X" | bash\nls\nX',
     [["cat", "<<", "X"], ["bash"], ["ls"], ["X"]]),
]


class TokenizeTests(unittest.TestCase):
    def test_tokenize_inalterado(self):
        for cmd, expected in HEREDOC_TOKENS:
            with self.subTest(cmd=cmd):
                self.assertEqual(tokenize(cmd), expected)

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

    def test_checkout_e_switch_forcados(self):
        g = Guard(str(self.repo))
        for cmd, name in (("git checkout -f main", "git checkout"), ("git checkout --force main", "git checkout"),
                          ("git checkout -fb x", "git checkout"),
                          ("git switch --discard-changes main", "git switch"),
                          ("git switch -f main", "git switch"), ("git switch --force main", "git switch")):
            with self.subTest(cmd=cmd):
                reason = g.evaluate(cmd)
                self.assertIsNotNone(reason, cmd)
                self.assertIn(f"`{name}` forçado", reason)
                self.assertTrue(reason.endswith(HINT_TEXT))
        for cmd in ("git checkout main", "git checkout -b x", "git switch main", "git switch -c x",
                    "git checkout -- -f", "git checkout main -- -f", "git switch -- -f"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(g.evaluate(cmd), cmd)

    def test_stash_drop_e_clear(self):
        g = Guard(str(self.repo))
        for cmd in ("git stash drop", "git stash drop stash@{1}", "git stash clear"):
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(g.evaluate(cmd), cmd)
        for cmd in ("git stash", "git stash push -m drop", "git stash pop", "git stash apply",
                    "git stash list", "git stash show"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(g.evaluate(cmd), cmd)

    def test_shell_com_flags_combinadas(self):
        g = Guard(str(self.repo))
        for shell in ("bash", "sh", "zsh", "dash"):
            for flag in ("-lc", "-ec", "-xec"):
                with self.subTest(shell=shell, flag=flag):
                    self.assertIsNotNone(g.evaluate(f'{shell} {flag} "git reset --hard"'))
                    self.assertIsNotNone(g.evaluate(f"{shell} {flag} 'git clean -fd'"))
                    self.assertIsNone(g.evaluate(f'{shell} {flag} "git status"'))
            with self.subTest(shell=shell, flag="-c"):
                self.assertIsNotNone(g.evaluate(f'{shell} -c "git reset --hard"'))

    def test_heredoc_de_dado_passa(self):
        g = Guard(str(self.repo))
        for cmd in ("cat <<'EOF' > notas.md\ngit reset --hard\nEOF",
                    "cat <<EOF > notas.md\ngit reset --hard\nEOF",
                    "cat <<-EOF > notas.md\n\tgit reset --hard\n\tEOF",
                    'cat <<"EOF" > notas.md\ngit reset --hard\nEOF',
                    "git commit -m \"$(cat <<'EOF'\nfix\n\ngit reset --hard\nEOF\n)\"",
                    # dois heredocs na mesma linha e em linhas separadas
                    "cat <<A <<B > notas.md\none\nA\ngit reset --hard\nB",
                    "cat <<A > a.md\none\nA\ncat <<B > b.md\ngit reset --hard\nB",
                    # heredoc sem fecho: o corpo vai até o fim do comando
                    "cat <<EOF > notas.md\ngit reset --hard",
                    # comentário depois do operador
                    "cat <<'EOF' > a.md # nota\ngit reset --hard\nEOF",
                    # o heredoc pertence ao cat; o bash é de outro segmento
                    "cat <<EOF > a; bash -c true\ngit reset --hard\nEOF",
                    # cada delimitador guarda a sua variante: só <<- aceita tab antes do delimitador
                    "cat <<-A <<B\none\nA\n\tB\ngit reset --hard\nB"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(g.evaluate(cmd), cmd)

    def test_heredoc_para_shell_bloqueia(self):
        g = Guard(str(self.repo))
        for cmd in ("bash <<EOF\ngit reset --hard\nEOF", "sh <<'EOF'\ngit reset --hard\nEOF",
                    "bash -s <<EOF\ngit reset --hard\nEOF",
                    "cat <<EOF | bash\ngit reset --hard\nEOF",
                    "cat <<EOF 2>&1 | bash\ngit reset --hard\nEOF",
                    "cat <<EOF > a.md\nok\nEOF\ngit reset --hard",
                    # << em comentário ou em string não abre heredoc
                    "echo ok # <<EOF\ngit reset --hard",
                    'echo "<<EOF"\ngit reset --hard',
                    "echo '<<EOF'\ngit reset --hard",
                    # aspas sem fechar: na dúvida, a linha seguinte é analisada
                    "echo 'x <<EOF\ngit reset --hard",
                    # dois heredocs: o que vai para o shell continua analisado
                    "cat <<A > a.md\nx\nA\nbash <<B\ngit reset --hard\nB"):
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(g.evaluate(cmd), cmd)
        self.assertIsNone(g.evaluate("bash <<EOF\ngit status\nEOF"))

    def test_decisions_guard_lote2(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        start = text.index("### SC-196:")
        nxt = text.find("\n### ", start + 1)
        entry = text[start:nxt if nxt != -1 else len(text)]
        for field in ("**Problema", "**Decisão", "**Motivo", "**Por que não é bug"):
            self.assertIn(field, entry)
        decision = next(l for l in entry.splitlines() if l.startswith("- **Decisão"))
        conditions = (
            # R1
            "`git checkout` com `-f`/`--force` (inclusive combinado, como `-fb`)",
            "`git switch` com `--discard-changes`, `-f` ou `--force` são bloqueados em qualquer repo",
            "com o comando e o `HINT`", "`checkout main`, `checkout -b x` e `switch main` passam",
            # R2
            "`git stash drop` (com ou sem referência) e `git stash clear` são bloqueados em qualquer repo",
            "`stash`, `push`, `pop`, `apply`, `list` e `show` passam",
            # R3
            "`bash`, `sh`, `zsh` e `dash` com flag curta combinada que contém `c` (`-lc`, `-ec`, `-xec`)",
            "tem o argumento seguinte analisado como comando",
            # R4
            "com o modo Git 1, `git cherry-pick`, `revert`, `am`, `pull` e `rebase` são bloqueados",
            "exceto as flags de controle `--abort`, `--continue`, `--quit`, `--skip`",
            "`cherry-pick`/`revert` com `-n` ou `--no-commit`", "nos modos 2, 3 e 4 passam",
            # R5
            "(`<<EOF`, `<<-EOF`, `<<'EOF'`, `<<\"EOF\"`)",
            "cujo comando não é um shell e não está ligado por `|` a um shell é ignorado até o delimitador",
            "`git commit -m \"$(cat <<'EOF' ...)\"`",
            # R6
            "(`bash <<EOF`, `sh <<EOF`, `cat <<EOF | bash`) continua analisado linha a linha",
            "um comando depois do delimitador continua analisado",
            # R7 e os fechamentos da rodada pós-Q
            "`tokenize` não mudou (R7)",
            "fora de comentário e de aspas", "depois de `--` vem caminho", "cada heredoc pertence ao seu comando",
            "só o `<<-` aceita tab",
        )
        for phrase in conditions:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, decision)
        why = next(l for l in entry.splitlines() if l.startswith("- **Por que não é bug"))
        for name in ("test_checkout_e_switch_forcados", "test_stash_drop_e_clear",
                     "test_shell_com_flags_combinadas", "test_modo_1_comandos_que_criam_commit",
                     "test_heredoc_de_dado_passa", "test_heredoc_para_shell_bloqueia",
                     "test_tokenize_inalterado"):
            self.assertIn(name, why)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
        self.assertIn("(SC-196)", unreleased)
        doc = (ROOT / "hooks" / "scripts" / "git_guard.py").read_text(encoding="utf-8").split('"""')[1]
        for term in ("forced checkout (-f/--force)", "forced switch (--discard-changes/-f/--force)",
                     "stash drop/clear", "`bash -lc", "`sh -ec", "cherry-pick, revert, am, pull, rebase",
                     "except control", "--no-commit", "heredoc whose body is only data",
                     "heredoc that goes to a shell", "comment or in quotes"):
            with self.subTest(term=term):
                self.assertIn(term, doc)

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

    def test_modo_1_comandos_que_criam_commit(self):
        blocked = ("git cherry-pick abc123", "git revert HEAD", "git am p.patch", "git pull",
                   "git pull origin main", "git rebase main")
        control = ("--abort", "--continue", "--quit", "--skip")
        allowed = [f"git {c} {f}" for c in ("cherry-pick", "revert", "am", "pull", "rebase") for f in control]
        allowed += [f"git {c} {f} abc" for c in ("cherry-pick", "revert") for f in ("-n", "--no-commit")]
        self.set_mode(1)
        for cmd in blocked:
            with self.subTest(mode=1, cmd=cmd):
                self.assertIn("modo Git deste worktree é 1", self.guard(cmd) or "")
        for cmd in allowed:
            with self.subTest(mode=1, cmd=cmd):
                self.assertIsNone(self.guard(cmd), cmd)
        for cmd in ("git rebase -n main", "git pull --no-commit", "git am -n p.patch"):
            with self.subTest(mode=1, cmd=cmd):
                self.assertIsNotNone(self.guard(cmd), cmd)  # -n/--no-commit só isenta cherry-pick e revert
        for mode in (2, 3, 4):
            self.set_mode(mode)
            for cmd in blocked:
                with self.subTest(mode=mode, cmd=cmd):
                    self.assertIsNone(self.guard(cmd), cmd)

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

    def test_git_guard_nega_push_force_pelo_powershell(self):
        outs = {}
        for tool in ("Bash", "PowerShell"):
            payload = {"tool_name": tool, "tool_input": {"command": "git push --force origin main"},
                       "cwd": str(self.repo)}
            res = self.run_hook(json.dumps(payload))
            self.assertEqual(res.returncode, 0)
            outs[tool] = json.loads(res.stdout)["hookSpecificOutput"]
        self.assertEqual(outs["PowerShell"]["permissionDecision"], "deny")
        self.assertEqual(outs["PowerShell"]["permissionDecisionReason"], outs["Bash"]["permissionDecisionReason"])

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

    def test_extract_agy_real_payload_uses_workspace_path(self):
        payload = json.loads((FIXTURES / "agy-pretooluse-commit.json").read_text(encoding="utf-8"))
        payload["workspacePaths"] = [str(self.repo)]
        self.assertEqual(extract(payload, True), ('git commit -m "chore: teste"', str(self.repo)))
        payload["toolCall"]["args"]["Cwd"] = str(self.tmp)
        self.assertEqual(extract(payload, True)[1], str(self.tmp))  # Cwd explícito tem prioridade

    def test_agy_real_payload_applies_worktree_mode(self):
        self.write_repo_config()
        self.set_mode(1)
        payload = json.loads((FIXTURES / "agy-pretooluse-commit.json").read_text(encoding="utf-8"))
        payload["workspacePaths"] = [str(self.repo)]
        outside = self.tmp / "plugin"
        outside.mkdir()
        res = subprocess.run([sys.executable, str(HOOK), "--agy"], input=json.dumps(payload), cwd=outside,
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(json.loads(res.stdout or "{}").get("decision"), "deny", res.stderr)

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
