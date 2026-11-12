"""R39: tools/aceite.py materializa as fixtures de aceite fora do repositório."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, run_git

TOOL = ROOT / "tools" / "aceite.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True,
                          stdin=subprocess.DEVNULL)


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
            self.assertIn(str(dest), res.stdout)
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
