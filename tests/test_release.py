"""tools/release.py with a fake command runner (R14, R23, R24)."""
from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from helpers import ROOT  # noqa: F401  (sets sys.path)

import release

CHANGELOG = """# Changelog

## [Unreleased]

## [1.2.3] - 2026-01-01

### Adicionado

- Item novo.

## [1.0.0] - 2025-01-01

- Antigo.
"""


class Fake:
    def __init__(self, remote_out=""):
        self.calls = []
        self.remote_out = remote_out

    def __call__(self, cmd, **kw):
        self.calls.append(list(cmd))
        out = self.remote_out if "ls-remote" in cmd else ""
        return SimpleNamespace(returncode=0, stdout=out, stderr="")


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        (self.tmp / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")

    def run_main(self, argv, runner=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = release.main(argv, runner=runner or Fake(), root=self.tmp)
        return rc, out.getvalue(), err.getvalue()

    def test_release_check_accepts_matching_tag(self):
        self.assertEqual(self.run_main(["check", "--tag", "v1.2.3"])[0], 0)

    def test_release_check_rejects_tag_diverging_from_version(self):
        rc, _, err = self.run_main(["check", "--tag", "v9.9.9"])
        self.assertEqual(rc, 1)
        self.assertIn("tag v9.9.9 diverge de VERSION 1.2.3", err)

    def test_release_notes_extracted_from_changelog(self):
        rc, out, _ = self.run_main(["notes"])
        self.assertEqual(rc, 0)
        self.assertIn("- Item novo.", out)
        self.assertIn("### Adicionado", out)
        self.assertNotIn("## [1.2.3]", out)
        self.assertNotIn("Antigo", out)

    def test_release_notes_fails_without_section(self):
        (self.tmp / "VERSION").write_text("2.0.0\n", encoding="utf-8")
        self.assertEqual(self.run_main(["notes"])[0], 1)

    def test_release_refuses_existing_remote_tag(self):
        fake = Fake(remote_out="abc123\trefs/tags/v1.2.3\n")
        rc, _, err = self.run_main(["create", "--yes"], fake)
        self.assertEqual(rc, 1)
        self.assertIn("tag v1.2.3 já existe no remoto", err)
        self.assertEqual(len(fake.calls), 1)
        self.assertIn("ls-remote", fake.calls[0])
        self.assertFalse(any("--force" in c for call in fake.calls for c in call))

    def test_release_create_requires_yes_flag(self):
        fake = Fake()
        rc, out, _ = self.run_main(["create"], fake)
        self.assertEqual(rc, 0)
        self.assertEqual(len(fake.calls), 1)  # só o ls-remote
        self.assertIn('git tag -a v1.2.3 -m "StarCode v1.2.3"', out)
        self.assertIn("git push origin v1.2.3", out)
        self.assertIn("gh release create v1.2.3 --notes-file", out)

        fake = Fake()
        rc, _, _ = self.run_main(["create", "--yes"], fake)
        self.assertEqual(rc, 0)
        self.assertEqual(fake.calls[0], ["git", "ls-remote", "--tags", "origin", "v1.2.3"])
        self.assertEqual(fake.calls[1], ["git", "tag", "-a", "v1.2.3", "-m", "StarCode v1.2.3"])
        self.assertEqual(fake.calls[2], ["git", "push", "origin", "v1.2.3"])
        self.assertEqual(fake.calls[3][:4], ["gh", "release", "create", "v1.2.3"])
        self.assertIn("--notes-file", fake.calls[3])


if __name__ == "__main__":
    unittest.main()
