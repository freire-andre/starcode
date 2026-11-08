"""Perfis postgresql e mysql com registro real e Docker real (T9, R5, R20)."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "scaffold.py"


def run(*argv: str, timeout: int) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "STARCODE_REGISTRY_FIXTURE"}
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(list(argv), capture_output=True, env=env, stdin=subprocess.DEVNULL,
                          encoding="utf-8", errors="replace", timeout=timeout)


def leftovers() -> list[str]:
    res = run("docker", "ps", "-a", "--filter", "name=starcode-eph-", "--format", "{{.Names}}",
              timeout=60)
    return [n for n in res.stdout.split() if n.startswith("starcode-eph-")]


class SlowDbTests(unittest.TestCase):
    def _gates(self, engine: str) -> None:
        with tempfile.TemporaryDirectory(prefix=f"starcode-{engine}-slow-") as tmp:
            folder = Path(tmp) / f"app-{engine}"
            res = run(sys.executable, str(SCRIPT), "new", str(folder), "--profile",
                      "python-flask", "--db", engine, timeout=300)
            self.assertEqual(res.returncode, 0, res.stderr)
            res = run(sys.executable, str(SCRIPT), "gates", str(folder), timeout=1800)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            lines = [ln for ln in res.stdout.splitlines() if ln.startswith(("PASS", "FAIL", "SKIP"))]
            self.assertTrue(lines, res.stdout)
            self.assertTrue(all(ln.startswith("PASS") for ln in lines), res.stdout)
            self.assertTrue(any("ephemeral_db.py" in ln for ln in lines), res.stdout)
        self.assertEqual(leftovers(), [])

    def test_flask_postgresql_gates_pass(self) -> None:
        self._gates("postgresql")

    def test_flask_mysql_gates_pass(self) -> None:
        self._gates("mysql")


if __name__ == "__main__":
    unittest.main()
