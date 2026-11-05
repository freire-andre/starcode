"""Banner lines for the execution phase: open breaker and degraded verification (R30, R36)."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import TempRepoCase

import banner
import handoff


class BannerExecutionTests(TempRepoCase):
    def build(self):
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]):
            return banner.build_banner(str(self.repo), False)

    def feature(self, slug: str = "task-priority"):
        self.write_repo_config()
        feat = self.repo / ".specs" / "features" / slug
        feat.mkdir(parents=True)
        (feat / "tasks.md").write_text("# Tasks\n", encoding="utf-8")
        return feat

    def test_banner_shows_open_breaker(self):
        self.feature()
        for _ in range(3):
            handoff.set_handoff("task-priority", self.repo, {"phase": "execute"}, attempt="worker-T2=fail")
        text, line, _ = self.build()
        self.assertIn("\n⚠️ Disjuntor aberto: task-priority (worker-T2)\n", "\n" + text + "\n")
        self.assertIn("disjuntor aberto", line)

    def test_banner_shows_degraded_verification(self):
        feat = self.feature()
        handoff.set_handoff("task-priority", self.repo, {"phase": "review"})
        (feat / "verification.md").write_text("# v\n\n**Verification:** self-verified\n", encoding="utf-8")
        text, line, _ = self.build()
        self.assertIn("\n⚠️ Verificação: degradada (task-priority)\n", "\n" + text + "\n")
        self.assertIn("verificação degradada", line)

    def test_banner_shows_degraded_verification_marker(self):
        # C14/R30: the `**Verification:** degraded (<reason>)` marker counts as much as `self-verified`.
        feat = self.feature()
        handoff.set_handoff("task-priority", self.repo, {"phase": "review"})
        (feat / "verification.md").write_text(
            "# v\n\n**Verification:** degraded (Q na mesma família: claude)\n", encoding="utf-8")
        text, line, _ = self.build()
        self.assertIn("\n⚠️ Verificação: degradada (task-priority)\n", "\n" + text + "\n")
        self.assertIn("verificação degradada", line)

    def test_no_breaker_line_when_closed(self):
        self.feature()
        handoff.set_handoff("task-priority", self.repo, {"phase": "execute"}, attempt="worker-T2=fail")
        text, _, _ = self.build()
        self.assertNotIn("Disjuntor aberto", text)

    def test_markers_in_prose_before_handoff_are_ignored(self):
        # tasks.md prose may quote `## Handoff`, `**Phase:**` and `**Breaker:** open (<id>)`;
        # only the real `## Handoff` heading section counts.
        feat = self.feature()
        (feat / "tasks.md").write_text(
            "# Tasks\n\nNunca altere a seção `## Handoff`; o banner lê `**Phase:**` e "
            "`**Breaker:** open (<id>)`.\n", encoding="utf-8")
        handoff.set_handoff("task-priority", self.repo, {"phase": "execute"})
        text, _, _ = self.build()
        self.assertIn("task-priority (fase: execute)", text)
        self.assertNotIn("Disjuntor aberto", text)


class BannerDegradedMarkerTests(BannerExecutionTests):
    def test_table_citing_self_verified_is_not_degraded(self):
        # C8/R5: a table row that merely mentions `self-verified` is not the marker.
        feat = self.feature()
        handoff.set_handoff("task-priority", self.repo, {"phase": "review"})
        (feat / "verification.md").write_text(
            "# v\n\n**Verification:** independent\n\n| C1 | self-verified? | no |\n"
            "Texto com **Verification:** degraded no meio da linha.\n", encoding="utf-8")
        text, line, _ = self.build()
        self.assertNotIn("Verificação: degradada", text)
        self.assertNotIn("verificação degradada", line)


class BannerCliTests(TempRepoCase):
    def build(self, cli, plugin_root):
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]), \
             mock.patch.object(banner.sc, "PLUGIN_ROOT", plugin_root):
            return banner.build_banner(str(self.repo), False, cli)[0]

    def plugin(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def lines(self, text):
        return text.split("\n")

    def test_cli_line_and_unavailable_extras_from_json(self):
        root = self.plugin()
        (root / "capabilities.json").write_text(json.dumps({"schemaVersion": 1, "cli": "codex", "extras": {
            "hooks": {"status": "unavailable", "fallback": "Fase 5"},
            "orca_worker": {"status": "ok"}}}), encoding="utf-8")
        lines = self.lines(self.build("codex", root))
        self.assertIn("CLI: codex", lines)
        self.assertIn("Indisponível neste CLI: hooks → Fase 5", lines)
        self.assertFalse(any("orca_worker" in l for l in lines))

    def test_without_cli_no_cli_line(self):
        text = self.build(None, self.plugin())
        self.assertNotIn("CLI:", text)
        self.assertNotIn("Indisponível", text)

    def test_falls_back_to_source_yaml(self):
        # C7/R4: no capabilities.json beside the plugin -> src/capabilities.yaml (that CLI's section).
        real = Path(__file__).resolve().parent.parent
        root = self.plugin()
        (root / "src").mkdir()
        shutil.copy(real / "src" / "capabilities.yaml", root / "src" / "capabilities.yaml")
        (root / "tools").mkdir()
        shutil.copy(real / "tools" / "miniyaml.py", root / "tools" / "miniyaml.py")
        lines = self.lines(self.build("codex", root))
        self.assertIn("Indisponível neste CLI: linear_mcp → issue-mãe pelo orca linear", lines)
        self.assertFalse(any("orca_worker" in l for l in lines))

    def test_claude_lists_nothing_unavailable(self):
        root = self.plugin()
        (root / "capabilities.json").write_text(json.dumps({"schemaVersion": 1, "cli": "claude", "extras": {
            "hooks": {"status": "ok"}}}), encoding="utf-8")
        text = self.build("claude", root)
        self.assertIn("CLI: claude", self.lines(text))
        self.assertNotIn("Indisponível", text)


if __name__ == "__main__":
    unittest.main()
