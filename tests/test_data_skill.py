"""Content tests for the Data skill: Linear publication without the MCP (R15, R16, R17)."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

SKILL = (ROOT / "skills" / "data" / "SKILL.md").read_text(encoding="utf-8")
PUBLISH = (ROOT / "skills" / "data" / "references" / "linear-publish.md").read_text(encoding="utf-8")


def _section_2b() -> str:
    return PUBLISH.split("## 2b.", 1)[1].split("## Failures", 1)[0]


def _commands(section: str) -> list[str]:
    """Shell commands of the fenced/indented blocks of the section, continuation lines joined."""
    cmds, cur = [], ""
    for raw in section.splitlines():
        if not raw.startswith("        "):
            continue
        line = raw.strip()
        cur = f"{cur} {line}".strip() if cur else line
        if cur.endswith("\\"):
            cur = cur[:-1].rstrip()
            continue
        cmds.append(cur)
        cur = ""
    return cmds


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8",
                          stdin=subprocess.DEVNULL, cwd=cwd)


class DataParentIssueTests(unittest.TestCase):
    def test_data_parent_issue_fallback(self):
        # R15: with linear_mcp unavailable the skill picks the parent-issue path, from capabilities.json
        for text in (SKILL, PUBLISH):
            self.assertIn("linear_mcp.status", text)
            self.assertIn("`unavailable`", text)
            self.assertIn("capabilities.json", text)
        cmds = _commands(_section_2b())
        creates = [c for c in cmds if c.startswith("orca linear create")]
        self.assertEqual(len(creates), 2, creates)
        parent, sub = creates
        self.assertIn('--body-file ".specs/features/<slug>/spec.md"', parent)
        self.assertNotIn("--parent", parent)
        self.assertNotIn("--project", parent)
        self.assertIn("--parent <parent ID>", sub)
        self.assertNotIn("--project", sub)
        self.assertIn('--body-file "<body file>"', sub)
        self.assertLess(cmds.index(parent), cmds.index(sub), "a issue-mãe vem antes das sub-issues")
        # no Project / Document is created on this path
        self.assertIn("No Project and no Document are created", _section_2b())
        self.assertFalse([c for c in cmds if "project" in c.lower() and "create" in c.lower() and "--parent" not in c
                          and "orca linear create" not in c])

    def test_publish_gate_accepts_parent_issue(self):
        # R16: blocks relations, `record` of the ticket IDs only, and `publish` accepting it without a Project
        cmds = _commands(_section_2b())
        relations = [c for c in cmds if c.startswith("orca linear relation add")]
        self.assertEqual(len(relations), 1, relations)
        self.assertIn("--type blocks", relations[0])
        self.assertIn("--related <blocked ID>", relations[0])
        record = next((c for c in cmds if "tasks_export.py" in c and " record " in c), None)
        publish = next((c for c in cmds if "run_gates.py" in c and " publish " in c), None)
        self.assertIsNotNone(record, "falta o `tasks_export.py record`")
        self.assertIsNotNone(publish, "falta o `run_gates.py publish`")
        self.assertLess(cmds.index(record), cmds.index(publish))
        self.assertLess(cmds.index(relations[0]), cmds.index(record))

        with tempfile.TemporaryDirectory(prefix="starcode-data-") as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "tests" / "fixtures" / "gates" / "large", root / "large")
            repo = root / "large"
            gates = ROOT / "scripts" / "gates"

            def build(cmd: str) -> list[str]:
                cmd = cmd.replace("<plugin-root>/scripts/gates/", "").replace("<slug>", "export-csv")
                cmd = cmd.replace("T1=<ID>", "T1=SC-20").replace("T2=<ID>", "T2=SC-21").replace(" ...", "").replace('"', "")
                parts = cmd.split()
                assert parts[0] == "python"
                return [str(gates / parts[1]), *parts[2:], "--root", str(repo)]

            refused = _run(build(publish))  # no IDs recorded yet: the gate refuses
            self.assertEqual(refused.returncode, 1, refused.stdout)
            self.assertIn("VERMELHO", refused.stdout)
            self.assertIn("sem `**Linear**", refused.stdout)

            rec = _run(build(record))
            self.assertEqual(rec.returncode, 0, rec.stdout + rec.stderr)
            tasks = (repo / ".specs" / "features" / "export-csv" / "tasks.md").read_text(encoding="utf-8")
            self.assertIn("**Linear**: SC-20", tasks)
            self.assertIn("**Linear**: SC-21", tasks)
            self.assertNotIn("Project", tasks)
            accepted = _run(build(publish))  # IDs recorded, no Project anywhere: accepted
            self.assertEqual(accepted.returncode, 0, accepted.stdout)
            self.assertIn("VERDE", accepted.stdout)

    def test_data_reports_publish_path(self):
        for text in (SKILL, PUBLISH):
            self.assertIn("Projeto e Documento pelo MCP", text)
            self.assertIn("issue-mãe pelo orca linear, MCP indisponível neste CLI", text)


if __name__ == "__main__":
    unittest.main()
