"""tools/install_local.py with a fake command runner (R9-R14)."""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from helpers import ROOT  # noqa: F401  (sets sys.path)

import install_local


class Fake:
    def __init__(self, fail_on=None):
        self.calls = []
        self.fail_on = fail_on

    def __call__(self, cmd, **kw):
        self.calls.append(list(cmd))
        rc = 1 if self.fail_on and self.fail_on in cmd else 0
        return SimpleNamespace(returncode=rc, stdout="", stderr="")


class InstallLocalTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.root = self.tmp / "repo"
        for cli in ("codex", "antigravity", "opencode"):
            (self.root / "dist" / cli).mkdir(parents=True)
        for s in ("engajar", "spock"):
            (self.root / "dist/opencode/skills" / s).mkdir(parents=True)
            (self.root / "dist/opencode/skills" / s / "SKILL.md").write_text("x", encoding="utf-8")
        (self.root / "dist/opencode/commands").mkdir()
        (self.root / "dist/opencode/commands/sc-q.md").write_text("q", encoding="utf-8")
        self.home = self.tmp / "home"
        self.conf = self.home / ".config/opencode/opencode.json"

    def run_cli(self, *argv, fake=None, which=lambda n: "/bin/" + n):
        fake = fake or Fake()
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = install_local.main(list(argv), runner=fake, which=which, root=self.root)
        return rc, out.getvalue(), err.getvalue(), fake

    def test_codex_registers_marketplace_and_installs(self):  # C9
        rc, out, _, fake = self.run_cli("--cli", "codex")
        self.assertEqual(rc, 0)
        self.assertEqual(fake.calls, [
            ["/bin/codex", "plugin", "marketplace", "add", str(self.root)],
            ["/bin/codex", "plugin", "add", "starcode@starcode"]])
        self.assertIn("plugin add", out)

    def test_antigravity_validates_then_installs(self):  # C10
        rc, _, _, fake = self.run_cli("--cli", "antigravity")
        self.assertEqual(rc, 0)
        self.assertEqual(fake.calls[0][1:], ["plugin", "validate", "dist/antigravity", "--strict"])
        self.assertEqual(fake.calls[1][1:3], ["plugin", "install"])
        self.assertEqual(Path(fake.calls[1][3]), (self.root / "dist/antigravity").resolve())

    def test_antigravity_validate_failure_skips_install(self):  # C10
        rc, _, _, fake = self.run_cli("--cli", "antigravity", fake=Fake(fail_on="validate"))
        self.assertEqual(rc, 1)
        self.assertEqual(len(fake.calls), 1)

    def test_opencode_preserves_keys_and_copies_commands(self):  # C11
        self.conf.parent.mkdir(parents=True)
        self.conf.write_text(json.dumps({"theme": "dark", "skills": {"paths": ["/x"]}}), encoding="utf-8")
        rc, *_ = self.run_cli("--cli", "opencode", "--home", str(self.home))
        self.assertEqual(rc, 0)
        data = json.loads(self.conf.read_text(encoding="utf-8"))
        self.assertEqual(data["theme"], "dark")
        self.assertEqual(data["skills"]["paths"][0], "/x")
        self.assertEqual(len(data["skills"]["paths"]), 3)
        self.assertTrue(all(Path(p).is_absolute() for p in data["skills"]["paths"]))
        self.assertTrue((self.home / ".config/opencode/commands/sc-q.md").exists())

    def test_opencode_creates_skills_key(self):
        self.conf.parent.mkdir(parents=True)
        self.conf.write_text('{"a": 1}', encoding="utf-8")
        self.run_cli("--cli", "opencode", "--home", str(self.home))
        data = json.loads(self.conf.read_text(encoding="utf-8"))
        self.assertEqual(data["a"], 1)
        self.assertEqual(len(data["skills"]["paths"]), 2)

    def test_idempotent(self):  # C12
        self.run_cli("--cli", "opencode", "--home", str(self.home))
        first = self.conf.read_text(encoding="utf-8")
        self.run_cli("--cli", "opencode", "--home", str(self.home))
        self.assertEqual(self.conf.read_text(encoding="utf-8"), first)
        self.assertEqual(len(list((self.home / ".config/opencode/commands").glob("*.md"))), 1)

    def test_missing_binary_exits_2_untouched(self):  # C13
        rc, _, err, fake = self.run_cli("--cli", "opencode", "--home", str(self.home), which=lambda n: None)
        self.assertEqual(rc, 2)
        self.assertIn("opencode: opencode não encontrado", err)
        self.assertFalse(self.home.exists())
        self.assertEqual(fake.calls, [])

    def test_missing_dist_exits_2(self):  # C13
        shutil.rmtree(self.root / "dist/codex")
        rc, _, err, fake = self.run_cli("--cli", "codex")
        self.assertEqual(rc, 2)
        self.assertIn("codex: dist/codex não encontrado", err)
        self.assertEqual(fake.calls, [])

    def test_invalid_json_exits_2_without_writing(self):
        self.conf.parent.mkdir(parents=True)
        self.conf.write_text("{oops", encoding="utf-8")
        rc, *_ = self.run_cli("--cli", "opencode", "--home", str(self.home))
        self.assertEqual(rc, 2)
        self.assertEqual(self.conf.read_text(encoding="utf-8"), "{oops")
        self.assertFalse((self.home / ".config/opencode/commands").exists())

    def test_dry_run_changes_nothing(self):  # C14
        for cli in ("codex", "antigravity", "opencode"):
            rc, out, _, fake = self.run_cli("--cli", cli, "--dry-run", "--home", str(self.home))
            self.assertEqual(rc, 0)
            self.assertIn("[dry-run]", out)
            self.assertEqual(fake.calls, [])
        self.assertFalse(self.home.exists())


if __name__ == "__main__":
    unittest.main()
