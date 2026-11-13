from __future__ import annotations

import re
import unittest

from helpers import ROOT

DOC = ROOT / "skills" / "engajar" / "references" / "execute.md"


def _sections() -> dict[str, str]:
    text = DOC.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^## ", text)
    return {p.split(" ", 1)[0]: p for p in parts[1:]}


class ExecuteDocStartSettle(unittest.TestCase):
    def test_execute_usa_start_e_settle(self):
        text = DOC.read_text(encoding="utf-8")
        secs = _sections()
        self.assertIn('dispatch.py" start', secs["2."])
        self.assertIn('dispatch.py" start', secs["2F."])
        self.assertIn('dispatch.py" settle', secs["2F."])
        self.assertIn('dispatch.py" settle', secs["3."])
        self.assertNotIn('--dispatched "<T>', text)
        self.assertNotIn("git merge --no-ff <ticket branch>", text)

    def test_execute_sem_worker_show_posicional(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertNotIn("worker-show <", text)
        self.assertNotIn("worker-read <", text)
        self.assertIn("worker-read --dispatch", text)

    def test_execute_diz_onde_ler_o_modelo(self):
        text = DOC.read_text(encoding="utf-8")
        text = " ".join(text.split())
        self.assertRegex(text, r"`model` field of the (`worker-start`|`worker-start --json`) receipt")


if __name__ == "__main__":
    unittest.main()
