"""Tests for scripts/statusline.py (F6-9): active crew + gradient progress bar."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from helpers import TempRepoCase, run_git
import statusline

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def plain(s: str) -> str:
    return ANSI.sub("", s)


class GradientTest(TempRepoCase):
    def test_stops_are_the_requested_colors(self):
        self.assertEqual(statusline.gradient(0), (0xC5, 0xDB, 0xFF))
        self.assertEqual(statusline.gradient(50), (0x75, 0xC3, 0xFF))
        self.assertEqual(statusline.gradient(100), (0x00, 0x28, 0xB3))
        self.assertEqual(statusline.gradient(-5), statusline.gradient(0))
        self.assertEqual(statusline.gradient(150), statusline.gradient(100))

    def test_gradient_darkens_monotonically(self):
        sums = [sum(statusline.gradient(p)) for p in range(0, 101, 5)]
        self.assertEqual(sums, sorted(sums, reverse=True))

    def test_bar_cells_and_tip_color(self):
        b = statusline.bar(40)
        self.assertEqual(plain(b), "████░░░░░░ 40%")
        self.assertIn("\x1b[38;2;0;40;179m", statusline.bar(100))  # last cell = #0028B3
        self.assertNotIn("░", plain(statusline.bar(100)))
        self.assertEqual(plain(statusline.bar(0)), "░░░░░░░░░░ 0%")


class SegmentTest(TempRepoCase):
    def live(self, crew: dict | None = None, progress: dict | None = None):
        d = self.repo / ".starcode" / "live"
        d.mkdir(parents=True, exist_ok=True)
        if crew is not None:
            (d / "crew.json").write_text(json.dumps(crew), encoding="utf-8")
        if progress is not None:
            (d / "progress.json").write_text(json.dumps(progress), encoding="utf-8")

    def iso(self, delta: timedelta = timedelta()) -> str:
        return (datetime.now(timezone.utc) - delta).isoformat()

    def test_nothing_without_live_folder_or_outside_git(self):
        self.assertEqual(statusline.segment(str(self.repo)), "")
        self.assertEqual(statusline.segment(str(self.tmp)), "")

    def test_active_members_and_most_recent_running_feature(self):
        self.live({"picard": 1, "spock": 0, "laforge": 1},
                  {"old": {"done": 1, "total": 4, "percent": 25, "phase": "execute",
                           "updatedAt": self.iso(timedelta(hours=2))},
                   "export-csv": {"done": 2, "total": 5, "percent": 40, "phase": "execute",
                                  "updatedAt": self.iso()}})
        out = plain(statusline.segment(str(self.repo)))
        self.assertIn("Picard", out)
        self.assertIn("LaForge", out)
        self.assertNotIn("Spock", out)
        self.assertIn("export-csv ████░░░░░░ 40% 2/5", out)
        self.assertNotIn("old", out)

    def test_linked_worktree_reads_main_worktree_files(self):
        self.live({"q": 1}, {})
        wt = self.tmp / "wt"
        run_git(self.repo, "worktree", "add", "-q", "-b", "x", str(wt))
        self.assertIn("Q", plain(statusline.segment(str(wt))))

    def test_done_feature_shows_for_a_while_then_disappears(self):
        self.live({"picard": 0}, {"f": {"done": 3, "total": 3, "percent": 100, "phase": "done",
                                        "updatedAt": self.iso(timedelta(hours=1))}})
        out = plain(statusline.segment(str(self.repo)))
        self.assertIn("em espera", out)
        self.assertIn("f ██████████ 100% 3/3", out)
        self.live(progress={"f": {"done": 3, "total": 3, "percent": 100, "phase": "done",
                                  "updatedAt": self.iso(timedelta(days=2))}})
        self.assertEqual(statusline.segment(str(self.repo)), "")

    def test_corrupt_files_never_break(self):
        d = self.repo / ".starcode" / "live"
        d.mkdir(parents=True)
        (d / "crew.json").write_text("{not json", encoding="utf-8")
        (d / "progress.json").write_text("[1,2]", encoding="utf-8")
        self.assertEqual(statusline.segment(str(self.repo)), "")
