"""Tests for scripts/crew_live.py (F6-6 header, F6-7 crew status, F6-8 progress)."""
from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import tempfile
from pathlib import Path

from helpers import FIXTURES, ROOT, TempRepoCase, run_git
import crew_live

CREW_SKILLS = {"picard": "engajar", "troi": "troi", "spock": "spock", "data": "data", "laforge": "laforge",
               "mccoy": "mccoy", "q": "q"}


class CrewLiveTest(TempRepoCase):
    def run_cli(self, *args: str, cwd: Path | None = None) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = crew_live.main(["--cwd", str(cwd or self.repo), *args])
        return code, out.getvalue(), err.getvalue()

    def crew(self) -> dict:
        return json.loads((self.repo / ".starcode" / "live" / "crew.json").read_text(encoding="utf-8"))

    def progress(self) -> dict:
        return json.loads((self.repo / ".starcode" / "live" / "progress.json").read_text(encoding="utf-8"))

    # F6-6 / F6-7 ---------------------------------------------------------------------------

    def test_start_prints_header_and_marks_working(self):
        code, out, _ = self.run_cli("start", "spock", "--mission", "export-csv")
        self.assertEqual(code, 0)
        self.assertIn("SPOCK ASSUME A PONTE", out)
        self.assertIn("Spec e arquitetura", out)
        self.assertIn("Missão: export-csv", out)
        self.assertIn("Fascinante.", out)
        self.assertTrue(all(line.startswith(">") for line in out.strip().splitlines()))
        self.assertEqual(self.crew()["spock"], 1)

    def test_status_file_is_flat_zero_or_one_for_the_whole_crew(self):
        self.run_cli("start", "picard")
        self.run_cli("set", "laforge", "1")
        code, out, _ = self.run_cli("stop", "picard")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "Picard: parado")
        data = self.crew()
        self.assertTrue(set(CREW_SKILLS) <= set(data))
        self.assertTrue(all(v in (0, 1) for v in data.values()))
        self.assertEqual((data["picard"], data["laforge"], data["spock"]), (0, 1, 0))
        self.run_cli("reset")
        self.assertEqual(set(self.crew().values()), {0})

    def test_live_folder_ignores_itself_in_git(self):
        self.run_cli("start", "picard")
        self.assertEqual(run_git(self.repo, "status", "--porcelain"), "")

    def test_linked_worktree_writes_to_the_main_worktree(self):
        wt = self.tmp / "wt-child"
        run_git(self.repo, "worktree", "add", "-q", "-b", "child", str(wt))
        code, _, _ = self.run_cli("set", "laforge", "1", cwd=wt)
        self.assertEqual(code, 0)
        self.assertEqual(self.crew()["laforge"], 1)
        self.assertFalse((wt / ".starcode" / "live").exists())

    def test_unknown_member_and_outside_git(self):
        code, _, err = self.run_cli("start", "kirk-x")
        self.assertEqual(code, 1)
        self.assertIn("desconhecido", err)
        outside = Path(tempfile.mkdtemp(prefix="starcode-nogit-"))
        try:
            code, _, _ = self.run_cli("start", "picard", cwd=outside)
        finally:
            shutil.rmtree(outside, ignore_errors=True)
        self.assertEqual(code, 1)

    # F6-8 ----------------------------------------------------------------------------------

    def test_progress_explicit_counts_and_done_phase(self):
        code, out, _ = self.run_cli("progress", "dark-mode", "--done", "0", "--total", "1", "--phase", "execute")
        self.assertEqual(code, 0)
        entry = self.progress()["dark-mode"]
        self.assertTrue(entry.pop("updatedAt"))
        self.assertEqual(entry, {"done": 0, "total": 1, "percent": 0, "phase": "execute"})
        self.run_cli("progress", "export-csv", "--done", "2", "--total", "3")
        self.assertEqual(self.progress()["export-csv"]["percent"], 67)
        self.run_cli("progress", "export-csv", "--done", "2", "--total", "3", "--phase", "done")
        self.assertEqual(self.progress()["export-csv"]["percent"], 100)
        self.assertIn("dark-mode", self.progress())  # other features are kept

    def test_progress_counts_integrated_tickets_from_git(self):
        self.write_repo_config("main")
        src = FIXTURES / "gates" / "large" / ".specs" / "features" / "export-csv"
        dest = self.repo / ".specs" / "features" / "export-csv"
        shutil.copytree(src, dest)
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "docs(specs): tasks")
        run_git(self.repo, "branch", "feature/export-csv")
        code, out, err = self.run_cli("progress", "export-csv", "--root", str(self.repo))
        self.assertEqual(code, 0, err)
        total = self.progress()["export-csv"]["total"]
        self.assertGreaterEqual(total, 2)
        self.assertEqual(self.progress()["export-csv"]["done"], 0)
        run_git(self.repo, "checkout", "-q", "feature/export-csv")
        run_git(self.repo, "commit", "-q", "--allow-empty", "-m", "merge: integra T1 em feature/export-csv")
        run_git(self.repo, "checkout", "-q", "main")
        _, out, _ = self.run_cli("progress", "export-csv", "--root", str(self.repo))
        entry = self.progress()["export-csv"]
        self.assertEqual(entry["done"], 1)
        self.assertEqual(entry["percent"], round(100 / total))
        self.assertIn(f"1/{total}", out)

    def test_progress_without_tasks_needs_total(self):
        code, _, err = self.run_cli("progress", "no-such-feature", "--root", str(self.repo))
        self.assertEqual(code, 1)
        self.assertIn("--total", err)
        code, _, _ = self.run_cli("progress", "Bad Slug", "--done", "1", "--total", "1")
        self.assertEqual(code, 2)


class CrewLiveContractTest(TempRepoCase):
    def test_every_crew_skill_opens_with_the_header_and_stops(self):
        for member, skill in CREW_SKILLS.items():
            text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertRegex(text, rf"crew_live\.py\" start {member}\b", skill)
            self.assertRegex(text, rf"crew_live\.py\" stop {member}\b", skill)

    def test_execute_marks_workers_and_progress(self):
        text = (ROOT / "skills" / "engajar" / "references" / "execute.md").read_text(encoding="utf-8")
        for needle in ("set laforge 1", "set laforge 0", "set q 1", "progress <slug> --phase done"):
            self.assertIn(needle, text)
        self.assertTrue(re.search(r"crew_live\.py\" progress <slug>` \(counts", text))
