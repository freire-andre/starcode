"""Template tauri com fim de linha LF (R32)."""
from __future__ import annotations

import unittest

from helpers import ROOT
from test_profile_ts_tauri import ProfileCase

TEMPLATE = ROOT / "profiles" / "tauri" / "template" / ".gitattributes"


class GitattributesTests(ProfileCase):
    def test_template_tauri_gitattributes_lf(self) -> None:
        self.assertTrue(TEMPLATE.is_file())
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("* text=auto eol=lf", text)
        for pattern in ("*.png", "*.ico", "*.icns"):
            self.assertRegex(text, rf"(?m)^{pattern.replace('*', r'\*')}\s+binary$")
        folder = self.ok("tauri", "meu-tauri")
        self.assertEqual((folder / ".gitattributes").read_bytes(), TEMPLATE.read_bytes())


if __name__ == "__main__":
    unittest.main()
