"""Content tests for the Uhura skill, its templates and the execute.md wiring (R28, R29, R30)."""
from __future__ import annotations

import unittest
from pathlib import Path

from helpers import ROOT
from test_support import execute_text

CLIS = ("claude", "codex", "antigravity", "opencode")
EXEC_HEAD = "## Text for the PR and the Linear comments (Uhura)"


def _roots() -> list[Path]:
    return [ROOT] + [ROOT / "dist" / cli for cli in CLIS]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


class UhuraSkillTests(unittest.TestCase):
    def test_uhura_skill_context7_protocol(self):
        # R28, in the source and in the 4 CLIs
        for root in _roots():
            text = _read(root, "skills/uhura/SKILL.md")
            self.assertTrue(text.startswith("---\nname: uhura\n"), root)
            self.assertIn("description:", text.split("---", 2)[1])
            for needle in ("resolve-library-id", "query-docs", "stack_cache.py\" write", "stack_cache.py\" check",
                           "`main: true`", "não verificada", "--verified", "Never from Context7",
                           "crew_live.py", "references/pr-body.md", "references/linear-comments.md"):
                self.assertIn(needle, text, f"{root}: {needle}")
            self.assertRegex(text, r"(?i)\*\*bootstrap")
            self.assertRegex(text, r"(?i)\*\*on demand")
            self.assertRegex(text, r"(?i)\*\*refresh")
            self.assertRegex(text, r"(?i)\*\*only\*\*")

    def test_uhura_pr_and_comment_templates(self):
        # R29
        for root in _roots():
            pr = _read(root, "skills/uhura/references/pr-body.md")
            sections = [l for l in pr.splitlines() if l.startswith("## ")]
            self.assertEqual(sections, ["## Resumo", "## Issue", "## Mudanças", "## Gates",
                                        "## Verificação do Q", "## Riscos"], root)
            comments = _read(root, "skills/uhura/references/linear-comments.md")
            models = [l for l in comments.splitlines() if l.startswith("## ")]
            self.assertEqual(models, ["## Início", "## Integrado", "## Bloqueado", "## Cancelado",
                                      "## Concluído"], root)

    def test_execute_uses_uhura_for_pr_and_comments(self):
        # R30
        for root in _roots():
            text = execute_text(root)
            self.assertIn(EXEC_HEAD, text)
            sec = text.split(EXEC_HEAD, 1)[1].split("\n## ", 1)[0]
            for needle in ("`uhura`", "subagent", "Uhura's model", "the session itself follows the skill",
                           "gh pr create", "orca linear comment", "you confirm"):
                self.assertIn(needle, sec, f"{root}: {needle}")
            ctx = _read(root, "src/context/STARCODE.md" if root == ROOT else "context/STARCODE.md")
            c7 = ctx.split("Context7 is the source", 1)[1].split("\n- Issue text", 1)[0]
            self.assertIn("`uhura`", c7)


if __name__ == "__main__":
    unittest.main()
