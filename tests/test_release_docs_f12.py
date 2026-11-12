from __future__ import annotations

import re
import unittest

from helpers import ROOT


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


class ReleaseDocsF12Tests(unittest.TestCase):
    def test_build_leva_snapshot_e_impact(self):
        for cli in ("claude", "codex", "antigravity", "opencode"):
            for rel in ("scripts/snapshot.py", "scripts/impact.py", "briefs/q-verify.md"):
                self.assertTrue((ROOT / "dist" / cli / rel).is_file(), f"{cli}: {rel} ausente")

    def test_registros_fase_12(self):
        decisions = _read("DECISIONS.md")
        ids = re.findall(r"^### (F12-\d+):", decisions, flags=re.M)
        self.assertEqual(len(ids), len(set(ids)), "F12-n duplicada")
        self.assertIn("F12-7", ids)

        changelog = _read("CHANGELOG.md")
        section = re.split(r"^## ", changelog.split("## [Unreleased]", 1)[1], flags=re.M)[0]
        self.assertIn("snapshot", section)
        self.assertIn("raio de impacto", section)

        compat = _read("docs/compatibilidade.md").splitlines()
        self.assertTrue(any("napshot" in l and "modo 1" in l for l in compat), "linha do snapshot ausente")
        self.assertTrue(any("aio de impacto" in l for l in compat), "linha do raio de impacto ausente")

        plano = _read("PLANO_STARCODE.md")
        self.assertIn("refs/starcode/snapshots/<slug>/<ticket>", plano)


if __name__ == "__main__":
    unittest.main()
