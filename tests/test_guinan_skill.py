"""Content tests for the Guinan skill (R21, R24)."""
from __future__ import annotations

import unittest
from pathlib import Path

from helpers import ROOT

CLIS = ("claude", "codex", "antigravity", "opencode")
SIGNALS = ("weak_test", "spec_precision_gap", "ac_gap", "spec_deviation", "gate_fail", "review_finding")
CATEGORIES = ("navigation", "automatic checks", "reviewer rules", "AGENTS/CLAUDE.md", "tool economy",
              "instructions without effect", "information access")


def _roots() -> list[Path]:
    return [ROOT] + [ROOT / "dist" / cli for cli in CLIS]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


class GuinanSkillTests(unittest.TestCase):
    def test_guinan_skill_signals_and_no_finding_no_lesson(self):
        # R21
        for root in _roots():
            text = _read(root, "skills/guinan/SKILL.md")
            ref = _read(root, "skills/guinan/references/lessons.md")
            self.assertTrue(text.startswith("---\nname: guinan\n"), root)
            desc = text.split("---", 2)[1]
            for trigger in ("Guinan, faça a retro", "retrospectiva da feature", "registre as lições"):
                self.assertIn(trigger, desc, root)
            self.assertIn("Not for reviewing a pull request", desc)
            for needle in ("verification.md", "proofs.md", "review.md", "lessons.py\" add",
                           "confirmed", "blocker", "should-fix", "crew_live.py", "PT-BR"):
                self.assertIn(needle, text, f"{root}: {needle}")
            for sig in SIGNALS:
                self.assertIn(sig, ref, f"{root}: {sig}")
            self.assertIn("review_finding", text)
            self.assertIn("no finding, no lesson", ref)
            self.assertIn("one lesson per finding", ref)
            self.assertIn("methodology", ref)
            if root != ROOT:
                self.assertNotIn("{{", text)

    def test_guinan_lista_licoes_e_reusa_id(self):
        # R9
        for root in _roots():
            text = _read(root, "skills/guinan/SKILL.md")
            sec = text.split("## 1. Lessons", 1)[1].split("\n## ", 1)[0]
            lines = sec.splitlines()
            lst = [i for i, l in enumerate(lines) if 'scripts/lessons.py" list --status all' in l]
            wr = [i for i, l in enumerate(lines) if 'scripts/lessons.py" add --feature' in l]
            self.assertEqual((len(lst), len(wr)), (1, 1), root)
            self.assertLess(lst[0], wr[0], root)
            rec = [i for i, l in enumerate(lines) if 'scripts/lessons.py" add --id L<n> --feature <slug> '
                   '--signal <signal> --source "<file:line or id>"' in l]
            self.assertEqual(len(rec), 1, root)
            self.assertLess(lst[0], rec[0], root)
            start = max(i for i, l in enumerate(lines[:rec[0] + 1]) if l[:2].strip().rstrip(".").isdigit())
            step = "\n".join(lines[start:rec[0] + 3])
            for needle in ("candidate", "confirmed", "recorrência", "same cause and same fix"):
                self.assertIn(needle, step, f"{root}: {needle}")

    def test_guinan_skill_retro_contract(self):
        # R24
        for root in _roots():
            text = _read(root, "skills/guinan/SKILL.md")
            ref = _read(root, "skills/guinan/references/retro.md")
            self.assertIn(".specs/features/<slug>/retro.md", text)
            self.assertIn("at most 7", text)
            self.assertIn("severity", text)
            for needle in ("category", "evidence", "proposed action", "never applied",
                           "never become a lesson on their own", "at most 5 lines", "3 top"):
                self.assertIn(needle, text, f"{root}: {needle}")
            for cat in CATEGORIES:
                self.assertIn(cat, ref, f"{root}: {cat}")
            self.assertIn("mattpocock/skills", ref)
            self.assertIn("MIT", ref)
            self.assertIn("never touch\n`.specs/STATE.md`", text)

    def test_guinan_routing_evals_exist(self):
        for name, skill_min in (("pos-guinan-retro", "min: 1"), ("pos-guinan-lessons", "min: 1"),
                                ("neg-guinan-review-pr", "max: 0")):
            case = _read(ROOT, f"evals/routing/{name}/case.yaml")
            self.assertIn("starcode:guinan", case)
            self.assertIn(skill_min, case)


if __name__ == "__main__":
    unittest.main()
