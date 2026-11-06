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


class Scripted:
    """Fake runner: the first `marketplace add` fails with the stale-source message until `remove` runs."""

    MSG = ("Error: marketplace 'starcode' is already added from a different source; "
           "remove it before adding this source")

    def __init__(self, stale=True):
        self.calls = []
        self.stale = stale

    def __call__(self, cmd, **kw):
        self.calls.append(list(cmd))
        if cmd[1:4] == ["plugin", "marketplace", "remove"]:
            self.stale = False
        if cmd[1:4] == ["plugin", "marketplace", "add"] and self.stale:
            return SimpleNamespace(returncode=1, stdout="", stderr=self.MSG)
        return SimpleNamespace(returncode=0, stdout="", stderr="")


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
        (self.root / "dist/opencode/plugins").mkdir()
        (self.root / "dist/opencode/plugins/starcode.js").write_text(
            'const R = "{{STARCODE_ROOT}}"\n', encoding="utf-8")
        self.agy_hooks = self.home / ".gemini/config/plugins/starcode/hooks.json"
        self.hooks_src = '{"c": "python \\"{{STARCODE_ROOT}}/hooks/scripts/g.py\\""}'

    def seed_agy_copy(self):
        self.agy_hooks.parent.mkdir(parents=True, exist_ok=True)
        self.agy_hooks.write_text(self.hooks_src, encoding="utf-8")

    def run_cli(self, *argv, fake=None, which=lambda n: "/bin/" + n):
        fake = fake or Fake()
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = install_local.main(list(argv), runner=fake, which=which, root=self.root)
        return rc, out.getvalue(), err.getvalue(), fake

    def test_install_codex_runs_marketplace_and_install(self):  # C9
        rc, out, _, fake = self.run_cli("--cli", "codex")
        self.assertEqual(rc, 0)
        self.assertEqual(fake.calls, [
            ["/bin/codex", "plugin", "marketplace", "add", str(self.root)],
            ["/bin/codex", "plugin", "add", "starcode@starcode"]])
        self.assertIn("plugin add", out)

    def test_codex_replaces_marketplace_from_other_source(self):  # item 1
        rc, out, _, fake = self.run_cli("--cli", "codex", fake=Scripted())
        self.assertEqual(rc, 0)
        add = ["/bin/codex", "plugin", "marketplace", "add", str(self.root)]
        self.assertEqual(fake.calls, [
            add, ["/bin/codex", "plugin", "marketplace", "remove", "starcode"], add,
            ["/bin/codex", "plugin", "add", "starcode@starcode"]])
        self.assertIn("outra fonte", out)

    def test_codex_same_source_stays_idempotent(self):  # item 1
        rc, _, _, fake = self.run_cli("--cli", "codex", fake=Scripted(stale=False))
        self.assertEqual(rc, 0)
        self.assertEqual(len(fake.calls), 2)
        self.assertNotIn("remove", [c[3] for c in fake.calls])

    def test_codex_other_marketplace_failure_is_not_retried(self):  # item 1
        rc, _, _, fake = self.run_cli("--cli", "codex", fake=Fake(fail_on="add"))
        self.assertEqual(rc, 1)
        self.assertEqual(len(fake.calls), 1)

    def test_codex_remove_failure_stops(self):  # item 1
        class RemoveFails(Scripted):
            def __call__(self, cmd, **kw):
                res = Scripted.__call__(self, cmd, **kw)
                if cmd[3] == "remove":
                    return SimpleNamespace(returncode=1, stdout="", stderr="boom")
                return res

        rc, _, _, fake = self.run_cli("--cli", "codex", fake=RemoveFails())
        self.assertEqual(rc, 1)
        self.assertEqual([c[3] for c in fake.calls], ["add", "remove"])

    def test_codex_dry_run_only_prints_the_plan(self):  # item 1
        rc, out, _, fake = self.run_cli("--cli", "codex", "--dry-run", fake=Scripted())
        self.assertEqual((rc, fake.calls), (0, []))
        self.assertIn("marketplace remove starcode", out)

    def test_install_antigravity_validates_first(self):  # C10
        self.seed_agy_copy()
        rc, _, _, fake = self.run_cli("--cli", "antigravity", "--home", str(self.home))
        self.assertEqual(rc, 0)
        self.assertEqual(fake.calls[0][1:], ["plugin", "validate", "dist/antigravity", "--strict"])
        self.assertEqual(fake.calls[1][1:3], ["plugin", "install"])
        self.assertEqual(Path(fake.calls[1][3]), (self.root / "dist/antigravity").resolve())

    def test_install_writes_absolute_paths_in_installed_copy(self):  # C13
        self.seed_agy_copy()
        rc, _, _, _ = self.run_cli("--cli", "antigravity", "--home", str(self.home))
        self.assertEqual(rc, 0)
        inst = (self.home / ".gemini/config/plugins/starcode").as_posix()
        text = self.agy_hooks.read_text(encoding="utf-8")
        self.assertNotIn("{{STARCODE_ROOT}}", text)
        self.assertIn(inst + "/hooks/scripts/g.py", text)
        rc, out, _, _ = self.run_cli("--cli", "opencode", "--home", str(self.home))
        self.assertEqual(rc, 0)
        js = self.home / ".config/opencode/plugins/starcode.js"
        dist = (self.root / "dist/opencode").resolve().as_posix()
        self.assertEqual(js.read_text(encoding="utf-8"), f'const R = "{dist}"\n')
        self.assertIn(str(js), out)

    def test_install_twice_keeps_single_registration(self):  # C14
        for _ in range(2):
            self.seed_agy_copy()
            self.assertEqual(self.run_cli("--cli", "antigravity", "--home", str(self.home))[0], 0)
            self.assertEqual(self.run_cli("--cli", "opencode", "--home", str(self.home))[0], 0)
        # reinstalar sobre a cópia já trocada também não duplica
        self.assertEqual(self.run_cli("--cli", "antigravity", "--home", str(self.home))[0], 0)
        text = self.agy_hooks.read_text(encoding="utf-8")
        self.assertEqual(text.count("/hooks/scripts/g.py"), 1)
        files = sorted(p.name for p in (self.home / ".config/opencode/plugins").glob("starcode*.js"))
        self.assertEqual(files, ["starcode.js"])

    def test_dry_run_writes_no_plugin_or_hooks(self):
        self.seed_agy_copy()
        self.run_cli("--cli", "antigravity", "--dry-run", "--home", str(self.home))
        rc, out, _, _ = self.run_cli("--cli", "opencode", "--dry-run", "--home", str(self.home))
        self.assertEqual(rc, 0)
        self.assertIn("starcode.js", out)
        self.assertFalse((self.home / ".config/opencode/plugins").exists())
        self.assertIn("{{STARCODE_ROOT}}", self.agy_hooks.read_text(encoding="utf-8"))

    def test_antigravity_validate_failure_skips_install(self):  # C10
        rc, _, _, fake = self.run_cli("--cli", "antigravity", fake=Fake(fail_on="validate"))
        self.assertEqual(rc, 1)
        self.assertEqual(len(fake.calls), 1)

    def test_install_opencode_writes_skills_and_commands(self):  # C11
        self.conf.parent.mkdir(parents=True)
        self.conf.write_text(json.dumps({"theme": "dark", "skills": {"paths": [str(self.tmp / "x")]}}), encoding="utf-8")
        rc, *_ = self.run_cli("--cli", "opencode", "--home", str(self.home))
        self.assertEqual(rc, 0)
        data = json.loads(self.conf.read_text(encoding="utf-8"))
        self.assertEqual(data["theme"], "dark")
        self.assertEqual(data["skills"]["paths"][0], str(self.tmp / "x"))
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

    def test_install_is_idempotent(self):  # C12
        self.run_cli("--cli", "opencode", "--home", str(self.home))
        first = self.conf.read_text(encoding="utf-8")
        self.run_cli("--cli", "opencode", "--home", str(self.home))
        self.assertEqual(self.conf.read_text(encoding="utf-8"), first)
        self.assertEqual(len(list((self.home / ".config/opencode/commands").glob("*.md"))), 1)

    def test_install_missing_binary_exits_2(self):  # C13
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

    def test_install_dry_run_changes_nothing(self):  # C14
        for cli in ("codex", "antigravity", "opencode"):
            rc, out, _, fake = self.run_cli("--cli", cli, "--dry-run", "--home", str(self.home))
            self.assertEqual(rc, 0)
            self.assertIn("[dry-run]", out)
            self.assertEqual(fake.calls, [])
        self.assertFalse(self.home.exists())


if __name__ == "__main__":
    unittest.main()
