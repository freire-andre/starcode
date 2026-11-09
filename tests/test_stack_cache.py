"""Tests for scripts/stack_cache.py (R26, R27)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

SCRIPT = ROOT / "scripts" / "stack_cache.py"


def run(*args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, env=env)
    return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8")


class StackCacheTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)
        self.summary = self.repo / "sum.txt"
        self.summary.write_text("linha 1\nlinha 2\n", encoding="utf-8")

    def write(self, lib="flask", proj="3.1.3", doc="3.1.x", date="2026-11-08", summary=None, extra=()):
        return run("write", self.repo, lib, "--id", "/pallets/flask", "--project-version", proj,
                   "--doc-version", doc, "--summary-file", summary or self.summary,
                   "--date", date, *extra)

    def entry(self, name="flask.md"):
        return (self.repo / ".specs" / "stack" / name).read_text(encoding="utf-8")

    def test_stack_cache_write_replaces_entry(self):
        code, _, err = self.write()
        self.assertEqual(code, 0, err)
        text = self.entry()
        self.assertIn("# flask\n", text)
        self.assertIn("**Context7 ID**: /pallets/flask\n", text)
        self.assertIn("**Project version**: 3.1.3\n", text)
        self.assertIn("**Doc version**: 3.1.x\n", text)
        self.assertIn("**Fetched**: 2026-11-08\n", text)
        self.assertIn("**Verified**: context7\n", text)
        self.assertIn("## Summary\nlinha 1\nlinha 2", text)
        # second write replaces, never duplicates
        self.summary.write_text("nova\n", encoding="utf-8")
        code, _, err = self.write(proj="3.2.0", doc="3.2.x")
        self.assertEqual(code, 0, err)
        files = list((self.repo / ".specs" / "stack").iterdir())
        self.assertEqual([f.name for f in files], ["flask.md"])
        text = self.entry()
        self.assertEqual(text.count("# flask"), 1)
        self.assertIn("**Project version**: 3.2.0", text)
        self.assertNotIn("linha 1", text)
        self.assertIn("nova", text)

    def test_stack_cache_write_normalizes_name_and_cuts_summary(self):
        self.summary.write_text("\n".join(f"l{i}" for i in range(40)) + "\n", encoding="utf-8")
        code, _, err = self.write(lib="@tauri-apps/api", extra=["--verified", "não verificada (https://tauri.app)"])
        self.assertEqual(code, 0)
        self.assertIn("30", err)
        text = self.entry("tauri-apps-api.md")
        self.assertIn("# @tauri-apps/api\n", text)
        self.assertIn("**Verified**: não verificada (https://tauri.app)", text)
        self.assertIn("l29", text)
        self.assertNotIn("l30", text)

    def test_stack_cache_write_usage_errors(self):
        code, _, _ = run("write", self.repo, "x", "--id", "/a/b")
        self.assertEqual(code, 2)
        code, _, _ = self.write(date="08/11/2026")
        self.assertEqual(code, 2)
        code, _, _ = run("write", self.repo, "x", "--id", "/a/b", "--project-version", "1",
                         "--doc-version", "1", "--summary-file", self.repo / "nao-existe.txt")
        self.assertEqual(code, 2)

    def test_stack_cache_check_states(self):
        self.write("fresh", date="2026-11-01", extra=())
        self.write("old", date="2026-09-01")
        self.write("moved", date="2026-11-01")
        self.write("other", doc="3.0.x", date="2026-11-01")
        self.write("unknown", doc="desconhecida", date="2026-11-01")
        (self.repo / ".starcode").mkdir()
        (self.repo / ".starcode" / "stack.json").write_text(json.dumps({"versions": {
            "fresh": {"version": "3.1.3"}, "old": {"version": "3.1.3"},
            "moved": {"version": "3.2.0"}, "other": {"version": "3.1.3"},
            "unknown": {"version": "3.1.3"}}}), encoding="utf-8")
        code, out, err = run("check", self.repo, "--json", "--today", "2026-11-08")
        self.assertEqual(code, 1, err)
        got = {e["lib"]: e["state"] for e in json.loads(out)}
        self.assertEqual(got, {"fresh": "ok", "old": "velha", "moved": "versão mudou",
                               "other": "outra versão", "unknown": "ok (doc sem versão)"})
        code, out, _ = run("check", self.repo, "--today", "2026-11-08")
        self.assertEqual(code, 1)
        self.assertIn("old: velha", out)

    def test_stack_cache_unknown_doc_version_flow(self):
        self.write(doc="desconhecida", date="2026-11-09")
        code, out, err = run("check", self.repo, "--today", "2026-11-09")
        self.assertEqual((code, out.strip()), (0, "flask: ok (doc sem versão)"), err)
        # 30 dias ainda vale; 31 dias é velha
        code, out, _ = run("check", self.repo, "--today", "2026-12-09")
        self.assertEqual((code, out.strip()), (0, "flask: ok (doc sem versão)"))
        code, out, _ = run("check", self.repo, "--today", "2026-12-10")
        self.assertEqual((code, out.strip()), (1, "flask: velha"))
        # manifesto com outro major
        (self.repo / "pyproject.toml").write_text(
            '[project]\nname="x"\ndependencies = ["flask>=4.0.0"]\n', encoding="utf-8")
        code, out, _ = run("check", self.repo, "--today", "2026-11-09")
        self.assertEqual((code, out.strip()), (1, "flask: versão mudou"))
        (self.repo / "pyproject.toml").unlink()
        self._rejects_non_literal_doc_version()

    def _rejects_non_literal_doc_version(self):
        # só o literal "desconhecida" pula a comparação (achado do Q2, R27)
        import shutil
        stack = self.repo / ".specs" / "stack"
        shutil.rmtree(stack)
        code, _, err = self.write(doc="abc")
        self.assertEqual(code, 2)
        self.assertIn("doc-version inválida: use uma versão (ex.: 3.1) ou desconhecida", err)
        self.assertFalse(stack.exists())
        # entrada escrita à mão com valor sem versão numérica é inválida
        stack.mkdir(parents=True)
        base = ("# flask\n**Context7 ID**: /pallets/flask\n**Project version**: 3.1.3\n"
                "**Doc version**: {}\n**Fetched**: 2026-11-09\n**Verified**: context7\n## Summary\nx\n")
        (stack / "flask.md").write_text(base.format("abc"), encoding="utf-8")
        code, out, _ = run("check", self.repo, "--today", "2026-11-09")
        self.assertEqual((code, out.strip()), (1, "flask: inválida"))
        (stack / "flask.md").write_text(base.format("desconhecida"), encoding="utf-8")
        code, out, _ = run("check", self.repo, "--today", "2026-11-09")
        self.assertEqual((code, out.strip()), (0, "flask: ok (doc sem versão)"))

    def test_stack_cache_check_all_ok_and_manifest(self):
        self.write("flask", date="2026-11-08")
        self.write("vite", proj="8.3.6", doc="8.3.x", date="2026-11-08")
        self.write("tauri", proj="2.12.4", doc="2.12.x", date="2026-11-08")
        (self.repo / "pyproject.toml").write_text(
            '[project]\nname="x"\ndependencies = ["flask>=3.1.3"]\n', encoding="utf-8")
        (self.repo / "package.json").write_text(
            json.dumps({"devDependencies": {"vite": "^8.3.6"}}), encoding="utf-8")
        (self.repo / "Cargo.toml").write_text(
            '[package]\nname="x"\n[dependencies]\ntauri = { version = "2.12", features = [] }\n',
            encoding="utf-8")
        code, out, err = run("check", self.repo, "--today", "2026-11-08")
        self.assertEqual(code, 0, out + err)
        # manifest moves on
        (self.repo / "pyproject.toml").write_text(
            '[project]\nname="x"\ndependencies = ["flask>=3.2.0"]\n', encoding="utf-8")
        code, out, _ = run("check", self.repo, "--today", "2026-11-08")
        self.assertEqual(code, 1)
        self.assertIn("flask: versão mudou", out)

    def test_stack_cache_check_empty_and_bad_repo(self):
        code, _, _ = run("check", self.repo)
        self.assertEqual(code, 0)
        code, _, _ = run("check", self.repo / "nao-existe")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
