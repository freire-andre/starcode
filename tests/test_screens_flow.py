"""Telas no fluxo da tripulação: Picard, Q, Spock e LaForge (R28 a R30)."""
from __future__ import annotations

import unittest

from helpers import ROOT

import dispatch

EXECUTE = (ROOT / "skills" / "engajar" / "references" / "execute.md").read_text(encoding="utf-8")
Q_SKILL = (ROOT / "skills" / "q" / "SKILL.md").read_text(encoding="utf-8")
SPOCK = (ROOT / "skills" / "spock" / "SKILL.md").read_text(encoding="utf-8")
TEMPLATE = (ROOT / "skills" / "spock" / "references" / "spec-template.md").read_text(encoding="utf-8")
LAFORGE = (ROOT / "skills" / "laforge" / "SKILL.md").read_text(encoding="utf-8")


class ScreensFlowTests(unittest.TestCase):
    def test_execute_despacha_juiz_de_telas(self):
        for marker in ("screens.py\" list <slug>", "dispatch.py\" screens-brief", "`screens` profile", "stack.json",
                       "never in the LaForge's family", "**Verifier**:", "`differs`", "--round 2",
                       "goes to the user"):
            self.assertIn(marker, EXECUTE)
        self.assertLess(EXECUTE.index("screens-brief"), EXECUTE.index("## 5. Post-Q cycle"))

    def test_q_aponta_juiz_separado(self):
        self.assertIn("screens-verify.md", Q_SKILL)
        self.assertIn("separate worker", Q_SKILL)

    def test_spock_regras_de_captura_sem_d25(self):
        self.assertNotIn("D25", SPOCK)
        self.assertNotIn("not verified automatically", SPOCK)
        for marker in ("captures/", "## Sources", "one requirement per screen", "character by character"):
            self.assertIn(marker, SPOCK)
        self.assertIn("![", TEMPLATE)
        self.assertIn("captures/", TEMPLATE)

    def test_laforge_foto_do_autor(self):
        for text in (LAFORGE, dispatch.WORKER_RULES):
            self.assertIn("screens.py", text)
            self.assertIn("captures/<nome>.running.png", text)
        self.assertIn("May change", LAFORGE)
        self.assertIn("capture", dispatch.WORKER_RULES)


if __name__ == "__main__":
    unittest.main()
