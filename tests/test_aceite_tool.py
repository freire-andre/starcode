"""R39: tools/aceite.py materializa as fixtures de aceite fora do repositório."""
from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, run_git

TOOL = ROOT / "tools" / "aceite.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "commit.gpgsign",
           "GIT_CONFIG_VALUE_0": "false"}
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True,
                          stdin=subprocess.DEVNULL, env=env)


class AceiteToolTests(unittest.TestCase):
    def test_aceite_preparar_materializa_fixture(self):
        with tempfile.TemporaryDirectory(prefix="aceite-test-") as tmp:
            dest = Path(tmp) / "app"
            res = _run("preparar", "telas", "--destino", str(dest))
            self.assertEqual(res.returncode, 0, res.stderr)
            for rel in ("package.json", "src/main.ts", ".gitattributes", ".starcode/config.json",
                        ".specs/features/tela-saudacao/spec.md", "src-tauri/Cargo.toml"):
                self.assertTrue((dest / rel).is_file(), rel)
            self.assertFalse((dest / "node_modules").exists())
            self.assertEqual(run_git(dest, "rev-list", "--count", "HEAD"), "1")
            self.assertEqual(run_git(dest, "config", "core.autocrlf"), "false")
            self.assertIn(str(Path(dest).resolve()), res.stdout)
            self.assertIn("npm ci", res.stdout)
            self.assertIn("orca repo add", res.stdout)
            self.assertIn("starcode:setup", res.stdout)
            # destino não vazio
            self.assertEqual(_run("preparar", "telas", "--destino", str(dest)).returncode, 2)
            # destino dentro do repositório
            inside = ROOT / "aceite-destino-teste"
            self.assertEqual(_run("preparar", "telas", "--destino", str(inside)).returncode, 2)
            self.assertFalse(inside.exists())
            self.assertEqual(_run("preparar", "telas", "--destino", str(ROOT / "aceite" / "x")).returncode, 2)
            # nome inexistente
            self.assertEqual(_run("preparar", "nao-existe", "--destino",
                                  str(Path(tmp) / "outro")).returncode, 2)

    def test_aceite_preparar_nao_grava_identidade_na_copia(self):
        with tempfile.TemporaryDirectory(prefix="aceite-id-") as tmp:
            vazio = Path(tmp) / "gitconfig-vazio"
            vazio.write_text("", encoding="utf-8")
            env = {"GIT_CONFIG_GLOBAL": str(vazio), "GIT_CONFIG_NOSYSTEM": "1"}
            old = dict(os.environ)
            os.environ.update(env)
            try:
                dest = Path(tmp) / "app"
                res = _run("preparar", "telas", "--destino", str(dest))
            finally:
                os.environ.clear()
                os.environ.update(old)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertEqual(run_git(dest, "rev-list", "--count", "HEAD"), "1")
            local = subprocess.run(["git", "config", "--local", "user.email"], cwd=dest,
                                   capture_output=True, text=True, stdin=subprocess.DEVNULL)
            self.assertEqual(local.stdout.strip(), "")
            local = subprocess.run(["git", "config", "--local", "user.name"], cwd=dest,
                                   capture_output=True, text=True, stdin=subprocess.DEVNULL)
            self.assertEqual(local.stdout.strip(), "")

    def test_aceite_preparar_filtra_pastas_em_toda_a_arvore(self):
        sys.path.insert(0, str(ROOT / "tools"))
        try:
            import aceite
        finally:
            sys.path.remove(str(ROOT / "tools"))
        env = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "commit.gpgsign",
               "GIT_CONFIG_VALUE_0": "false"}
        with tempfile.TemporaryDirectory(prefix="aceite-filtro-") as tmp:
            fixtures = Path(tmp) / "fixtures"
            src = fixtures / "mini"
            for rel in ("keep.txt", "a/b/node_modules/x.js", "src-tauri/target/y.bin",
                        "pkg/dist/z.js", "node_modules/r.js", "dist/r.js", "target/r.bin",
                        "sub/.git/config", "sub/ok.txt"):
                f = src / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text("x", encoding="utf-8")
            dest = Path(tmp) / "app"
            old_fixtures, old_env = aceite.FIXTURES, dict(os.environ)
            aceite.FIXTURES = fixtures
            os.environ.update(env)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    rc = aceite.preparar("mini", str(dest))
            finally:
                aceite.FIXTURES = old_fixtures
                os.environ.clear()
                os.environ.update(old_env)
            self.assertEqual(rc, 0)
            self.assertTrue((dest / "keep.txt").is_file())
            self.assertTrue((dest / "sub" / "ok.txt").is_file())
            for nome in ("node_modules", "target", "dist"):
                self.assertEqual(list(dest.rglob(nome)), [], nome)
            self.assertEqual([p for p in dest.rglob(".git")], [dest / ".git"])

    def test_listar_mostra_telas(self):
        res = _run("listar")
        self.assertEqual(res.returncode, 0)
        self.assertIn("telas", res.stdout)

    def test_aceite_fora_do_dist(self):
        dist = ROOT / "dist"
        found = [p for p in dist.rglob("*") if "aceite" in p.relative_to(dist).parts[1:2]
                 or p.name == "aceite"]
        self.assertEqual(found, [])
        self.assertFalse((dist / "claude" / "aceite").exists())


if __name__ == "__main__":
    unittest.main()
