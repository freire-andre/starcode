"""Tests for scripts/handoff.py (F2-10)."""
from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401  (sys.path)
import handoff


class HandoffTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-handoff-")
        self.root = Path(self._tmp.name)
        self.feat = self.root / ".specs" / "features" / "dark-mode"
        self.feat.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = handoff.main([*args, "--root", str(self.root)])
        return code, out.getvalue()

    def test_creates_section_with_defaults_and_prints_one_line(self):
        (self.feat / "context.md").write_text("# Dark mode: Context\n\n## Problem\nx\n", encoding="utf-8")
        code, out = self.run_cli("set", "dark-mode", "--phase", "discovery", "--next", "Spock escreve a spec")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 1)
        text = (self.feat / "context.md").read_text(encoding="utf-8")
        self.assertIn("## Problem\nx\n\n## Handoff\n", text)
        self.assertIn("**Phase:** discovery", text)
        self.assertIn("**Breaker:** closed", text)
        self.assertIn("**Next:** Spock escreve a spec", text)

    def test_moves_to_most_advanced_artifact_and_keeps_fields(self):
        (self.feat / "context.md").write_text("# C\n", encoding="utf-8")
        self.run_cli("set", "dark-mode", "--phase", "discovery", "--git-mode", "2", "--size", "MEDIUM")
        (self.feat / "spec.md").write_text("# Spec\n\n## Context\ny\n", encoding="utf-8")
        code, _ = self.run_cli("set", "dark-mode", "--phase", "spec")
        self.assertEqual(code, 0)
        ctx = (self.feat / "context.md").read_text(encoding="utf-8")
        spec = (self.feat / "spec.md").read_text(encoding="utf-8")
        self.assertNotIn("## Handoff", ctx)
        self.assertEqual(spec.count("## Handoff"), 1)
        self.assertIn("**Phase:** spec", spec)
        self.assertIn("**Git mode:** 2", spec)
        self.assertIn("**Size:** MEDIUM", spec)

    def test_section_in_the_middle_is_replaced_in_place_of_appending_twice(self):
        (self.feat / "spec.md").write_text(
            "# S\n\n## Handoff\n\n**Phase:** spec\n**Next:** a\n\n## Requirements\n- R1 - x\n", encoding="utf-8")
        self.run_cli("set", "dark-mode", "--next", "b")
        text = (self.feat / "spec.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("## Handoff"), 1)
        self.assertIn("## Requirements\n- R1 - x", text)
        self.assertIn("**Next:** b", text)
        self.assertIn("**Phase:** spec", text)

    def test_settle_appends_dated_entries(self):
        (self.feat / "spec.md").write_text("# S\n", encoding="utf-8")
        target, values = handoff.set_handoff("dark-mode", self.root, {}, settle="usar tema do sistema",
                                             today="2026-11-04")
        target, values = handoff.set_handoff("dark-mode", self.root, {}, settle="sem toggle", today="2026-11-05")
        self.assertEqual(values["settled"], "2026-11-04: usar tema do sistema; 2026-11-05: sem toggle")

    def test_handoff_inside_code_fence_is_ignored(self):
        (self.feat / "spec.md").write_text("# S\n\n```\n## Handoff\n**Phase:** done\n```\n", encoding="utf-8")
        self.run_cli("set", "dark-mode", "--phase", "spec")
        text = (self.feat / "spec.md").read_text(encoding="utf-8")
        self.assertIn("```\n## Handoff\n**Phase:** done\n```", text)
        self.assertIn("\n## Handoff\n\n**Phase:** spec", text)

    def test_invalid_phase_and_missing_feature(self):
        (self.feat / "spec.md").write_text("# S\n", encoding="utf-8")
        self.assertEqual(self.run_cli("set", "dark-mode", "--phase", "pronto")[0], 2)
        self.assertEqual(self.run_cli("set", "nao-existe", "--phase", "spec")[0], 1)

    def test_banner_reads_what_handoff_writes(self):
        import banner
        (self.feat / "spec.md").write_text("# S\n", encoding="utf-8")
        self.run_cli("set", "dark-mode", "--phase", "spec", "--breaker", "open (E1, attempts 3/3)")
        wip, _, breaker = banner.work_in_progress(self.root)
        self.assertTrue(any("dark-mode" in w for w in wip))
        self.assertTrue(any("dark-mode" in b for b in breaker))

    def tasks(self) -> None:
        (self.feat / "tasks.md").write_text("# Dark mode: Tasks\n\n## Tasks\n", encoding="utf-8")

    def test_handoff_execution_fields(self):
        self.tasks()
        code, _ = self.run_cli("set", "dark-mode", "--phase", "execute", "--integration-branch", "feature/dark-mode",
                               "--dispatched", "T1 · SC-7 · base abc1234 · dispatch d-1 · model claude-sonnet-5-5")
        self.assertEqual(code, 0)
        self.run_cli("set", "dark-mode", "--last-integrated", "def5678", "--report", "T1: 2 arquivos, gates verdes")
        self.run_cli("set", "dark-mode", "--report", "T2: 1 arquivo")
        text = (self.feat / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("**Integration branch:** feature/dark-mode", text)
        self.assertIn("**Dispatched:** T1 · SC-7 · base abc1234 · dispatch d-1", text)
        self.assertIn("**Last integrated:** def5678", text)
        self.assertRegex(text, r"\*\*Reports:\*\* \d{4}-\d{2}-\d{2}: T1: 2 arquivos, gates verdes; \d{4}-\d{2}-\d{2}: T2: 1 arquivo")
        self.assertIn("**Phase:** execute", text)  # fields not passed are kept

    def test_attempts_count_and_reset(self):
        self.tasks()
        self.run_cli("set", "dark-mode", "--attempt", "gate-T1=fail")
        self.run_cli("set", "dark-mode", "--attempt", "gate-T1=fail")
        self.run_cli("set", "dark-mode", "--attempt", "worker-T2=fail")
        text = (self.feat / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("**Attempts:** gate-T1=2, worker-T2=1", text)
        self.run_cli("set", "dark-mode", "--attempt", "gate-T1=ok")
        text = (self.feat / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("**Attempts:** worker-T2=1", text)
        self.assertIn("**Breaker:** closed", text)
        code, _ = self.run_cli("set", "dark-mode", "--attempt", "gate-T1")
        self.assertEqual(code, 2)

    def test_third_failure_opens_breaker(self):
        self.tasks()
        for _ in range(2):
            self.run_cli("set", "dark-mode", "--attempt", "gate-T1=fail")
        code, out = self.run_cli("set", "dark-mode", "--attempt", "gate-T1=fail")
        self.assertEqual(code, 0)
        self.assertIn("DISJUNTOR ABERTO", out)
        text = (self.feat / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("**Breaker:** open (gate-T1, attempts 3/3)", text)
        self.run_cli("set", "dark-mode", "--breaker", "closed", "--attempt", "gate-T1=ok")
        text = (self.feat / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("**Breaker:** closed", text)


if __name__ == "__main__":
    unittest.main()
