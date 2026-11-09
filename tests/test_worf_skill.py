"""Content tests for the Worf skill and its references (R3, R11, R12, R13, R19)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from helpers import ROOT

CLIS = ("claude", "codex", "antigravity", "opencode")


def _roots() -> list[Path]:
    return [ROOT] + [ROOT / "dist" / cli for cli in CLIS]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


class WorfSkillTests(unittest.TestCase):
    def test_worf_skill_review_flow_order(self):
        # R11: the 6 steps in order, with the scan and gate commands
        for root in _roots():
            text = _read(root, "skills/worf/SKILL.md")
            self.assertTrue(text.startswith("---\nname: worf\n"), root)
            desc = text.split("---", 2)[1]
            for trigger in ("Worf, revise o PR", "review do PR", "revise esse PR"):
                self.assertIn(trigger, desc, f"{root}: {trigger}")
            self.assertIn("Not for fixing code", desc)
            marks = ["**Deterministic ladder.**", "**Bypass scan.**", "**External research.**",
                     "**Review.**", "**`review.json`.**", "**Gate.**"]
            pos = [text.index(m) for m in marks]
            self.assertEqual(pos, sorted(pos), root)
            for needle in ("`**Build**`/`**Run**`", "scaffold.py\" checks",
                           "git diff <base>...<head> | python \"<plugin-root>/scripts/review/scan_bypasses.py\"",
                           "resolve-library-id", "query-docs", "official documentation",
                           "review_gate.py\" <review.json>", "until it exits with 0",
                           "crew_live.py", "post_review.py", "nada para revisar: <alvo>",
                           "references/review-standards.md", "references/security-evidence.md",
                           "references/comment-voice.md"):
                self.assertIn(needle, text, f"{root}: {needle}")
            self.assertIn("confirm", text.split("**Publishing.**", 1)[1])

    def test_worf_skill_evidence_or_silence(self):
        # R12
        for root in _roots():
            text = _read(root, "skills/worf/SKILL.md")
            sec = text.split("## 2. Evidence or silence (R12)", 1)[1].split("\n## ", 1)[0]
            for needle in ("URL or a Context7 ID", "downgrade", "or remove it", "arquivo:linha",
                           "Not read, no finding"):
                self.assertIn(needle, sec, f"{root}: {needle}")

    def test_worf_skill_review_md_contract(self):
        # R13
        for root in _roots():
            text = _read(root, "skills/worf/SKILL.md")
            sec = text.split("## 3. review.md (R13)", 1)[1].split("\n## ", 1)[0]
            for needle in ("**Round**: <N>", "**Verdict**:", "**Reviewer**:", "## TL;DR",
                           "| ID | Severity | Where | Finding | Evidence | State |", "`W<n>`",
                           "Escada determinística", "Pesquisa"):
                self.assertIn(needle, sec, f"{root}: {needle}")

    def test_worf_review_standards_bypass_rule(self):
        # R3
        for root in _roots():
            text = _read(root, "skills/worf/references/review-standards.md")
            sec = text.split("## Bypasses (R3)", 1)[1].split("\n## ", 1)[0]
            self.assertRegex(sec, r"justificativa e link de issue.*aceita")
            for needle in ("candidata", "should-fix", "blocker", "`tls-bypass`", "`hook-bypass`"):
                self.assertIn(needle, sec, f"{root}: {needle}")
            self.assertIn("dist/", text)
            self.assertIn("3 rodadas", text)
            ev = _read(root, "skills/worf/references/security-evidence.md")
            for needle in ("Cloudflare", "MIT", "hardening", "needs-validation", "impacto demonstrado"):
                self.assertIn(needle, ev, f"{root}: {needle}")
            voice = _read(root, "skills/worf/references/comment-voice.md")
            self.assertRegex(voice, r"(?i)uma ideia por comentário")

    def test_worf_skill_never_merges(self):
        # R19
        for root in _roots():
            text = _read(root, "skills/worf/SKILL.md")
            sec = text.split("## 4. Never (R19)", 1)[1]
            for needle in ("Never approve a merge", "Never merge", "gh pr merge",
                           "Never edit any file other than `review.md` and `review.json`"):
                self.assertIn(needle, sec, f"{root}: {needle}")


if __name__ == "__main__":
    unittest.main()
