"""Tests for scaffold.py detect/record (R31): perfis pelos manifestos, stack.json com source manifest."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

SCRIPT = ROOT / "scripts" / "scaffold.py"

PYPROJECT = """[project]
name = "api"
version = "0.1.0"
dependencies = ["flask>=3.0", "psycopg[binary]==3.2.1"]
[dependency-groups]
dev = ["pytest>=8"]
"""
UV_LOCK = """version = 1
[[package]]
name = "flask"
version = "3.1.3"
[[package]]
name = "psycopg"
version = "3.2.9"
"""


def sc(*argv: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    env.pop("STARCODE_PROFILES_DIR", None)
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True,
                          encoding="utf-8", stdin=subprocess.DEVNULL, env=env, cwd=cwd)


class DetectCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-detect-")
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)

    def put(self, rel: str, text: str) -> None:
        f = self.repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")

    def detect(self) -> dict:
        r = sc("detect", str(self.repo), "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def stack(self) -> dict:
        return json.loads((self.repo / ".starcode" / "stack.json").read_text(encoding="utf-8"))

    def test_scaffold_detect_and_record_profiles(self):
        # flask + psycopg -> python-flask + postgresql
        self.put("pyproject.toml", PYPROJECT)
        self.put("uv.lock", UV_LOCK)
        got = self.detect()
        self.assertEqual(got["profiles"], ["python-flask", "postgresql"])
        self.assertFalse(got["ambiguous"])
        # sem --yes: só mostra, nada é gravado
        r = sc("record", str(self.repo), "--profiles", "python-flask,postgresql")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("python-flask", r.stdout)
        self.assertFalse((self.repo / ".starcode").exists())
        # com --yes grava, com versões do lockfile (e do manifesto quando não há lock)
        r = sc("record", str(self.repo), "--profiles", "python-flask,postgresql", "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        stack = self.stack()
        self.assertEqual(stack["schemaVersion"], 1)
        self.assertEqual(stack["profiles"], ["python-flask", "postgresql"])
        self.assertEqual(stack["versions"]["flask"]["version"], "3.1.3")
        self.assertEqual(stack["versions"]["psycopg"]["version"], "3.2.9")
        self.assertEqual(stack["versions"]["pytest"]["version"], "8")
        self.assertTrue(all(v["source"] == "manifest" for v in stack["versions"].values()))
        self.assertNotIn("ruff", stack["versions"])  # não está no manifesto: não inventa
        self.assertEqual(sorted(p.name for p in self.repo.iterdir() if p.name != ".git"),
                         [".starcode", "pyproject.toml", "uv.lock"])  # sem template copiado
        # o checks do Data lê o arquivo gravado
        r = sc("checks", str(self.repo))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Build**:", r.stdout)
        self.assertIn("**Run integration**:", r.stdout)

    def test_detect_other_stacks(self):
        self.put("package.json", json.dumps({"devDependencies": {"typescript": "^5.4.0", "vitest": "~2.1.0"}}))
        self.assertEqual(self.detect()["profiles"], ["typescript"])
        r = sc("record", str(self.repo), "--profiles", "typescript", "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.stack()["versions"]["vitest"]["version"], "2.1.0")
        self.assertEqual(self.stack()["versions"]["typescript"]["version"], "5.4.0")

    def test_detect_rust_tauri_and_empty(self):
        self.assertEqual(self.detect()["profiles"], [])
        self.put("Cargo.toml", '[package]\nname = "x"\nversion = "0.1.0"\n[dependencies]\n')
        self.assertEqual(self.detect()["profiles"], ["rust"])
        self.put("Cargo.toml", '[package]\nname = "x"\nversion = "0.1.0"\n[dependencies]\ngpui = "0.2.1"\n')
        self.assertEqual(self.detect()["profiles"], ["gpui"])
        (self.repo / "Cargo.toml").unlink()
        self.put("package.json", json.dumps({"devDependencies": {"typescript": "^5"}}))
        self.put("src-tauri/tauri.conf.json", "{}")
        self.put("src-tauri/Cargo.toml", '[dependencies]\ntauri = { version = "2.1.0", features = [] }\n')
        got = self.detect()
        self.assertEqual(got["profiles"], ["tauri"])  # o tauri engloba o pacote TS
        self.put("src-tauri/Cargo.lock", '[[package]]\nname = "tauri"\nversion = "2.1.7"\n')
        r = sc("record", str(self.repo), "--profiles", "tauri", "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.stack()["versions"]["tauri"]["version"], "2.1.7")

    def test_mixed_profiles_are_ambiguous_and_record_validates(self):
        self.put("pyproject.toml", PYPROJECT)
        self.put("package.json", json.dumps({"devDependencies": {"typescript": "^5"}}))
        got = self.detect()
        self.assertTrue(got["ambiguous"])
        self.assertEqual(sorted(got["profiles"]), ["postgresql", "python-flask", "typescript"])
        r = sc("record", str(self.repo), "--profiles", "nao-existe", "--yes")
        self.assertEqual(r.returncode, 2)
        self.assertFalse((self.repo / ".starcode").exists())
        r = sc("record", str(self.repo), "--profiles", "postgresql", "--yes")  # banco sem app
        self.assertEqual(r.returncode, 2)
        r = sc("record", str(self.repo / "nada"), "--profiles", "rust", "--yes")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
