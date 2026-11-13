from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401  (sys.path)
import handoff


class HandoffReportDateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-handoff-date-")
        self.root = Path(self._tmp.name)
        feat = self.root / ".specs" / "features" / "dark-mode"
        feat.mkdir(parents=True)
        (feat / "spec.md").write_text("# S\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def values(self, **kw) -> dict[str, str]:
        return handoff.set_handoff("dark-mode", self.root, {}, today="2026-11-14", **kw)[1]

    def test_report_com_data_iso_nao_prefixa(self):
        self.assertEqual(self.values(report="2026-11-13: T1 ok")["reports"], "2026-11-13: T1 ok")
        got = self.values(report="2026-11-13T10:00Z: T1 ok")["reports"]
        self.assertEqual(got, "2026-11-13: T1 ok; 2026-11-13T10:00Z: T1 ok")

    def test_report_sem_data_prefixa_hoje(self):
        self.assertEqual(self.values(report="T1 em 2026-11-13")["reports"], "2026-11-14: T1 em 2026-11-13")

    def test_report_com_data_impossivel_prefixa_hoje(self):
        got = self.values(report="2026-99-99: inválida")["reports"]
        self.assertEqual(got, "2026-11-14: 2026-99-99: inválida")
        got = self.values(report="2026-02-30: inválida")["reports"]
        self.assertEqual(got, "2026-11-14: 2026-99-99: inválida; 2026-11-14: 2026-02-30: inválida")

    def test_settle_continua_prefixando(self):
        self.assertEqual(self.values(settle="2026-11-13: x")["settled"], "2026-11-14: 2026-11-13: x")
