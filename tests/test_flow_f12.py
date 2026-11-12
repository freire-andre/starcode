from __future__ import annotations

import re
import unittest

from helpers import ROOT


def _execute() -> str:
    return (ROOT / "skills/engajar/references/execute.md").read_text(encoding="utf-8")


def _section(text: str, number: str) -> str:
    m = re.search(rf"^## {number}\. .*?(?=^## |\Z)", text, re.S | re.M)
    assert m, number
    return m.group(0)


class FlowF12Tests(unittest.TestCase):
    def test_execute_md_snapshot_antes_do_ticket(self):
        sec = _section(_execute(), "7")
        self.assertIn('snapshot.py" take <slug> <ticket>', sec)
        self.assertIn("handoff.py set --report", sec)
        self.assertRegex(sec, r"fails.*not\*\* dispatched")

    def test_execute_md_saida_b_restaura_snapshot(self):
        sec = _section(_execute(), "6")
        for frag in ('snapshot.py" restore <slug> <ticket>', "without `--yes`", "fora do ticket",
                     "yes for this", "`--yes`", "--breaker closed", "worker-stop"):
            self.assertIn(frag, sec)

    def test_execute_md_drop_no_done(self):
        sec = _section(_execute(), "7")
        self.assertRegex(sec, r"--phase done`, run `python \"<plugin-root>/scripts/snapshot\.py\" drop <slug>`")

    def test_mccoy_skill_raio_de_impacto(self):
        text = (ROOT / "skills/mccoy/SKILL.md").read_text(encoding="utf-8")
        self.assertIn('impact.py" select --diff <base>', text)
        self.assertIn("baseBranch", text)
        self.assertIn("rodar tudo", text)
        self.assertLess(text.index("impact.py"), text.index("gate", text.index("impact.py")) + 1)
        self.assertIn("verdict line in the report", text)
        self.assertIn("whole suite", text)
