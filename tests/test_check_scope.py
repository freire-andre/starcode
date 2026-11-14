"""Tests for scripts/gates/check_scope.py (R6, R38)."""
from __future__ import annotations

import unittest
from pathlib import Path

from helpers import TempRepoCase, run_git

import check_scope

TASKS = """# Demo: Tasks

## Tasks

### T1: Store
**Depends on**: none
**Linear**: PROJ-7

#### BOUNDARIES
May change: `app/store.py`, `tests/`, `docs/*.md`

## Handoff

**Phase:** execute
"""


class CheckScopeTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.fdir = self.repo / ".specs" / "features" / "demo"
        self.fdir.mkdir(parents=True)
        (self.fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        (self.fdir / "tasks.md").write_text(TASKS, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "specs")
        self.base = run_git(self.repo, "rev-parse", "HEAD")

    def commit(self, files: dict[str, str]) -> str:
        for rel, text in files.items():
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feat: x\n\nRefs: PROJ-7")
        return run_git(self.repo, "rev-parse", "HEAD")

    def test_in_scope_passes(self):
        head = self.commit({"app/store.py": "x\n", "tests/test_store.py": "y\n", "docs/uso.md": "z\n"})
        res = check_scope.evaluate("demo", "T1", f"{self.base}..{head}", self.repo)
        self.assertTrue(res.ok, res.report())
        by_id = check_scope.evaluate("demo", "PROJ-7", f"{self.base}..{head}", self.repo)
        self.assertTrue(by_id.ok, by_id.report())

    def test_check_scope_flags_outside_may_change(self):
        head = self.commit({"app/store.py": "x\n", "app/cli.py": "y\n", "docs/sub/a.md": "z\n"})
        res = check_scope.evaluate("demo", "T1", f"{self.base}..{head}", self.repo)
        errs = "\n".join(res.errors)
        self.assertIn("app/cli.py: fora do `May change`", errs)
        self.assertNotIn("app/store.py: fora", errs)

    def test_check_scope_flags_state_and_handoff(self):
        new_tasks = TASKS.replace("**Phase:** execute", "**Phase:** done")
        head = self.commit({".specs/STATE.md": "AD-001\n", ".specs/features/demo/tasks.md": new_tasks})
        res = check_scope.evaluate("demo", "T1", f"{self.base}..{head}", self.repo)
        errs = "\n".join(res.errors)
        self.assertIn("`.specs/STATE.md` alterado", errs)
        self.assertIn("`## Handoff` alterado em .specs/features/demo/tasks.md", errs)

    def test_directory_entry_with_trailing_slash(self):
        # C7/R6: `May change: app/` allows files under app/ and refuses a sibling that only shares the prefix.
        (self.fdir / "tasks.md").write_text(TASKS.replace("`app/store.py`, `tests/`, `docs/*.md`", "`app/`"),
                                            encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "scope")
        base = run_git(self.repo, "rev-parse", "HEAD")
        head = self.commit({"app/child.py": "x\n", "apps/x.py": "y\n"})
        res = check_scope.evaluate("demo", "T1", f"{base}..{head}", self.repo)
        errs = "\n".join(res.errors)
        self.assertIn("apps/x.py: fora do `May change`", errs)
        self.assertNotIn("app/child.py: fora", errs)

    def test_no_commit_is_an_error(self):
        res = check_scope.evaluate("demo", "T1", f"{self.base}..{self.base}", self.repo)
        self.assertTrue(any("nenhum commit" in e for e in res.errors), res.report())

    def test_unknown_ticket_is_usage_error(self):
        res = check_scope.evaluate("demo", "T9", f"{self.base}..HEAD", self.repo)
        self.assertTrue(res.usage_error)


    def set_may_change(self, value: str) -> str:
        (self.fdir / "tasks.md").write_text(TASKS.replace("`app/store.py`, `tests/`, `docs/*.md`", value),
                                            encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "scope")
        return run_git(self.repo, "rev-parse", "HEAD")

    def test_scope_aceita_decisions_com_scripts(self):
        base = self.set_may_change("`scripts/x.py`")
        head = self.commit({"scripts/x.py": "x" + chr(10), "DECISIONS.md": "d" + chr(10)})
        res = check_scope.evaluate("demo", "T1", f"{base}..{head}", self.repo)
        self.assertEqual(res.errors, [])
        head2 = self.commit({"README.md": "r" + chr(10), "DECISIONS.md": "e" + chr(10)})
        res2 = check_scope.evaluate("demo", "T1", f"{head}..{head2}", self.repo)
        self.assertEqual(res2.errors,
                         ["README.md: fora do `May change` de T1 (scripts/x.py, DECISIONS.md)"])

    def test_scope_media_aceita_decisions(self):
        fdir = self.repo / ".specs" / "features" / "media"
        fdir.mkdir(parents=True)
        spec = "# Média: Spec" + chr(10) + chr(10) + "**Linear**: PROJ-9" + chr(10) + "**May change**: scripts/x.py" + chr(10)
        (fdir / "spec.md").write_text(spec, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "media")
        base = run_git(self.repo, "rev-parse", "HEAD")
        head = self.commit({"scripts/x.py": "x" + chr(10), "DECISIONS.md": "d" + chr(10)})
        res = check_scope.evaluate("media", "T1", f"{base}..{head}", self.repo)
        self.assertEqual(res.errors, [])
        head2 = self.commit({"README.md": "r" + chr(10)})
        res2 = check_scope.evaluate("media", "PROJ-9", f"{head}..{head2}", self.repo)
        self.assertEqual(res2.errors,
                         ["README.md: fora do `May change` de PROJ-9 (scripts/x.py, DECISIONS.md)"])


if __name__ == "__main__":
    unittest.main()
