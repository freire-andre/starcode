"""Fase pr-review do Worf (SC-198, R1 a R7)."""
from __future__ import annotations

import contextlib
import io
import re
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT
import handoff

CLIS = ("claude", "codex", "antigravity", "opencode")


def _roots() -> list[Path]:
    return [ROOT] + [ROOT / "dist" / cli for cli in CLIS]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _section(text: str, header: str) -> str:
    m = re.search(rf"^{re.escape(header)}.*?(?=^## |\Z)", text, re.S | re.M)
    assert m, header
    return m.group(0)


class PrReviewTests(unittest.TestCase):
    def test_fase_pr_review(self):
        # R1
        self.assertEqual(handoff.PHASES.index("pr-review"), handoff.PHASES.index("review") + 1)
        self.assertEqual(handoff.PHASES.index("done"), handoff.PHASES.index("pr-review") + 1)
        with tempfile.TemporaryDirectory(prefix="starcode-prr-") as tmp:
            root = Path(tmp)
            feat = root / ".specs" / "features" / "x"
            feat.mkdir(parents=True)
            (feat / "spec.md").write_text("# S\n", encoding="utf-8")

            def run(*args):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    return handoff.main([*args, "--root", str(root)])

            self.assertEqual(run("set", "x", "--phase", "pr-review"), 0)
            self.assertIn("**Phase:** pr-review\n", (feat / "spec.md").read_text(encoding="utf-8"))
            self.assertEqual(run("set", "x", "--phase", "pr-revisao"), 2)
            self.assertIn("**Phase:** pr-review\n", (feat / "spec.md").read_text(encoding="utf-8"))

    def test_execute_fase_pr_review(self):
        # R2
        for root in _roots():
            text = _read(root, "skills/engajar/references/execute.md")
            sec = _section(text, "## 5.")
            self.assertRegex(sec, r"\*\*Modes 3/4:\*\* right after the PR is open, `python \"P/scripts/handoff\.py\" set <slug> --phase pr-review`", root)
            self.assertRegex(sec, r"`--phase done` comes only after the merge, or after the\s+user's explicit refusal of the merge", root)
            self.assertRegex(sec, r"\*\*Modes 1/2 \(no PR\):\*\* right after the Guinan, `--phase done` and\s+`python \"P/scripts/crew_live\.py\" progress <slug> --phase done` \(100%\)", root)
            self.assertLess(sec.index("--phase pr-review"), sec.index("**Modes 1/2"))
            rev = _section(text, "## Review (Worf)")
            self.assertRegex(rev, r"`--phase done` is written only after the merge, or\s+after the user's explicit refusal of the merge", root)
            self.assertRegex(rev, r"Then, only when the last round leaves no `blocker` or `should-fix` open \(a finding the user sent to a\s+follow-up issue does not count as open\), the merge authorization is asked\s+\(`git-modes\.md`\)", root)
            self.assertRegex(rev, r"and right then \(modes 3/4 as well as 1/2\) run\s+`python \"P/scripts/crew_live\.py\" progress <slug> --phase done` \(100%\)", root)

    def test_execute_gates_apos_correcao_worf(self):
        # R3
        for root in _roots():
            rev = _section(_read(root, "skills/engajar/references/execute.md"), "## Review (Worf)")
            self.assertRegex(rev, r"After each LaForge fix is integrated, run `python \"P/scripts/gates/run_gates\.py\" proofs <slug>` and\s+`python \"P/scripts/gates/run_gates\.py\" done <slug>` on the new HEAD \*\*before\*\* the next Worf round", root)
            self.assertRegex(rev, r"After each round record `python \"P/scripts/handoff\.py\" set <slug> --report \"Worf r<N> <verdict>\"`", root)
            self.assertLess(rev.index("one LaForge dispatch"), rev.index('run_gates.py" proofs'))
            self.assertLess(rev.index('run_gates.py" done'), rev.index("--report"))

    def test_guinan_licoes_do_review(self):
        # R4
        for root in _roots():
            rev = _section(_read(root, "skills/engajar/references/execute.md"), "## Review (Worf)")
            self.assertRegex(rev, r"When the last Worf round ends \(APPROVE, or round 3\) and `review\.md` has a `blocker` or\s+`should-fix` finding fixed or confirmed in any round, the Picard invokes the Guinan in lessons-only mode", root)
            self.assertRegex(rev, r"records the `review_finding` lessons through `lessons\.py` and does not rewrite\s+`retro\.md`", root)
            self.assertRegex(rev, r"Without such a finding the Guinan is not invoked", root)
            self.assertRegex(rev, r"Before the merge is asked, commit on the PR branch `review\.md`,\s+`review\.json` and the lessons \(`\.specs/lessons\.json` and `\.specs/LESSONS\.md`\) with the message\s+`docs\(specs\): review e lições \(<slug>\)` and the `Refs` footer, and push with the user's confirmation\s+\(`git-modes\.md`\)", root)
            self.assertLess(rev.index("Without such a finding"), rev.index("docs(specs): review e lições"))
            self.assertLess(rev.index("docs(specs): review e lições"), rev.index("the merge authorization is asked"))
            sec = _section(_read(root, "skills/guinan/SKILL.md"), "## 1c. Lessons-only mode")
            self.assertRegex(sec, r"`review_finding` signal only, through `lessons\.py`", root)
            self.assertRegex(sec, r"Do not write or rewrite `retro\.md`", root)
            self.assertRegex(sec, r"Here a `blocker` or `should-fix` finding \*\*resolved \(fixed\) or confirmed\*\* in any round counts, an explicit\s+exception to the section 1 exclusion of what was not confirmed", root)

    def test_piloto_encerra_apos_worf(self):
        # R5
        for root in _roots():
            sec = _section(_read(root, "skills/piloto-automatico/SKILL.md"), "## 5b.")
            self.assertRegex(sec, r"\*\*stays on\*\* during the Worf rounds", root)
            self.assertRegex(sec, r"At\s+the merge authorization stop, after the last round and the Guinan's lessons, run\s+`piloto\.py encerrar <slug> --reason \"parada da autorização de merge\"`", root)
            self.assertLess(sec.index("stays on"), sec.index("piloto.py encerrar"))

    def test_state_format_pr_review(self):
        # R6
        for root in _roots():
            text = _read(root, "skills/engajar/references/state-format.md")
            self.assertRegex(text, r"(?m)^\*\*Phase:\*\* .*execute \| review \| pr-review \| done$", root)
            self.assertRegex(text, r"(?m)^\| PR open, Phase `pr-review` \| pr-review \| read `review\.md` \(round and verdict\); continue with the LaForge fix, or the next Worf round, or the merge authorization request; PR already merged \(per Git\) → write `--phase done` and `python \"P/scripts/crew_live\.py\" progress <slug> --phase done` \|$", root)

    def test_decisions_pr_review(self):
        # R7
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        start = text.index("### SC-198:")
        nxt = text.find("\n### ", start + 1)
        entry = text[start:nxt if nxt != -1 else len(text)]
        for field in ("- **Problema**", "- **Decisão**", "- **Motivo**", "- **Por que não é bug**"):
            self.assertIn(field, entry)
        decisao = next(ln for ln in entry.splitlines() if ln.startswith("- **Decisão"))
        for phrase in ("a F9-5 (mantida)", "`--phase pr-review`",
                       "`--phase done` só depois do merge ou da recusa explícita do merge pelo usuário",
                       "depois de cada correção do LaForge integrada",
                       "`run_gates.py proofs <slug>` e `run_gates.py done <slug>` no novo HEAD",
                       "`--report \"Worf r<N> <veredito>\"`", "modo só lições", "`review_finding`",
                       "não reescreve o `retro.md`", "`piloto.py encerrar`", "parada da autorização de merge",
                       "commit e push do `review.md`, do `review.json` e das lições antes do merge",
                       "issue de acompanhamento não conta como aberto"):
            self.assertIn(phrase, decisao, phrase)
        porque = next(ln for ln in entry.splitlines() if ln.startswith("- **Por que não é bug"))
        for name in ("test_fase_pr_review", "test_execute_fase_pr_review", "test_execute_gates_apos_correcao_worf",
                     "test_guinan_licoes_do_review", "test_piloto_encerra_apos_worf", "test_state_format_pr_review",
                     "test_decisions_pr_review"):
            self.assertIn(f"`{name}`", porque)
        cl = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        i = cl.index("## [Unreleased]")
        j = cl.find("\n## [", i + 1)
        unreleased = cl[i:j if j != -1 else len(cl)]
        self.assertTrue(any("(SC-198)" in ln and "`pr-review`" in ln and ln.startswith("- Fase `pr-review`")
                            for ln in unreleased.splitlines()))


if __name__ == "__main__":
    unittest.main()
