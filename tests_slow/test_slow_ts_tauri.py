"""Perfis typescript e tauri com registro real: gera o projeto e roda `scaffold.py gates` (R4, R9; C48, C49).

Precisa de rede, node/npm e (tauri) cargo. O primeiro build do Tauri leva vários minutos.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD = ROOT / "scripts" / "scaffold.py"
TIMEOUT_MIN = 30


def scaffold(*argv: str, timeout: float) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "STARCODE_REGISTRY_FIXTURE"}
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([sys.executable, str(SCAFFOLD), *argv], capture_output=True, env=env,
                          stdin=subprocess.DEVNULL, timeout=timeout)
    return subprocess.CompletedProcess(argv, proc.returncode, proc.stdout.decode("utf-8", "replace"),
                                       proc.stderr.decode("utf-8", "replace"))


class TsTauriGatesTests(unittest.TestCase):
    def assert_gates_pass(self, profile: str) -> None:
        with tempfile.TemporaryDirectory(prefix=f"starcode-slow-{profile}-") as tmp:
            folder = Path(tmp) / f"slow-{profile}"
            made = scaffold("new", str(folder), "--profile", profile, "--pin-tested", timeout=300)
            self.assertEqual(made.returncode, 0, made.stdout + made.stderr)
            gates = scaffold("gates", str(folder), "--timeout-min", str(TIMEOUT_MIN),
                             timeout=TIMEOUT_MIN * 60 * 8)
            output = gates.stdout + gates.stderr
            self.assertEqual(gates.returncode, 0, output)
            verdicts = [ln for ln in gates.stdout.splitlines() if ln.split(" ", 1)[0] in ("PASS", "FAIL", "SKIP")]
            self.assertTrue(verdicts, output)
            self.assertTrue(all(ln.startswith("PASS ") for ln in verdicts), output)

    @unittest.skipUnless(shutil.which("node") and shutil.which("npm"), "node/npm ausentes")
    def test_typescript_template_gates_pass(self) -> None:
        self.assert_gates_pass("typescript")

    @unittest.skipUnless(shutil.which("node") and shutil.which("npm") and shutil.which("cargo"),
                         "node/npm/cargo ausentes")
    def test_tauri_template_gates_pass(self) -> None:
        self.assert_gates_pass("tauri")


if __name__ == "__main__":
    unittest.main()
