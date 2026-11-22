from __future__ import annotations

import re
import unittest

from helpers import ROOT
from test_support import execute_text


def _execute() -> str:
    return execute_text()


def _section(text: str, number: str) -> str:
    m = re.search(rf"^## {number}\. .*?(?=^## |\Z)", text, re.S | re.M)
    assert m, number
    return m.group(0)


class FlowF12Tests(unittest.TestCase):
    def assertOrdem(self, text: str, *frags: str) -> None:
        pos = -1
        for frag in frags:
            self.assertIn(frag, text)
            nxt = text.find(frag, pos + 1)
            self.assertGreater(nxt, pos, f"fora de ordem: {frag!r}")
            pos = nxt

    def test_execute_md_snapshot_antes_do_ticket(self):
        sec = _section(_execute(), "7")
        self.assertOrdem(sec, 'snapshot.py" take <slug> <ticket>', "before every LaForge dispatch")
        self.assertRegex(sec, r"take <slug> <ticket>` before every LaForge dispatch and record\s+the printed line "
                              r"with `handoff\.py set --report`")
        self.assertRegex(sec, r"If `take` fails, the ticket is \*\*not\*\* dispatched")
        self.assertOrdem(sec, "handoff.py set --report", "If `take` fails")

    def test_execute_md_saida_b_restaura_snapshot(self):
        sec = _section(_execute(), "6")
        self.assertRegex(sec, r"If `\*\*Dispatched:\*\*`\s+is not closed, `worker-stop` first\.")
        self.assertRegex(sec, r"restore <slug> <ticket>`\s+\*\*without `--yes`\*\*")
        self.assertRegex(sec, r'the plan and the "fora do ticket" list')
        self.assertRegex(sec, r"ask for a yes for this\s+restore")
        self.assertRegex(sec, r"Only then run it again with `--yes` and record `--breaker closed`")
        self.assertOrdem(sec, "`worker-stop` first", 'snapshot.py" restore <slug> <ticket>', "without `--yes`",
                         '"fora do ticket" list', "ask for a yes for this", "run it again with `--yes`",
                         "record `--breaker closed`")

    def test_execute_md_drop_no_done(self):
        sec = _section(_execute(), "7")
        self.assertRegex(sec, r"--phase done`, run `python \"<plugin-root>/scripts/snapshot\.py\" drop <slug>`")
        self.assertRegex(sec, r"after `--phase done`, run")
        self.assertEqual(sec.count("snapshot.py\" drop"), 1)

    def test_mccoy_skill_raio_de_impacto(self):
        text = (ROOT / "skills/mccoy/SKILL.md").read_text(encoding="utf-8")
        sec = text[text.index("**Impact radius (R31).**"):]
        sec = sec[:sec.index("- **Only files in `May change`.**")]
        self.assertRegex(sec, r"After the regression test and the fix, run\s+`python \"<plugin-root>/scripts/impact\.py\" "
                              r"select --diff <base>` \(base = `baseBranch` of the config\)")
        self.assertRegex(sec, r"Run the tests it chooses \(the whole suite only when the verdict is `rodar tudo` or the selection fails\), "
                              r"before the ticket's\s+gate")
        self.assertRegex(sec, r"put the verdict line in the report")
        self.assertRegex(sec, r"The whole suite runs at the done gate \(`Run unit` of the spec\) and in CI")
        self.assertOrdem(sec, 'impact.py" select --diff <base>', "baseBranch", "the tests it chooses",
                         "whole suite only when the verdict is `rodar tudo`", "gate", "verdict line in the report",
                         "The whole suite runs at the done gate")
