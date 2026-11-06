import re
import unittest

from helpers import TempRepoCase, run_git

import check_decisions as cd


class CheckDecisionsTests(TempRepoCase):
    def commit(self, path, text, msg):
        f = self.repo / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        run_git(self.repo, "add", path)
        run_git(self.repo, "commit", "-q", "-m", msg)

    def test_flow(self):
        self.commit("DECISIONS.md", "# d\n", "decisions")
        self.assertEqual(cd.check(self.repo)[0], 0)
        self.commit("skills/x/SKILL.md", "x\n", "skill")
        code, msg = cd.check(self.repo)
        self.assertEqual(code, 1)
        self.assertIn("FALHOU", msg)
        self.commit("DECISIONS.md", "# d\n- F1\n", "decision for skill")
        self.assertEqual(cd.check(self.repo)[0], 0)

    def test_same_commit_ok(self):
        (self.repo / "DECISIONS.md").write_text("# d\n", encoding="utf-8")
        (self.repo / "hooks").mkdir()
        (self.repo / "hooks" / "h.py").write_text("x\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "both")
        self.assertEqual(cd.check(self.repo)[0], 0)

    def test_dirty_watched_without_decisions_fails(self):
        self.commit("DECISIONS.md", "# d\n", "decisions")
        (self.repo / "scripts").mkdir()
        (self.repo / "scripts" / "a.py").write_text("x\n", encoding="utf-8")
        self.assertEqual(cd.check(self.repo)[0], 1)
        (self.repo / "DECISIONS.md").write_text("# d\n- new\n", encoding="utf-8")
        self.assertEqual(cd.check(self.repo)[0], 0)

    def test_missing_file(self):
        self.assertEqual(cd.check(self.repo)[0], 2)


    def test_decisions_f6_1_sandbox_mission_day(self):
        from helpers import ROOT
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        m = re.search(r"^### F6-1: .*\n(.*?)(?=^### |\Z)", text, re.M | re.S)
        self.assertIsNotNone(m, "DECISIONS.md sem F6-1")
        for needle in ("starcode-sandbox", "projeto real", "2026-11-06", "Por que não é bug"):
            self.assertIn(needle, m.group(0))


if __name__ == "__main__":
    unittest.main()
