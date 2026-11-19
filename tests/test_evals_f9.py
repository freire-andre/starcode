"""F9 T11 (C36): evals de roteamento de worf, guinan e diagnostico (R33)."""
from __future__ import annotations

import unittest

from helpers import ROOT

SKILLS = ("worf", "guinan", "diagnostico")


class EvalsF9Tests(unittest.TestCase):
    def test_evals_f9_routing_cases(self):
        base = ROOT / "evals" / "routing"
        total = 0
        for skill in SKILLS:
            pos = sorted(p.name for p in base.glob(f"pos-{skill}-*") if (p / "case.yaml").is_file())
            neg = sorted(p.name for p in base.glob(f"neg-{skill}-*") if (p / "case.yaml").is_file())
            self.assertGreaterEqual(len(pos), 2, f"{skill}: positivos {pos}")
            self.assertGreaterEqual(len(neg), 1, f"{skill}: negativos {neg}")
            if skill == "worf":
                self.assertEqual(pos, ["pos-worf-review-pr", "pos-worf-security"])
                self.assertEqual(neg, ["neg-worf-fix-code", "neg-worf-generic-pr"])
            total += len(pos) + len(neg)
            for name in pos:
                text = (base / name / "case.yaml").read_text(encoding="utf-8")
                self.assertIn(f"starcode:{skill}", text, name)
                self.assertIn("min: 1", text, name)
            for name in neg:
                text = (base / name / "case.yaml").read_text(encoding="utf-8")
                self.assertIn(f"starcode:{skill}", text, name)
                self.assertIn("max: 0", text, name)
        self.assertEqual(total, 10)

    def test_evals_readme_lists_counts_and_cases(self):
        readme = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        cases = [p for p in (ROOT / "evals" / "routing").iterdir() if p.is_dir()]
        self.assertIn(f"{len(cases)} frases", readme)
        for skill in SKILLS:
            self.assertIn(f"`{skill}`", readme)
        self.assertIn("9 casos", readme)
        for name in ("pos-worf-review-pr", "pos-worf-security", "pos-guinan-lessons", "pos-guinan-retro",
                     "pos-diagnostico-harness", "pos-diagnostico-level", "neg-worf-fix-code",
                     "neg-guinan-review-pr", "neg-diagnostico-setup"):
            self.assertIn(name, readme)


if __name__ == "__main__":
    unittest.main()
