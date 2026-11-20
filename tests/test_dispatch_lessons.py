"""Tests for the `## Lessons` section in dispatch briefs (R25, C23, C24)."""
from __future__ import annotations

import contextlib
import io
import json
import unittest

from helpers import TempRepoCase, run_git

import dispatch
from test_dispatch import TASKS


def lesson(n: int, status: str = "confirmed", updated: str | None = None) -> dict:
    return {"id": f"L{n}", "text": f"texto {n}", "signal": "gate_fail", "status": status,
            "features": [], "sources": [], "scope": "", "created": "2026-01-01",
            "updated": updated or f"2026-02-{n:02d}"}


class DispatchLessonsTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_repo_config()
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        (fdir / "tasks.md").write_text(TASKS, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "specs")

    def briefs(self) -> tuple[str, str]:
        return (dispatch.worker_brief("demo", "T2", self.repo),
                dispatch.q_brief("demo", self.repo, "main", "abc1234"))

    def store(self, content) -> None:
        text = content if isinstance(content, str) else json.dumps({"lessons": content})
        (self.repo / ".specs" / "lessons.json").write_text(text, encoding="utf-8")

    def test_briefs_include_up_to_ten_confirmed_lessons(self):
        self.store([lesson(n) for n in range(1, 13)] + [lesson(20, "candidate"), lesson(21, "quarantined")])
        for text in self.briefs():
            self.assertEqual(text.count("## Lessons"), 1)
            sec = text.split("## Lessons")[1].split("\n## ")[0]
            lines = [ln for ln in sec.splitlines() if ln.startswith("- ")]
            self.assertEqual(lines, [f"- L{n}: texto {n}" for n in range(12, 2, -1)])
        worker, q = self.briefs()
        self.assertTrue(q.rstrip().endswith("- L3: texto 3"))
        self.assertLess(worker.index("## Lessons"), worker.index("## Regras fixas do worker (StarCode)"))

    def test_briefs_unchanged_without_confirmed_lessons(self):
        base = self.briefs()
        self.store([lesson(1, "candidate"), lesson(2, "quarantined")])
        self.assertEqual(self.briefs(), base)
        self.store("{não é json")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(self.briefs(), base)
        self.assertEqual(len(err.getvalue().strip().splitlines()), 2)
        self.assertIn("lessons.json", err.getvalue())
        for text in base:
            self.assertNotIn("## Lessons", text)


if __name__ == "__main__":
    unittest.main()
