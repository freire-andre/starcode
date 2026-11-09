"""Tests for scripts/review/scan_bypasses.py (R1, R2)."""
from __future__ import annotations

import subprocess
import sys
import unittest

from helpers import FIXTURES, ROOT

SCRIPT = ROOT / "scripts" / "review" / "scan_bypasses.py"
REVIEW = FIXTURES / "review"


def scan(data: bytes = b"", *args: str):
    res = subprocess.run([sys.executable, "-I", str(SCRIPT), *args], input=data, capture_output=True)
    return res.returncode, res.stdout.decode("utf-8"), res.stderr.decode("utf-8")


class ScanBypassesTests(unittest.TestCase):
    def test_scan_reports_each_category_with_new_line_number(self) -> None:
        code, out, err = scan((REVIEW / "categories.diff").read_bytes())
        self.assertEqual(code, 0)
        rows = [r.split("\t") for r in out.splitlines()]
        got = {(r[0], r[1]) for r in rows}
        expected = {
            ("src/app.ts:2", "suppression"),
            ("src/app.ts:3", "test-dodge"),
            ("src/app.ts:4", "hook-bypass"),
            ("src/app.ts:5", "tls-bypass"),
            ("src/app.ts:6", "type-bypass"),
            ("src/app.ts:7", "error-swallow"),
            ("src/app.ts:8", "unsafe-html"),
            ("src/app.ts:9", "sync-hack"),
        }
        self.assertEqual(got, expected)
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(len(r) == 3 and len(r[2]) <= 160 for r in rows))
        self.assertIn("eslint-disable-next-line", rows[0][2])
        self.assertIn("scan: 8 candidate(s)", err)

    def test_scan_ignores_removed_context_and_always_exits_zero(self) -> None:
        code, out, err = scan((REVIEW / "mixed.diff").read_bytes())
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertIn("scan: 0 candidate(s)", err)
        for data in (b"", b"not a diff\n\xff\xfe garbage\n", b"@@ broken @@\n+x # noqa\n"):
            code, out, err = scan(data)
            self.assertEqual(code, 0)
            self.assertIn("scan: 0 candidate(s)", err)
        code, _, err = scan(b"", "--diff", str(REVIEW / "does-not-exist.diff"))
        self.assertEqual(code, 0)
        self.assertIn("scan: 0 candidate(s)", err)

    def test_scan_reads_diff_file_and_utf8(self) -> None:
        code, out, _ = scan(b"", "--diff", str(REVIEW / "categories.diff"))
        self.assertEqual(code, 0)
        self.assertEqual(len(out.splitlines()), 8)
        data = "+++ b/é.py\n@@ -1 +1 @@\n+x = 1  # noqa  ção\n".encode("utf-8")
        _, out, _ = scan(data)
        self.assertEqual(out, "é.py:1\tsuppression\tx = 1  # noqa  ção\n")


if __name__ == "__main__":
    unittest.main()
