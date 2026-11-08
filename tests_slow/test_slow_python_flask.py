"""Perfil python-flask com registro real (T8, R4): gera e roda todos os gates."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "scaffold.py"


def scaffold(*argv: str, timeout: int) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "STARCODE_REGISTRY_FIXTURE"}
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, env=env,
                          stdin=subprocess.DEVNULL, encoding="utf-8", errors="replace",
                          timeout=timeout)


class SlowPythonFlaskTests(unittest.TestCase):
    def test_flask_template_gates_pass(self) -> None:
        with tempfile.TemporaryDirectory(prefix="starcode-flask-slow-") as tmp:
            folder = Path(tmp) / "app-flask"
            res = scaffold("new", str(folder), "--profile", "python-flask", timeout=300)
            self.assertEqual(res.returncode, 0, res.stderr)
            res = scaffold("gates", str(folder), timeout=1800)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            lines = [ln for ln in res.stdout.splitlines() if ln.startswith(("PASS", "FAIL", "SKIP"))]
            self.assertEqual(len(lines), 5, res.stdout)
            self.assertTrue(all(ln.startswith("PASS") for ln in lines), res.stdout)


if __name__ == "__main__":
    unittest.main()
