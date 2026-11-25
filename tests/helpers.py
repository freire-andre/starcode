"""Shared test helpers (stdlib only)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
for p in (ROOT / "scripts", ROOT / "scripts" / "config", ROOT / "scripts" / "gates", ROOT / "scripts" / "review", ROOT / "hooks" / "scripts", ROOT / "tools"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def run_git(cwd: Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True,
                         stdin=subprocess.DEVNULL)
    return res.stdout.strip()


class TempRepoCase(unittest.TestCase):
    """Each test gets a fresh git repo on branch main with one commit and an isolated STARCODE_HOME."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-test-")
        self.tmp = Path(self._tmp.name).resolve()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        run_git(self.repo, "init", "-q", "-b", "main")
        run_git(self.repo, "config", "user.email", "test@example.com")
        run_git(self.repo, "config", "user.name", "Test")
        run_git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "README.md").write_text("hello\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "init")
        self._old_home = os.environ.get("STARCODE_HOME")
        os.environ["STARCODE_HOME"] = str(self.tmp / "starcode-home")

    def tearDown(self) -> None:
        if self._old_home is None:
            os.environ.pop("STARCODE_HOME", None)
        else:
            os.environ["STARCODE_HOME"] = self._old_home
        self._tmp.cleanup()

    def write_repo_config(self, base: str = "main") -> None:
        cfg = json.loads((FIXTURES / "config" / "valid" / "repo-full.json").read_text(encoding="utf-8"))
        cfg["baseBranch"] = base
        path = self.repo / ".starcode" / "config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cfg), encoding="utf-8")

    def set_mode(self, mode: int) -> None:
        import starcode_common as sc

        data = sc.read_session(self.repo)
        data.update({"gitMode": mode, "setAt": sc.now_iso()})
        sc.write_session(self.repo, data)
