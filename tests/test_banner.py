"""Banner lines for the execution phase: open breaker and degraded verification (R30, R36)."""
from __future__ import annotations

import unittest
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
        self.assertIn("Disjuntor aberto: task-priority (worker-T2)", text)
        self.assertIn("disjuntor aberto", line)

    def test_banner_shows_degraded_verification(self):
        feat = self.feature()
        handoff.set_handoff("task-priority", self.repo, {"phase": "review"})
        (feat / "verification.md").write_text("# v\n\n**Verification:** self-verified\n", encoding="utf-8")
        text, line, _ = self.build()
        self.assertIn("Verificação: degradada (task-priority)", text)
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


if __name__ == "__main__":
    unittest.main()
