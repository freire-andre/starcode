"""Content tests for the Data skill: Linear publication without the MCP (R15, R16, R17)."""
from __future__ import annotations

import unittest

from helpers import ROOT

SKILL = (ROOT / "skills" / "data" / "SKILL.md").read_text(encoding="utf-8")
PUBLISH = (ROOT / "skills" / "data" / "references" / "linear-publish.md").read_text(encoding="utf-8")


class DataParentIssueTests(unittest.TestCase):
    def test_data_parent_issue_fallback(self):
        for text in (SKILL, PUBLISH):
            self.assertIn("linear_mcp", text)
            self.assertIn("unavailable", text)
            self.assertIn("capabilities.json", text)
        self.assertIn("orca linear create", PUBLISH)
        self.assertIn("--parent", PUBLISH)
        self.assertIn("issue-mãe", PUBLISH)
        self.assertIn("spec.md", PUBLISH)
        self.assertIn("sub-issue", PUBLISH)

    def test_publish_gate_accepts_parent_issue(self):
        section = PUBLISH.split("## 2b.", 1)[1]
        self.assertIn("--type blocks", section)
        self.assertIn("tasks_export.py", section)
        self.assertIn("record", section)
        self.assertIn("run_gates.py", section)
        self.assertIn("Projeto", section)  # the gate accepts the parent issue instead of a Project

    def test_data_reports_publish_path(self):
        for text in (SKILL, PUBLISH):
            self.assertIn("Projeto e Documento pelo MCP", text)
            self.assertIn("issue-mãe pelo orca linear, MCP indisponível neste CLI", text)


if __name__ == "__main__":
    unittest.main()
