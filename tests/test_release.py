"""tools/release.py with a fake command runner (R14, R23, R24)."""
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

import release

CHANGELOG = """# Changelog

## [Unreleased]

## [1.2.3] - 2026-01-01

### Adicionado

- Item novo.

## [1.0.0] - 2025-01-01

- Antigo.
"""


SHA = "0123456789abcdef0123456789abcdef01234567"
ACEITE = """# Aceite da Fase 6

## Claude

**Resultado**: aprovado

## Codex

**Resultado**: aprovado
"""
MUTATING = (("git", "tag"), ("git", "push"), ("gh", "release"))


class Fake:
    def __init__(self, remote_out="", branch="main", head=SHA, origin=SHA, ci=None):
        self.calls = []
        self.remote_out = remote_out
        self.branch = branch
        self.head = head
        self.origin = origin
        self.ci = [{"conclusion": "success", "status": "completed"}] if ci is None else ci

    def __call__(self, cmd, **kw):
        self.calls.append(list(cmd))
        out = ""
        if "ls-remote" in cmd:
            out = self.remote_out
        elif cmd[:3] == ["git", "rev-parse", "--abbrev-ref"]:
            out = self.branch + "\n"
        elif cmd == ["git", "rev-parse", "HEAD"]:
            out = self.head + "\n"
        elif cmd == ["git", "rev-parse", "origin/main"]:
            out = self.origin + "\n"
        elif cmd[:3] == ["gh", "run", "list"]:
            out = json.dumps(self.ci)
        return SimpleNamespace(returncode=0, stdout=out, stderr="")

    def mutating(self):
        return [c for c in self.calls if tuple(c[:2]) in MUTATING]


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        (self.tmp / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
        (self.tmp / "docs" / "aceite").mkdir(parents=True)
        self.aceite = self.tmp / "docs" / "aceite" / "fase-6.md"
        self.aceite.write_text(ACEITE, encoding="utf-8")

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
        self.assertIn("ls-remote", fake.calls[-1])
        self.assertEqual(fake.mutating(), [])
        self.assertFalse(any("--force" in c for call in fake.calls for c in call))

    def test_release_create_requires_yes_flag(self):
        fake = Fake()
        rc, out, _ = self.run_main(["create"], fake)
        self.assertEqual(rc, 0)
        self.assertEqual(fake.mutating(), [])  # só confere e imprime o plano
        self.assertIn('git tag -a v1.2.3 -m "StarCode v1.2.3"', out)
        self.assertIn("git push origin v1.2.3", out)
        self.assertIn("gh release create v1.2.3 --notes-file", out)

        fake = Fake()
        rc, _, _ = self.run_main(["create", "--yes"], fake)
        self.assertEqual(rc, 0)
        self.assertIn(["git", "ls-remote", "--tags", "origin", "v1.2.3"], fake.calls)
        m = fake.mutating()
        self.assertEqual(m[0], ["git", "tag", "-a", "v1.2.3", "-m", "StarCode v1.2.3"])
        self.assertEqual(m[1], ["git", "push", "origin", "v1.2.3"])
        self.assertEqual(m[2][:4], ["gh", "release", "create", "v1.2.3"])
        self.assertIn("--notes-file", m[2])

    def assert_refused(self, fake, expected, yes=True):
        rc, out, err = self.run_main(["create", "--yes"] if yes else ["create"], fake)
        self.assertEqual(rc, 1)
        self.assertEqual(err, expected)
        self.assertEqual(out, "")
        self.assertEqual(fake.mutating(), [])

    def test_release_refuses_branch_other_than_main(self):  # R23
        for yes in (True, False):
            self.assert_refused(Fake(branch="feature/x"),
                                "release só a partir de main (ramo atual: feature/x)\n", yes)

    def test_release_refuses_head_diverging_from_origin_main(self):  # R23
        fake = Fake(origin="f" * 40)
        self.assert_refused(fake, "HEAD diverge de origin/main: faça pull ou push antes do release\n")
        self.assertIn(["git", "fetch", "origin", "main"], fake.calls)
        self.assert_refused(Fake(origin="f" * 40),
                            "HEAD diverge de origin/main: faça pull ou push antes do release\n", False)

    def test_release_refuses_ci_not_green(self):  # R23
        cases = [
            ([], "sem run"),
            ([{"status": "in_progress", "conclusion": ""}], "in_progress"),
            ([{"status": "completed", "conclusion": "failure"}], "failure"),
        ]
        for ci, estado in cases:
            for yes in (True, False):
                fake = Fake(ci=ci)
                self.assert_refused(fake, f"CI de main não está verde em {SHA[:7]} ({estado})\n", yes)
                self.assertIn(["gh", "run", "list", "--workflow", "CI", "--branch", "main",
                               "--commit", SHA, "--json", "conclusion,status", "--limit", "1"],
                              fake.calls)

    def test_release_refuses_unapproved_acceptance(self):  # R23
        self.aceite.write_text(ACEITE.replace("aprovado", "pendente", 1), encoding="utf-8")
        for yes in (True, False):
            self.assert_refused(Fake(), "aceite não aprovado em docs/aceite/fase-6.md: Claude\n", yes)


if __name__ == "__main__":
    unittest.main()
