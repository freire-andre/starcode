"""Content tests for the diagnostico skill and its crew declaration (R29, R30, R32)."""
from __future__ import annotations

import unittest
from pathlib import Path

from helpers import ROOT

CLIS = ("claude", "codex", "antigravity", "opencode")


def _roots() -> list[Path]:
    return [ROOT] + [ROOT / "dist" / cli for cli in CLIS]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _block(text: str, header: str) -> str:
    """Indented block under `header` (2-space key) in crew.yaml."""
    lines = text.splitlines()
    start = lines.index(header)
    out = []
    for ln in lines[start + 1:]:
        if ln.strip() and not ln.startswith("    "):
            break
        out.append(ln)
    return "\n".join(out)


class DiagnosticoSkillTests(unittest.TestCase):
    def test_diagnostico_skill_cost_approval(self):
        # R29
        for root in _roots():
            text = _read(root, "skills/diagnostico/SKILL.md")
            self.assertTrue(text.startswith("---\nname: diagnostico\n"), root)
            desc = text.split("---", 2)[1]
            for trigger in ("diagnóstico do harness", "nível L0–L4", "harness score"):
                self.assertIn(trigger, desc, f"{root}: {trigger}")
            self.assertIn('scripts/diagnostico.py" run', text)
            self.assertIn("at most **5 lines**", text)
            sec = text.split("## 2. Tracks B/C: cost approval (R29)", 1)[1].split("\n## ", 1)[0]
            self.assertLess(sec.index("estimate first"), sec.index("Only then ask"), root)
            for needle in ("claims.jsonl", "2 judges", "only for this run", "Never write it to any config",
                           "não executados (sem aprovação de custo)"):
                self.assertIn(needle, sec, f"{root}: {needle}")

    def test_diagnostico_judge_protocol(self):
        # R30
        for root in _roots():
            ref = _read(root, "skills/diagnostico/references/judge-prompts.md")
            for needle in ("Dois juízes independentes", "segundo juiz é cego", "model: <id>",
                           "model: <MODEL_ID>", "merge_agreement.py", "merge_usefulness.py", "slim_fanin.py",
                           "CC-BY-4.0", "Nunca aplique", "trap-key.json"):
                self.assertIn(needle, ref, f"{root}: {needle}")
            blind = ref.split("### Juiz 2 (B, cego)", 1)[1].split("```", 2)[1]
            self.assertIn("Do NOT read", blind)
            self.assertIn("05-redundancy-j1.md", blind)
            skill = _read(root, "skills/diagnostico/SKILL.md")
            sec = skill.split("## 4. Never (R30)", 1)[1]
            self.assertIn("report only", sec)
            self.assertIn("Never delete", sec)

    def test_crew_declares_diagnostico_skill(self):
        # R32
        text = _read(ROOT, "src/crew.yaml")
        block = _block(text, "  diagnostico:")
        self.assertIn("owner: laforge", block)
        self.assertIn("invocation: user", block)
        self.assertIn('release: "1.3"', block)
        self.assertGreater(text.index("  diagnostico:"), text.index("\nskills:"))

    def test_crew_worf_guinan_invocation_both(self):
        # R32
        text = _read(ROOT, "src/crew.yaml")
        for who in ("worf", "guinan"):
            self.assertIn("invocation: both", _block(text, f"  {who}:"), who)


if __name__ == "__main__":
    unittest.main()
