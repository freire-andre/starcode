"""Fake secrets are assembled at runtime so this file never contains a literal token
(it would trip the StarCode hook itself and GitHub push protection)."""
import json
import subprocess
import sys
import unittest

from helpers import FIXTURES, ROOT, TempRepoCase, run_git

import secret_scan as ss
from test_support import changelog_recent

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
    "postgresql://postgres:postgres@localhost",
    "postgres://user:${DB_PASSWORD}@db",
    "AUTHOR_EMAIL=dev2024.bot@empresa.com.br",
    'token_url = "https://auth.example.com/oauth2/token"',
]


class ScanTextTests(unittest.TestCase):
    def setUp(self):
        self.allow = ss.Allowlist(None)

    def test_each_fake_secret_is_found(self):
        for kind, value in FAKE.items():
            with self.subTest(kind=kind):
                self.assertTrue(ss.scan_text(f"value: {value}", self.allow), kind)

    def test_lookalikes_pass(self):
        for novo in ("postgresql://postgres:postgres@localhost", "postgres://user:${DB_PASSWORD}@db",
                     "AUTHOR_EMAIL=dev2024.bot@empresa.com.br",
                     'token_url = "https://auth.example.com/oauth2/token"'):
            self.assertIn(novo, LOOKALIKES)
        for text in LOOKALIKES:
            with self.subTest(text=text):
                self.assertEqual(ss.scan_text(text, self.allow), [], text)

    def test_conexao_placeholder_e_local_passam(self):
        ok = ["postgresql://postgres:postgres@localhost", "postgres://user:${DB_PASSWORD}@db",
              "postgres://user:$DB_PASSWORD@db", "postgres://user:<senha>@db",
              "redis://u:hunter22@127.0.0.1:6379/0", "postgres://u:hunter22@[::1]:5432/app"]
        for text in ok:
            with self.subTest(text=text):
                self.assertEqual(ss.scan_text(text, self.allow), [], text)
        found = ss.scan_text(FAKE["dsn"], self.allow)
        self.assertEqual([f[1] for f in found], ["string de conexão com senha"])
        # W1: `$NOME` só em maiúsculas; `$ecretPassw0rd9` é senha real
        found = ss.scan_text("postgres" + "ql://app:" + "$ecretPassw0rd9" + "@db.internal:5432/app", self.allow)
        self.assertEqual([f[1] for f in found], ["string de conexão com senha"])
        self.assertEqual(ss.scan_text("postgres" + "ql://app:" + "$DB_PASSWORD" + "@db.internal:5432/app",
                                      self.allow), [])
        for text in ("postgres://u:hunter22@localhost:5432@evil.com/db",
                     "postgres://u:hunter22@::1evil.example/db",
                     "postgres://u:hunter22@localhost.evil.com/db",
                     "postgres://u:hunter22@127.0.0.1.nip.io/db",
                     "postgres://u:hunter22@localhost:5432x/db",
                     "postgres://u:hunter22@[::1]evil.com/db"):
            with self.subTest(text=text):
                found = ss.scan_text(text, self.allow)
                self.assertEqual([f[1] for f in found], ["string de conexão com senha"], text)

    def test_auth_so_como_parte_inteira(self):
        self.assertEqual(ss.scan_text("AUTHOR_EMAIL=dev2024.bot@empresa.com.br", self.allow), [])
        for name in ("AUTH_TOKEN", "OAUTH_SECRET", "X_AUTH", "AUTH", "OAUTH"):
            with self.subTest(name=name):
                found = ss.scan_text(f"{name}=q8Zr2Lm9Xv4Tn7Wp1Ks6Yd3", self.allow)
                self.assertEqual([f[1] for f in found], [f"valor de alta entropia em {name}"])
        jwt = "eyJ" + "hbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiJ4OUsyIn0" + "." + "Zx9Yw8Vu7Ts6Rq5Po4Nm"
        found = ss.scan_text(f"AUTHORIZATION={jwt}", self.allow)
        self.assertEqual([f[1] for f in found], ["valor de alta entropia em AUTHORIZATION"])

    def test_url_sem_credencial_passa(self):
        self.assertEqual(ss.scan_text('token_url = "https://auth.example.com/oauth2/token"', self.allow), [])
        self.assertEqual(ss.scan_text("TOKEN_URL=https://alice@auth.example.com/oauth2/token", self.allow), [])
        slack = ("https://hooks.slack.com/services/" + "T0AB12CDE/" + "B0XY98ZWV/" + "q8Zr2Lm9Xv4Tn7Wp1Ks6Yd3Hb")
        found = ss.scan_text("SLACK_WEBHOOK_" + "TOKEN=" + slack, self.allow)
        self.assertEqual([f[1] for f in found], ["valor de alta entropia em SLACK_WEBHOOK_TOKEN"])
        discord = "https://discord.com/api/webhooks/" + "123456789012345678/" + "Zx9Yw8Vu7Ts6Rq5Po4Nm3Lk2Ji1Hg0FeDcBa"
        found = ss.scan_text("DISCORD_WEBHOOK_" + "TOKEN=" + discord, self.allow)
        self.assertEqual([f[1] for f in found], ["valor de alta entropia em DISCORD_WEBHOOK_TOKEN"])
        found = ss.scan_text('API_KEY="https://app:S3cr3tPassw0rd@host.example.com/x"', self.allow)
        self.assertEqual([f[1] for f in found], ["string de conexão com senha"])
        found = ss.scan_text("TOKEN_URL=https://app:S3cr3tPassw0rd@host.example.com/x", self.allow)
        self.assertEqual([f[1] for f in found], ["string de conexão com senha"])

    def test_decisions_scanner_lote2(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = text.split("### SC-195:", 1)[1].split("\n### ", 1)[0]
        for campo in ("**Problema**", "**Decisão**", "**Motivo**", "**Por que não é bug**"):
            self.assertIn(campo, entry)
        decisao = " ".join(entry.split("**Decisão**", 1)[1].split("**Motivo**", 1)[0].split())
        for frase in (
                "tem o texto inteiro do comando escaneado, inclusive o corpo de heredoc",
                "`git commit`, `gh pr create|edit|comment|review`, `gh issue create|comment|edit` ou `orca linear`",
                "`cat <<EOF > notas.md` sozinho não é alvo",
                "`gh issue create`, `gh issue comment`, `gh issue edit` e `gh pr review` escaneiam o texto "
                "e os arquivos de `--body-file`/`-F`",
                "senha placeholder (`${...}`, `$NOME` só com maiúsculas, dígitos e `_`, `<...>`)",
                "`$ecretPassw0rd9` não é placeholder",
                "host local (`localhost`, `127.0.0.1`, `::1`)",
                "o host é o que vem depois do último `@` da autoridade e tem que ser exatamente local, "
                "com porta opcional e mais nada; na dúvida, acusa",
                "`FAKE[\"dsn\"]` (host `db.internal`) continua achada",
                "`AUTH` no nome da chave só vale como parte inteira, separada por `_` ou na borda "
                "(`AUTH`, `AUTH_TOKEN`, `OAUTH`, `X_AUTH`), então `AUTHOR_EMAIL` passa",
                "URL `http://` ou `https://` sem `usuário:senha@` não é acusado como alta entropia",
                "a isenção só vale quando nenhum segmento do caminho ou da query, separado por `/`, `?`, `&` "
                "ou `=`, passa sozinho na regra de alta entropia (comprimento de 16 ou mais, entropia de 3,5 ou "
                "mais, com dígito e letra)",
                "um webhook com token no caminho continua acusado",
                "`AUTHORIZATION` continua sendo chave de segredo",
                "usuário sem senha (`https://alice@host`) também não é credencial",
                "com `usuário:senha@` continua acusado",
                "todas as fixtures `FAKE` seguem achadas",
                "os `LOOKALIKES`, agora com os quatro exemplos, seguem sem achado"):
            self.assertIn(frase, decisao)
        porque = entry.split("**Por que não é bug**", 1)[1]
        for teste in ("test_heredoc_de_comando_que_publica_e_escaneado", "test_gh_issue_e_pr_review_sao_escaneados",
                      "test_conexao_placeholder_e_local_passam", "test_auth_so_como_parte_inteira",
                      "test_url_sem_credencial_passa", "test_lookalikes_pass", "test_each_fake_secret_is_found"):
            self.assertIn(teste, porque)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("SC-195", changelog_recent())

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

    def test_frase_binary_files_em_texto_e_escaneada(self):  # R5
        self.stage("notas.md", f"Binary files a and b differ\nTOKEN = '{FAKE['github']}'\n")
        findings = ss.evaluate("git commit -m x", str(self.repo))
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("notas.md:2", findings[0])
        self.assertIn("token do GitHub", findings[0])
        # binário de verdade: o git diz `Binary files ... differ` e o arquivo é pulado
        run_git(self.repo, "reset", "-q")
        path = self.repo / "blob.bin"
        path.write_bytes(b"\x00\x01" + f"TOKEN = '{FAKE['github']}'".encode() + b"\x00")
        run_git(self.repo, "add", "blob.bin")
        self.assertEqual(ss.evaluate("git commit -m x", str(self.repo)), [])

    def test_arquivo_pulado_avisa(self):  # R6
        import contextlib
        import io
        from unittest import mock

        self.stage("ruim.txt", "x\n")
        self.stage("bom.py", f"TOKEN = '{FAKE['github']}'\n")
        real = subprocess.run

        def fake(args, *a, **kw):
            if "--unified=0" in args and args[-1] == "ruim.txt":
                return subprocess.CompletedProcess(args, 128, "", "fatal")
            return real(args, *a, **kw)

        err = io.StringIO()
        with mock.patch.object(ss.subprocess, "run", fake), contextlib.redirect_stderr(err):
            findings = ss.evaluate("git commit -m x", str(self.repo))
        self.assertEqual(err.getvalue(), "StarCode hook: secret_scan pulou ruim.txt (git diff saiu com 128)\n")
        self.assertEqual(len(findings), 1, findings)  # o outro arquivo seguiu e foi escaneado
        self.assertIn("bom.py:1", findings[0])

    def test_byte_nulo_depois_de_8000_e_binario(self):  # R5: o byte nulo conta em qualquer posição do diff
        self.assertTrue(ss._is_binary("a" * 8000 + "\x00"))
        self.assertTrue(ss._is_binary("a" * 20000 + "\x00" + "b"))
        self.assertFalse(ss._is_binary("a" * 20000))
        self.stage("tarde.dat", "x" * 9000 + "\x00" + f"TOKEN = '{FAKE['github']}'\n")
        self.assertEqual(ss.evaluate("git commit -m x", str(self.repo)), [])

    def test_timeout_do_git_diff_avisa_e_segue(self):  # R6
        import contextlib
        import io
        from unittest import mock

        self.stage("lento.txt", "x\n")
        self.stage("bom.py", f"TOKEN = '{FAKE['github']}'\n")
        real = subprocess.run

        def fake(args, *a, **kw):
            if "--unified=0" in args and args[-1] == "lento.txt":
                raise subprocess.TimeoutExpired(args, kw.get("timeout", 0))
            return real(args, *a, **kw)

        err = io.StringIO()
        with mock.patch.object(ss.subprocess, "run", fake), contextlib.redirect_stderr(err):
            findings = ss.evaluate("git commit -m x", str(self.repo))
        self.assertEqual(err.getvalue(), "StarCode hook: secret_scan pulou lento.txt (TimeoutExpired)\n")
        self.assertEqual(len(findings), 1, findings)  # o segredo do outro arquivo ainda bloqueia
        self.assertIn("bom.py:1", findings[0])
        self.assertIn("token do GitHub", findings[0])

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

    def test_add_force_inclui_ignorados(self):
        self.write(".gitignore", ".env\nsegredo.py\n")
        self.commit_all(".gitignore")
        self.write(".env", "DEBUG=1\n")
        self.write("segredo.py", self.segredo())
        findings = ss.evaluate("git add -f .env segredo.py && git commit -m x", str(self.repo))
        self.assertEqual(findings, [".env: arquivo .env no commit (variáveis de ambiente não vão para o Git)",
                                    self.achado("segredo.py")])
        findings = ss.evaluate("git add --force .env segredo.py && git commit -m x", str(self.repo))
        self.assertEqual(findings, [".env: arquivo .env no commit (variáveis de ambiente não vão para o Git)",
                                    self.achado("segredo.py")])
        self.assertEqual(ss.evaluate("git add .env segredo.py && git commit -m x", str(self.repo)), [])

    def test_nome_nao_ascii_e_escaneado(self):
        self.write("café.py", "a = 1\n")
        self.commit_all("café.py")
        self.write("café.py", self.segredo())
        self.assertEqual(ss.evaluate("git add -A && git commit -m x", str(self.repo)), [self.achado("café.py")])
        self.assertEqual(ss.evaluate("git add café.py && git commit -m x", str(self.repo)), [self.achado("café.py")])
        run_git(self.repo, "add", "café.py")
        self.assertEqual(ss.evaluate("git commit -m x", str(self.repo)), [self.achado("café.py")])

    def test_add_pathspec_raiz(self):
        self.write("sub/ok.py", "a = 1\n")
        self.commit_all("sub/ok.py")
        self.write("raiz.py", self.segredo())
        sub = str(self.repo / "sub")
        self.assertEqual(ss.evaluate("git add -A :/ && git commit -m x", sub), [self.achado("raiz.py")])
        self.assertEqual(ss.evaluate("git add ':(top)' && git commit -m x", sub), [self.achado("raiz.py")])

    def test_add_flags_combinadas_com_force(self):
        self.write(".gitignore", "segredo.py\n")
        self.commit_all(".gitignore")
        self.write("segredo.py", self.segredo())
        for flags in ("-Af", "-fA"):
            with self.subTest(flags=flags):
                findings = ss.evaluate(f"git add {flags} && git commit -m x", str(self.repo))
                self.assertEqual(findings, [self.achado("segredo.py")])
        self.write("README.md", self.segredo())
        for flags in ("-uf", "-fu"):
            with self.subTest(flags=flags):
                findings = ss.evaluate(f"git add {flags} && git commit -m x", str(self.repo))
                self.assertEqual(findings, [self.achado("README.md")])

    def test_add_all_em_subdiretorio_ve_raiz(self):
        self.write("sub/ok.py", "a = 1\n")
        self.commit_all("sub/ok.py")
        self.write("raiz.py", self.segredo())
        sub = str(self.repo / "sub")
        for cmd in ("git add -A && git commit -m x", "git add --all && git commit -m x"):
            with self.subTest(cmd=cmd):
                self.assertEqual(ss.evaluate(cmd, sub), [self.achado("raiz.py")])
        self.write("README.md", self.segredo())
        findings = ss.evaluate("git add -u && git commit -m x", sub)
        self.assertEqual(findings, [self.achado("README.md")])
        findings = ss.evaluate("git -C sub add -A; git -C sub commit -m x", str(self.repo))
        self.assertEqual(findings, [self.achado("README.md"), self.achado("raiz.py")])

    def test_commit_do_indice_em_subdiretorio(self):
        self.write("sub/ok.py", "a = 1\n")
        self.write("x.py", self.segredo())
        run_git(self.repo, "add", "x.py")
        findings = ss.evaluate("git commit -m x", str(self.repo / "sub"))
        self.assertEqual(findings, [self.achado("x.py")])

    def test_git_stage_conta_como_add(self):
        self.write("novo.py", self.segredo())
        self.assertEqual(ss.evaluate("git stage -A && git commit -m x", str(self.repo)), [self.achado("novo.py")])

    def test_add_pathspec_from_file_escaneia_tudo(self):
        self.write("novo.py", self.segredo())
        self.write("lista.txt", "ok.py\n")
        findings = ss.evaluate("git add --pathspec-from-file=lista.txt && git commit -m x", str(self.repo))
        self.assertEqual(findings, [self.achado("novo.py")])
        findings = ss.evaluate("git add --pathspec-from-file lista.txt && git commit -m x", str(self.repo))
        self.assertEqual(findings, [self.achado("novo.py")])

    def test_add_binario_novo_grande_passa(self):
        (self.repo / "dados.bin").write_bytes(bytes(5_000))
        old = ss.MAX_DIFF_BYTES
        ss.MAX_DIFF_BYTES = 1_000
        try:
            findings = ss.evaluate("git add -A && git commit -m x", str(self.repo))
        finally:
            ss.MAX_DIFF_BYTES = old
        self.assertEqual(findings, [])

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

    def test_heredoc_de_comando_que_publica_e_escaneado(self):
        tok = FAKE["github"]
        for cmd in (f"gh pr create --title t --body \"$(cat <<'EOF'\nresumo {tok}\nEOF\n)\"",
                    f"git commit -m \"$(cat <<'EOF'\nfix: x {tok}\nEOF\n)\""):
            with self.subTest(cmd=cmd[:20]):
                found = ss.evaluate(cmd, str(self.repo))
                self.assertTrue(any("token do GitHub" in f and "linha 2" in f for f in found), found)
        self.assertEqual(ss.evaluate(f"cat <<EOF > notas.md\n{tok}\nEOF", str(self.repo)), [])

    def test_gh_issue_e_pr_review_sao_escaneados(self):
        (self.repo / "limpo.md").write_text("tudo certo\n", encoding="utf-8")
        (self.repo / "sujo.md").write_text(f"chave {FAKE['openai']}\n", encoding="utf-8")
        cmds = ["gh issue create --title t", "gh issue comment 3", "gh issue edit 3", "gh pr review 3 --approve"]
        for base in cmds:
            with self.subTest(base=base):
                esperado = {
                    f"{base} --body '{FAKE['anthropic']}'":
                        [("texto do comando, linha 1", "chave da Anthropic")],
                    f"{base} --body-file sujo.md":
                        [("arquivo sujo.md, linha 1", "chave da OpenAI")],
                    f"{base} -F sujo.md":
                        [("arquivo sujo.md, linha 1", "chave da OpenAI")],
                }
                for cmd, origens in esperado.items():
                    found = ss.evaluate(cmd, str(self.repo))
                    self.assertEqual(len(found), len(origens), found)
                    for f, (origem, tipo) in zip(found, origens):
                        self.assertTrue(f.startswith(f"{origem}: {tipo} ("), f)
                        self.assertNotIn(FAKE["anthropic"], f)
                        self.assertNotIn(FAKE["openai"], f)
                self.assertEqual(ss.evaluate(f"{base} --body 'tudo certo'", str(self.repo)), [])
                self.assertEqual(ss.evaluate(f"{base} --body-file limpo.md", str(self.repo)), [])

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
