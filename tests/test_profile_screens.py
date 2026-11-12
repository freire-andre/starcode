from __future__ import annotations

import re
import unittest

from helpers import ROOT

import scaffold

TAURI = ROOT / "profiles" / "tauri"


class ProfileScreensTests(unittest.TestCase):
    def test_perfil_tauri_tem_screens(self):
        doc = scaffold.loads((TAURI / "profile.yaml").read_text(encoding="utf-8"))
        self.assertEqual(doc["screens"], {"serve": "npm run dev", "url": "http://localhost:5173"})
        vite = (TAURI / "template" / "vite.config.ts").read_text(encoding="utf-8")
        self.assertIn("port: 5173", vite)

    def test_template_tauri_mockipc_so_em_dev(self):
        src = TAURI / "template" / "src"
        main = (src / "main.ts").read_text(encoding="utf-8")
        mocks = (src / "dev-mocks.ts").read_text(encoding="utf-8")
        self.assertRegex(main, r"import\.meta\.env\.DEV\s*&&\s*!\(?\s*\"__TAURI_INTERNALS__\"\s+in\s+window")
        self.assertRegex(main, r"await import\(\"\./dev-mocks\"\)")
        self.assertNotRegex(main, r"(?m)^import .*dev-mocks")
        self.assertNotIn("@tauri-apps/api/mocks", main)
        self.assertRegex(mocks, r"import\(\"@tauri-apps/api/mocks\"\)")
        self.assertNotRegex(mocks, r"(?m)^import .*mocks")
        self.assertIn("greet", mocks)
        self.assertTrue((src / "dev-mocks.test.ts").is_file())
        self.assertIsNone(re.search(r"(?m)^import .*dev-mocks", main))


if __name__ == "__main__":
    unittest.main()
